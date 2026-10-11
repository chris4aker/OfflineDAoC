"""Summarize persona_sim results. Usage: python3 summarize_persona.py results/persona_120h.json"""
import json, statistics as st, sys
d = json.load(open(sys.argv[1] if len(sys.argv) > 1 else "results/persona_120h.json"))
m = lambda xs, n=0: round(st.mean(xs), n) if xs else None
for name, runs in d.items():
    print("\n##", name, f"({len(runs)} seeds)")
    H = len(runs[0]["hourly"])
    for hour in (24, 60, 120):
        if hour > H: continue
        rows = [[h for h in r["hourly"] if hour - 3 <= h["hour"] <= hour] for r in runs]
        f = lambda k: m([st.mean(h[k] for h in rr) for rr in rows], 1)
        bands = [m([st.mean(h["online_bands"][i] for h in rr) for rr in rows]) for i in range(5)]
        print(f" h{hour}: online {f('online')} | zones {f('zones')} | busiest zone {f('top_zone_share')} | crowded {f('crowded')} | online by band {bands} | near me {f('near_me')}")
    near = [h["near_me"] for r in runs for h in r["hourly"]]
    print(f" near me overall: avg {m(near,1)}, hours with <3 nearby {round(100*sum(1 for x in near if x<3)/len(near),1)}%")
    for i in (1, 5, 11):
        if i >= len(runs[0]["snaps"]): continue
        sn = [r["snaps"][i] for r in runs]
        g = lambda k: m([s[k] for s in sn], 1)
        print(f" snap h{sn[0]['hour']}: chars {g('characters_total')} (active {g('characters_active')}) | lvl50 {g('level50')} templated {g('templated')} | all-char bands {[m([s['level_bands_all'][k] for s in sn]) for k in range(5)]} | crafters {g('crafters')} median skill {g('crafter_skill_median')} legendary {g('legendary')} 700+ {g('skill_700_plus')} | gold total {g('gold_total')} median {g('gold_median')} | open orders {g('open_orders')}")
    S = lambda k: m([r["stats"].get(k, 0) for r in runs])
    print(" stats:", {k: S(k) for k in ("alts_created", "retired_players", "reached_50", "orders_placed", "orders_filled", "orders_filled_in_guild", "orders_expired", "masterpieces", "skillup_crafts", "rare_drops", "rare_market_sales", "craft_min", "craft_idle_min")})
    print(" roster sizes (last):", runs[0]["snaps"][-1]["roster_sizes"])
    gi = {k: m([r["gold_in"].get(k, 0) for r in runs]) for k in runs[0]["gold_in"]}
    go = {k: m([r["gold_out"].get(k, 0) for r in runs]) for k in runs[0]["gold_out"]}
    print(" gold in:", gi); print(" gold out:", go)
    print(" gold median: crafter players", m([r["gold_crafter_players"] for r in runs]), "others", m([r["gold_other_players"] for r in runs]))
    tp = {}
    for r in runs:
        for s, v in r["templates"].items():
            tp.setdefault(s, []).append((v["n"], v["median_hours"]))
    print(" templates:", {s: (m([a for a, _ in v], 1), m([b for _, b in v if b is not None], 1)) for s, v in tp.items()}, "| shortcut math:", runs[0]["shortcut"])
    print(" me:", [r["me"] for r in runs])
