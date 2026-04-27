# Kentucky Derby 2026 — Monte Carlo Widgets

Self-contained widgets for embedding in WordPress (or any CMS) via iframe. Powered by 10,000 Monte Carlo simulations of the 152nd Kentucky Derby.

## Repo structure

```
.
├── index.html              — landing page listing both widgets
├── table.html              — data table widget (model probabilities, fair odds, edges)
├── sim.html                — race simulator widget (TBD: animated race + toteboard)
├── data/
│   ├── derby-data.json     — canonical 20-horse field roster + saddle cloth palette
│   └── derby_sims.json     — 10,000 pre-computed sim results + per-horse stats
└── scripts/
    ├── derby_sim.py        — Monte Carlo simulator (regenerates derby_sims.json)
    └── build_table_widget.py — generator for table.html
```

## Local preview

Just open any `.html` file directly in a browser. They are fully self-contained — no build step or server required.

## Deploy to GitHub Pages

1. Create a new repo on GitHub (e.g. `derby2026`).
2. Initialize and push this directory:

   ```bash
   cd deploy/
   git init
   git add .
   git commit -m "Initial Derby 2026 widget bundle"
   git branch -M main
   git remote add origin git@github.com:YOUR_USERNAME/derby2026.git
   git push -u origin main
   ```

3. In GitHub repo settings, enable **Pages** with source branch `main`, folder `/ (root)`.
4. After ~1 min the widgets are live at:
   - `https://YOUR_USERNAME.github.io/derby2026/table.html`
   - `https://YOUR_USERNAME.github.io/derby2026/sim.html` (when added)

## WordPress embed

In a Custom HTML block, paste:

### Table widget

```html
<iframe
  src="https://YOUR_USERNAME.github.io/derby2026/table.html"
  width="100%"
  height="940"
  frameborder="0"
  style="border:0; max-width:1200px; display:block; margin:0 auto;"
  loading="lazy"
  title="Kentucky Derby 2026 Monte Carlo Probabilities"
></iframe>
```

Adjust `height` if your theme's content area changes the wrap behavior. 940px fits the 20-row table comfortably with header + footer.

### Sim widget (when ready)

```html
<iframe
  src="https://YOUR_USERNAME.github.io/derby2026/sim.html"
  width="100%"
  height="780"
  frameborder="0"
  style="border:0; max-width:1200px; display:block; margin:0 auto;"
  loading="lazy"
  title="Kentucky Derby 2026 Race Simulator"
></iframe>
```

## Updating the model

If you need to re-run with updated MLs or anecdotal layer changes:

```bash
cd scripts/
python3 derby_sim.py        # regenerates ../data/derby_sims.json
python3 build_table_widget.py   # regenerates ../table.html with new fair odds

git add -A
git commit -m "Update model"
git push
```

GitHub Pages will redeploy in 1-2 minutes; iframe in WordPress refreshes automatically on next page load.

## Model methodology

See `scripts/derby_sim.py` docstring for the full v3.10 model. Key features:
- Beyer composite (best 0.55, avg 0.25) + class/distance/surface/trainer/form/paired-figs/workout/J-T at CD
- Continuous TFUS pace fingerprint (L−E) per horse
- Probabilistic trip events (bad break, boxed in, wide trip, used-up clearing) gated by post + style + pace shape
- EP tactical-speed bonus (+2.5 ability)
- Per-horse trip bonuses for pace setup (Renegade rail pocket, Further Ado clean lane, Pavlovian/Litmus Test compromised)
- 75% fast / 22% honest / 3% slow pace shape probability based on field configuration

## Credits

Model + data analysis: [@SeanZerillo](https://twitter.com/SeanZerillo)
