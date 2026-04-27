# How the Model Works (Plain English)

A reader-friendly explanation of what the Derby 2026 Monte Carlo model does, what's baked in, and what's NOT — written for a general audience, not handicapping nerds.

## The big picture

The model runs the 152nd Kentucky Derby **10,000 times**. Each run produces a finish order. The percentages you see in the widget (Win %, Board %, Top 4 %) are the count of times each horse finished in those positions across all 10,000 simulated races.

Each horse gets a **base ability rating** from a blend of speed figures, then each simulated race adds randomness for pace shape, trip trouble, and day-of-form variance.

## What goes into a horse's base rating

Every horse has a numeric "ability" score made from:

1. **Speed Figures** — Beyer Speed Figures (best lifetime + average) plus a continuous pace fingerprint from TimeformUS (early speed vs. late speed). The composite weights best-fig more than average — Derby asks for top performance, not consistency.
2. **Class** — small adjustment for graded-stakes-level competition each horse has run against.
3. **Distance and surface fit** — how well-suited each horse is to 1¼ miles on dirt, scored 1-10.
4. **Trainer quality and connection** — Pletcher/Cox/Brown/Mott/Baffert get the highest grades; less-experienced barns get lower.
5. **Form trend** — is the horse improving (+) or regressing (−)?
6. **Paired figures flag** — if the horse has run two consecutive top-tier figures, that's a meaningful consistency signal worth +2 ability points.
7. **Workout score** — clocker assessment of training sharpness, 1-10.
8. **Jockey-trainer at Churchill** — recent strike rate of this combo at this track.
9. **EP tactical-speed bonus** — Derby winners are disproportionately tactical types (can press, stalk, or close). +2.5 ability points if classified EP.
10. **Trip bonus** — race-specific pace setup tailwind/headwind (e.g., Renegade has all the speed inside him so he gets a clean rail pocket; Pavlovian is sandwiched in a pace duel).

## What happens in each simulated race

For each of 10,000 simulated runs:

- **Pace shape is drawn at random** — 75% fast, 22% honest, 3% slow. (Why fast-heavy? Three confirmed senders inside — Litmus Test, Pavlovian, Six Speed — make a contested fast pace nearly inevitable.)
- **Pace adjustment** — closers get a bump on fast pace; pure speed types get hurt.
- **Form variance** — random Gaussian noise reflecting day-of form swings.
- **Trip noise** — small random adjustment for residual trip variance.
- **Probabilistic trip events** fire based on post position and running style:
  - Bad break (5% any horse)
  - Boxed in (6% for stalker types from posts 1-3)
  - Wide trip (25% for any horse from posts 15-20)
  - "Used up clearing" (30% for outside speed on fast pace)

The horse's total speed in this run = base + pace adjustment + form noise + trip noise + any trip events that fired.

After 10,000 runs, count the finish frequencies. That gives you the win %, board %, top 4 %, and the implied fair odds.

## What IS in the model

| Component | Source |
|-----------|--------|
| Beyer Speed Figures (best + avg) | DRF past performances |
| TimeformUS pace fingerprints (E and L) | TimeformUS PPs |
| Workout sharpness | Mike Welsch DRF clocker reports (Apr 17–26) plus YouTube handicapping podcasts |
| Form trend | Closer Look bios + analyst views |
| Paired-figs flag | Hand-tagged from race-by-race Beyer trajectory |
| Trainer quality | Hand-graded based on Derby track record (Cox/Brown/Mott/Pletcher/Baffert top tier) |
| J/T strike rate at Churchill | Each horse's PP J/T 2025-26 CD line |
| Distance fit | Hand-encoded from Closer Look pedigree commentary |
| Surface fit | Hand-encoded from race history |
| Pace setup trip bonus | Hand-encoded from analyst pace projection |

## What is NOT in the model

| Not modeled | Why not |
|------------|---------|
| **General pedigree database lookups** | We don't run a stallion-by-stallion or dam-side database query. Distance fit comes from analyst commentary in DRF Closer Look + podcast handicapping (e.g., "ample stamina top and bottom" for a Curlin out of a Bernardini mare). For a general race we wouldn't have this richness — but for the Derby, every horse gets a pedigree write-up from multiple expert sources. |
| **Weather / track condition** | The model assumes a fast dirt track. If the forecast changes meaningfully, the entire pace dynamic shifts and the model would need a re-run with adjusted style behavior. |
| **Live odds tracking** | Uses morning-line as the published "market" reference. Closing odds will differ — bettors should expect more compressed prices on favorites. |
| **Real-time scratches** | If a horse scratches after the model runs, posts shift inside per Derby rules. The post-position-tied trip events would need re-pointed. The data table here is a frozen pre-race read; refresh after any scratch. |
| **Crowd / paddock behavior** | Not modeled. |
| **Equine biomechanics or vet signals** | Not modeled — we trust trainer/clocker reads instead. |
| **Inter-horse head-to-head adjustments beyond pace** | The pace shape captures most of this; we don't explicitly compute "Horse A beat Horse B by X lengths in their last common race." |

## Why the model is Derby-specific (not a general race model)

The Kentucky Derby is the most-handicapped race in North America. Every horse gets:
- A DRF Closer Look bio (~150 words of hand-handicapped analysis)
- TimeformUS PP commentary
- DRF clocker reports (Mike Welsch + colleagues every morning of Derby week)
- Multiple handicapping podcasts (3+ hours of commentary across the field)
- Analyst pace projections

The model leverages all of that human analysis and encodes it into the model fields (workout_score, dist_fit, paired_figs, etc.). For a regular race that doesn't have this depth of expert coverage, we'd need either:
- A structured pedigree database for distance/surface fit
- A trip-trouble database for past races
- A regression model on prep races

We don't have those. So this model works well for the Derby specifically and would need to be substantially redesigned for other races.

## What you can trust this model to tell you

- **Relative ranking of contenders** — who the model thinks are the top 4, and roughly what win probability spread separates them.
- **Where the market is over- or under-paying** — the "Edge" column shows the gap between sim win % and morning-line implied %. Big positive edges are overlay candidates (model thinks they're better than ML); big negative edges are fade candidates.
- **Position distributions** — Win %, Board %, and Top 4 % give you a sense of how often each horse hits the money in different exotic structures.

## What the model is uncertain about

- **Long-shot horses with thin race records** (the international horses, the lightly-raced colts) get higher variance in the model — their numbers are more guess than known.
- **The actual race-day track condition** — if it rains, every assumption shifts.
- **Late scratches** — if the field changes, results need a re-run.

## Where to send questions

Methodology details: see `METHODOLOGY.md` for the full math.
Author: [@SeanZerillo](https://twitter.com/SeanZerillo)
