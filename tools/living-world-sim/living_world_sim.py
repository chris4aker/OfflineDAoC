"""Living World M1 simulation: baseline (current decision rules) vs mild and strong personalities.

This is a design model, not the game. See README.md for assumptions and how to read results.

Abstract agent model of Midgard autonomous gamebots over 20 game hours from a fresh
start. Camps come from the repo's real CapnBry camp catalog. Numbers taken from the code:
goal mix 60/40/0 (1-19), 40/40/20 (20-49); PvE tenure 45-120 min; group matchmaking
timeout 20 min; train 90% and 15% town break at task boundaries (live rules); safer camps after
2 deaths; dungeon preference 100/300/400 permille; outdoor camps weighted by live spawns.
CORRECTION (2026-10-11): an earlier version also used the trainer 0.28 / craft 0.16 / downtime 0.035
rules from AutonomousBotDecisionEngine.Choose, which no live code calls. They were replaced by the
live between-task rules above, and bots no longer craft.
Everything else (XP curve, death rates, travel times, capacity) is a labelled assumption.
"""
import json, math, os, random, statistics, sys, collections

# Usage: python3 living_world_sim.py [catalog.json] [seeds e.g. 1,2,3,4,5] [output.json]
_HERE = os.path.dirname(os.path.abspath(__file__))
_DEFAULT_CATALOG = os.path.join(_HERE, "..", "..", "source", "server", "GameServer", "bots",
                                "autonomous", "data", "capnbry_classic_si_goals.json")
CATALOG = sys.argv[1] if len(sys.argv) > 1 and sys.argv[1] else _DEFAULT_CATALOG
SEEDS = [int(s) for s in sys.argv[2].split(",")] if len(sys.argv) > 2 and sys.argv[2] else [1, 2, 3, 4, 5]
N_BOTS = 300
HOURS = int(os.environ.get("LWS_HOURS", "20"))   # 40 for the trade study
sys.path.insert(0, _HERE)
import lw_economy
MIDGARD = {100, 125, 126, 127, 128, 129, 150, 151, 161, 249}
DUNGEON_REGIONS = {125, 126, 127, 128, 129, 150, 161, 249}

