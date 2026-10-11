"""Summarize a long run: level and zone spread over time, plus crafting.
Usage: python3 summarize_population.py results/trade_60h_results.json   (needs TRADE_KEEP_HOURLY=1 data)"""
import json, statistics as st, sys
d = json.load(open(sys.argv[1] if len(sys.argv) > 1 else "results/trade_60h_results.json"))
m = lambda xs, n=1: round(st.mean(xs), n)

def window(r, hour, key):                      # average of the 4 hours ending at `hour`
    hs = [h for h in r["hourly"] if hour - 3 <= h["hour"] <= hour]
    return st.mean(h[key] for h in hs)

def top_zone(r, hour):
    hs = [h for h in r["hourly"] if hour - 3 <= h["hour"] <= hour]
    return st.mean(max(h["zone_counts"].values()) / max(1, sum(h["zone_counts"].values())) if h["zone_counts"] else 0 for h in hs)

def bands(r, hour):
    hs = [h for h in r["hourly"] if hour - 3 <= h["hour"] <= hour]
    return [st.mean(h["bands"][i] for h in hs) for i in range(5)]

for name, runs in d.items():
    H = len(runs[0]["hourly"])
    print("\n##", name)
    print(" hour | online | zones w/ hunters | zones present | evenness | top-zone share | crowded | in town | exploring | mean level | bots by level band 1-10/11-20/21-30/31-40/41-50")
    for hour in (10, 20, 30, 40, 50, 60):
        if hour > H: continue
        print(f" {hour:4} | {m([window(r, hour, 'online') for r in runs], 0):>6} | {m([window(r, hour, 'zones') for r in runs]):>16} | {m([window(r, hour, 'present_zones') for r in runs]):>13} | "
              f"{m([window(r, hour, 'evenness') for r in runs], 2):>8} | {m([100 * top_zone(r, hour) for r in runs], 0):>13}% | {m([100 * window(r, hour, 'crowded') for r in runs], 0):>6}% | "
              f"{m([100 * window(r, hour, 'town') for r in runs], 0):>6}% | {m([100 * window(r, hour, 'exploring') for r in runs], 0):>8}% | {m([window(r, hour, 'mean_level') for r in runs]):>10} | "
              f"{[round(st.mean(bands(r, hour)[i] for r in runs)) for i in range(5)]}")
    if "econ" in runs[0]:
        for i, hour in enumerate((10, 20, 30, 40, 50, 60)):
            if i >= len(runs[0]["econ"]["snaps"]): continue
            sn = [r["econ"]["snaps"][i] for r in runs]
            f = lambda k: m([s["sets"][k] for s in sn])
            n = max(1, m([s["sets"]["n"] for s in sn]))
            print(f" craft h{hour}: full sets {m([100 * s['sets']['full'] / max(1, s['sets']['n']) for s in sn], 0)}% | crafted share of worn {m([100 * s['sets']['crafted_pieces'] / max(1, s['sets']['worn']) for s in sn], 0)}% | "
                  f"perfect sets {f('perfect')} | fully crafted sets {f('crafted_full')} | crafter skill mean/max {m([s['crafter_skill_mean'] for s in sn])}/{m([s['crafter_skill_max'] for s in sn])} vs p90 level {m([s['p90_level'] for s in sn])} | open orders {m([s['open_orders'] for s in sn], 0)}")
        e = lambda k: m([r["econ"][k] for r in runs])
        print(f" crafts/crafter {e('crafts_per_crafter')} | crafter lvl {e('crafter_level')} vs other {e('other_level')} | crafter gold {e('crafter_gold')} vs other {e('other_gold')}")
