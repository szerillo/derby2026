#!/usr/bin/env node
/**
 * scrape_pool.js — Scrape NYRA Bets exacta probables matrix for the Derby R12
 * and emit data/derby_pool_payouts.json.
 *
 * Output schema (same as bundled in sim.html POOL_DATA):
 *   {
 *     "updated_at": "ISO8601",
 *     "race_id": 102081587,
 *     "field": [1, 2, ..., 22],          // post numbers in our 20-horse field
 *     "strengths": { "1": 0.149, ... },   // Plackett-Luce strengths derived from pool
 *     "exacta_payouts_dollar1": { "1-2": 285, ... },
 *     "ex_factor": 0.834,                 // calibrated 1 - effective takeout
 *     "tri_factor": 0.78,
 *     "super_factor": 0.75
 *   }
 *
 * Usage:
 *   npm install playwright
 *   npx playwright install chromium
 *   node scripts/scrape_pool.js
 */
const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

const RACE_URL = 'https://www.nyrabets.com/race?raceId=102081587';
const OUT_PATH = path.join(__dirname, '..', 'data', 'derby_pool_payouts.json');
const FIELD = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 14, 15, 16, 17, 18, 19, 21, 22];
const TRI_FACTOR = 0.78;
const SUPER_FACTOR = 0.75;

async function main() {
  const browser = await chromium.launch({ args: ['--no-sandbox'] });
  const ctx = await browser.newContext({ viewport: { width: 1500, height: 800 } });
  const page = await ctx.newPage();

  console.log('Navigating to', RACE_URL);
  await page.goto(RACE_URL, { waitUntil: 'domcontentloaded', timeout: 60000 });

  // Click "Toteboard" tab in the program iframe
  console.log('Waiting for program iframe...');
  await page.waitForTimeout(4000);

  // Click toteboard tab via coordinate (it's at ~1188, 112 in the original page)
  // Then Probables sub-tab
  await page.evaluate(() => {
    function clickTab(label) {
      // search for tab with given text in any iframe
      const allDocs = [document, ...Array.from(document.querySelectorAll('iframe')).map(f => { try { return f.contentDocument; } catch(e) { return null; } }).filter(Boolean)];
      for (const doc of allDocs) {
        const els = doc.querySelectorAll('a, span, div, li, button');
        for (const el of els) {
          if (el.innerText && el.innerText.trim() === label && el.offsetParent !== null) {
            el.click();
            return true;
          }
        }
      }
      return false;
    }
    if (!clickTab('Toteboard')) console.warn('Toteboard tab not found');
    setTimeout(() => clickTab('Probables'), 800);
  });

  // Wait for probables matrix to render
  console.log('Waiting for probables table...');
  await page.waitForTimeout(6000);

  // Extract matrix from DOM (across iframes)
  const matrix = await page.evaluate(() => {
    const allDocs = [document, ...Array.from(document.querySelectorAll('iframe')).map(f => { try { return f.contentDocument; } catch(e) { return null; } }).filter(Boolean)];
    for (const doc of allDocs) {
      const t = doc.querySelector('table.gep-probablesTable');
      if (t && t.rows.length >= 20) {
        const out = [];
        for (const row of t.rows) {
          const cells = [];
          for (const c of row.cells) cells.push(c.innerText.trim().replace(/,/g, ''));
          out.push(cells);
        }
        return out;
      }
    }
    return null;
  });

  await browser.close();

  if (!matrix) {
    throw new Error('Could not extract probables matrix from page');
  }

  console.log(`Matrix shape: ${matrix.length} x ${matrix[0].length}`);

  // Parse matrix into exacta payouts
  // Header row: ["$1 EX", "1", "2", ..., "24"]
  const header = matrix[0];
  const colPosts = header.slice(1).map(Number);
  const exacta = {};
  for (let r = 1; r < matrix.length; r++) {
    const row = matrix[r];
    const rowLabel = row[0].replace(/\s*WITH\s*$/, '').trim();
    const rowPost = Number(rowLabel);
    if (!Number.isFinite(rowPost)) continue;
    for (let c = 1; c < row.length; c++) {
      const colPost = colPosts[c - 1];
      if (rowPost === colPost) continue;
      const val = row[c].trim();
      if (val === '' || val === '0') continue;
      const n = Number(val);
      if (Number.isFinite(n) && n > 0) exacta[`${rowPost}-${colPost}`] = n;
    }
  }

  console.log(`Parsed ${Object.keys(exacta).length} exacta entries`);
  if (Object.keys(exacta).length < 100) {
    throw new Error('Suspiciously few exacta entries — page probably did not load matrix');
  }

  // Derive Plackett-Luce strengths
  const POOL_HORSES = [...new Set(Object.keys(exacta).flatMap(k => k.split('-').map(Number)))].sort((a, b) => a - b);

  // Implied probs (using 1/X interpretation)
  const probs = {};
  let totalP = 0;
  for (const [k, v] of Object.entries(exacta)) {
    const p = 1 / v;
    probs[k] = p;
    totalP += p;
  }
  // Normalize
  for (const k in probs) probs[k] /= totalP;

  // Marginal win prob = strength
  const strengthsFull = {};
  for (const h of POOL_HORSES) {
    strengthsFull[h] = 0;
    for (const b of POOL_HORSES) {
      if (b === h) continue;
      const k = `${h}-${b}`;
      if (probs[k]) strengthsFull[h] += probs[k];
    }
  }

  // Re-normalize to our 20-horse field
  const fieldStrength = {};
  let fieldSum = 0;
  for (const h of FIELD) {
    fieldStrength[h] = strengthsFull[h] || 0;
    fieldSum += fieldStrength[h];
  }
  for (const h of FIELD) fieldStrength[h] = fieldStrength[h] / fieldSum;

  // Calibrate exacta takeout factor (median over field pairs)
  const factors = [];
  for (const a of FIELD) {
    for (const b of FIELD) {
      if (a === b) continue;
      const ex = exacta[`${a}-${b}`];
      if (!ex) continue;
      const pl_p = (fieldStrength[a] * fieldStrength[b]) / (1 - fieldStrength[a]);
      factors.push(pl_p * ex);
    }
  }
  factors.sort((a, b) => a - b);
  const median = factors[Math.floor(factors.length / 2)];

  // Filter exacta to FIELD only (drop scratched 13, and AE 23/24 not in our field)
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
    strengths: Object.fromEntries(FIELD.map(h => [String(h), Number(fieldStrength[h].toFixed(4))])),
    exacta_payouts_dollar1: fieldExacta,
    ex_factor: Number(median.toFixed(4)),
    tri_factor: TRI_FACTOR,
    super_factor: SUPER_FACTOR,
  };

  fs.mkdirSync(path.dirname(OUT_PATH), { recursive: true });
  fs.writeFileSync(OUT_PATH, JSON.stringify(out));
  console.log(`Wrote ${OUT_PATH} — ex_factor=${out.ex_factor}, ${Object.keys(fieldExacta).length} pairs`);
}

main().catch(e => {
  console.error('FAIL:', e.message);
  process.exit(1);
});
