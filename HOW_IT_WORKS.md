# How the Model Works (Plain English)

A reader-friendly explanation of what the Derby 2026 Monte Carlo model does, what's baked in, and what's not. Written for a general audience, not handicapping nerds.

## The big picture

The model runs the 152nd Kentucky Derby 10,000 times. Each run produces a finish order. The percentages you see in the widget (Win, Board, Top 4) are the count of times each horse finished in those positions across all 10,000 simulated races.

Each horse gets a base ability rating from a blend of speed figures, then each simulated race adds randomness for pace shape, trip trouble, and day-of form variance.

## What goes into a horse's base rating

Every horse has a numeric "ability" score made from:

1. Speed Figures (Beyer Speed Figures, best plus average) plus a continuous pace fingerprint from TimeformUS (early speed vs late speed). Best fig matters more, since the Derby asks for top performance.
2. Class adjustment for graded-stakes-level competition.
3. Distance and surface fit, scored 1 to 10.
4. Trainer quality and connection (top barns score highest).
5. Form trend (improving or regressing).
6. Paired figures flag (consistency at a high level).
7. Workout score (clocker assessment of training sharpness).
8. Jockey-trainer at Churchill (recent strike rate of this combo at this track).
9. EP tactical-speed bonus (Derby winners are disproportionately tactical types).
10. Trip bonus (race-specific pace setup tailwind or headwind).

## What happens in each simulated race

For each of 10,000 simulated runs:
- Pace shape is drawn at random. Most likely fast, occasionally honest, rarely slow.
- Pace adjustment fires: closers get a bump on fast pace, pure speed types get hurt.
- Form variance: random Gaussian noise reflecting day-of swings.
- Trip noise: small random adjustment for residual trip variance.
- Probabilistic trip events fire based on post position and running style (bad break for any horse, boxed in for inside stalker types, wide trip for outside posts, used-up clearing for outside speed on fast pace).

The horse's total speed in this run sets their finish in that simulation. Repeat 10,000 times, count the finishes. That gives you Win, Board, Top 4 percentages and the implied fair odds.

## What IS in the model

| Component | Source |
|-----------|--------|
| Beyer Speed Figures (best + avg) | DRF past performances |
| TimeformUS pace fingerprints | TimeformUS PPs |
| Workout sharpness | Mike Welsch DRF clocker reports plus handicapping podcasts |
| Form trend | Closer Look bios plus analyst views |
| Paired-figs flag | Hand-tagged from Beyer trajectory |
| Trainer quality | Hand-graded by Derby track record |
| J/T strike rate at Churchill | Each horse's PP J/T 2025-26 CD line |
| Distance fit | Hand-encoded from Closer Look pedigree commentary |
| Surface fit | Hand-encoded from race history |
| Pace setup trip bonus | Hand-encoded from analyst pace projection |

## What is NOT in the model

| Not modeled | Why not |
|-------------|---------|
| General pedigree database lookups | We don't run a stallion-by-stallion or dam-side database query. Distance fit comes from analyst commentary in DRF Closer Look plus podcast handicapping. For a regular race we wouldn't have this richness; for the Derby, every horse gets a pedigree write-up from multiple expert sources. |
| Weather and track condition | The model assumes a fast dirt track. If the forecast changes meaningfully, the entire pace dynamic shifts and the model would need a re-run with adjusted style behavior. |
| Live odds tracking | Uses morning-line as the published "market" reference. Closing odds will differ; bettors should expect more compressed prices on favorites. |
| Real-time scratches | If a horse scratches after the model runs, posts shift inside per Derby rules. The post-position-tied trip events would need to be re-pointed. Refresh after any scratch. |
| Crowd or paddock behavior | Not modeled. |
| Equine biomechanics or vet signals | Not modeled; we trust trainer/clocker reads instead. |
| Inter-horse head-to-head adjustments beyond pace | The pace shape captures most of this. We don't explicitly compute "Horse A beat Horse B by X lengths in their last common race." |

## Why the model is Derby-specific (not a general race model)

The Kentucky Derby is the most-handicapped race in North America. Every horse gets:
- A DRF Closer Look bio (~150 words of hand-handicapped analysis).
- TimeformUS PP commentary.
- DRF clocker reports (Mike Welsch and colleagues every morning of Derby week).
- Multiple handicapping podcasts (3+ hours of commentary across the field).
- Analyst pace projections.

The model leverages all of that human analysis and encodes it into the model fields. For a regular race that doesn't have this depth of expert coverage, we'd need either a structured pedigree database for distance/surface fit, a trip-trouble database for past races, or a regression model on prep races. We don't have those, so this model works well for the Derby specifically and would need to be substantially redesigned for other races.

## What you can trust this model to tell you

- Relative ranking of contenders: who the model thinks are the top 4, and roughly what win probability spread separates them.
- Where the market is over- or under-paying: the Edge column shows the gap between sim Win percent and morning-line implied percent. Big positive edges are overlay candidates; big negative edges are fade candidates.
- Position distributions: Win, Board, and Top 4 percentages give you a sense of how often each horse hits the money in different exotic structures.

## What the model is uncertain about

- Long-shot horses with thin race records (the international horses, the lightly-raced colts) get higher variance. Their numbers are more guess than known.
- The actual race-day track condition. If it rains, every assumption shifts.
- Late scratches. If the field changes, results need a re-run.

## Where to send questions

Author: [@SeanZerillo](https://twitter.com/SeanZerillo)
