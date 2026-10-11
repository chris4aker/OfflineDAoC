"""Summarize xp_study results. Usage: python3 summarize_xp.py results/xp_study_120h.json"""
import json, statistics as st, sys
d = json.load(open(sys.argv[1] if len(sys.argv) > 1 else "results/xp_study_120h.json"))
m = lambda xs, n=0: round(st.mean(xs), n)
def at(r, hour, key):
    hs = [h for h in r["hourly"] if hour - 3 <= h["hour"] <= hour]
    return st.mean(h[key] for h in hs) if not isinstance(hs[0][key], list) else [st.mean(h[key][i] for h in hs) for i in range(5)]
print("case | your chars at 50 | bots hunting within 3 lvls of you (avg / lonely hours <3) | bands at week 4 | week 12 | week 24 | zones present wk24 | full gear sets wk24")
for name, runs in d.items():
    H = len(runs[0]["hourly"])
    near = [h["near_player"] for r in runs for h in r["hourly"]]
    lonely = 100 * sum(1 for x in near if x < 3) / len(near)
    b = lambda hour: [round(st.mean(at(r, hour, "bands")[i] for r in runs)) for i in range(5)]
    sets = m([100 * r["econ"]["final_sets"]["full"] / max(1, r["econ"]["final_sets"]["n"]) for r in runs])
    print(f"{name} | {m([r['player']['chars_at_50'] for r in runs], 1)} | {m(near, 1)} / {round(lonely)}% | {b(20)} | {b(60)} | {b(min(H, 120))} | "
          f"{m([at(r, min(H, 120), 'present_zones') for r in runs], 1)} | {sets}%")
