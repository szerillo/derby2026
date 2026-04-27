"""
Kentucky Derby 2026 Monte Carlo Simulator — v3

v3 model changes vs v2:
  1. Probabilistic trip events replace deterministic post bias:
       a. Bad break:        5% any horse, -10 to -18 ability
       b. Boxed in inside:  6% for P only from posts 1-3, -4 to -8
                            (S deep closers drop back to the rail; E clears)
       c. Wide trip out:    25% for any style from posts 15-20, -5 to -10
       d. Used up clearing: 30% E/EP from posts 15+, ONLY on fast pace, -6 to -12
     Inside post 1 is no longer flat-penalized; deep closers from inside get
     no inside-post penalty at all (they drop back to the rail and don't
     contend with front-quarter traffic).
     Outside speed is only penalized when there is actual pace pressure.
  2. Tactical-speed bonus:  EP style +2.5 ability (Derby's preferred profile;
     horses who can set, stalk, or close based on shape).
  3. Removed fixed mid-post tailwind (+0.3 for posts 5-13).

v2 carryovers:
  - Continuous TFUS_L−TFUS_E pace fingerprint
  - Workout sharpness score
  - J/T Churchill Downs strike-rate

Per-horse base rating:
  base = 0.55 * best_beyer + 0.25 * avg_beyer
       + 0.10 * (class - 88)
       + 0.70 * (dist_fit - 6)
       + 0.90 * (surface_fit - 7)
       + 0.40 * (trainer_q - 6)
       + 1.50 * form_trend
       + 2.00 * paired_figs
       + 0.50 * (workout_score - 5)
       + 0.70 * jt_cd_score
       + 2.50 * (style == EP)

Per-sim:
  pace_shape sampled from {fast 65%, honest 30%, slow 5%}
  pace_adj   = fingerprint * 0.05 (sign flips with shape)
  form_var   ~ Normal(0, 7.5)
  trip_noise ~ Normal(0, 2.5)
  trip_evt   = sum of probabilistic trip events (see above)
  unknown    ~ Normal(0, sigma) for horses with class uncertainty

Speed_i = base + pace_adj + form_var + trip_noise + trip_evt + unknown
Sort descending → finish order. 10,000 sims.
"""
import json, random
from collections import Counter

random.seed(42)

RACE = {
    "name": "Kentucky Derby",
    "year": 2026,
    "venue": "Churchill Downs",
    "distance": "1 1/4 miles",
    "surface": "dirt",
    "beyer_par": 103
}

# Pace-fingerprint defaults for horses without published TFUS L-E
# Calibrated so the multiplier 0.05 produces magnitudes similar to v1 categorical
STYLE_DEFAULT_PACE_FP = {"E": -40, "EP": -25, "P": 0, "S": 25, "DS": 50}
PACE_MULTIPLIER = 0.05

