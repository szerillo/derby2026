# Kentucky Derby 2026 Monte Carlo — Model Methodology

This document describes the simulation model that powers the Derby 2026 widgets. The model is implemented in `scripts/derby_sim.py` and outputs to `data/derby_sims.json` (consumed by widgets for win %, board %, top-4 %, fair odds, edge, position distributions).

## Files

- `data/derby-data.json` — canonical 20-horse field roster + saddle cloth palette
- `scripts/derby_sim.py` — Monte Carlo simulator (current version: v3.10)
- `data/derby_sims.json` — 10,000 pre-computed sims with per-horse stats and per-sim finish orders
- `scripts/build_table_widget.py` — generator for `table.html`
- `table.html` — embeddable data table widget (live)
- `sim.html` — embeddable race simulator widget (in progress)

## Model version: v3.10

This is the locked race-eve model. Decision log of every version below.

### Per-horse base rating

Composite figure score plus structural and tactical adjustments:

```
base = 0.55 * best_beyer + 0.25 * avg_beyer
     + 0.10 * (class - 88)
     + 0.70 * (dist_fit - 6)
     + 0.90 * (surface_fit - 7)
     + 0.40 * (trainer_q - 6)
     + 1.50 * form_trend                   (-2 to +2 scale)
     + 2.00 * paired_figs                  (1 if paired top figs in last 2 starts)
     + 0.50 * (workout_score - 5)          (1-10 scale; 5 = neutral)
     + 0.70 * jt_cd_score                  (Jockey/Trainer Churchill strike-rate score)
     + 2.50 * (style == "EP")              (Derby tactical-speed bonus)
     + trip_bonus                          (per-horse, captures pace setup; v3.8+)
```

Defensible because:
- Best Beyer carries more weight than average — Derby asks for top performance, not consistency
- Class is small (Beyers already reflect class implicitly)
- Distance/surface fit and trainer quality are pedigree- and connection-driven priors
- Paired figs reward consistency at a high level (Pletcher/Cox/Brown/Mott prep style)
- Workout score is the sharpness check; clocker context overrides published ranks
- J/T strike-rate at Churchill captures track-specific factor
- EP bonus reflects tactical types historically outperforming pure E and pure S in the Derby
- Trip bonus is the per-horse pace-setup tailwind/headwind (Renegade rail pocket, Further Ado clean stalking lane, Pavlovian pace duel, etc.)

### Per-sim variance

Each of the 10,000 sims:

```
shape       ~ {fast 75%, honest 22%, slow 3%}    # v3.8: 4/16/17 all sending = honest-fast lock
pace_adj    = (TFUS_L − TFUS_E) * 0.05           # sign flips with shape; honest = 0
form_var    ~ Normal(0, 7.5)                     # day-of variance
trip_noise  ~ Normal(0, 2.5)                     # residual trip variance
trip_evt    = sum of probabilistic trip events   # see below
unknown     ~ Normal(0, sigma)                   # for international horses with class uncertainty

speed = base + pace_adj + form_var + trip_noise + trip_evt + unknown
```

Sort descending → finish order.

### Pace fingerprint

Continuous TFUS pace fingerprint = TFUS_L − TFUS_E.

- High positive (e.g. Renegade +73, Commandment +65) = closer profile, gets boost on fast pace
- Negative (e.g. Pavlovian −12, Litmus Test −15) = pure speed, hurt on fast pace, helped on slow

For horses with no published TFUS, falls back to style-derived defaults:
- E: −40
- EP: −25
- P: 0
- S: +25
- DS: +50

### Probabilistic trip events

These replace v2's deterministic post-bias buckets. They model 20-horse Derby chaos.

| Event | Trigger | Probability | Hit |
|-------|---------|-------------|-----|
| Bad break | any horse | 5% | −10 to −18 ability |
| Boxed in | post 1-3, P style only | 6% | −4 to −8 ability |
| Wide trip | post 15-20, any style | 25% | −5 to −10 ability |
| Used up clearing | post 15+, E or EP, ONLY on fast pace | 30% | −6 to −12 ability |

