# Kentucky Derby 2026 — Monte Carlo Widgets

Self-contained widgets for embedding in WordPress (or any CMS) via iframe. Powered by 10,000 Monte Carlo simulations of the 152nd Kentucky Derby. Model v3.10 (locked race-eve).

By [@SeanZerillo](https://twitter.com/SeanZerillo)

## Live URLs

| Asset | URL | Status |
|-------|-----|--------|
| Index page | https://szerillo.github.io/derby2026/ | Live |
| **Data table widget** | https://szerillo.github.io/derby2026/table.html | Live |
| Race simulator widget | https://szerillo.github.io/derby2026/sim.html | In progress |

## What's in this repo

```
.
├── index.html              — landing page listing both widgets
├── table.html              — embeddable data table (model probabilities, fair odds, edges)
├── sim.html                — embeddable race simulator (TBD: animated race + toteboard)
├── README.md               — this file (deployment, embed, update protocol)
├── METHODOLOGY.md          — full technical model spec (formulas, trip events, version history)
├── HOW_IT_WORKS.md         — plain-English explainer (what is/isn't in the model)
├── data/
│   ├── derby-data.json     — canonical 20-horse field roster + saddle cloth palette
│   └── derby_sims.json     — 10,000 pre-computed sim results + per-horse stats
└── scripts/
    ├── derby_sim.py        — Monte Carlo simulator (regenerates derby_sims.json)
    └── build_table_widget.py — generator for table.html
```

## WordPress embed snippets

### Data table widget (live)

In a Custom HTML block:

```html
<iframe
  src="https://szerillo.github.io/derby2026/table.html"
  width="100%" height="940" frameborder="0"
  style="border:0; max-width:1200px; display:block; margin:0 auto;"
  loading="lazy"
  title="Kentucky Derby 2026 Monte Carlo Probabilities"
></iframe>
```

Adjust `height` if your theme's content area changes the wrap behavior. 940px fits the 20-row table comfortably with header + footer.

### Race simulator widget (when ready)

```html
<iframe
  src="https://szerillo.github.io/derby2026/sim.html"
  width="100%" height="780" frameborder="0"
  style="border:0; max-width:1200px; display:block; margin:0 auto;"
  loading="lazy"
  title="Kentucky Derby 2026 Race Simulator"
></iframe>
```

## What the model does

See `HOW_IT_WORKS.md` for a plain-English explainer. Highlights:

- **10,000 Monte Carlo simulations** of the 152nd Derby
- Each horse rated on Beyer Speed Figures (best + avg), TimeformUS pace fingerprint, class, distance/surface fit, trainer quality, form trend, paired-figs flag, workout score, J/T at Churchill, EP tactical-speed bonus, and per-horse trip bonus
- **Pace shape sampled per sim**: 75% fast / 22% honest / 3% slow (locked due to 3 confirmed senders inside)
- **Probabilistic trip events** model 20-horse Derby chaos: bad break (5%), boxed in (6% for inside stalkers), wide trip (25% for outside posts), used-up clearing (30% for outside speed on fast pace)
- **Per-horse trip bonuses** capture race-specific pace setup that the generic events miss

See `METHODOLOGY.md` for the full math, decision log, and model version history.

## What's hand-encoded vs. computed

| Field | Source |
|-------|--------|
| `best_beyer`, `avg_beyer` | DRF past performances |
| `tfus_e`, `tfus_l` (pace fingerprint) | TimeformUS PPs |
| `top_tfus` | TimeformUS top lifetime fig |
| `workout_score` | Mike Welsch DRF clocker reports + handicapping podcasts (hand-graded) |
| `form_trend` | Closer Look bios + analyst views (hand-graded) |
| `paired_figs` | Hand-tagged from Beyer trajectory |
| `trainer_q` | Hand-graded by Derby track record |
| `dist_fit`, `surface_fit` | **Hand-encoded** from DRF Closer Look pedigree commentary (Derby-specific; we do not run a general pedigree DB query) |
| `trip_bonus` | Hand-encoded from analyst pace projection |
| `style` | Hand-classified, validated against TFUS labels |
| `ml`, `ml_dec` | Morning-line odds from official Derby program |

The model leverages the depth of hand-analysis available for the Derby (Closer Look bios, podcasts, clocker reports). For other races without this analyst coverage, this approach wouldn't transfer cleanly.

## Updating the model

If you need to re-run with updated MLs, late scratches, or rare anecdotal-layer changes:

```bash
cd scripts/
python3 derby_sim.py             # regenerates ../data/derby_sims.json
python3 build_table_widget.py    # regenerates ../table.html
```

Then push to GitHub:

```bash
git add -A
git commit -m "Update model"
git push
```

GitHub Pages redeploys in 30-60 seconds; iframe in WordPress refreshes automatically on next page load.

## Deployment notes (for editors)

The repository is already deployed to GitHub Pages from `main` branch / root folder. The widgets are static HTML — no build pipeline, no server, no API key required.

To embed a widget:
1. Copy the iframe snippet from the relevant section above
2. Paste into a WordPress Custom HTML block
3. Position the block where you want the widget to appear in the article

That's it. No additional WordPress plugins or theme modifications required.

## Changelog

| Date | Version | Change |
|------|---------|--------|
| Apr 27, 2026 | v3.10 lock | Model locked. Data table widget live. International horses display "—" for unpublished Beyers. |
| Apr 27, 2026 | — | Force light-mode rendering on table widget |
| Apr 27, 2026 | — | Updated METHODOLOGY.md and added HOW_IT_WORKS.md for editor / reader transparency |
| TBD | — | Race simulator widget (animated race + toteboard) |

## Credits

Model + data analysis: [@SeanZerillo](https://twitter.com/SeanZerillo)