HORSES = [
    {"post":1,"name":"Renegade","ml":"4-1","ml_dec":4,"trainer":"Pletcher","jockey":"Ortiz I Jr",
     "silk":{"tw":"#E11A1A","nm":"#FFFFFF"},"style":"S",
     "best_beyer":98,"avg_beyer":92,"tfus_e":60,"tfus_l":133,
     "class":100,"dist_fit":8,"surface_fit":9,"trainer_q":10,"form_trend":2,"unknown_var":0,"paired_figs":1,
     "workout_score":5.5,"jt_cd_score":1.5,"trip_bonus":1.5,
     "notes":"Clean rail pocket trip (#2 not quick, #3-4 may send, #5 not quick) to stalk while saving ground; Welsch 'not flashy but exactly what you want'; powered home in last pair; Pletcher 2x Derby winner"},
    {"post":2,"name":"Albus","ml":"30-1","ml_dec":30,"trainer":"R Mott","jockey":"Franco",
     "silk":{"tw":"#FFFFFF","nm":"#000000"},"style":"EP",
     "best_beyer":84,"avg_beyer":82,"tfus_e":100,"tfus_l":74,
     "class":92,"dist_fit":5,"surface_fit":9,"trainer_q":7,"form_trend":2,"unknown_var":0,"paired_figs":0,
     "workout_score":5.5,"jt_cd_score":0,
     "notes":"G2 Wood winner from well back, tactical speed shown; needs hefty Beyer jump (84 vs par 103); back better after break"},
    {"post":3,"name":"Intrepido","ml":"50-1","ml_dec":50,"trainer":"Mullins","jockey":"Berrios",
     "silk":{"tw":"#1B4FB0","nm":"#FFFFFF"},"style":"P",
     "best_beyer":89,"avg_beyer":85,"tfus_e":87,"tfus_l":99,
     "class":92,"dist_fit":6,"surface_fit":9,"trainer_q":6,"form_trend":-1,"unknown_var":0,"paired_figs":0,
     "workout_score":7.5,"jt_cd_score":0,
     "notes":"Welsch 4/26 'even quicker than Potente, honing speed for Derby Day'; Kaitton conflicting read no spark in mornings; 3yo figs on par with 2yo (regression risk)"},
    {"post":4,"name":"Litmus Test","ml":"50-1","ml_dec":50,"trainer":"Baffert","jockey":"Garcia M",
     "silk":{"tw":"#F4DA15","nm":"#000000"},"style":"E",
     "best_beyer":96,"avg_beyer":90,"tfus_e":111,"tfus_l":96,
     "class":92,"dist_fit":6,"surface_fit":9,"trainer_q":10,"form_trend":-1,"unknown_var":0,"paired_figs":0,
     "workout_score":7.0,"jt_cd_score":0,"trip_bonus":-1.5,
     "notes":"Welsch 4/23 serious gate work, Bob very pleased; sending hard from post 4 into contested pace (16/17 also sending); blinkers reapplied; last 11 blinkers-on best finish 4th"},
    {"post":5,"name":"Right to Party","ml":"30-1","ml_dec":30,"trainer":"McPeek","jockey":"Elliott",
     "silk":{"tw":"#1F8A3A","nm":"#FFFFFF"},"style":"S",
     "best_beyer":81,"avg_beyer":78,"tfus_e":70,"tfus_l":108,
     "class":86,"dist_fit":7,"surface_fit":9,"trainer_q":7,"form_trend":1,"unknown_var":0,"paired_figs":0,
     "workout_score":5.0,"jt_cd_score":0,
     "notes":"Welsch 'just okay' on 4/18, 'asked more than company' on 4/25 final; lack of speed compounds Wood-style trip; McPeek won 2024 with Mystik Dan"},
    {"post":6,"name":"Commandment","ml":"6-1","ml_dec":6,"trainer":"Cox","jockey":"Saez",
     "silk":{"tw":"#000000","nm":"#FFD400"},"style":"P",
     "best_beyer":101,"avg_beyer":95,"tfus_e":67,"tfus_l":132,
     "class":100,"dist_fit":8,"surface_fit":9,"trainer_q":10,"form_trend":2,"unknown_var":0,"paired_figs":1,
     "workout_score":6.5,"jt_cd_score":0.8,
     "notes":"4-of-5 winner with 2 triple-digit Beyers; won close decisions in last 2 (guts); Into Mischief sire produced 3 Derby winners; Cox won 2021 Mandaloun"},
    {"post":7,"name":"Danon Bourbon","ml":"20-1","ml_dec":20,"trainer":"Ikezoe (Jpn)","jockey":"Nishimura",
     "silk":{"tw":"#F26B1F","nm":"#000000"},"style":"P",
     "best_beyer":88,"avg_beyer":84,"tfus_e":None,"tfus_l":None,
     "class":92,"dist_fit":7,"surface_fit":6,"trainer_q":6,"form_trend":2,"unknown_var":9,"paired_figs":0,
     "workout_score":4.5,"jt_cd_score":0,
     "notes":"Kaitton: bolted twice badly, reluctant to train forward on backstretch — major red flag; Japan unbeaten 3/3 but no Beyers; yet to race counter-clockwise; Forever Young is the bench mark"},
    {"post":8,"name":"So Happy","ml":"15-1","ml_dec":15,"trainer":"Glatt","jockey":"Smith M E",
     "silk":{"tw":"#FFADC8","nm":"#000000"},"style":"EP",
     "best_beyer":100,"avg_beyer":95,"tfus_e":107,"tfus_l":80,
     "class":100,"dist_fit":7,"surface_fit":9,"trainer_q":7,"form_trend":2,"unknown_var":0,"paired_figs":0,
     "workout_score":7.0,"jt_cd_score":0,
     "notes":"Welsch openly underwhelmed: 'lazy in mornings, not particularly impressive by Derby standards'; TFUS Power Pick; SA Derby winner; Mike Smith aboard; daddy won this race"},
    {"post":9,"name":"The Puma","ml":"10-1","ml_dec":10,"trainer":"Delgado","jockey":"Castellano",
     "silk":{"tw":"#1FD9E8","nm":"#000000"},"style":"P",
     "best_beyer":100,"avg_beyer":96,"tfus_e":91,"tfus_l":104,
     "class":95,"dist_fit":8,"surface_fit":9,"trainer_q":6,"form_trend":2,"unknown_var":0,"paired_figs":1,
     "workout_score":7.0,"jt_cd_score":0,
     "notes":"Welsch: 4/18 GP work was super, 'reminiscent of how Delgado brought Mage'; Mage-style steady gallops not sharp finals; in Mage's Barn 42 stall; paired top Beyers 100/100"},
    {"post":10,"name":"Wonder Dean","ml":"30-1","ml_dec":30,"trainer":"Takayanagi (Jpn)","jockey":"Sakai",
     "silk":{"tw":"#7B1FA2","nm":"#FFFFFF"},"style":"P",
     "best_beyer":97,"avg_beyer":90,"tfus_e":None,"tfus_l":None,
     "class":92,"dist_fit":7,"surface_fit":7,"trainer_q":6,"form_trend":1,"unknown_var":5,"paired_figs":0,
     "workout_score":6.0,"jt_cd_score":0,
     "notes":"Welsch: 'still not doing all that much', 4/25 6f drill effectively a 5f, broke slow, soft; UAE Derby G2 winner Timeform 107; counter-clockwise concern"},
    {"post":11,"name":"Incredibolt","ml":"20-1","ml_dec":20,"trainer":"R Mott","jockey":"Torres J A",
     "silk":{"tw":"#9E9E9E","nm":"#E11A1A"},"style":"P",
     "best_beyer":88,"avg_beyer":85,"tfus_e":93,"tfus_l":93,
     "class":82,"dist_fit":6,"surface_fit":9,"trainer_q":7,"form_trend":1,"unknown_var":0,"paired_figs":0,
     "workout_score":8.0,"jt_cd_score":0,
     "notes":"Welsch: particularly impressive first impression since returning to CD; VA Derby winner; 2-for-2 at CD; no Beyers cracking 90 still a ceiling concern"},
    {"post":12,"name":"Chief Wallabee","ml":"8-1","ml_dec":8,"trainer":"W Mott","jockey":"Alvarado",
     "silk":{"tw":"#B6E04C","nm":"#000000"},"style":"P",
     "best_beyer":100,"avg_beyer":96,"tfus_e":98,"tfus_l":104,
     "class":97,"dist_fit":8,"surface_fit":9,"trainer_q":9,"form_trend":2,"unknown_var":0,"paired_figs":1,
     "workout_score":9.0,"jt_cd_score":1.5,
     "notes":"Welsch most enthused horse all week: 'reminds me going back to Sovereignty last year'; 4/20 stunner work in blinkers, 4/26 maintenance with totally in hand; FL Derby loss was focus not ability"},
    {"post":13,"name":"Silent Tactic","ml":"20-1","ml_dec":20,"trainer":"Casse","jockey":"Torres C A",
     "silk":{"tw":"#4A2C1A","nm":"#FFFFFF"},"style":"S",
     "best_beyer":91,"avg_beyer":88,"tfus_e":73,"tfus_l":112,
     "class":90,"dist_fit":8,"surface_fit":9,"trainer_q":8,"form_trend":1,"unknown_var":0,"paired_figs":1,
     "workout_score":6.0,"jt_cd_score":-0.8,
     "notes":"Renegade beat him handily in Ark Derby but reportedly fighting foot bruise; trainer Casse says past it; needs career-top Beyer to contend"},
    {"post":14,"name":"Potente","ml":"20-1","ml_dec":20,"trainer":"Baffert","jockey":"Hernandez J J",
     "silk":{"tw":"#6F1010","nm":"#FFD400"},"style":"EP",
     "best_beyer":95,"avg_beyer":91,"tfus_e":111,"tfus_l":94,
     "class":92,"dist_fit":6,"surface_fit":9,"trainer_q":10,"form_trend":1,"unknown_var":0,"paired_figs":0,
     "workout_score":8.5,"jt_cd_score":0.8,"trip_bonus":2.0,
     "notes":"Favorable post 14 to stalk contested pace; improving Beyers each start; Kaitton's contrarian Medina-Spirit-style Baffert pick; Welsch blistering 5f 57.77 work; cost $2.4M"},
    {"post":15,"name":"Emerging Market","ml":"15-1","ml_dec":15,"trainer":"C Brown","jockey":"Prat",
     "silk":{"tw":"#C9B98A","nm":"#000000"},"style":"P",
     "best_beyer":97,"avg_beyer":94,"tfus_e":86,"tfus_l":102,
     "class":92,"dist_fit":9,"surface_fit":9,"trainer_q":10,"form_trend":2,"unknown_var":0,"paired_figs":0,
     "workout_score":7.5,"jt_cd_score":0,
     "notes":"Welsch: 'loved him', big gallout 59.4/1:13.3 on fast track, Pratt sitting chilly; undefeated 2/2 with G2 LA Derby win; only Leonatus (1883) won Derby off just 2 starts; Brown overdue"},
    {"post":16,"name":"Pavlovian","ml":"30-1","ml_dec":30,"trainer":"O'Neill","jockey":"Maldonado",
     "silk":{"tw":"#6FA8DC","nm":"#F26B1F"},"style":"EP",
     "best_beyer":90,"avg_beyer":84,"tfus_e":98,"tfus_l":86,
     "class":88,"dist_fit":5,"surface_fit":9,"trainer_q":7,"form_trend":1,"unknown_var":0,"paired_figs":0,
     "workout_score":5.5,"jt_cd_score":0,"trip_bonus":-2.5,
     "notes":"Welsch: AE Robusta 'looked better than Pavlovian'; sandwiched in pace duel with 4/17; LA Derby was flattered by speed bias day; Chip Honcho was probably the better horse"},
    {"post":17,"name":"Six Speed","ml":"50-1","ml_dec":50,"trainer":"Seemar (UAE)","jockey":"Hernandez B J Jr",
     "silk":{"tw":"#0B1F4D","nm":"#FFFFFF"},"style":"E",
     "best_beyer":88,"avg_beyer":85,"tfus_e":None,"tfus_l":None,
     "class":82,"dist_fit":4,"surface_fit":7,"trainer_q":5,"form_trend":-1,"unknown_var":6,"paired_figs":0,
     "workout_score":5.0,"jt_cd_score":0,
     "notes":"Already stopped at 9.5f in UAE Derby — distance concern at 10f; Seemar said horse is difficult to harness so pace will be genuine; UAE Derby horses 0-for-21 historically"},
    {"post":18,"name":"Further Ado","ml":"6-1","ml_dec":6,"trainer":"Cox","jockey":"Velazquez",
     "silk":{"tw":"#0E3F1A","nm":"#FFD400"},"style":"EP",
     "best_beyer":106,"avg_beyer":96,"tfus_e":109,"tfus_l":88,
     "class":102,"dist_fit":9,"surface_fit":9,"trainer_q":10,"form_trend":1,"unknown_var":0,"paired_figs":0,
     "workout_score":8.5,"jt_cd_score":0,"trip_bonus":2.5,
     "notes":"Quantified trip credit: avoids used-up-clearing event (~+2 EV) plus structural stalking advantage (+0.5); Welsch 2nd-favorite all week; top Beyer 106 + top Brisnet 105; JV 2-of-3 first-time-jock Derby wins since 2010"},
    {"post":19,"name":"Golden Tempo","ml":"30-1","ml_dec":30,"trainer":"DeVaux","jockey":"Ortiz J L",
     "silk":{"tw":"#6F8FAF","nm":"#E11A1A"},"style":"S",
     "best_beyer":88,"avg_beyer":86,"tfus_e":57,"tfus_l":113,
     "class":85,"dist_fit":9,"surface_fit":9,"trainer_q":7,"form_trend":1,"unknown_var":0,"paired_figs":1,
     "workout_score":8.0,"jt_cd_score":1.5,
     "notes":"3rd in G2 LA Derby; Beyers creeping north; deepest closer in field; first action away from FG; snappy KEE works; Curlin progeny stamina"},
    {"post":20,"name":"Fulleffort","ml":"20-1","ml_dec":20,"trainer":"Cox","jockey":"Gaffalione",
     "silk":{"tw":"#E91E8C","nm":"#FFD400"},"style":"S",
     "best_beyer":94,"avg_beyer":88,"tfus_e":67,"tfus_l":106,
     "class":88,"dist_fit":7,"surface_fit":6,"trainer_q":10,"form_trend":1,"unknown_var":3,"paired_figs":0,
     "workout_score":8.5,"jt_cd_score":-0.3,"trip_bonus":0.5,
     "notes":"Deep closer benefits from 75% fast pace lock (modest trip credit); Welsch tipped as price play after final drill; 'might be flying under radar'; better suited to dirt than Final Gambit; Ed's top longshot pick"}
]