Why these rules:
- **Inside post 1 not flat-penalized**: historical post-1 ITM% is 19.1% (close to 20-horse field baseline of 15%). A deep closer (S) from inside drops back to the rail and avoids front-quarter traffic, so they get NO inside penalty.
- **Pure speed (E) from inside posts not penalized**: they clear and rate.
- **Stalker/presser (P) from inside is the one who gets boxed**: stuck trying to maintain forward position in tight quarters.
- **Wide trip applies to all styles 15-20**: lots of ground to cover on the turn, real cost.
- **Speed from outside only penalized on fast pace**: "speed-to-the-outside" handicapping principle. If they clear and nobody presses, they often do well. Only the pace-pressure scenario kills them.

### Per-horse trip bonuses (v3.8+)

Layered on top of the probabilistic trip events to capture race-specific pace-setup reads that the generic events don't cover.

| Horse | Post | Trip bonus | Reason |
|-------|------|-----------|--------|
| Renegade | 1 | +1.5 | Clean rail pocket — adjacent posts (#2, #3, #5) lack speed, so he can stalk while saving ground |
| Litmus Test | 4 | −1.5 | Sending hard from inside into contested pace (16, 17 also sending) |
| Potente | 14 | +2.0 | Favorable mid-pack post to stalk contested pace |
| Pavlovian | 16 | −2.5 | Sandwiched between Six Speed (17) outside and Litmus Test (4) inside in pace duel |
| Further Ado | 18 | +2.5 | Quantified — avoids "used up clearing" trip event (~+2.0 EV on fast pace) plus structural advantage of having all speed inside him (+0.5) |
| Fulleffort | 20 | +0.5 | Deep closer profile benefits from 75% fast-pace lock |

### Style/tactical bonus rationale

EP horses get +2.5 ability across all sims:
- Tactical speed is the Derby's preferred profile historically
- They can win in different ways (set, stalk, close based on shape)
- Pace fingerprint already partially captures this; the structural Derby-fit bonus is still warranted

Pure E gets no flat bonus; only conditional outside-post penalty when fast pace fires.
Pure S gets no flat bonus; their pace-fingerprint boost on fast pace is their reward.

### International horses (no published Beyers)

Three horses (Danon Bourbon, Wonder Dean, Six Speed) come from Japan/UAE and have no Beyer Speed Figures published. The model uses estimated Beyer-equivalents for base-rating computation but flags `beyer_published: False` so the widget displays "—" rather than a fake number. For these horses the model also bumps `unknown_var` (Gaussian noise term) to reflect class-transition uncertainty.

TimeformUS Speed Figures are sometimes assigned by TFUS for international horses (Wonder Dean 107, Six Speed 103) and shown in the widget. Danon Bourbon has no TFUS either.

## Calibration anchors

### Beyer Speed Figures
Standard scale, par for the Derby field is 103. Top figs in this field:
- Further Ado 106 (Blue Grass)
- Commandment 101 (paired G1/G2)
- Chief Wallabee, So Happy, The Puma 100

### TimeformUS Speed Figures (Top Lifetime)
Different scale than Beyer. Top figs in field:
- Further Ado 121
- So Happy 120
- Potente 118
- Renegade 117
- Commandment 115, The Puma 115
- Litmus Test 114, Chief Wallabee 114
- Silent Tactic 113, Pavlovian 112, Intrepido 112
- Emerging Market 110, Fulleffort 110
- Golden Tempo 109
- Wonder Dean 107, Incredibolt 107
- Right to Party 104, Six Speed 103, Albus 101
- Danon Bourbon — (none)

### Pace fingerprints
From DRF PPs where published. 3 horses missing TFUS data fall back to style defaults (Danon Bourbon, Wonder Dean, Six Speed).

### Workout score scale
1-10 from clocker rank percentiles in last 5-6 works, **adjusted for clocker commentary**:
- DRF clocker reports (Mike Welsch) Apr 18-26
- DRF Closer Look bios per horse
- YouTube handicapping podcast notes (Mark, Ed, Kaitton, Ron)

### Jockey-trainer at Churchill score
J/T combo's recent CD strike-rate scaled to a −1.5 to +1.5 nudge. Sourced from each horse's PP J/T 2025-26 CD line.

## Output schema (data/derby_sims.json)

Top-level: `{ race, model_meta, horses: [...], sims: [...] }`. Each horse has `post`, `name`, `ml`, `ml_dec`, `style`, `style_label`, `best_beyer`, `avg_beyer`, `beyer_published`, `top_tfus`, `pace_fingerprint`, `workout_score`, `jt_cd_score`, `win_prob`, `board_prob`, `top4_prob`, `super_prob`, `pos_2_prob`, `pos_3_prob`, `pos_4_prob`, `fair_odds_dec`, `fair_odds_frac`, `edge`, `notes`. The `sims` array contains all 10,000 finish orders.

## Decision log (version history)

### v1
- Categorical 5-bucket pace adjustment (E/EP/P/S/DS)
- Beyer composite + class/dist/surface/trainer/form
- Static post-bias buckets (post 1 = -0.6, post 17+ = -0.6, etc.)

### v2
- Replaced 5-bucket pace with continuous TFUS_L − TFUS_E
- Added workout score and J/T at CD components

### v3
- Probabilistic trip events replace deterministic post bias
- Removed flat post-1 penalty (-0.6) and post-17+ penalty (-0.6)
- Removed mid-post tailwind (+0.3 for 5-13)
- Boxed-in event applies only to P style from inside posts
- Used-up-clearing only fires on fast pace (speed-to-the-outside principle)
- Added EP tactical-speed +2.5 bonus

### v3.5 (anecdotal layer integrated)
- ML odds updated to current published values
- Closer Look bios processed per horse → form_trend, paired_figs, workout_score adjustments
- Welsch clocker reports applied (Intrepido, Potente, Chief Wallabee, etc.)
- YouTube transcript reads applied (morning behavior, Mage comparison, etc.)
- Style reclassifications based on TFUS (So Happy P→EP, Pavlovian E→EP, Fulleffort P→S)
- Style labels updated to: Pace / Tactical / Presser / Closer / Deep Closer

### v3.7 (workout calibration)
- Final workout scores adjusted using full-week DRF clocker narrative
- Welsch's editorial tone given more weight than published rank percentiles

### v3.8 (pace setup + trip bonuses)
- Pace shape probability bumped to 75% fast / 22% honest / 3% slow (3 senders confirmed: Litmus Test, Pavlovian, Six Speed)
- Per-horse `trip_bonus` field added
- Further Ado +4.0 (later quantified to +2.5), Renegade +1.5, Potente +2.0, Pavlovian -2.5, Litmus Test -1.5, Fulleffort +0.5

### v3.10 (lock)
- Further Ado trip_bonus formalized: +2.5 = expected value of avoiding "used up clearing" trip event (~2.0) + structural stalking advantage (~0.5)
- `beyer_published` flag added; international horses display "—" in widget instead of estimated values
- Display labels finalized: Pace / Tactical / Presser / Closer / Deep Closer

## What the model does and doesn't do

**What it DOES:**
- Combines Beyer Speed Figures (best + average) with TFUS pace fingerprint per horse
- Models 20-horse field chaos via probabilistic trip events tied to post + style + pace shape
- Captures Derby-specific pace setup via per-horse trip bonuses
- Reflects clocker workout assessment (not just published ranks) via workout_score
- Reflects jockey-trainer recent Churchill performance via jt_cd_score

**What it DOESN'T do:**
- General pedigree database lookups (`dist_fit` and `surface_fit` are hand-encoded from Closer Look bios, podcasts, and DRF analysis — not from a structured pedigree DB)
- Weather forecasts (race-day track condition assumes "fast")
- Live odds tracking (uses morning-line; closing odds will differ)
- Real-time scratches (if a horse scratches, fields ≥ scratched post should shift inside per Derby rules; the model would need a re-run)
- Equine biomechanics or veterinary signals
- Crowd noise / paddock behavior

See `HOW_IT_WORKS.md` for a plain-English version of this for a general audience.

## Known limitations

- TFUS data missing for 3 horses; style defaults are reasonable proxies but coarser
- Workout scores are subjective — multiple clockers might disagree
- No explicit head-to-head adjustment from prep-race intersections (pace shape captures most of it)
- Foreign horses (Danon Bourbon, Wonder Dean, Six Speed) carry unknown_var Gaussian to reflect class transition uncertainty
- Trip-event rates are calibrated against historical post-position ITM data, not a regression on past 20-horse fields (sample too small)
- Per-horse trip bonuses are subjective — they reflect handicapper reads of pace setup

## Reproducing the sim

```bash
cd scripts/
python3 derby_sim.py
```

Random seed is 42 in `derby_sim.py` for reproducibility. Change seed if testing variance.

To regenerate the table widget HTML:
```bash
python3 build_table_widget.py
```
