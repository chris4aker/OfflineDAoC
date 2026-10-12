"""Three-realm RvR model for Offline DAoC (a design model, not the game).

Grounded in the server's bot RvR code where it exists:
- Siege scheduler (AutonomousRvrEventLayer.SiegeStartChancePerMinute): with no siege running the chance
  per minute is 0.25 + 0.25 x idle minutes; with one, 0.04; with two, 0.012; never more than three.
- Siege caps: 128 attackers (240 for relic raids); relic raids are about 12% of sieges; 12-minute muster;
  defenders answer the army that actually marched (at least 8); a 12-minute cooldown per target.
- Realm points (AutonomousBotRealmPointRewards, pre-1.81): a victim is worth (level-20)^2 + realm level,
  split among the killers, plus 12.5% per extra group contributor; realm ranks from the server's table.
- RvR goal mix (BotGoalSettings defaults): 20% of levels 20-49 and 40% of level 50s choose RvR.

Not in the server today, proposed here: PvE camps in each realm's own frontier (the bots' camp catalog has
no frontier zones), with better rewards nearer the enemy, and warnings when enemies are in a zone.

Everything marked ASSUMPTION is a guess. Compare scenarios; do not trust absolute numbers.
Usage: python3 rvr_sim.py [seeds e.g. 1,2,3] [hours] [output.json]
"""
import collections, json, math, os, random, statistics, sys
from multiprocessing import Pool

REALMS = ("Albion", "Midgard", "Hibernia")
RINGS = ("border", "middle", "inner")
RP_TABLE = {10: 7125, 20: 61750, 30: 213875, 40: 513500}   # realm level index -> RP (RR2, RR3, RR4, RR5), server table
RR_LEVELS = [0, 0, 25, 125, 350, 750, 1375, 2250, 3500, 5125, 7125, 9625, 12625, 16125, 20125, 24625, 29625,
             35125, 41125, 47625, 54625, 61750, 71750, 82750, 94750, 107750, 121750, 136750, 152750, 169750,
             187750, 213875, 236375, 260375, 285875, 312875, 341375, 371375, 402875, 435875, 470375, 513500]


def realm_level(rp):
    lvl = 0
    for i, need in enumerate(RR_LEVELS):
        if rp >= need:
            lvl = i
    return lvl


def rp_value(level, rlevel):
    m = level - 20
    return max(1, m * m) + rlevel


# ---------------- ASSUMPTIONS ----------------
POOL_PER_1000 = 400          # RvR-capable characters per realm per 1,000 online (they rotate through sessions)
ROLE_SHARES = (("zerg", 0.45), ("roam", 0.43), ("stealth", 0.12))
NOLIFER_SHARE = 0.10         # of the RvR pool: always online
GUARDS = {"keep": 10, "relic": 25}          # guard strength in level-50 bot equivalents
DOOR_MULT = {"keep": 1.3, "relic": 1.5}     # defenders' advantage behind doors and walls
DEFENSE_RATIO = 0.8          # defenders sent per attacker who marched (server: "DefenseRatio", value not checked)
THIRD_REALM_JOIN = 0.3
MEET_PER_MIN = 0.04          # chance per minute that two hostile groups in the same zone meet
STEALTH_KILL_PER_MIN = 0.003 # chance per minute that a stealther finds and kills a given enemy PvE bot in its (large) zone
SPOT_PER_MIN = 0.005         # chance per minute a roaming group sweeps past a given enemy PvE bot (zones are large)
STEALTH_CAUGHT_PER_MIN = 0.002   # chance per minute an enemy roaming group catches a stealther in its zone
WARNED_EVADE = 0.6           # PvE bots warned of a group in their zone escape this often (stealthers give no warning)
RELIC_BONUS = 0.05           # power per relic held beyond your own two (classic relics gave +10% damage per type)
RUN_BACK_MIN = 15            # after a death: release, respawn and travel back
# ---- fixes under test (2026-10-11), each behind an option ----
GUARD_FACTOR = {"border": 1.0, "middle": 0.6, "inner": 0.25}   # guarded_frontier: guards and patrols cut enemy reach by depth
GUARD_PATROL_PER_MIN = 0.01  # guarded_frontier: chance per minute an enemy group deep in the inner zone loses members to guards
REWARD = {"border": 2.0, "middle": 1.5, "inner": 1.2}       # proposed frontier PvE reward vs a home zone, by depth


