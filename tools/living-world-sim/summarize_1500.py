"""Summarize study_1500 results. Usage: python3 summarize_1500.py results/study_1500_120h.json"""
import json, statistics as st, sys
d = json.load(open(sys.argv[1] if len(sys.argv) > 1 else "results/study_1500_120h.json"))
m = lambda xs, n=0: round(st.mean(xs), n) if xs else None
def snap(r, hour): return next(s for s in r["snaps"] if s["hour"] == hour)
for name, runs in d.items():
    print("\n##", name, f"(template price {round(runs[0]['template_price'])}, leveling piece at 30: {round(runs[0]['leveling_price_30'])})")
    for hour in (20, 60, 120):
        S = [snap(r, hour) for r in runs if any(s["hour"] == hour for s in r["snaps"])]
        if not S: continue
        f = lambda k, n=0: m([s[k] for s in S], n)
        b = [round(st.mean(s["bands"][i] for s in S)) for i in range(5)]
        ob = [round(st.mean(s["online_bands"][i] for s in S)) for i in range(5)]
        l50src = {k: round(100 * st.mean(s["l50_slots"].get(k, 0) / max(1, sum(s["l50_slots"].values())) for s in S)) for k in ("template", "rare", "crafted", "loot")}
        levsrc = round(100 * st.mean(s["leveling_slots"].get("crafted", 0) / max(1, sum(s["leveling_slots"].values())) for s in S))
        sts = lambda k: m([s["stats"].get(k, 0) for s in S])
        print(f" h{hour}: online {f('online')} | chars {f('characters')} | bands all {b} online {ob} | zones hunted {f('zones_hunted')} | top zone {m([100*s['top_zone_share'] for s in S])}% | crowded {m([100*s['crowded'] for s in S])}%")
        print(f"       level 50: {f('l50')} chars, top set {m([100*s['l50_topset']/max(1,s['l50']) for s in S])}% | L50 slots template/rare/crafted/loot % {l50src} | leveling slots crafted {levsrc}%")
        print(f"       crafters: skill mean {f('crafter_skill_mean')}, legendary {f('crafters_legendary')}, can make templates {f('crafters_can_template')} | gold median all {f('gold_median')} crafters {f('crafter_gold_median')} | gold total {f('gold_total')}")
        print(f"       cumulative: earned {sts('coins_earned')} sunk in materials {sts('coins_sunk_materials')} | crafts {sts('crafts')} (skill-up {sts('crafted_skillup')}, leveling {sts('crafted_leveling')}, template {sts('crafted_template')}), masterpieces {sts('masterpieces')}, blocked by gold {sts('craft_blocked_gold')} | template orders {sts('template_orders')} expired {sts('orders_expired_template')} | rare drops {sts('rare_drops')} | alts {sts('alts_created')} blocked by names {sts('alts_blocked_by_names')}")
    done = [x for r in runs for x in r["l50_done"]]
    if done:
        print(f" top sets completed: {len(done)/len(runs):.0f} per run; median hours at 50 to finish {st.median(x[0] for x in done):.1f}; avg template slots {st.mean(x[1] for x in done):.1f}, rare slots {st.mean(x[2] for x in done):.1f}")
