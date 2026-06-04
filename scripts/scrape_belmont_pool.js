#!/usr/bin/env node
/**
 * scrape_belmont_pool.js — Fetch NYRA Bets exacta probables for Belmont Stakes R13
 * (Saratoga Saturday 6/6/2026) from the GetProbables.ashx API.
 * Emits data/belmont/belmont_pool_payouts.json in the same shape as the Derby file.
 *
 * Pure Node, no Playwright, no npm deps. Runs in any Node 18+.
 */
const https = require('https');
const fs = require('fs');
const path = require('path');

// Race-specific pool IDs for Belmont Stakes 2026 R13 at Saratoga
// (captured from NYRA Bets DOM 6/4/2026 — verified against /race?raceId=102099175)
// Order: WIN, PLACE, SHOW, EXACTA, TRIFECTA, SUPERFECTA
const POOL_IDS = [116080240, 116080241, 116080242, 116080243, 116080244, 116080246];
const RACE_ID = 102099175;
const API_URL = 'https://brk0201-iapi-webservice.nyrabets.com/GetProbables.ashx';
const FIELD = [1, 2, 3, 4, 5, 6, 7, 8, 9];
const TRI_FACTOR = 0.78;
const SUPER_FACTOR = 0.75;

const OUT_PATH = path.join(__dirname, '..', 'data', 'belmont', 'belmont_pool_payouts.json');

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
          'User-Agent': 'derby2026-belmont-pool-scraper/1.0',
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
  console.log('Fetching Belmont Stakes probables from NYRA Bets API...');
  const formBody = 'request=' + encodeURIComponent(JSON.stringify(REQUEST_BODY));
  const r = await postForm(API_URL, formBody);
  if (r.status !== 200) throw new Error(`Bad status: ${r.status}`);
  const data = JSON.parse(r.text);
  console.log(`Got response with ${data.pools.length} pools`);

  const exPool = data.pools.find((p) => p.poolTypeCode === 'EX');
  if (!exPool) throw new Error('No EXACTA pool in response');
  console.log(`Exacta pool has ${exPool.probables.length} probables`);

  // Pool totals — always growing as bets come in (visual proof data is live)
  const poolTotals = {};
  for (const p of data.pools) {
    poolTotals[p.poolTypeCode] = {
      type: p.poolTypeName,
      gross: Math.round(p.currentTotalPoolGross?.amount || 0),
      net: Math.round(p.currentTotalPoolNet?.amount || 0),
      status: p.poolStatus,
    };
  }

  // WIN pool gross per horse (shows where the money is going)
  const winPool = data.pools.find((p) => p.poolTypeCode === 'WN');
  const winGross = {};
  if (winPool) {
    for (const p of winPool.probables) {
      winGross[p.selection] = Math.round(p.totalPoolGross?.amount || 0);
    }
  }

  // Parse exacta probables: selection like "1,4" → key "1-4"
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
  if (Object.keys(exacta).length < 30) {
    throw new Error('Suspiciously few exacta entries — pool may be empty or stale');
  }

  // Derive Plackett-Luce strengths from the exacta pool
  const POOL_HORSES = [
    ...new Set(Object.keys(exacta).flatMap((k) => k.split('-').map(Number))),
  ].sort((a, b) => a - b);

  const probs = {};
  let totalP = 0;
  for (const [k, v] of Object.entries(exacta)) {
    const p = 1 / v;
    probs[k] = p;
    totalP += p;
  }
  for (const k in probs) probs[k] /= totalP;

  const strengthsFull = {};
  for (const h of POOL_HORSES) {
    strengthsFull[h] = 0;
    for (const b of POOL_HORSES) {
      if (b === h) continue;
      const k = `${h}-${b}`;
      if (probs[k]) strengthsFull[h] += probs[k];
    }
  }

  // Normalize to FIELD
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
    race_id: RACE_ID,
    field: FIELD,
    pool_totals: poolTotals,
    win_pool_gross: winGross,
    strengths: Object.fromEntries(FIELD.map((h) => [String(h), Number(fieldStrength[h].toFixed(4))])),
    exacta_payouts_dollar1: fieldExacta,
    ex_factor: Number(median.toFixed(4)),
    tri_factor: TRI_FACTOR,
    super_factor: SUPER_FACTOR,
  };

  fs.mkdirSync(path.dirname(OUT_PATH), { recursive: true });
  fs.writeFileSync(OUT_PATH, JSON.stringify(out, null, 2));
  console.log(
    `Wrote ${OUT_PATH}: ${Object.keys(fieldExacta).length} pairs, ex_factor=${out.ex_factor}, EX pool $${poolTotals.EX?.gross}`
  );
}

main().catch((e) => {
  console.error('FAIL:', e.message);
  console.error(e.stack);
  process.exit(1);
});