PACE_PROBS = {"fast": 0.75, "honest": 0.22, "slow": 0.03}  # v3.8: 4/16/17 all sending = honest-fast lock

# Top TimeformUS Speed Figure per horse (from TFUS PP, 4/27 update)
# Different scale than Beyer; useful display companion for handicappers
TOP_TFUS = {
    1: 117, 2: 101, 3: 112, 4: 114, 5: 104, 6: 115, 7: None, 8: 120,
    9: 115, 10: 107, 11: 107, 12: 114, 13: 113, 14: 118, 15: 110, 16: 112,
    17: 103, 18: 121, 19: 109, 20: 110
}

# Display-friendly running style labels
STYLE_LABELS = {"E": "Pace", "EP": "Tactical", "P": "Presser", "S": "Closer", "DS": "Deep Closer"}

def pace_fingerprint(h):
    """Returns TFUS_L − TFUS_E if available, else style-derived default."""
    if h.get("tfus_e") is not None and h.get("tfus_l") is not None:
        return h["tfus_l"] - h["tfus_e"]
    return STYLE_DEFAULT_PACE_FP.get(h["style"], 0)

def pace_adj(h, shape):
    fp = pace_fingerprint(h)
    if shape == "fast":  return  fp * PACE_MULTIPLIER
    if shape == "slow":  return -fp * PACE_MULTIPLIER
    return 0  # honest

