"""
Generates the Derby 2026 data-table widget as a self-contained HTML file
embeddable in a WordPress Custom HTML block.

Reads derby_sims.json and outputs derby_table_widget.html.
"""
import json

with open("derby_sims.json") as f:
    data = json.load(f)

horses = data["horses"]
meta = data["model_meta"]
race = data["race"]

# Sort by post position by default
horses_by_post = sorted(horses, key=lambda h: h["post"])

# Build the HTML
def edge_class(edge):
    if edge >= 0.20: return "edge-strong-pos"
    if edge >= 0.05: return "edge-pos"
    if edge >= -0.05: return "edge-neutral"
    if edge >= -0.20: return "edge-neg"
    return "edge-strong-neg"

def fmt_pct(p, decimals=1):
    return f"{p*100:.{decimals}f}%"

def fmt_edge(e):
    sign = "+" if e >= 0 else ""
    return f"{sign}{e*100:.1f}pp"

def fmt_fair_odds(h):
    """Fair odds: 1 decimal under 100-1, rounded integer over 100-1."""
    if h["win_prob"] <= 0:
        return "999-1"
    frac = (1 / h["win_prob"]) - 1
    if frac >= 100:
        return f"{int(round(frac))}-1"
    return f"{frac:.1f}-1"

def absolute_edge_pp(h):
    """Edge in percentage points (sim% − ML%) per user preference."""
    return h["win_prob"] - h["ml_prob_raw"]

def saddlecloth_html(h):
    tw = h["silk"]["tw"]
    nm = h["silk"]["nm"]
    return (f'<span class="saddle" style="background:{tw};color:{nm};">'
            f'{h["post"]}</span>')

def distribution_bar(h):
    """Horizontal stacked bar showing P(1st), P(2-3), P(4), P(5+)."""
    win = h["win_prob"]
    p_2_3 = h["board_prob"] - win
    p_4 = h["top4_prob"] - h["board_prob"]
    p_5 = h["super_prob"] - h["top4_prob"]
    p_rest = 1 - h["super_prob"]
    segs = [
        ("seg-win", win, f"Win {fmt_pct(win)}"),
        ("seg-board", p_2_3, f"2-3 {fmt_pct(p_2_3)}"),
        ("seg-top4", p_4, f"4th {fmt_pct(p_4)}"),
        ("seg-top5", p_5, f"5th {fmt_pct(p_5)}"),
        ("seg-rest", p_rest, f"6+ {fmt_pct(p_rest)}"),
    ]
    parts = []
    for cls, w, label in segs:
        if w > 0:
            parts.append(
                f'<span class="{cls}" style="width:{w*100:.1f}%;" '
                f'title="{label}"></span>'
            )
    return f'<div class="dist-bar">{"".join(parts)}</div>'

# Generate row HTML for each horse
def row_html(h):
    edge_pp = absolute_edge_pp(h)
    edge_cls = edge_class(edge_pp)
    sign = "+" if edge_pp >= 0 else ""
    edge_disp = f"{sign}{edge_pp*100:.1f}%"
    tfus_disp = f"{h['top_tfus']} TFUS" if h["top_tfus"] is not None else "no TFUS"
    return f'''<tr data-post="{h["post"]}" data-win="{h["win_prob"]}" data-edge="{edge_pp}">
  <td class="cell-post">{saddlecloth_html(h)}</td>
  <td class="cell-name">
    <div class="horse-name-row">
      <span class="horse-name">{h["name"]}</span>
      <span class="horse-ml">{h["ml"]} ML</span>
    </div>
    <div class="horse-meta">{h["style_label"]} · {h["best_beyer"]} BEY / {tfus_disp} · {h["jockey"]} / {h["trainer"]}</div>
  </td>
  <td class="cell-num cell-fair">{fmt_fair_odds(h)}</td>
  <td class="cell-edge {edge_cls}">{edge_disp}</td>
  <td class="cell-num cell-pct">{fmt_pct(h["win_prob"])}</td>
  <td class="cell-num">{fmt_pct(h["top4_prob"])}</td>
</tr>'''

rows_html = "\n".join(row_html(h) for h in horses_by_post)

# Top picks for the insight banner
sorted_by_win = sorted(horses, key=lambda h: -h["win_prob"])
top_pick = sorted_by_win[0]
sorted_by_edge = sorted(horses, key=lambda h: -absolute_edge_pp(h))
top_overlay = next(h for h in sorted_by_edge if h["post"] != top_pick["post"])
# Top fade = chalk-fade angle. Horse with biggest negative edge among single-digit ML horses,
# OR among horses with material sim chance (>3%) if no single-digit-ML underlay.
chalk = [h for h in horses if h["ml_dec"] <= 10 and absolute_edge_pp(h) < 0]
if chalk:
    top_underlay = min(chalk, key=lambda h: absolute_edge_pp(h))
