# Kentucky Derby 2026 Monte Carlo Widgets

Self-contained widgets for embedding in WordPress (or any CMS) via iframe. Powered by 10,000 Monte Carlo simulations of the 152nd Kentucky Derby.

By [@SeanZerillo](https://twitter.com/SeanZerillo)

## Live URLs

| Asset | URL |
|-------|-----|
| Index page | https://szerillo.github.io/derby2026/ |
| Data table widget | https://szerillo.github.io/derby2026/table.html |
| Race simulator widget | https://szerillo.github.io/derby2026/sim.html |

## Repo structure

```
.
├── index.html              landing page listing both widgets
├── table.html              embeddable data table (probabilities, fair odds, edges)
├── sim.html                embeddable race simulator (animation, calls, toteboard)
├── README.md               this file
├── METHODOLOGY.md           model overview (high level)
├── HOW_IT_WORKS.md         plain-English explainer
├── data/
│   ├── derby-data.json     canonical 20-horse field roster + saddle cloth palette
│   └── derby_sims.json     10,000 pre-computed sim results + per-horse stats
└── scripts/
    ├── derby_sim.py        Monte Carlo simulator
    └── build_table_widget.py  generator for table.html
```

## WordPress embed snippets

### Data table widget

Paste into a Custom HTML block:

```html
<iframe
  src="https://szerillo.github.io/derby2026/table.html"
  width="100%" height="940" frameborder="0"
  style="border:0; max-width:1200px; display:block; margin:0 auto;"
  loading="lazy"
  title="Kentucky Derby 2026 Monte Carlo Probabilities"
></iframe>
```

### Race simulator widget

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

See `HOW_IT_WORKS.md` for the plain-English version. Highlights:

- 10,000 Monte Carlo simulations of the 152nd Derby.
- Each horse rated on Beyer Speed Figures (best + avg), TimeformUS pace fingerprint, class, distance/surface fit, trainer quality, form trend, paired-figs flag, workout score, J/T at Churchill, EP tactical-speed bonus, and per-horse trip bonus.
- Pace shape sampled per sim: 75 percent fast, 22 percent honest, 3 percent slow (locked due to three confirmed senders inside).
- Probabilistic trip events model 20-horse Derby chaos: bad break, boxed in for inside stalkers, wide trip for outside posts, used-up clearing for outside speed on fast pace.
- Per-horse trip bonuses capture race-specific pace setup that the generic events miss.

See `METHODOLOGY.md` for the full overview.

## Updating the model

If you need to re-run with updated MLs, late scratches, or anecdotal-layer changes:

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

GitHub Pages redeploys in 30 to 60 seconds; iframe in WordPress refreshes automatically on next page load.

## Deployment notes

The repository is deployed to GitHub Pages from `main` branch / root folder. The widgets are static HTML, no build pipeline, no server, no API key required.

To embed a widget:
1. Copy the iframe snippet from the relevant section above.
2. Paste into a WordPress Custom HTML block.
3. Position the block where you want the widget to appear.

That's it. No additional WordPress plugins or theme modifications required.

## Credits

Model and data analysis: [@SeanZerillo](https://twitter.com/SeanZerillo)