def style_bonus(h):
    """Derby preference for tactical speed (EP) — horses who can win in different
    ways based on race shape. +2.5 is a meaningful but not field-warping nudge."""
    return 2.5 if h["style"] == "EP" else 0.0

def base_rating(h):
    beyer_score   = 0.55 * h["best_beyer"] + 0.25 * h["avg_beyer"]
    class_bonus   = 0.10 * (h["class"] - 88)
    dist_adj      = (h["dist_fit"] - 6) * 0.7
    surface_adj   = (h["surface_fit"] - 7) * 0.9
    trainer_adj   = (h["trainer_q"] - 6) * 0.4
    form_adj      = h["form_trend"] * 1.5
    paired_bonus  = h.get("paired_figs", 0) * 2.0
    workout_adj   = (h.get("workout_score", 5) - 5) * 0.5
    jt_cd_adj     = h.get("jt_cd_score", 0) * 0.7
    style_adj     = style_bonus(h)
    trip_bonus    = h.get("trip_bonus", 0.0)                    # NEW v3.8
    return (beyer_score + class_bonus + dist_adj + surface_adj + trainer_adj
            + form_adj + paired_bonus + workout_adj + jt_cd_adj + style_adj
            + trip_bonus)

def trip_events(h, shape):
    """Probabilistic trip events that model 20-horse Derby chaos.

    Replaces v2's deterministic post bias. Designed so that:
      - Inside post 1 is NOT flat-penalized; only closers/stalkers get traffic
        trouble, and at a low rate.
      - Outside speed is only "used up clearing" when there's actual pace
        pressure (fast pace shape). On honest/slow pace, an outside E/EP that
        clears and rates gets no penalty. ('Speed to the outside' principle.)
    """
    adj = 0.0
    # Bad break — 5% any horse
    if random.random() < 0.05:
        adj -= 10 + random.random() * 8
    # Boxed in — 6% for stalker types from inside posts.
    # Deep closers (S) drop back, find the rail, and don't suffer this trip.
    # Pure speed (E) clears and rates. Only the P type stuck in traffic gets boxed.
    if h["post"] <= 3 and h["style"] == "P":
        if random.random() < 0.06:
            adj -= 4 + random.random() * 4
    # Wide trip — 25% for any style from posts 15-20
    if h["post"] >= 15:
        if random.random() < 0.25:
            adj -= 5 + random.random() * 5
    # Used up clearing — 30% E/EP from outside posts, only on fast pace
    if shape == "fast" and h["style"] in ("E", "EP") and h["post"] >= 15:
        if random.random() < 0.30:
            adj -= 6 + random.random() * 6
    return adj