class World:
    def __init__(self, seed, opts):
        self.rng = random.Random(seed)
        self.o = opts
        self.t = 0
        self.zones = [(r, ring, i) for r in REALMS for ring, n in (("border", 2), ("middle", 2), ("inner", 1)) for i in range(n)]
        # keeps: 7 per frontier (border 1 each, middle 2 each, inner 1) + 2 relic keeps in the inner zone
        self.keeps = []
        for r in REALMS:
            for z in self.zones:
                if z[0] != r:
                    continue
                n = {"border": 1, "middle": 2, "inner": 1}[z[1]]
                for i in range(n):
                    self.keeps.append(dict(id=f"{r}-{z[1]}{z[2]}-{i}", frontier=r, zone=z, kind="keep", owner=r, cooldown=0))
            for i in range(2):
                self.keeps.append(dict(id=f"{r}-relic-{i}", frontier=r, zone=(r, "inner", 0), kind="relic", owner=r, cooldown=0,
                                       relic_home=r, relic_holder=r))
        self.agents = []
        for r in REALMS:
            pop = opts.get("population", {}).get(r, 1000)
            for i in range(int(POOL_PER_1000 * pop / 1000)):
                role = self.rng.choices([x for x, _ in ROLE_SHARES], weights=[w for _, w in ROLE_SHARES])[0]
                nolifer = self.rng.random() < NOLIFER_SHARE
                level = 50 if self.rng.random() < 0.5 else self.rng.randint(20, 49)
                self.agents.append(dict(realm=r, role=role, nolifer=nolifer, level=level, rp=0.0, kills=0, deaths=0,
                                        online=nolifer, until=0 if nolifer else self.rng.randint(0, 240),
                                        state="idle", busy_until=0, group=None, zone=None, active_min=0, rp_log=[],
                                        role_rp=collections.Counter(), role_min=collections.Counter()))
        # PvE bots farming their own frontier (proposed content): per realm, a share of the level 35+ PvE population
        self.pve = []
        share = opts.get("frontier_pve_share", 0.08)
        for r in REALMS:
            pop = opts.get("population", {}).get(r, 1000)
            n = int(pop * 0.36 * share)               # about 36% of online bots are 35+ and doing PvE (ASSUMPTION)
            for i in range(n):
                ring = self.rng.choices(RINGS, weights=opts.get("pve_ring_weights", (0.4, 0.4, 0.2)))[0]
                zones = [z for z in self.zones if z[0] == r and z[1] == ring]
                self.pve.append(dict(realm=r, ring=ring, zone=self.rng.choice(zones), dead_until=0, deaths=0, minutes=0))
        self.groups = {}           # id -> dict(realm, members, zone, until, kind)
        self.next_gid = 0
        self.sieges = []
        self.idle_since = 0
        self.stats = collections.Counter()
        self.hourly = []
        self.df_owner = None
        self.role_rates = {}
        self.df_minutes = collections.Counter()

    # ----- helpers -----
    def power(self, a):
        held = sum(1 for k in self.keeps if k["kind"] == "relic" and k["relic_holder"] == a["realm"])
        mult = 1 + (RELIC_BONUS * (held - 2) if self.o.get("relic_bonus", True) else 0)
        mult *= 1 + self.underdog(a["realm"])
        return (a["level"] / 50) ** 2 * (1 + 0.03 * (realm_level(a["rp"]) // 10)) * mult

    def underdog(self, realm):
        if not self.o.get("underdog_bonus"):
            return 0.0
        counts = {r: sum(1 for k in self.keeps if k["owner"] == r and k["kind"] == "keep") for r in REALMS}
        return self.o["underdog_bonus"] if counts[realm] == min(counts.values()) and counts[realm] < max(counts.values()) else 0.0

    def available(self, realm, roles):
        return [a for a in self.agents if a["realm"] == realm and a["online"] and a["state"] == "idle" and a["role"] in roles]

    def add_rp(self, a, amount):
        a["rp"] += amount
        a["role_rp"][a["role"]] += amount

    def kill(self, victims, killers, mult=1.0):
        """Victims die; killers share realm points like the server formula (mult: small-group bonus under test)."""
        if not victims:
            return
        n = max(1, len(killers))
        for v in victims:
            v["deaths"] += 1
            v["state"] = "dead"
            v["busy_until"] = self.t + RUN_BACK_MIN
            self.leave_group(v)
            if not killers:
                continue
            val = rp_value(v["level"], realm_level(v["rp"]))
            for k in killers:
                share = min(val / n, 2 * rp_value(k["level"], realm_level(k["rp"])))
                self.add_rp(k, share * (1 + 0.125 * (n - 1)) * mult)
                k["kills"] += 1 / n
            self.stats["rvr_deaths"] += 1

    def small_bonus(self, killers, victims_side):
        """Option smallgroup_rp: open-field kills by groups of 8 or fewer pay 1.5x, and outnumbered kills pay up to 2x more."""
        if not self.o.get("smallgroup_rp") or not killers:
            return 1.0
        mult = 1.5 if len(killers) <= 8 else 1.0
        return mult * min(2.0, max(1.0, len(victims_side) / len(killers)))

    def leave_group(self, a):
        g = a.get("group")
        if g is not None and g in self.groups:
            self.groups[g]["members"] = [m for m in self.groups[g]["members"] if m is not a]
            if not self.groups[g]["members"]:
                del self.groups[g]
        a["group"] = None

    def fight(self, A, B):
        """Lanchester square: the stronger side usually wins; the loser is mostly wiped."""
        rng = self.rng
        sa, sb = sum(self.power(a) for a in A), sum(self.power(b) for b in B)
        if sa <= 0 or sb <= 0:
            return None
        p = sa * sa / (sa * sa + sb * sb)
        win, lose, sw, sl = (A, B, sa, sb) if rng.random() < p else (B, A, sb, sa)
        lose_dead = [x for x in lose if rng.random() < rng.uniform(0.7, 1.0)]
        win_dead = [x for x in win if rng.random() < min(0.9, rng.uniform(0.1, 0.4) * sl / sw)]
        self.kill(lose_dead, [x for x in win if x not in win_dead], self.small_bonus(win, lose))
        self.kill(win_dead, [x for x in lose if x not in lose_dead], self.small_bonus(lose, win))
        self.stats["fights"] += 1
        return win

    # ----- sieges -----
    def siege_tick(self):
        rng, t = self.rng, self.t
        active = [s for s in self.sieges if s["phase"] != "done"]
        if not active and self.idle_since is None:
            self.idle_since = t
        if active:
            self.idle_since = None
        idle = (t - self.idle_since) if self.idle_since is not None else 0
        chance = {0: min(1.0, 0.25 + 0.25 * idle), 1: 0.04, 2: 0.012}.get(len(active), 0.0)
        if rng.random() < chance:
            self.start_siege()
        for s in active:
            if s["phase"] == "muster" and t >= s["march_at"]:
                self.march(s)
            elif s["phase"] == "battle" and t >= s["end_at"]:
                self.resolve(s)
        self.sieges = [s for s in self.sieges if s["phase"] != "done"]

    def start_siege(self):
        rng, t = self.rng, self.t
        realm_force = {r: len(self.available(r, ("zerg",))) for r in REALMS}
        attacker = rng.choices(REALMS, weights=[max(1, realm_force[r]) for r in REALMS])[0]
        if realm_force[attacker] < 10:
            return
        # retake own keeps first, then border keeps of enemies; relic raids about 12% (needs 3+ keeps in that frontier)
        targets = [k for k in self.keeps if k["owner"] != attacker and k["cooldown"] <= t and k["kind"] == "keep"]
        own_lost = [k for k in targets if k["frontier"] == attacker]
        if own_lost and rng.random() < 0.6:
            target = rng.choice(own_lost)
        else:
            relics = [k for k in self.keeps if k["kind"] == "relic" and k["relic_holder"] != attacker and k["cooldown"] <= t
                      and sum(1 for x in self.keeps if x["frontier"] == k["frontier"] and x["owner"] == attacker and x["kind"] == "keep") >= 3]
            if relics and rng.random() < 0.12:
                target = rng.choice(relics)
            elif targets:
                w = [{"border": 6, "middle": 3, "inner": 1}[k["zone"][1]] for k in targets]
                target = rng.choices(targets, weights=w)[0]
            else:
                return
        cap = 240 if target["kind"] == "relic" else 128
        army = self.available(attacker, ("zerg",))[:cap]
        for a in army:
            a["state"] = "siege"
        s = dict(attacker=attacker, target=target, army=army, phase="muster", march_at=t + 12, start=t)
        self.sieges.append(s)
        target["cooldown"] = t + 12
        self.stats["sieges_started"] += 1
        self.stats["relic_raids"] += target["kind"] == "relic"

    def march(self, s):
        rng, t = self.rng, self.t
        k = s["target"]
        defender = k["owner"] if k["kind"] == "keep" else k["relic_holder"]
        s["army"] = [a for a in s["army"] if a["state"] == "siege"]
        need = max(8, int(DEFENSE_RATIO * len(s["army"])))
        pool = self.available(defender, ("zerg",)) + self.available(defender, ("roam",))
        s["defense"] = pool[:need]
        for a in s["defense"]:
            a["state"] = "siege"
        s["third"] = []
        third = [r for r in REALMS if r not in (s["attacker"], defender)][0]
        if rng.random() < THIRD_REALM_JOIN:
            s["third"] = self.available(third, ("zerg",))[: max(4, len(s["army"]) // 2)]
            for a in s["third"]:
                a["state"] = "siege"
        s["defender"] = defender
        s["phase"] = "battle"
        s["end_at"] = t + rng.randint(20, 45)

    def resolve(self, s):
        rng = self.rng
        k = s["target"]
        A = [a for a in s["army"] if a["state"] == "siege"]
        D = [a for a in s["defense"] if a["state"] == "siege"]
        T = [a for a in s["third"] if a["state"] == "siege"]
        guards = GUARDS[k["kind"]]
        sa = sum(self.power(a) for a in A)
        sd = (sum(self.power(a) for a in D) + guards) * DOOR_MULT[k["kind"]]
        if T:                                   # the third realm hits whichever side is winning
            st_ = sum(self.power(a) for a in T)
            if sa > sd:
                sa = max(0.1, sa - 0.5 * st_)
            else:
                sd = max(0.1, sd - 0.5 * st_)
        p = sa * sa / (sa * sa + sd * sd) if sa > 0 else 0.0
        attacker_wins = rng.random() < p
        win, lose = (A, D) if attacker_wins else (D, A)
        loss_l, loss_w = rng.uniform(0.4, 0.7), rng.uniform(0.15, 0.35)
        dead_l = [x for x in lose if rng.random() < loss_l]
        dead_w = [x for x in win if rng.random() < loss_w]
        self.kill(dead_l, [x for x in win if x not in dead_w])
        self.kill(dead_w, [x for x in lose if x not in dead_l])
        if T:
            dead_t = [x for x in T if rng.random() < 0.3]
            self.kill(dead_t, [x for x in win if x not in dead_w])
        if attacker_wins:
            self.stats["sieges_won"] += 1
            if k["kind"] == "keep":
                k["owner"] = s["attacker"]
                self.stats["keep_flips"] += 1
            else:
                k["relic_holder"] = s["attacker"]
                self.stats["relic_captures"] += 1
        for a in A + D + T:
            if a["state"] == "siege":
                a["state"] = "idle"
        s["phase"] = "done"
        self.stats["siege_participants"] += len(s["army"]) + len(s["defense"]) + len(s["third"])

    # ----- roaming and stealth -----
    def form_groups(self):
        for r in REALMS:
            free = self.available(r, ("roam",))
            self.rng.shuffle(free)
            for i in range(0, len(free) - 2, 8):
                members = free[i:i + 8]
                if len(members) < 3:
                    break
                self.new_group(r, members, "roam")
            for a in self.available(r, ("stealth",)):
                self.new_group(r, [a], "stealth")

    def new_group(self, realm, members, kind):
        gid = self.next_gid
        self.next_gid += 1
        zone = self.pick_zone(realm, kind)
        travel = {"border": 10, "middle": 20, "inner": 30}[zone[1]]
        self.groups[gid] = dict(realm=realm, members=members, zone=zone, arrive=self.t + travel,
                                until=self.t + travel + self.rng.randint(30, 60), kind=kind)
        for a in members:
            a["state"] = "group"
            a["group"] = gid

    def pick_zone(self, realm, kind):
        rng = self.rng
        if kind == "roam" and rng.random() < 0.25:     # defensive patrol in your own border zones
            return rng.choice([z for z in self.zones if z[0] == realm and z[1] == "border"])
        enemy = rng.choice([r for r in REALMS if r != realm])
        weights = (0.55, 0.35, 0.10) if kind == "roam" else (0.4, 0.4, 0.2)
        ring = rng.choices(RINGS, weights=weights)[0]
        return rng.choice([z for z in self.zones if z[0] == enemy and z[1] == ring])

    def roam_tick(self):
        rng, t = self.rng, self.t
        by_zone = collections.defaultdict(list)
        for gid, g in list(self.groups.items()):
            if t >= g["until"] or not g["members"]:
                for a in g["members"]:
                    a["state"] = "idle"
                    a["group"] = None
                self.groups.pop(gid, None)
                continue
            if t >= g["arrive"]:
                by_zone[g["zone"]].append(gid)
        for zone, gids in by_zone.items():
            # group vs group
            for i in range(len(gids)):
                for j in range(i + 1, len(gids)):
                    a, b = self.groups.get(gids[i]), self.groups.get(gids[j])
                    if not a or not b or a["realm"] == b["realm"] or "stealth" in (a["kind"], b["kind"]):
                        continue
                    if rng.random() < MEET_PER_MIN:
                        # the smaller side tries to run if badly outnumbered
                        small, big = (a, b) if len(a["members"]) < len(b["members"]) else (b, a)
                        if len(big["members"]) >= 2 * len(small["members"]) and rng.random() < 0.5:
                            self.stats["evasions"] += 1
                            continue
                        self.fight(list(a["members"]), list(b["members"]))
            # roaming groups sometimes catch enemy stealthers in their zone
            for gid in gids:
                g = self.groups.get(gid)
                if not g or g["kind"] != "stealth":
                    continue
                hunters = [self.groups[h] for h in gids if h in self.groups and self.groups[h]["kind"] == "roam"
                           and self.groups[h]["realm"] != g["realm"]]
                if hunters and rng.random() < STEALTH_CAUGHT_PER_MIN * len(hunters):
                    self.kill(list(g["members"]), list(hunters[0]["members"]))
            # guards and patrols in the inner zone wear down enemy groups (guarded_frontier)
            if self.o.get("guarded_frontier") and zone[1] == "inner":
                for gid in gids:
                    g = self.groups.get(gid)
                    if g and g["realm"] != zone[0] and rng.random() < GUARD_PATROL_PER_MIN * (1 if g["kind"] == "roam" else 0.5):
                        lost = g["members"][: rng.randint(1, 2)]
                        self.kill(list(lost), [])
                        self.stats["guard_kills"] += len(lost)
            # hunters vs PvE bots farming that frontier
            hostile = [self.groups[g] for g in gids if g in self.groups and self.groups[g]["realm"] != zone[0]]
            if not hostile:
                continue
            warned = any(h["kind"] == "roam" for h in hostile) and self.o.get("warnings", True)
            for pb in self.pve:
                if pb["zone"] != zone or pb["dead_until"] > t:
                    continue
                for h in hostile:
                    p = STEALTH_KILL_PER_MIN if h["kind"] == "stealth" else SPOT_PER_MIN
                    if self.o.get("guarded_frontier"):
                        p *= GUARD_FACTOR[pb["ring"]]
                    if rng.random() < p:
                        if h["kind"] == "roam" and warned and rng.random() < WARNED_EVADE:
                            self.stats["pve_escapes"] += 1
                            break
                        pb["deaths"] += 1
                        pb["dead_until"] = t + RUN_BACK_MIN
                        self.stats[f"pve_deaths_{pb['ring']}"] += 1
                        lvl = 45
                        for k in h["members"]:
                            self.add_rp(k, rp_value(lvl, 0) / len(h["members"]) * (1 + 0.125 * (len(h["members"]) - 1)))
                        break

    def maybe_switch_role(self, a):
        """Option adaptive_roles: half the time at login, re-pick a role weighted by base share x the realm's recent RP per hour."""
        if not self.o.get("adaptive_roles") or self.rng.random() < 0.5:
            return
        rates = self.role_rates.get(a["realm"])
        if not rates:
            return
        roles = [r for r, _ in ROLE_SHARES]
        w = [share * max(1.0, rates.get(r, 1.0)) for r, share in ROLE_SHARES]
        a["role"] = self.rng.choices(roles, weights=w)[0]

    def update_role_rates(self):
        self.role_rates = {}
        for realm in REALMS:
            rates = {}
            for role, _ in ROLE_SHARES:
                rp = sum(a["role_rp"][role] for a in self.agents if a["realm"] == realm)
                mins = sum(a["role_min"][role] for a in self.agents if a["realm"] == realm)
                rates[role] = rp / max(1, mins / 60)
            self.role_rates[realm] = rates

    # ----- sessions -----
    def sessions(self):
        rng, t = self.rng, self.t
        for a in self.agents:
            if a["nolifer"]:
                a["online"] = True
            elif t >= a["until"]:
                if a["online"] and a["state"] in ("idle", "dead"):
                    a["online"] = False
                    a["until"] = t + rng.randint(60, 240)
                elif not a["online"]:
                    a["online"] = True
                    a["until"] = t + rng.randint(120, 300)
                    self.maybe_switch_role(a)
            if a["state"] == "dead" and t >= a["busy_until"]:
                a["state"] = "idle"
            if a["online"]:
                a["active_min"] += 1
                a["role_min"][a["role"]] += 1
            if a["nolifer"] and t % 180 == 0 and a["state"] == "idle":
                self.maybe_switch_role(a)
        for pb in self.pve:
            if pb["dead_until"] <= t:
                pb["minutes"] += 1

    def run(self, hours):
        for t in range(hours * 60):
            self.t = t
            self.sessions()
            self.siege_tick()
            if t % 10 == 0:
                self.form_groups()
            if t % 60 == 0 and t > 0:
                self.update_role_rates()
            self.roam_tick()
            counts = {r: sum(1 for k in self.keeps if k["owner"] == r and k["kind"] == "keep") for r in REALMS}
            top = max(counts.values())
            leaders = [r for r in REALMS if counts[r] == top]
            if self.df_owner not in leaders:
                self.df_owner = leaders[0] if len(leaders) == 1 else self.df_owner
            if self.df_owner:
                self.df_minutes[self.df_owner] += 1
            if t % 60 == 59:
                self.hourly.append(dict(hour=t // 60 + 1, keeps=counts,
                                        relics={r: sum(1 for k in self.keeps if k["kind"] == "relic" and k["relic_holder"] == r) for r in REALMS},
                                        df=self.df_owner,
                                        roam_groups={r: sum(1 for g in self.groups.values() if g["realm"] == r and g["kind"] == "roam") for r in REALMS},
                                        in_siege=sum(1 for a in self.agents if a["state"] == "siege"),
                                        rp_mean={r: round(statistics.mean(a["rp"] for a in self.agents if a["realm"] == r)) for r in REALMS}))
        return self.result(hours)

    def result(self, hours):
        out = dict(stats=dict(self.stats), hourly=self.hourly, df_share={r: round(self.df_minutes[r] / (hours * 60), 3) for r in REALMS})
        roles = {}
        for r in REALMS:
            for role in ("zerg", "roam", "stealth"):
                grp = [a for a in self.agents if a["realm"] == r and a["role"] == role and a["active_min"] > 0]
                if not grp:
                    continue
                rph = [a["rp"] / (a["active_min"] / 60) for a in grp]
                dph = [a["deaths"] / (a["active_min"] / 60) for a in grp]
                roles[f"{r}/{role}"] = dict(rp_per_hour=round(statistics.mean(rph)), deaths_per_hour=round(statistics.mean(dph), 2),
                                            kills_per_hour=round(statistics.mean(a["kills"] / (a["active_min"] / 60) for a in grp), 2))
        out["roles"] = roles
        ranks = {}
        for r in REALMS:
            grp = [a for a in self.agents if a["realm"] == r]
            ranks[r] = dict(rr2_plus=sum(1 for a in grp if a["rp"] >= RP_TABLE[10]), rr3_plus=sum(1 for a in grp if a["rp"] >= RP_TABLE[20]),
                            rr4_plus=sum(1 for a in grp if a["rp"] >= RP_TABLE[30]), rr5_plus=sum(1 for a in grp if a["rp"] >= RP_TABLE[40]),
                            top_rp=round(max(a["rp"] for a in grp)), nolifer_rp_median=round(statistics.median(a["rp"] for a in grp if a["nolifer"])),
                            pool=len(grp))
        out["ranks"] = ranks
        pve = {}
        for ring in RINGS:
            grp = [p for p in self.pve if p["ring"] == ring]
            mins = sum(p["minutes"] for p in grp)
            pve[ring] = dict(bots=len(grp), deaths_per_hour=round(sum(p["deaths"] for p in grp) / max(1, mins / 60), 3))
        for ring in RINGS:
            grp = [p for p in self.pve if p["ring"] == ring]
            alive = sum(p["minutes"] for p in grp) / max(1, len(grp) * hours * 60)
            pve[ring]["alive_share"] = round(alive, 3)
            pve[ring]["value_vs_home"] = round(REWARD[ring] * alive, 2)
        out["frontier_pve"] = pve
        shares, rates = {}, {}
        for r in REALMS:
            mins = collections.Counter()
            rp = collections.Counter()
            for a in self.agents:
                if a["realm"] == r:
                    mins.update(a["role_min"])
                    rp.update(a["role_rp"])
            tot = sum(mins.values()) or 1
            shares[r] = {k: round(mins[k] / tot, 3) for k, _ in ROLE_SHARES}
            rates[r] = {k: round(rp[k] / max(1, mins[k] / 60)) for k, _ in ROLE_SHARES}
        out["role_time_share"] = shares
        out["role_rp_per_hour"] = rates
        return out


SCENARIOS = {
    "balanced 1000/1000/1000": dict(),
    "Hibernia underpopulated (750)": dict(population={"Hibernia": 750}),
    "Hibernia 750 + underdog bonus 15%": dict(population={"Hibernia": 750}, underdog_bonus=0.15),
    "balanced, no relic bonus": dict(relic_bonus=False),
    "balanced, no enemy warnings for frontier PvE": dict(warnings=False),
}


FIX_SCENARIOS = {
    "baseline (balanced)": dict(),
    "adaptive roles, no fix": dict(adaptive_roles=True),
    "small-group RP bonus + adaptive roles": dict(smallgroup_rp=True, adaptive_roles=True),
    "guarded, graded frontier": dict(guarded_frontier=True),
    "both fixes + adaptive roles": dict(smallgroup_rp=True, adaptive_roles=True, guarded_frontier=True),
}
ACTIVE = FIX_SCENARIOS if os.environ.get("RVR_SET") == "fix" else SCENARIOS


def _job(a):
    name, seed, hours = a
    return name, seed, World(seed, ACTIVE[name]).run(hours)


if __name__ == "__main__":
    seeds = [int(s) for s in (sys.argv[1] if len(sys.argv) > 1 else "1,2,3").split(",")]
    hours = int(sys.argv[2]) if len(sys.argv) > 2 else 60
    out = sys.argv[3] if len(sys.argv) > 3 else "rvr_results.json"
    with Pool(2) as pool:
        done = pool.map(_job, [(n, s, hours) for n in ACTIVE for s in seeds])
    json.dump({n: [r for nn, s, r in done if nn == n] for n in ACTIVE}, open(out, "w"))
    print("saved", out)
