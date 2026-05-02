#!/usr/bin/env node
/**
 * scrape_pool.js — Fetch NYRA Bets exacta probables for the Derby R12 directly
 * from the GetProbables.ashx API and emit data/derby_pool_payouts.json.
 *
 * Pure Node, no Playwright, no headless browser. Uses built-in https module
 * so there are zero npm dependencies — runs in any Node 18+ environment.
 */
const https = require('https');
const fs = require('fs');
const path = require('path');

// Race-specific pool IDs for Derby 2026 R12 (captured from NYRA Bets DOM).
// If NYRA changes the IDs (rare), update them here.
const POOL_IDS = [115909273, 115909274, 115909275, 115909276, 115919053];
const API_URL = 'https://brk0201-iapi-webservice.nyrabets.com/GetProbables.ashx';
// Post 5 (Right to Party) scratched 4/30; AE3 Robusta drew in as post 23.
// Post 9 (The Puma) scratched 5/2 morning. Field is 19.
const FIELD = [1, 2, 3, 4, 6, 7, 8, 10, 11, 12, 14, 15, 16, 17, 18, 19, 21, 22, 23];
const TRI_FACTOR = 0.78;
const SUPER_FACTOR = 0.75;

const OUT_PATH = path.join(__dirname, '..', 'data', 'derby_pool_payouts.json');

const REQUEST_BODY = {
  header: {
    version: 2,
    fragmentLanguage: 'Javascript',
    fragmentVersion: '',
    clientIdentifier: 'nyra.1b',
  },
  wageringCohort: 'NBI',
  poolIds: POOL_IDS,
};

function postForm(urlStr, body) {
  return new Promise((resolve, reject) => {
    const u = new URL(urlStr);
    const req = https.request(
      {
        hostname: u.hostname,
        path: u.pathname + u.search,
        method: 'POST',
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
          'Content-Length': Buffer.byteLength(body),
          'User-Agent': 'derby2026-pool-scraper/1.0',
        },
      },
      (res) => {
        const chunks = [];
        res.on('data', (c) => chunks.push(c));
        res.on('end', () =>
          resolve({ status: res.statusCode, text: Buffer.concat(chunks).toString() })
        );
      }
    );
    req.on('error', reject);
    req.write(body);
    req.end();
  });
}

async function main() {
  console.log('Fetching probables from NYRA Bets API...');
  const formBody = 'request=' + encodeURIComponent(JSON.stringify(REQUEST_BODY));
  const r = await postForm(API_URL, formBody);
  if (r.status !== 200) throw new Error(`Bad status: ${r.status}`);
  const data = JSON.parse(r.text);
  console.log(`Got response with ${data.pools.length} pools`);

  const exPool = data.pools.find((p) => p.poolTypeCode === 'EX');
  if (!exPool) throw new Error('No EXACTA pool in response');
  console.log(`Exacta pool has ${exPool.probables.length} probables`);

  // Capture pool totals (always growing as bets come in — visual proof data is live)
  const poolTotals = {};
  for (const p of data.pools) {
    poolTotals[p.poolTypeCode] = {
      type: p.poolTypeName,
      gross: Math.round(p.currentTotalPoolGross?.amount || 0),
      net: Math.round(p.currentTotalPoolNet?.amount || 0),
      status: p.poolStatus,
    };
  }

  // Parse exacta probables: selection like "1,10" → key "1-10"
  const exacta = {};
  for (const p of exPool.probables) {
    if (!p.selection) continue;
    const parts = p.selection.split(',').map(Number);
    if (parts.length !== 2) continue;
    const [a, b] = parts;
    const payout = p.lowProbablePayout?.amount;
    if (a && b && Number.isFinite(payout) && payout > 0) {
      exacta[`${a}-${b}`] = payout;
    }
  }
  console.log(`Parsed ${Object.keys(exacta).length} exacta entries`);
  if (Object.keys(exacta).length < 100) {
    throw new Error('Suspiciously few exacta entries — pool may be empty or stale');
  }

  // Derive Plackett-Luce strengths from the full pool, then re-normalize to FIELD.
  const POOL_HORSES = [
    ...new Set(Object.keys(exacta).flatMap((k) => k.split('-').map(Number))),
  ].sort((a, b) => a - b);

  // Implied prob ≈ 1/X. Normalize to remove overround.
  const probs = {};
  let totalP = 0;
  for (const [k, v] of Object.entries(exacta)) {
    const p = 1 / v;
    probs[k] = p;
    totalP += p;
  }
  for (const k in probs) probs[k] /= totalP;

  // Marginal win prob per horse = sum of P(h, b) over b
  const strengthsFull = {};
  for (const h of POOL_HORSES) {
    strengthsFull[h] = 0;
    for (const b of POOL_HORSES) {
      if (b === h) continue;
      const k = `${h}-${b}`;
      if (probs[k]) strengthsFull[h] += probs[k];
    }
  }

  // Re-normalize to our 20-horse field (drop scratched 5/13/20, keep AE-drawn-in 21/22/23)
  const fieldStrength = {};
  let fieldSum = 0;
  for (const h of FIELD) {
    fieldStrength[h] = strengthsFull[h] || 0;
    fieldSum += fieldStrength[h];
  }
  if (fieldSum <= 0) throw new Error('Field strengths sum to zero');
  for (const h of FIELD) fieldStrength[h] = fieldStrength[h] / fieldSum;

  // Calibrate exacta takeout factor (median over field pairs)
  const factors = [];
  for (const a of FIELD) {
    for (const b of FIELD) {
      if (a === b) continue;
      const ex = exacta[`${a}-${b}`];
      if (!ex) continue;
      const plP = (fieldStrength[a] * fieldStrength[b]) / (1 - fieldStrength[a]);
      factors.push(plP * ex);
    }
  }
  factors.sort((a, b) => a - b);
  const median = factors[Math.floor(factors.length / 2)];

  // Filter exacta to FIELD only
  const fieldExacta = {};
  for (const a of FIELD) {
    for (const b of FIELD) {
      if (a === b) continue;
      const k = `${a}-${b}`;
      if (exacta[k]) fieldExacta[k] = exacta[k];
    }
  }

  const out = {
    updated_at: new Date().toISOString(),
    race_id: 102081587,
    field: FIELD,
    pool_totals: poolTotals,
    strengths: Object.fromEntries(FIELD.map((h) => [String(h), Number(fieldStrength[h].toFixed(4))])),
    exacta_payouts_dollar1: fieldExacta,
    ex_factor: Number(median.toFixed(4)),
    tri_factor: TRI_FACTOR,
    super_factor: SUPER_FACTOR,
  };

  fs.mkdirSync(path.dirname(OUT_PATH), { recursive: true });
  // Pretty-print so the workflow's "only timestamp changed" diff check works
  // (each top-level field on its own line — required for grep -v 'updated_at' to be meaningful).
  fs.writeFileSync(OUT_PATH, JSON.stringify(out, null, 2));
  console.log(
    `Wrote ${OUT_PATH}: ${Object.keys(fieldExacta).length} pairs, ex_factor=${out.ex_factor}`
  );
}

main().catch((e) => {
  console.error('FAIL:', e.message);
  console.error(e.stack);
  process.exit(1);
});