else:
    contenders = [h for h in horses if h["win_prob"] >= 0.03]
    top_underlay = min(contenders, key=lambda h: absolute_edge_pp(h))

# Pace shape display
pace_obs = meta["pace_shape_observed"]
fast_pct = fmt_pct(pace_obs.get("fast", 0), 0)

html = f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<title>Kentucky Derby 2026 — Monte Carlo Probabilities</title>
<style>
:root {{
  --bg: #ffffff;
  --bg-muted: #f6f4f0;
  --text: #1a1a1a;
  --text-muted: #6b6b6b;
  --border: #e5e1d8;
  --accent: #8a1538;        /* Derby burgundy */
  --accent-dark: #5a0d24;
  --rose: #c9a0b1;
  --gold: #c8a951;
  --pos: #1d8348;
  --pos-soft: #d4f0dc;
  --neg: #b03030;
  --neg-soft: #f4d6d4;
  --neutral: #6b6b6b;
}}
.kd-widget {{
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
  color: var(--text);
  background: var(--bg);
  max-width: 1200px;
  margin: 0 auto;
  padding: 0;
  line-height: 1.4;
  font-size: 14px;
  box-sizing: border-box;
}}
.kd-widget *, .kd-widget *::before, .kd-widget *::after {{ box-sizing: border-box; }}
.kd-header {{
  position: relative;
  background: linear-gradient(135deg, var(--accent) 0%, var(--accent-dark) 100%);
  color: #fff;
  padding: 18px 22px;
  border-radius: 8px 8px 0 0;
  text-align: center;
}}
.kd-title {{
  font-size: 22px;
  font-weight: 700;
  margin: 0 0 4px;
  letter-spacing: 0.2px;
}}
.kd-subtitle {{
  font-size: 13px;
  opacity: 0.85;
  margin: 0;
}}
.kd-byline-header {{
  font-size: 12px;
  margin-top: 6px;
  opacity: 0.9;
}}
.kd-byline-header a {{
  color: #fff;
  text-decoration: none;
  font-weight: 600;
  border-bottom: 1px dotted rgba(255,255,255,0.5);
}}
.kd-byline-header a:hover {{ border-bottom-style: solid; }}
.kd-brand {{
  position: absolute;
  top: 14px;
  right: 18px;
  display: inline-flex;
  align-items: center;
  gap: 6px;
}}
.kd-brand-text {{
  font-weight: 900;
  font-size: 16px;
  letter-spacing: -0.3px;
  color: #fff;
}}
.kd-brand-check {{
  width: 18px;
  height: 18px;
  border-radius: 50%;
  background: #11c75c;
  display: inline-flex;
  align-items: center;
  justify-content: center;
}}
.kd-brand-check svg {{ width: 12px; height: 12px; }}
@media (max-width: 520px) {{
  .kd-brand {{ position: static; justify-content: center; margin-bottom: 8px; }}
  .kd-header {{ padding-top: 14px; }}
}}
.kd-controls {{
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px;
  padding: 10px 22px;
  border-bottom: 1px solid var(--border);
  background: var(--bg);
}}
.kd-controls span.label {{
  font-size: 12px;
  color: var(--text-muted);
  font-weight: 600;
}}
.kd-sort-btn {{
  background: var(--bg);
  border: 1px solid var(--border);
  border-radius: 4px;
  padding: 5px 10px;
  font-size: 12px;
  cursor: pointer;
  color: var(--text);
  font-family: inherit;
}}
.kd-sort-btn:hover {{ background: var(--bg-muted); }}
.kd-sort-btn.active {{
  background: var(--accent);
  border-color: var(--accent);
  color: #fff;
}}
.kd-table-wrap {{
  overflow-x: auto;
  -webkit-overflow-scrolling: touch;
}}
.kd-table {{
  width: 100%;
  border-collapse: collapse;
  font-size: 13px;
  min-width: 480px;
}}
.kd-table thead th {{
  background: var(--bg-muted);
  border-bottom: 2px solid var(--border);
  padding: 10px 8px;
  text-align: left;
  font-size: 11px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  color: var(--text-muted);
  white-space: nowrap;
}}
.kd-table thead th.tcenter {{ text-align: center; }}
.kd-table tbody td {{
  padding: 10px 8px;
  border-bottom: 1px solid var(--border);
  vertical-align: middle;
}}
.kd-table tbody tr:hover {{ background: var(--bg-muted); }}
.cell-post {{ width: 48px; text-align: center; }}
.saddle {{
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 32px; height: 32px;
  border-radius: 5px;
  font-weight: 800;
  font-size: 14px;
  border: 1px solid rgba(0,0,0,0.1);
  box-shadow: 0 1px 2px rgba(0,0,0,0.08);
}}
.cell-name {{ min-width: 180px; }}
.horse-name-row {{ display: flex; align-items: baseline; gap: 8px; }}
.horse-name {{ font-weight: 700; font-size: 14px; }}
.horse-ml {{ font-size: 11px; color: var(--text-muted); font-weight: 600; }}
.horse-meta {{ font-size: 11px; color: var(--text-muted); margin-top: 1px; }}
.cell-num {{ text-align: center; white-space: nowrap; }}
.cell-fair {{ font-weight: 600; }}
.cell-edge {{
  text-align: center;
  font-weight: 700;
  white-space: nowrap;
  font-variant-numeric: tabular-nums;
  border-radius: 4px;
}}
.edge-strong-pos {{ color: #0d5128; background: var(--pos-soft); }}
.edge-pos {{ color: var(--pos); }}
.edge-neutral {{ color: var(--neutral); }}
.edge-neg {{ color: var(--neg); }}
.edge-strong-neg {{ color: #6b1818; background: var(--neg-soft); }}
.cell-pct {{ font-weight: 600; }}
.cell-style {{
  font-size: 12px;
  color: var(--text-muted);
  white-space: nowrap;
}}
.kd-footer {{
  padding: 12px 22px;
  font-size: 11px;
  color: var(--text-muted);
  border-top: 1px solid var(--border);
  background: var(--bg-muted);
  border-radius: 0 0 8px 8px;
  line-height: 1.5;
}}
.kd-byline {{
  font-size: 12px;
  color: var(--text);
  margin-bottom: 6px;
  font-weight: 600;
}}
.kd-byline a {{
  color: var(--accent);
  text-decoration: none;
}}
.kd-byline a:hover {{ text-decoration: underline; }}
@media (max-width: 700px) {{
  .kd-title {{ font-size: 18px; }}
}}
</style>
</head>
<body>
<div class="kd-widget" id="kd-widget">
  <div class="kd-header">
    <div class="kd-brand">
      <span class="kd-brand-text">ACTION</span>
      <span class="kd-brand-check"><svg viewBox="0 0 14 14" xmlns="http://www.w3.org/2000/svg"><path d="M3 7.2 L6 10 L11 4" stroke="#fff" stroke-width="2.2" fill="none" stroke-linecap="round" stroke-linejoin="round"/></svg></span>
    </div>
    <div class="kd-title">152nd Kentucky Derby</div>
    <div class="kd-subtitle">10,000 simulations · {race["venue"]} · {race["distance"]}</div>
    <div class="kd-byline-header">By <a href="https://twitter.com/SeanZerillo" target="_blank" rel="noopener">@SeanZerillo</a></div>
  </div>
  <div class="kd-controls">
    <span class="label">Sort:</span>
    <button class="kd-sort-btn active" data-sort="win">Win %</button>
    <button class="kd-sort-btn" data-sort="post">Post</button>
    <button class="kd-sort-btn" data-sort="edge">Edge</button>
  </div>
  <div class="kd-table-wrap">
    <table class="kd-table">
      <thead>
        <tr>
          <th>Post</th>
          <th>Horse</th>
          <th class="tcenter">Fair</th>
          <th class="tcenter">Edge</th>
          <th class="tcenter">Win %</th>
          <th class="tcenter">Top 4 %</th>
        </tr>
      </thead>
      <tbody id="kd-table-body">
{rows_html}
      </tbody>
    </table>
  </div>
  <div class="kd-footer">
    BEY and TFUS values are highest lifetime figures (Beyer Speed Figure and TimeformUS Speed Figure, different scales). Edge is sim win % minus morning-line implied % in percentage points. Pace shape sampled per simulation; result reflects 75% fast / 22% honest / 3% slow probability based on field configuration.
  </div>
</div>
<script>
(function() {{
  var tbody = document.getElementById("kd-table-body");
  var btns = document.querySelectorAll(".kd-sort-btn");
  function sortBy(key) {{
    var rows = Array.prototype.slice.call(tbody.querySelectorAll("tr"));
    rows.sort(function(a, b) {{
      var av = parseFloat(a.dataset[key]);
      var bv = parseFloat(b.dataset[key]);
      if (key === "post") return av - bv;
      return bv - av;
    }});
    rows.forEach(function(r) {{ tbody.appendChild(r); }});
  }}
  btns.forEach(function(btn) {{
    btn.addEventListener("click", function() {{
      btns.forEach(function(b) {{ b.classList.remove("active"); }});
      btn.classList.add("active");
      sortBy(btn.dataset.sort);
    }});
  }});
  // Default sort: Win %
  sortBy("win");
}})();
</script>
</body>
</html>
'''

with open("derby_table_widget.html", "w") as f:
    f.write(html)

print(f"Generated derby_table_widget.html ({len(html):,} chars)")
print(f"Sorted by post; sortable by Win%, Edge")
print(f"Top picks: {top_pick['name']}, {top_overlay['name']}, fade {top_underlay['name']}")
