"""XP-rate study: the real player at xp_rate 8x, playing 5 hours a week, with bots at several bot_xp_rate
values and alt rates. The world only runs while the player plays, so 60 server hours = 12 weeks.
Usage: python3 xp_study.py [seeds] [hours] [output.json]"""
import json, os, sys
from multiprocessing import Pool
_seeds = sys.argv[1] if len(sys.argv) > 1 else "1,2,3"
_hours = sys.argv[2] if len(sys.argv) > 2 else "120"
_out = sys.argv[3] if len(sys.argv) > 3 else "xp_study_results.json"
os.environ["LWS_HOURS"] = _hours
sys.argv = ["living_world_sim.py", "", _seeds]
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import living_world_sim as L

BASE = {"loot_rate": 0.4, "player_xp": 8}
CASES = {f"bots {bx}x, alt every {alt} min": dict(BASE, bot_xp=bx, alt_every=alt)
         for bx, alts in ((1, (60,)), (2, (30, 60)), (4, (15, 30, 60)), (6, (10, 20, 40)))
         for alt in alts}
SEEDS = [int(s) for s in _seeds.split(",")]

def job(a):
    name, seed = a
    r = L.run(seed, True, "established", True, econ="craft", opts=CASES[name])
    return name, seed, r

if __name__ == "__main__":
    with Pool(2) as p:
        done = p.map(job, [(n, s) for n in CASES for s in SEEDS])
    json.dump({n: [r for nn, s, r in done if nn == n] for n in CASES}, open(_out, "w"))
    print("saved", _out)
