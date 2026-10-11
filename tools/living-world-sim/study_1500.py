"""1,500-online study with the persona simulator. Usage: python3 study_1500.py [seeds] [hours] [out.json]"""
import json, os, sys
from multiprocessing import Pool
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import persona_sim as PS

SEEDS = [int(s) for s in (sys.argv[1] if len(sys.argv) > 1 else "1,2").split(",")]
HOURS = int(sys.argv[2]) if len(sys.argv) > 2 else 120
OUT = sys.argv[3] if len(sys.argv) > 3 else "study_1500_results.json"
CASES = {
    "1 base: bots 2x, template gems 1500":            {},
    "2 bots 4x":                                       {"bot_xp": 4.0},
    "3 cheaper templates (gems 750)":                  {"gem_cost": 750},
    "4 crafters charge double margin":                 {"crafter_margin": 1.0, "template_margin": 0.6},
    "5 coin drops 1.5x":                               {"money_rate": 1.5},
    "6 half population (about 800 online)":            {"personas": 1300},
}
ONLY = os.environ.get("STUDY_ONLY")

def job(a):
    name, seed = a
    r = PS.World(seed, dict(CASES[name], hours=HOURS)).run()
    return name, seed, r

if __name__ == "__main__":
    names = [n for n in CASES if not ONLY or n.split()[0] in ONLY.split(",")]
    with Pool(2) as p:
        done = p.map(job, [(n, s) for n in names for s in SEEDS])
    json.dump({n: [r for nn, s, r in done if nn == n] for n in names}, open(OUT, "w"), default=str)
    print("saved", OUT)