def sample_pace_shape():
    r = random.random()
    if r < PACE_PROBS["fast"]: return "fast"
    if r < PACE_PROBS["fast"] + PACE_PROBS["honest"]: return "honest"
    return "slow"

def run_sim(horses):
    shape = sample_pace_shape()
    speeds = []
    for h in horses:
        base = base_rating(h)
        pace = pace_adj(h, shape)
        form_var = random.gauss(0, 7.5)
        trip_noise = random.gauss(0, 2.5)
        trip_evt = trip_events(h, shape)
        unknown = random.gauss(0, h["unknown_var"]) if h["unknown_var"] > 0 else 0
        speed = base + pace + form_var + trip_noise + trip_evt + unknown
        speeds.append((h["post"], speed))
    speeds.sort(key=lambda t: -t[1])
    return shape, [p for p, _ in speeds]

NUM_SIMS = 10_000

print("Base ratings + pace fingerprint (sanity check):")
for h in sorted(HORSES, key=lambda x: -base_rating(x)):
    fp = pace_fingerprint(h)
    fp_src = "TFUS" if h.get("tfus_e") is not None else "style"
    print(f"  #{h['post']:2d} {h['name']:<18} base={base_rating(h):6.2f}  "
          f"L−E={fp:+4d}({fp_src})  ML {h['ml']:>5}  style {h['style']}")
