"""Print a summary table of trade_40h_results.json. Usage: python3 summarize_trade.py [results.json]"""
import json, statistics as st, sys
d = json.load(open(sys.argv[1] if len(sys.argv) > 1 else "results/trade_40h_results.json"))
m = lambda runs, f: round(st.mean(f(r) for r in runs), 2)
cols = ["case", "gear fit", "full set", "perfect set", "crafted share of worn", "crafts/crafter", "crafter skill", "crafter lvl", "other lvl", "crafter gold", "other gold", "crafter sales", "orders unfilled"]
print(" | ".join(cols))
for name, runs in d.items():
    s = lambda r: r["econ"]["final_sets"]
    n = lambda r: max(1, s(r)["n"])
    e = lambda r, k: r["econ"][k]
    posted = lambda r: sum(r["econ"]["band_orders"].values())
    unf = lambda r: 1 - (r["econ"]["stats"].get("orders_filled_by_craft", 0) / max(1, posted(r) - r["econ"]["stats"].get("orders_voided_by_other_gear", 0)))
    row = [name[:3].strip(), m(runs, lambda r: s(r)["fit"] / n(r)), "%s%%" % m(runs, lambda r: 100 * s(r)["full"] / n(r)),
           "%s%%" % m(runs, lambda r: 100 * s(r)["perfect"] / n(r)), "%s%%" % m(runs, lambda r: 100 * s(r)["crafted_pieces"] / max(1, s(r)["worn"])),
           m(runs, lambda r: e(r, "crafts_per_crafter")), m(runs, lambda r: e(r, "crafter_skill")), m(runs, lambda r: e(r, "crafter_level")),
           m(runs, lambda r: e(r, "other_level")), m(runs, lambda r: e(r, "crafter_gold")), m(runs, lambda r: e(r, "other_gold")),
           m(runs, lambda r: e(r, "crafter_sales")), "%s%%" % m(runs, lambda r: 100 * unf(r))]
    print(" | ".join(str(x) for x in row))
