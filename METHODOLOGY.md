# Kentucky Derby 2026 Monte Carlo Model

This is the public-facing methodology overview. It describes what the model considers and how it produces its output without exposing the specific coefficients or trip-event probabilities.

## Files in this repo

- `data/derby-data.json`: canonical 20-horse field roster plus saddle cloth palette.
- `scripts/derby_sim.py`: Monte Carlo simulator (model implementation).
- `data/derby_sims.json`: 10,000 pre-computed sims with per-horse stats and per-sim finish orders.
- `scripts/build_table_widget.py`: generator for `table.html`.
- `table.html`: embeddable data table widget.
- `sim.html`: embeddable race simulator widget.

## What goes into a horse's base ability score

Each horse gets a numeric ability score made from:

1. Beyer Speed Figures (best plus average), with best weighted more heavily because the Derby asks for top performance, not consistency.
2. TimeformUS pace fingerprint (early speed minus late speed). Closers get a boost on fast pace; pure speed types get hurt.
3. Class adjustment, scaled to the level of competition each horse has run against.
4. Distance and surface fit, scored 1 to 10 from pedigree commentary in DRF Closer Look bios.
5. Trainer quality, with Cox, Brown, Mott, Pletcher, and Baffert at the top tier.
6. Form trend (improving vs regressing), graded from analyst views.
7. Paired-figures flag, set when a horse has run two consecutive top-tier figures.
8. Workout score, calibrated against Mike Welsch's daily DRF clocker reports plus the handicapping podcast circuit.
9. Jockey/trainer strike rate at Churchill, sourced from each horse's PP J/T 2025-26 CD line.
10. EP tactical-speed bonus, applied to horses with the Derby's preferred profile historically.
11. Per-horse trip bonus, capturing race-specific pace setup (clean rail pocket, contested pace duel, etc.).

## What happens in each simulated run

For each of 10,000 simulations:

- A pace shape is sampled. The default split is 75 percent fast, 22 percent honest, 3 percent slow, reflecting the field configuration with three confirmed senders inside.
- A pace adjustment is applied based on each horse's pace fingerprint. The sign flips with the shape.
- Day-of form variance is added as random noise.
- Trip noise is added as additional residual variance.
- Probabilistic trip events fire based on post and style: bad break for any horse, boxed in for inside stalker types, wide trip for outside posts, and used-up clearing for outside speed when pace is fast.
- Each horse's total speed determines their finish position in that run.

After 10,000 runs, finish frequencies are counted, giving the win percent, board percent, and top 4 percent shown in the widgets.

## What is hand-encoded vs computed

Hand-encoded fields (Derby-specific, sourced from analyst material):
- Distance fit and surface fit (from Closer Look pedigree commentary).
- Workout score (from Welsch clocker reports plus podcasts).
- Form trend (from analyst views).
- Paired-figures flag (from Beyer trajectory tagging).
- Trainer quality (graded by Derby track record).
- Per-horse trip bonus (from analyst pace projection).
- Style classification (cross-validated against TFUS labels).

Computed fields:
- Base ability score (composite of the inputs above).
- Pace adjustment per sim.
- Trip events (probabilistic).
- Final finish order.
- Win percent, board percent, top 4 percent.
- Fair odds and edge against morning line.

## Output schema

`data/derby_sims.json` has the structure `{ race, model_meta, horses: [...], sims: [...] }`. Each horse entry includes post, name, ML, style, Beyer ranges, TFUS pace data, win probability, board probability, top 4 probability, fair odds, edge, and notes. The `sims` array contains all 10,000 finish orders.

## What the model does and doesn't do

What it does:
- Combines published speed figures with TFUS pace data per horse.
- Models 20-horse field chaos via probabilistic trip events tied to post, style, and pace shape.
- Captures Derby-specific pace setup via per-horse trip bonuses.
- Reflects clocker workout assessment.
- Reflects jockey-trainer recent Churchill performance.

What it doesn't do:
- General pedigree database lookups (distance and surface fit are hand-encoded from Closer Look bios, podcasts, and DRF analysis, not from a structured pedigree DB).
- Weather forecasts (race-day track condition assumes fast).
- Live odds tracking (uses morning line; closing odds will differ).
- Real-time scratches (manual update if any AE draws in).
- Equine biomechanics or veterinary signals.
- Crowd noise or paddock behavior.

See `HOW_IT_WORKS.md` for a plain-English version aimed at general readers.

## Reproducing the sim

```bash
cd scripts/
python3 derby_sim.py
```

Random seed is fixed in the simulator for reproducibility. To regenerate the table widget HTML:

```bash
python3 build_table_widget.py
```

## Decision log (high level)

- v1: Categorical pace adjustment plus Beyer composite plus class/dist/surface/trainer/form, with static post bias.
- v2: Continuous TFUS pace fingerprint. Workout score and J/T at CD components added.
- v3: Probabilistic trip events replaced deterministic post bias. EP tactical-speed bonus added.
- v3.5 to v3.8: Anecdotal layer integrated (Closer Look bios, Welsch clocker reports, podcast handicapping). Style reclassifications based on TFUS. Pace shape probability tuned to field configuration. Per-horse trip bonuses added.
- v3.10: Locked race-eve. International horses display "no published Beyer" in widget when applicable. Display labels finalized.

## Limitations

- TFUS data missing for international horses. Style defaults are reasonable proxies but coarser.
- Workout scores reflect human handicapping; multiple clockers might disagree.
- No explicit head-to-head adjustment from prep-race intersections (pace shape captures most of it).
- International horses carry uncertainty noise to reflect class transition.
- Trip-event rates are calibrated against historical post-position data, not regression on past 20-horse fields (sample too small).
- Per-horse trip bonuses are subjective handicapper reads of pace setup.