print()

sims = []
shape_dist = Counter()
for _ in range(NUM_SIMS):
    shape, finish = run_sim(HORSES)
    shape_dist[shape] += 1
    sims.append(finish)

win_count = Counter()
top3_count = Counter()
top4_count = Counter()
top5_count = Counter()
position_counts = {h["post"]: [0] * 20 for h in HORSES}
for finish in sims:
    win_count[finish[0]] += 1
    for p in finish[:3]: top3_count[p] += 1
    for p in finish[:4]: top4_count[p] += 1
    for p in finish[:5]: top5_count[p] += 1
    for idx, post in enumerate(finish):
        position_counts[post][idx] += 1

ml_probs_raw = {h["post"]: 1 / (h["ml_dec"] + 1) for h in HORSES}
ml_overround = sum(ml_probs_raw.values())
ml_probs_fair = {p: q / ml_overround for p, q in ml_probs_raw.items()}

output_horses = []
for h in HORSES:
    p = h["post"]
    win_p = win_count[p] / NUM_SIMS
    top3_p = top3_count[p] / NUM_SIMS
    top4_p = top4_count[p] / NUM_SIMS
    top5_p = top5_count[p] / NUM_SIMS
    fair_dec = (1 / win_p) if win_p > 0 else 999
    fair_frac = fair_dec - 1
    ml_fair_p = ml_probs_fair[p]
    edge = (win_p - ml_fair_p) / ml_fair_p if ml_fair_p > 0 else 0
    pos_counts = position_counts[p]
    output_horses.append({
        "post": p, "name": h["name"], "ml": h["ml"], "ml_dec": h["ml_dec"],
        "ml_prob_raw": ml_probs_raw[p], "ml_prob_fair": ml_fair_p,
        "trainer": h["trainer"], "jockey": h["jockey"], "silk": h["silk"],
        "style": h["style"], "style_label": STYLE_LABELS.get(h["style"], h["style"]),
        "best_beyer": h["best_beyer"], "avg_beyer": h["avg_beyer"],
        "top_tfus": TOP_TFUS.get(p),
        "tfus_e": h["tfus_e"], "tfus_l": h["tfus_l"],
        "pace_fingerprint": pace_fingerprint(h),
        "workout_score": h["workout_score"], "jt_cd_score": h["jt_cd_score"],
        "win_count": win_count[p], "win_prob": win_p,
        "pos_2_prob": pos_counts[1] / NUM_SIMS,
        "pos_3_prob": pos_counts[2] / NUM_SIMS,
        "pos_4_prob": pos_counts[3] / NUM_SIMS,
        "top4_prob": top4_p,
        "board_prob": top3_p,
        "super_prob": top5_p,
        "fair_odds_dec": round(fair_dec, 2),
        "fair_odds_frac": f"{fair_frac:.1f}-1",
        "edge": edge, "notes": h["notes"]
    })

