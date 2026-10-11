"""40-hour crafting and trade study. Usage: python3 trade_study.py [seeds e.g. 1,2,3,4,5] [output.json]

Runs the proposed crafting economy (see lw_economy.py) against baselines and sensitivity cases.
A design model, not the game: compare rows, do not trust absolute numbers.
"""
import json, os, statistics, sys
from multiprocessing import Pool

os.environ["LWS_HOURS"] = os.environ.get("TRADE_HOURS", "40")
_seeds = sys.argv[1] if len(sys.argv) > 1 else "1,2,3,4,5"
_out = sys.argv[2] if len(sys.argv) > 2 else "trade_40h_results.json"
sys.argv = ["living_world_sim.py", "", _seeds]
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import living_world_sim as L

# name: (scenario, personalities, strong, econ, options)
CASES = {
    "A  today's rules + gear from loot only (no crafters)":      ("fresh", False, False, "loot", {}),
    "B  strong personalities, crafting does not exist":          ("fresh", True, True, "loot", {}),
    "C  strong personalities + crafting economy":                ("fresh", True, True, "craft", {}),
    "D  C, but loot gear is scarce (40%)":                       ("fresh", True, True, "craft", {"loot_rate": 0.4}),
    "E  D, plus easy high-quality crafting (+6)":                ("fresh", True, True, "craft", {"loot_rate": 0.4, "quality_bonus": 6}),
    "F  B, but loot gear is scarce (40%)":                       ("fresh", True, True, "loot", {"loot_rate": 0.4}),
    "G  C with 25% crafters":                                    ("fresh", True, True, "craft", {"crafter_share": 25}),
    "H  C with 8% crafters":                                     ("fresh", True, True, "craft", {"crafter_share": 8}),
    "I  C with scarce materials (30%)":                          ("fresh", True, True, "craft", {"mat_rate": 0.3}),
    "J  established world, strong, crafting does not exist":     ("established", True, True, "loot", {"loot_rate": 0.4}),
    "K  established world, strong + crafting economy":           ("established", True, True, "craft", {"loot_rate": 0.4}),
    "L  established world, today's rules, loot only":            ("established", False, False, "loot", {"loot_rate": 0.4}),
    "M  K, but one new alt per hour instead of every 15 min":    ("established", True, True, "craft", {"loot_rate": 0.4, "alt_every": 60}),
    "N  K, with no alts":                                        ("established", True, True, "craft", {"loot_rate": 0.4, "alt_every": 0}),
}
SEEDS = [int(s) for s in _seeds.split(",")]


def job(args):
    name, seed = args
    scen, P, strong, econ, opts = CASES[name]
    r = L.run(seed, P, scen, strong, econ=econ, opts=opts)
    if not os.environ.get("TRADE_KEEP_HOURLY"):
        r.pop("hourly")                   # keep files small
    return name, seed, r


ONLY = os.environ.get("TRADE_ONLY")      # optional: comma-separated case letters to run, e.g. "J,K"

if __name__ == "__main__":
    names = [n for n in CASES if not ONLY or n[0] in ONLY.split(",")]
    with Pool(2) as pool:
        done = pool.map(job, [(n, s) for n in names for s in SEEDS])
    out = {n: [r for nn, s, r in done if nn == n] for n in names}
    json.dump(out, open(_out, "w"))
    print("saved", _out)