# ---------------- world ----------------
def load_camps():
    goals = json.load(open(CATALOG))["goals"]
    camps = []
    for g in goals:
        if g["region_id"] not in MIDGARD or not g["levels"]:
            continue
        lv = sorted(g["levels"])[len(g["levels"]) // 2]
        camps.append(dict(id=g["id"], zone=g["zone"], region=g["region_id"], level=lv,
                          dungeon=g["region_id"] in DUNGEON_REGIONS,
                          weight=max(1, g.get("sightings", 1))))
    return camps

def travel_minutes(a_zone, a_region, camp):
    if a_zone == camp["zone"]:
        t = 2
    elif a_region == camp["region"] or (a_region in (100, 151) and camp["region"] in (100, 151) and a_region == camp["region"]):
        t = 7
    else:
        t = 14  # different region: boat, porter or dungeon descent (assumption)
    return t + (3 if camp["dungeon"] else 0)

def con(level, mob):
    d = mob - level
    if d <= -(3 + level // 10): return "grey"
    if d <= -2: return "green"
    if d == -1: return "blue"
    if d == 0: return "yellow"
    if d <= 2: return "orange"
    return "red"

XP_RATE = dict(green=0.45, blue=0.75, yellow=1.0, orange=1.25, red=1.45)          # assumption
DEATH_PER_HOUR = dict(green=0.01, blue=0.03, yellow=0.07, orange=0.18, red=0.45)   # assumption, solo
def hours_to_level(level): return 0.045 * 1.135 ** level                            # assumption
CAPACITY_UNITS = 2  # pulling units (solo bot or group) a camp cell sustains (assumption)

# ---------------- personalities ----------------
TYPES = {  # share, curiosity, risk, sociability, patience, chattiness  (0-10)
    "Leveler":   (30, 2, 5, 4, 8, 3),
    "Explorer":  (15, 9, 6, 4, 4, 6),
    "Casual":    (20, 5, 3, 6, 3, 7),
    "Socialite": (20, 4, 4, 9, 5, 9),
    "Daredevil": (15, 6, 9, 5, 5, 7),
}

STRONG_TYPES = {
    "Leveler":   (30, 2, 5, 4, 8, 3, (0.88, 0.04, 0.04, 0.04)),
    "Crafter":   (15, 3, 3, 5, 6, 4, (0.35, 0.55, 0.07, 0.03)),
    "Socialite": (20, 5, 4, 9, 5, 9, (0.50, 0.05, 0.30, 0.15)),
    "Explorer":  (15, 10, 6, 4, 4, 6, (0.45, 0.02, 0.08, 0.45)),
    "Daredevil": (20, 6, 9, 5, 5, 7, (0.85, 0.02, 0.08, 0.05)),
}
ACT_MINUTES = dict(hunt=80, craft=60, social=40, explore=60)  # mean durations used to turn time budgets into choice odds

ESTABLISHED_LEVELS = [(1, 10, 20), (11, 20, 20), (21, 30, 20), (31, 40, 20), (41, 50, 20)]  # assumption: even spread

def make_bot(i, rng, personalities, scenario="fresh", strong=False, weights=None):
    budget = None
    if strong:
        names = list(STRONG_TYPES)
        t = rng.choices(names, weights=weights or [STRONG_TYPES[n][0] for n in names])[0]
        _, c, r, s_, p, ch, budget = STRONG_TYPES[t]
        j = lambda v: max(0, min(10, v + rng.randint(-2, 2)))
        traits = dict(cur=j(c), risk=j(r), soc=j(s_), pat=j(p), chat=j(ch))
    elif personalities:
        names = list(TYPES)
        t = rng.choices(names, weights=[TYPES[n][0] for n in names])[0]
        _, c, r, s, p, ch = TYPES[t]
        j = lambda v: max(0, min(10, v + rng.randint(-2, 2)))
        traits = dict(cur=j(c), risk=j(r), soc=j(s), pat=j(p), chat=j(ch))
    else:
        t, traits = "Baseline", dict(cur=5, risk=5, soc=5, pat=5, chat=5)
    level = 1
    if scenario == "established":
        lo, hi, _ = rng.choices(ESTABLISHED_LEVELS, weights=[w for *_, w in ESTABLISHED_LEVELS])[0]
        level = rng.randint(lo, hi)
    online = scenario == "fresh" or rng.random() < 0.55
    return dict(id=i, type=t, tr=traits, level=level, xp=0.0, zone="Jordheim", region=100,
                state="offline", until=(rng.randint(0, 60) if online else rng.randint(60, 240)), camp=None, group=None,
                session_end=None, con_min=collections.Counter(),
                inv=0.0, mats=0, train=0, can_craft=False,   # no live caller for the Craft rule: today's bots never craft
                deaths_at={}, visited={}, deaths=0, chats=0, kind="SoloPve",
                rvr_min=0, grouped_min=0, town_min=0, active_min=0, budget=budget,
                hunt_min=0, craft_min=0, social_min=0, explore_min=0, act=None)

# ---------------- decision logic ----------------
def legal(bot, camp, group_size, P):
    c = con(bot["level"], camp["level"])
    if c == "grey": return False
    adv = 2 if group_size < 2 else 3
    if P and bot["tr"]["risk"] >= 8: adv += 1
    if camp["level"] > bot["level"] + adv: return False
    safer_after = 2 if not P else (4 if bot["tr"]["risk"] >= 8 else 1 if bot["tr"]["risk"] <= 3 else 2)
    if bot["deaths_at"].get(camp["id"], 0) >= safer_after and c != "green": return False
    return True

def choose_camp(bot, camps_by_band, occupancy, zone_pop, t, rng, P, group_size=1):
    L = bot["level"]
    cands = [c for c in camps_by_band.get(L, []) if legal(bot, c, group_size, P)]
    if not cands: return None
    has_d = any(c["dungeon"] for c in cands); has_o = any(not c["dungeon"] for c in cands)
    pref = 100 if group_size < 2 else (400 if L >= 50 else 300)
    if P:
        pref += bot["tr"]["risk"] * 15 - 75 + (50 if bot["type"] == "Explorer" else 0)
    want_d = has_d and (not has_o or rng.random() * 1000 < max(0, pref))
    pool = [c for c in cands if c["dungeon"] == want_d] or cands
    weights = []
    for c in pool:
        w = c["weight"]  # baseline: weighted by live spawns
        if P:
            tr = bot["tr"]
            last = bot["visited"].get(c["zone"])
            if last is None: w *= 1 + tr["cur"] * 0.5
            elif t - last < 180: w *= max(0.2, 1 - tr["cur"] * 0.06)
            w *= math.exp(-travel_minutes(bot["zone"], bot["region"], c) / (6 + tr["cur"] * 2))
            k = con(L, c["level"])
            w *= {"green": 1.2 - tr["risk"] * 0.08, "blue": 1.0, "yellow": 1.0,
                  "orange": 0.5 + tr["risk"] * 0.12, "red": 0.1 + tr["risk"] * 0.1}[k]
            if zone_pop.get(c["zone"], 0) > 0: w *= 1 + tr["soc"] * 0.08
            w = max(w, 1e-6)
        weights.append(w)
    return rng.choices(pool, weights=weights)[0]

def objective_kind(bot, rng, P):
    L = bot["level"]
    solo, group, rvr = (60, 40, 0) if L < 20 else (20, 40, 40) if L >= 50 else (40, 40, 20)
    if P:
        group = int(group * (0.5 + bot["tr"]["soc"] / 10)); total = solo + group + rvr
        solo, group, rvr = solo * 100 / total, group * 100 / total, rvr * 100 / total
    r = rng.random() * (solo + group + rvr)
    return "SoloPve" if r < solo else "GroupPve" if r < solo + group else "RvR"

def tenure(bot, rng, P):
    m = rng.randint(45, 120)
    return int(m * (0.6 + bot["tr"]["pat"] / 12.5)) if P else m

def downtime_chance(bot, P, strong=False):
    # LIVE rule (AutonomousTownDowntime): 15% chance of a 15-30 minute town break at each solo task boundary.
    if not P: return 0.15
    if strong: return 0.10   # time budgets already carry the personality's town time
    return 0.15 * {"Casual": 2.0, "Socialite": 1.7, "Explorer": 0.6, "Leveler": 0.3, "Daredevil": 1.0}[bot["type"]]

# ---------------- simulation ----------------
def run(seed, P, scenario="fresh", strong=False, econ=None, opts=None):
    """econ: None (no gear model), "loot" (gear from drops and vendors only) or "craft" (crafting economy)."""
    rng = random.Random(seed)
    opts = opts or {}
    camps = load_camps()
    zones = sorted({c["zone"] for c in camps})
    camps_by_band = {L: [c for c in camps if c["level"] - L <= 4 and c["level"] - L > -(4 + L // 10)] for L in range(1, 51)}
    weights = None
    if strong and "crafter_share" in opts:
        names = list(STRONG_TYPES); cs = opts["crafter_share"]; others = sum(STRONG_TYPES[n][0] for n in names if n != "Crafter")
        weights = [cs if n == "Crafter" else STRONG_TYPES[n][0] * (100 - cs) / others for n in names]
    bots = [make_bot(i, rng, P, scenario, strong, weights) for i in range(N_BOTS)]
    E = None
    if econ:
        E = lw_economy.Econ(random.Random(seed * 7919 + 1), econ == "craft", opts)
        E.by_id = {b["id"]: b for b in bots}
        for b in bots: E.init_bot(b, scenario == "established")
    zone_info = {}
    for c in camps:
        z = zone_info.setdefault(c["zone"], dict(region=c["region"], levels=[], dungeon=c["dungeon"]))
        z["levels"].append(c["level"])
    for z in zone_info.values():
        lv = sorted(z["levels"]); z["min"], z["median"] = lv[0], lv[len(lv) // 2]
    next_id = N_BOTS
    occupancy = collections.Counter(); group_of = {}; pool = []
    hourly = []
    for t in range(HOURS * 60):
        zone_pop = collections.Counter(b["zone"] for b in bots if b["state"] == "hunt")
        gsizes = collections.Counter(b["group"] for b in bots if b["group"])
        # group matchmaking: pool of (bot, joined_at)
        if pool:
            pool.sort(key=lambda e: e[0]["level"])
            formed, i = [], 0
            while i < len(pool):
                j = i
                while j + 1 < len(pool) and pool[j + 1][0]["level"] - pool[i][0]["level"] <= 4 and j - i < 5: j += 1
                if j - i + 1 >= 3:
                    members = [e[0] for e in pool[i:j + 1]]
                    lead = max(members, key=lambda b: b["level"])
                    gl = round(statistics.mean(b["level"] for b in members))
                    proxy = dict(lead, level=gl)
                    camp = choose_camp(proxy, camps_by_band, occupancy, zone_pop, t, rng, P, len(members))
                    if camp:
                        gid = (t, lead["id"]); occupancy[camp["id"]] += 1
                        dur = tenure(lead, rng, P)
                        for b in members:
                            b.update(state="hunt", camp=camp, group=gid, zone=camp["zone"], region=camp["region"],
                                     until=t + travel_minutes(b["zone"], b["region"], camp) + dur)
                            b["visited"][camp["zone"]] = t
                        formed.extend(range(i, j + 1))
                    i = j + 1
                else:
                    i += 1
            pool = [e for k, e in enumerate(pool) if k not in set(formed)]
            for e in list(pool):
                if t - e[1] >= 20:  # matchmaking timeout -> solo fallback
                    pool.remove(e); e[0]["kind"] = "SoloPve"; e[0]["state"] = "decide"; e[0]["until"] = t
        for b in bots:
            if b["state"] == "offline":
                if t >= b["until"]:
                    b["state"] = "decide"
                    if scenario == "established": b["session_end"] = t + rng.randint(120, 300)
                continue
            if b["state"] == "pool": continue
            b["active_min"] += 1
            if b["state"] == "hunt":
                camp = b["camp"]; c = con(b["level"], camp["level"])
                units = occupancy[camp["id"]]
                eff = min(1.0, CAPACITY_UNITS / max(1, units))
                gsize = gsizes[b["group"]] if b["group"] else 1
                rate = XP_RATE.get(c, 0.3) * eff * (1.15 if gsize >= 2 else 1.0)
                if E: rate *= 0.85 + 0.3 * b["fit"]; E.hunt_minute(b, camp["level"], eff)   # ASSUMPTION: gear helps
                b["xp"] += rate / 60 / hours_to_level(b["level"])
                b["inv"] += 22 / 60; b["mats"] += 1 / 60
                if b["group"]: b["grouped_min"] += 1
                b["con_min"][c] += 1; b["hunt_min"] += 1
                pdeath = DEATH_PER_HOUR.get(c, 0.6) / 60 * (0.4 if gsize >= 2 else 1.0)
                if E: pdeath *= 1.4 - 0.8 * b["fit"]
                if rng.random() < pdeath:
                    b["deaths"] += 1; b["deaths_at"][camp["id"]] = b["deaths_at"].get(camp["id"], 0) + 1
                    b["until"] += 8
                if P and rng.random() < b["tr"]["chat"] * 0.15 / 60: b["chats"] += 1
                elif not P and rng.random() < 0.5 / 60: b["chats"] += 1
                while b["xp"] >= 1 and b["level"] < 50:
                    b["xp"] -= 1; b["level"] += 1; b["train"] += 1
                    if E: b["fit"] = E.fit(b)
                if t >= b["until"] or b["inv"] >= 100:
                    if b["group"] is None or t >= b["until"]:
                        occupancy[camp["id"]] -= (1 if b["group"] is None or b["id"] == b["group"][1] else 0)
                        b.update(state="decide", camp=None, group=None)
            elif b["state"] == "explore":
                b["explore_min"] += 1
                zi = zone_info[b["zone"]]
                b["xp"] += 0.15 / 60 / hours_to_level(b["level"])
                pd = (0.25 if zi["median"] > b["level"] + 5 else 0.03) / 60
                if rng.random() < pd: b["deaths"] += 1; b["until"] += 8
                if P and rng.random() < b["tr"]["chat"] * 0.15 / 60: b["chats"] += 1
                while b["xp"] >= 1 and b["level"] < 50:
                    b["xp"] -= 1; b["level"] += 1; b["train"] += 1
                    if E: b["fit"] = E.fit(b)
                if t >= b["until"]: b["state"] = "decide"
            elif b["state"] in ("town", "rvr"):
                if b["state"] == "town":
                    b["town_min"] += 1
                    if b["act"] == "craft": b["craft_min"] += 1
                    elif b["act"] == "social": b["social_min"] += 1
                else: b["rvr_min"] += 1
                if P and b["state"] == "town" and rng.random() < b["tr"]["chat"] * 0.15 / 60: b["chats"] += 1
                if t >= b["until"]:
                    if E and b["state"] == "town": E.town_visit(b, t, b["type"] == "Crafter")
                    b["state"] = "decide"
            if b["state"] == "decide" and b["session_end"] is not None and t >= b["session_end"]:
                b.update(state="offline", until=t + rng.randint(60, 240), session_end=None); continue
            if b["state"] == "decide":
                # services first (mirrors AutonomousBotDecisionEngine.Choose order)
                if b["inv"] >= 88:
                    b.update(state="town", until=t + 6 + 8, inv=0, zone="Jordheim", region=100); continue
                if b["train"] > 0 and rng.random() < 0.90:   # live: RollBetweenTaskPlan trains 90% of boundaries
                    b.update(state="town", until=t + 6 + 5, train=0, zone="Jordheim", region=100); continue
                cc = 0.40 if (P and b["type"] == "Casual") else 0.16
                if b["can_craft"] and b["mats"] >= 3 and rng.random() < cc:
                    b.update(state="town", until=t + 6 + 15, mats=0, zone="Jordheim", region=100); continue
                in_town = b["zone"] == "Jordheim"
                if rng.random() < downtime_chance(b, P, strong):   # live: any solo task boundary
                    b.update(state="town", until=t + (0 if in_town else 6) + rng.randint(15, 30), zone="Jordheim", region=100); continue
                if P and not in_town and b["type"] in ("Casual", "Socialite") and rng.random() < 0.12:
                    b.update(state="town", until=t + 6 + rng.randint(15, 30), zone="Jordheim", region=100); continue
                b["act"] = None
                if E and b["level"] >= 8 and E.rng.random() < 0.12 and E.needy_slots(b):   # ASSUMPTION: shop at natural breaks
                    b.update(state="town", until=t + 6 + 6, zone="Jordheim", region=100); continue
                if strong:
                    w = [share / ACT_MINUTES[a] for share, a in zip(b["budget"], ("hunt", "craft", "social", "explore"))]
                    act = rng.choices(("hunt", "craft", "social", "explore"), weights=w)[0]
                    if act in ("craft", "social"):
                        dur = rng.randint(30, 90) if act == "craft" else rng.randint(20, 60)
                        b.update(state="town", act=act, until=t + (0 if b["zone"] == "Jordheim" else 6) + dur,
                                 zone="Jordheim", region=100, mats=0 if act == "craft" else b["mats"])
                        if E and act == "craft": E.craft_session(b, dur, t)
                        continue
                    if act == "explore":
                        L = b["level"]
                        options = [z for z, zi in zone_info.items() if zi["min"] <= L + 6]
                        def zw(z):
                            last = b["visited"].get(z)
                            return 6.0 if last is None else (0.3 if t - last < 240 else 1.0)
                        z = rng.choices(options, weights=[zw(z) for z in options])[0]
                        zi = zone_info[z]
                        b.update(state="explore", zone=z, region=zi["region"],
                                 until=t + (14 if zi["region"] != b["region"] else 7) + rng.randint(30, 90))
                        b["visited"][z] = t; continue
                kind = objective_kind(b, rng, P); b["kind"] = kind
                if kind == "RvR":
                    b.update(state="rvr", until=t + rng.randint(45, 120), zone="Frontier", region=163); continue
                if kind == "GroupPve":
                    b["state"] = "pool"; pool.append((b, t)); continue
                camp = choose_camp(b, camps_by_band, occupancy, zone_pop, t, rng, P)
                if camp is None:
                    b["until"] = t + 5; continue
                occupancy[camp["id"]] += 1
                b.update(state="hunt", camp=camp, zone=camp["zone"], region=camp["region"], group=None,
                         until=t + travel_minutes(b["zone"], b["region"], camp) + tenure(b, rng, P))
                b["visited"][camp["zone"]] = t
        alt_every = opts.get("alt_every", 15)   # minutes between new alts per 300 bots; 0 = no alts
        if scenario == "established" and alt_every and t % alt_every == 0 and t > 0:
            cands_alt = [b for b in bots if b["state"] == "offline" and b["level"] >= 30]
            if cands_alt:
                b = rng.choice(cands_alt)
                b.update(level=1, xp=0.0, deaths_at={}, visited={}, train=0, inv=0.0)
                if E: E.reset_alt(b)
        if E and t % 30 == 0: E.expire(t)
        if E and (t // 60 + 1) % 10 == 0 and t % 60 == 59:
            lv = sorted(b["level"] for b in bots)
            cr = [b for b in bots if b["type"] == "Crafter"]
            E.snap.append(dict(hour=t // 60 + 1, sets=E.sets(bots), p90_level=lv[int(.9 * (len(lv) - 1))],
                               median_level=lv[len(lv) // 2],
                               crafter_skill_mean=round(statistics.mean(b["skill"] for b in cr), 1) if cr else 0,
                               crafter_skill_max=round(max((b["skill"] for b in cr), default=0), 1),
                               crafter_level_mean=round(statistics.mean(b["level"] for b in cr), 1) if cr else 0,
                               open_orders=len(E.orders), listings=len(E.listings),
                               median_open_order_level=(sorted(o["level"] for o in E.orders)[len(E.orders) // 2] if E.orders else 0),
                               mat_stock=[round(x) for x in E.mat_stock]))
        if t % 60 == 59:
            hunters = [b for b in bots if b["state"] == "hunt"]
            zc = collections.Counter(b["zone"] for b in hunters)
            n = len(hunters) or 1
            ent = -sum((v / n) * math.log(v / n) for v in zc.values()) / math.log(len(zones))
            crowded = sum(1 for b in hunters if occupancy[b["camp"]["id"]] > CAPACITY_UNITS) / n
            hourly.append(dict(hour=t // 60 + 1, zones=len(zc), evenness=round(ent, 3), crowded=round(crowded, 3),
                               town=sum(1 for b in bots if b["state"] == "town") / N_BOTS,
                               grouped=sum(1 for b in hunters if b["group"]) / n,
                               mean_level=statistics.mean(b["level"] for b in bots),
                               bands=[sum(1 for b in bots if a <= b["level"] <= a + 9) for a in (1, 11, 21, 31, 41)],
                               online=sum(1 for b in bots if b['state'] != 'offline'),
                               near={X: sum(1 for b in hunters if abs(b['level'] - X) <= 3) for X in (5, 15, 25, 35, 45)},
                               zone_counts=dict(zc),
                               exploring=sum(1 for b in bots if b['state'] == 'explore') / N_BOTS,
                               present_zones=len({b['zone'] for b in bots if b['state'] in ('hunt', 'explore')})))
    by_type = collections.defaultdict(list)
    for b in bots: by_type[b["type"]].append(b)
    types = {k: dict(n=len(v), level=round(statistics.mean(b["level"] for b in v), 1),
                     zones_seen=round(statistics.mean(len(b["visited"]) for b in v), 1),
                     deaths_per_h=round(statistics.mean(b["deaths"] for b in v) / HOURS, 2),
                     town_share=round(statistics.mean(b["town_min"] for b in v) / (HOURS * 60), 3),
                     grouped_share=round(statistics.mean(b["grouped_min"] for b in v) / (HOURS * 60), 3),
                     chats_per_h=round(statistics.mean(b["chats"] for b in v) / HOURS, 2),
                     hunt_share=round(statistics.mean(b['hunt_min'] for b in v) / (HOURS * 60), 3),
                     craft_share=round(statistics.mean(b['craft_min'] for b in v) / (HOURS * 60), 3),
                     social_share=round(statistics.mean(b['social_min'] for b in v) / (HOURS * 60), 3),
                     explore_share=round(statistics.mean(b['explore_min'] for b in v) / (HOURS * 60), 3),
                     hard_share=round(sum(b['con_min']['orange'] + b['con_min']['red'] for b in v) / max(1, sum(sum(b['con_min'].values()) for b in v)), 3))
             for k, v in by_type.items()}
    lv = sorted(b["level"] for b in bots)
    q = lambda p: lv[int(p * (len(lv) - 1))]
    levels = dict(p10=q(.1), p50=q(.5), p90=q(.9), std=round(statistics.pstdev(lv), 1),
                  bands={f"{a}-{a+9}": sum(1 for x in lv if a <= x <= a + 9) for a in (1, 11, 21, 31, 41)})
    result = dict(hourly=hourly, types=types, levels=levels, zones_total=len(zones))
    if E:
        cr = [b for b in bots if b["type"] == "Crafter"]
        others = [b for b in bots if b["type"] != "Crafter"]
        st = E.stats
        result["econ"] = dict(
            snaps=E.snap, stats=dict(st),
            band_orders=dict(E.band_orders), band_filled=dict(E.band_filled),
            fill_wait_median_min=(statistics.median(E.fill_wait) if E.fill_wait else None),
            n_crafters=len(cr),
            crafts_per_crafter=round(statistics.mean(b["crafts"] for b in cr), 1) if cr else 0,
            crafts_orders_per_crafter=round(statistics.mean(b["crafts_orders"] for b in cr), 1) if cr else 0,
            crafts_stock_per_crafter=round(statistics.mean(b["crafts_stock"] for b in cr), 1) if cr else 0,
            craft_idle_share=round(statistics.mean(b["craft_idle_min"] for b in cr) / max(1, statistics.mean(b["craft_min"] for b in cr) or 1), 2) if cr else 0,
            crafter_gold=round(statistics.mean(b["gold"] for b in cr)) if cr else 0,
            crafter_sales=round(statistics.mean(b["sales"] for b in cr)) if cr else 0,
            other_gold=round(statistics.mean(b["gold"] for b in others)),
            crafter_level=round(statistics.mean(b["level"] for b in cr), 1) if cr else 0,
            other_level=round(statistics.mean(b["level"] for b in others), 1),
            crafter_skill=round(statistics.mean(b["skill"] for b in cr), 1) if cr else 0,
            crafted_bought_share=round(st["purchases_crafted"] / max(1, st["purchases"]), 3),
            final_sets=E.sets(bots), final_open_orders=len(E.orders))
    return result

if __name__ == "__main__":
    out = {}
    for scen in ("fresh", "established"):
        for mode, P, st_ in (("baseline", False, False), ("mild", True, False), ("strong", True, True)):
            out[f"{scen}/{mode}"] = [run(s, P, scen, st_) for s in SEEDS]
    json.dump(out, open(sys.argv[3] if len(sys.argv) > 3 and sys.argv[3] else "sim_results.json", "w"))
    for label in out:
        runs = out[label]
        def avg(f): return round(statistics.mean(f(r) for r in runs), 3)
        def rng_(f): return (round(min(f(r) for r in runs), 3), round(max(f(r) for r in runs), 3))
        last = lambda r, k: statistics.mean(h[k] for h in r["hourly"][-4:])
        print(f"\n=== {label} ({len(runs)} seeds) ===")
        for k in ("online", "zones", "present_zones", "evenness", "crowded", "town", "exploring", "grouped", "mean_level"):
            print(f"  hours 17-20 {k:10}: {avg(lambda r: last(r, k))}  range {rng_(lambda r: last(r, k))}")
        for X in (5, 15, 25, 35, 45):
            print(f"  hours 17-20 bots hunting within 3 levels of a level-{X} player: {avg(lambda r, X=X: statistics.mean(h['near'][X] for h in r['hourly'][-4:]))}")
        print("  levels p10/p50/p90/std:", [avg(lambda r, k=k: r['levels'][k]) for k in ("p10", "p50", "p90", "std")])
        print("  level bands:", {b: avg(lambda r, b=b: r['levels']['bands'][b]) for b in runs[0]['levels']['bands']})
        for ty in runs[0]["types"]:
            print(f"  {ty:10}", {m: avg(lambda r, m=m: r['types'][ty][m]) for m in runs[0]['types'][ty] if m != 'n'})