result = {
    "race": RACE,
    "model_meta": {
        "version": "v3",
        "num_sims": NUM_SIMS,
        "pace_shape_observed": {k: v / NUM_SIMS for k, v in shape_dist.items()},
        "ml_overround": ml_overround,
        "improvements_in_v3": [
            "Probabilistic trip events replace deterministic post bias",
            "Inside post 1 no longer flat-penalized; closers from inside get probabilistic boxed-in (6%, P/S only)",
            "Outside speed (E/EP from 15+) only penalized on fast pace shape (speed-to-the-outside principle)",
            "EP tactical-speed bonus (+2.5 ability) for Derby's preferred profile"
        ]
    },
    "horses": output_horses,
    "sims": sims
}

with open("derby_sims.json", "w") as f:
    json.dump(result, f)

print(f"Ran {NUM_SIMS:,} sims. Pace shape: " +
      ", ".join(f"{k} {v/NUM_SIMS:.0%}" for k, v in shape_dist.items()))
print()
print("Win % vs ML (sorted by sim win %):")
print(f"  {'Post':>4} {'Horse':<18} {'ML':>5} {'ML%':>5} {'Sim%':>6} {'Fair':>9} {'Δpp':>6}")
for oh in sorted(output_horses, key=lambda x: -x["win_prob"]):
    edge_pp = oh["win_prob"] * 100 - oh["ml_prob_raw"] * 100
    sign = "+" if edge_pp >= 0 else ""
    print(f"  {oh['post']:>4} {oh['name']:<18} {oh['ml']:>5} "
          f"{oh['ml_prob_raw']*100:>4.1f}% {oh['win_prob']*100:>5.1f}% "
          f"{oh['fair_odds_frac']:>9} {sign}{edge_pp:>5.1f}")
print()
print("Saved to derby_sims.json")
