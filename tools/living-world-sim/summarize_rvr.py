"""Summarize rvr_sim results. Usage: python3 summarize_rvr.py results/rvr_120h.json"""
import json, statistics as st, sys
d = json.load(open(sys.argv[1] if len(sys.argv) > 1 else "results/rvr_120h.json"))
m = lambda xs, n=1: round(st.mean(xs), n)
R = ("Albion", "Midgard", "Hibernia")
for name, runs in d.items():
    H = len(runs[0]["hourly"])
    S = lambda k: m([r["stats"].get(k, 0) / H for r in runs], 2)
    print(f"\n## {name} ({len(runs)} seeds, {H} h)")
    print(" per hour: sieges", S("sieges_started"), "| keep flips", S("keep_flips"), "| relic raids", S("relic_raids"),
          "| relic captures", S("relic_captures"), "| open-field fights", S("fights"), "| RvR deaths", S("rvr_deaths"))
    print(" Darkness Falls access share:", {r: m([x["df_share"][r] for x in runs], 2) for r in R})
    keeps = {r: (m([min(h["keeps"][r] for h in x["hourly"]) for x in runs], 0), m([st.mean(h["keeps"][r] for h in x["hourly"]) for x in runs]),
                 m([max(h["keeps"][r] for h in x["hourly"]) for x in runs], 0)) for r in R}
    print(" keeps held (min / mean / max of 21):", keeps)
    print(" relics held at end:", [x["hourly"][-1]["relics"] for x in runs])
    for r in R:
        roles = {role: (m([x["roles"][f"{r}/{role}"]["rp_per_hour"] for x in runs], 0), m([x["roles"][f"{r}/{role}"]["deaths_per_hour"] for x in runs], 2))
                 for role in ("zerg", "roam", "stealth")}
        rk = {k: m([x["ranks"][r][k] for x in runs], 0) for k in ("rr2_plus", "rr3_plus", "rr4_plus", "rr5_plus", "top_rp", "nolifer_rp_median", "pool")}
        print(f" {r}: RP/hour and deaths/hour by role {roles} | ranks {rk}")
    print(" frontier PvE deaths per hour by ring:", {ring: m([x["frontier_pve"][ring]["deaths_per_hour"] for x in runs], 2) for ring in ("border", "middle", "inner")},
          "| escapes/hour", S("pve_escapes"))
