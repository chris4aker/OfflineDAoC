"""Living World v3: bot PLAYERS with character rosters, at full-server scale (a design model, not the game).

What is new compared with living_world_sim.py:
- A bot player (persona) owns up to 3 characters. The main is kept forever; alts are ADDED, never
  rerolled. All characters share the player's gold (the server has an account vault).
- Players belong to guilds. Orders go to a guild crafter first.
- Occasionally a whole player retires and a new player joins with a level-1 main. Nothing is deleted.
- Crafting follows the server's real quality rule (AbstractCraftingSkill.GetQuality): crafted items are
  96-99% quality; a 100% masterpiece is a 2% chance, only for a Legendary crafter (skill 1000) or a
  grey recipe. Recipe level = item level x 20 (ASSUMPTION).
- Crafting materials are bought from vendors (a gold sink), as in DAoC.
- Gear has two parts: base (level x quality) and bonus stats B. Spellcrafting adds B up to 8 for gold.
  Rare drops have random B from 4 to 12. A "template" = all 7 slots level-appropriate with B >= 8.

Every number marked ASSUMPTION is a guess to be calibrated. Compare runs; do not trust absolutes.
Usage: python3 persona_sim.py [seeds e.g. 1,2,3] [hours] [output.json]
"""
import collections, json, math, os, random, statistics, sys
from multiprocessing import Pool

_HERE = os.path.dirname(os.path.abspath(__file__))
_saved = sys.argv
sys.argv = ["living_world_sim.py", "", "1"]
sys.path.insert(0, _HERE)
import living_world_sim as LW          # reuse the real camp catalog and camp choice
sys.argv = _saved

SLOTS = 7
TYPES = LW.STRONG_TYPES               # Leveler, Crafter, Socialite, Explorer, Daredevil with time budgets
ACTS = ("hunt", "craft", "social", "explore")


# ---------------- economy constants (ASSUMPTIONS) ----------------
def income_per_hour(level):            # coins per hunting hour (mob coin + vendor loot)
    return 2.0 * level ** 1.5


def mats_cost(item_level):             # vendor materials for one crafted piece
    return 0.25 * item_level ** 2


PRICE_MULT = 1.0                       # sensitivity: makes crafted + spellcrafted gear pricier


def spellcraft_cost(item_level, bonus):   # gems/dusts to add `bonus` stat points (max 8)
    return 0.05 * item_level ** 2 * bonus * PRICE_MULT


CRAFT_MARKUP = 2.0                     # crafter's price = materials x markup
CRAFT_MINUTES = 0.75                   # per craft (DAoC crafts take seconds to a minute)
SKILLUP_RESALE = 0.5                   # skill-up pieces are vendored for half their materials
COMMON_LOOT_PER_HOUR = 1.0
RARE_PER_HOUR = 0.25                   # rare drops per hunting hour at level 45+ camps (named, dungeons)
RARE_PER_HOUR_LOW = 0.08               # below level 45
UPKEEP = 0.05                          # share of income lost to repairs, deaths, travel fees (sink)


def craft_quality(skill, recipe, rng):
    """The server's rule (AbstractCraftingSkill.GetQuality + GetItemCon)."""
    if skill >= 1000 or recipe - skill <= -50:
        return 100 if rng.random() < 0.02 else 96 + rng.randrange(3)
    diff = recipe - skill
    delta = -2 if diff <= -31 else -1 if diff <= -11 else 0 if diff <= 0 else 1 if diff <= 19 else 2
    parts = [max((4 - i) * 100 - delta * 100, 0) for i in range(4)]
    roll = rng.randrange(sum(parts) or 1)
    for i in range(3, -1, -1):
        if roll < parts[i]:
            return 96 + i
        roll -= parts[i]
    return 96


def skill_gain_chance(skill, recipe):   # ASSUMPTION: gains come from yellow/orange recipes
    diff = recipe - skill
    if diff > 19: return 0.6           # red: risky
    if diff > 0: return 0.9            # orange
    if diff > -11: return 0.7          # yellow
    if diff > -31: return 0.3          # blue
    if diff > -50: return 0.08         # green
    return 0.0


def fail_chance(skill, recipe):
    diff = recipe - skill
    return 0.0 if diff <= 0 else 0.15 if diff <= 19 else 0.35


# ---------------- world ----------------
class World:
    def __init__(self, seed, opts):
        global PRICE_MULT
        PRICE_MULT = opts.get("price_mult", 1.0)
        self.rng = random.Random(seed)
        self.o = opts
        self.camps = LW.load_camps()
        self.zones = sorted({c["zone"] for c in self.camps})
        self.camps_by_band = {L: [c for c in self.camps if c["level"] - L <= 4 and c["level"] - L > -(4 + L // 10)]
                              for L in range(1, 51)}
        self.occupancy = collections.Counter()
        self.chars = []                   # every character ever created
        self.players = []
        self.orders = []                  # dict(char, slot, level, bonus, price_paid, guild, t)
        self.rare_market = []             # level-50 rare items for sale: dict(slot, B, q, price, seller)
        self.stats = collections.Counter()
        self.gold_in = collections.Counter()
        self.gold_out = collections.Counter()
        self.template_events = []         # (source, hours_from_50)
        self.snaps = []
        self.player_me = dict(level=1, xp=0.0, chars_at_50=0) if opts.get("player_xp") else None
        self.make_population()

    # ----- population -----
    def new_char(self, p, level, crafter=False):
        rng = self.rng
        _, c, r, s_, pa, ch, budget = TYPES[p["type"]]
        j = lambda v: max(0, min(10, v + rng.randint(-2, 2)))
        b = dict(id=len(self.chars), player=p, type=p["type"], tr=dict(cur=j(c), risk=j(r), soc=j(s_), pat=j(pa), chat=j(ch)),
                 budget=budget, level=level, xp=0.0, zone="Jordheim", region=100, state="idle", until=0, camp=None,
                 deaths_at={}, visited={}, gear=[None] * SLOTS, crafter=crafter, skill=0.0, reached_50=None,
                 templated=False, created=self.t if hasattr(self, "t") else 0, kind="SoloPve", group=None)
        self.chars.append(b)
        p["roster"].append(b)
        self.stats["characters_created"] += 1
        return b

    def make_population(self):
        rng, o = self.rng, self.o
        names = list(TYPES)
        weights = [TYPES[n][0] for n in names]
        n_guilds = o.get("n_personas", 1450) // 25
        for i in range(o.get("n_personas", 1450)):
            p = dict(id=i, type=rng.choices(names, weights=weights)[0], roster=[], gold=0.0, online=None,
                     until=rng.randint(0, 240), guild=(rng.randrange(n_guilds) if rng.random() < 0.75 else None),
                     retired=False, joined=0)
            self.players.append(p)
            # established start: a mature server has many level 50s (ASSUMPTION: 30%)
            level = 50 if rng.random() < 0.30 else rng.randint(1, 49)
            main = self.new_char(p, level, crafter=(p["type"] == "Crafter"))
            if main["crafter"]:
                main["skill"] = min(1000.0, level * 20 * rng.uniform(0.6, 1.05))
            if level == 50:
                main["reached_50"] = -1          # before the run started
                if rng.random() < 0.5 and len(p["roster"]) < 3:
                    self.new_char(p, rng.randint(5, 45))     # mature players already have an alt
            for ch in p["roster"]:
                self.starting_gear(ch)
            p["gold"] = 40 * level ** 1.5 * rng.uniform(0.3, 2.0)

    def starting_gear(self, b):
        rng, L = self.rng, b["level"]
        for i in range(SLOTS):
            if rng.random() < 0.7:
                lvl = max(1, L - rng.randint(0, 6))
                B = 0
                if L == 50 and rng.random() < 0.35:
                    B = rng.choice([4, 6, 8, 8, 10])
                b["gear"][i] = dict(level=lvl, q=rng.randint(86, 99), B=B, src="start")

    # ----- gear -----
    @staticmethod
    def piece_power(it, L):
        if it is None:
            return 0.0
        return min(1.0, it["level"] * it["q"] / 100 / L) * (1 + it["B"] / 40)

    def fit(self, b):
        return sum(self.piece_power(it, b["level"]) for it in b["gear"]) / SLOTS

    def equip(self, b, slot, item):
        cur = b["gear"][slot]
        if item["level"] <= b["level"] and self.piece_power(item, b["level"]) > self.piece_power(cur, b["level"]):
            b["gear"][slot] = item
            return True
        return False

    def template_complete(self, b):
        return b["level"] == 50 and all(it is not None and it["level"] >= 47 and it["B"] >= 8 for it in b["gear"])

    def check_template(self, b):
        if not b["templated"] and self.template_complete(b):
            b["templated"] = True
            srcs = collections.Counter(it["src"] for it in b["gear"])
            source = "bought" if srcs["crafted"] + srcs["market"] >= 5 else "farmed" if srcs["rare"] >= 5 else "mixed"
            start = b["reached_50"] if b["reached_50"] is not None and b["reached_50"] >= 0 else 0
            self.template_events.append((source, round((self.t - start) / 60, 1)))

    # ----- per-minute character activity -----
    def gold(self, b, amount, why):
        b["player"]["gold"] += amount
        (self.gold_in if amount > 0 else self.gold_out)[why] += abs(amount)

    def hunt_minute(self, b):
        rng, camp = self.rng, b["camp"]
        L = b["level"]
        c = LW.con(L, camp["level"])
        units = self.occupancy[camp["id"]]
        eff = min(1.0, LW.CAPACITY_UNITS / max(1, units))
        fit = self.fit(b) if rng.random() < 0.1 or "fit" not in b else b["fit"]
        b["fit"] = fit
        if L < 50:
            rate = LW.XP_RATE.get(c, 0.3) * eff * (0.85 + 0.3 * fit) * self.o.get("bot_xp", 2.0)
            b["xp"] += rate / 60 / LW.hours_to_level(L)
            while b["xp"] >= 1 and b["level"] < 50:
                b["xp"] -= 1
                b["level"] += 1
                if b["level"] == 50:
                    b["reached_50"] = self.t
                    self.stats["reached_50"] += 1
        inc = income_per_hour(L) * eff / 60
        self.gold(b, inc, "hunting")
        self.gold(b, -inc * UPKEEP, "upkeep")
        if rng.random() < COMMON_LOOT_PER_HOUR / 60:
            item = dict(level=max(1, camp["level"]), q=rng.randint(85, 95), B=0, src="loot")
            if not self.equip(b, rng.randrange(SLOTS), item):
                self.gold(b, 0.3 * mats_cost(item["level"]), "vendor_loot")
        rare = (RARE_PER_HOUR if camp["level"] >= 45 else RARE_PER_HOUR_LOW) * self.o.get("rare_mult", 1.0)
        if rng.random() < rare * eff / 60:
            self.stats["rare_drops"] += 1
            item = dict(level=min(50, camp["level"]), q=rng.randint(90, 100), B=rng.randint(4, 12), src="rare")
            slot = rng.randrange(SLOTS)
            if self.equip(b, slot, item):
                self.check_template(b)
            elif item["level"] >= 47 and item["B"] >= 8:
                price = (mats_cost(50) * CRAFT_MARKUP * PRICE_MULT + spellcraft_cost(50, 8)) * 0.8 * item["B"] / 8
                self.rare_market.append(dict(slot=slot, B=item["B"], q=item["q"], price=price, seller=b, t=self.t))
            else:
                self.gold(b, 0.3 * mats_cost(item["level"]), "vendor_loot")
        if rng.random() < LW.DEATH_PER_HOUR.get(c, 0.6) / 60 * (1.4 - 0.8 * fit):
            b["until"] += 8
            self.stats["deaths"] += 1

    # ----- town: shopping and orders -----
    def shop(self, b):
        p, L = b["player"], b["level"]
        if L < 10:
            return
        if L < 50:
            # leveling gear: plain crafted pieces when a slot is empty or 5+ levels behind
            for slot, it in enumerate(b["gear"]):
                if (it is None or it["level"] < L - 5) and not self.has_order(b, slot):
                    price = mats_cost(L) * CRAFT_MARKUP * PRICE_MULT
                    if price <= 0.25 * p["gold"]:
                        self.place_order(b, slot, L, 0, price)
                        break
            return
        # level 50: work toward a template, cheapest first: rare market, then crafted + spellcraft
        for slot, it in sorted(enumerate(b["gear"]), key=lambda x: (x[1] or {"B": -1})["B"]):
            if it is not None and it["level"] >= 47 and it["B"] >= 8:
                continue
            if self.has_order(b, slot):
                continue
            offers = [m for m in self.rare_market if m["slot"] == slot and m["seller"]["player"] is not p]
            best = min(offers, key=lambda m: m["price"], default=None)
            sc_price = mats_cost(50) * CRAFT_MARKUP * PRICE_MULT + spellcraft_cost(50, 8)
            if best and best["price"] <= sc_price and best["price"] <= 0.6 * p["gold"]:
                self.rare_market.remove(best)
                self.gold(b, -best["price"], "market_buy")
                self.gold(best["seller"], best["price"], "market_sell")
                self.stats["rare_market_sales"] += 1
                self.equip(b, slot, dict(level=50, q=best["q"], B=best["B"], src="market"))
                self.check_template(b)
            elif sc_price <= 0.6 * p["gold"] * self.o.get("buy_appetite", 1.0):
                self.place_order(b, slot, 50, 8, sc_price)
            break                                  # one purchase decision per visit

    def has_order(self, b, slot):
        return any(o["char"] is b and o["slot"] == slot for o in self.orders)

    def place_order(self, b, slot, level, bonus, price):
        self.gold(b, -price, "orders_paid")        # escrow at the Exchange
        self.orders.append(dict(char=b, slot=slot, level=level, bonus=bonus, price=price,
                                guild=b["player"]["guild"], t=self.t))
        self.stats["orders_placed"] += 1

    # ----- crafting sessions -----
    def craft_session(self, b, minutes):
        rng, p = self.rng, b["player"]
        left = minutes
        while left >= CRAFT_MINUTES:
            job = self.pick_order(b)
            if job is not None:
                recipe = job["level"] * 20
                cost = mats_cost(job["level"])
                if p["gold"] < cost:
                    break
                self.gold(b, -cost, "materials")
                left -= CRAFT_MINUTES
                if rng.random() < fail_chance(b["skill"], recipe):
                    self.stats["craft_failed"] += 1
                    continue
                self.gain_skill(b, recipe)
                q = craft_quality(b["skill"], recipe, rng)
                self.stats["masterpieces"] += q == 100
                self.orders.remove(job)
                if job["bonus"]:
                    self.gold(b, -spellcraft_cost(job["level"], job["bonus"]), "spellcraft_gems")
                self.gold(b, job["price"], "orders_earned")
                buyer = job["char"]
                same_guild = job["guild"] is not None and job["guild"] == p["guild"]
                self.stats["orders_filled"] += 1
                self.stats["orders_filled_in_guild"] += same_guild
                self.stats["order_wait_min_total"] += self.t - job["t"]
                self.equip(buyer, job["slot"], dict(level=job["level"], q=q, B=job["bonus"], src="crafted", by=b["id"]))
                self.check_template(buyer)
                continue
            # no order: skill-up crafting while the crafter can afford it (keeps a reserve)
            recipe = min(1000, int(b["skill"]) + 5)
            lvl = max(1, recipe // 20)
            cost = mats_cost(lvl)
            if b["skill"] >= 1000 or p["gold"] < cost + self.o.get("crafter_reserve", 2000):
                break
            self.gold(b, -cost, "materials")
            left -= CRAFT_MINUTES
            if rng.random() < fail_chance(b["skill"], recipe):
                continue
            self.gain_skill(b, recipe)
            self.gold(b, cost * SKILLUP_RESALE, "skillup_resale")
            self.stats["skillup_crafts"] += 1
        self.stats["craft_idle_min"] += left

    def gain_skill(self, b, recipe):
        if self.rng.random() < skill_gain_chance(b["skill"], recipe):
            b["skill"] = min(1000.0, b["skill"] + 1)

    def pick_order(self, b):
        best = None
        for o in self.orders:
            recipe = o["level"] * 20
            if recipe > b["skill"] + 19:              # orange at most for paid work
                continue
            # buyers wait up to 2 hours for a capable guild crafter before anyone else may take the order
            g = o["guild"]
            if (g is not None and g != b["player"]["guild"] and self.t - o["t"] < 120
                    and self.guild_best.get(g, 0) + 19 >= recipe):
                continue
            if o["char"]["player"] is b["player"]:
                key = (2, o["level"])
            elif o["guild"] is not None and o["guild"] == b["player"]["guild"]:
                key = (1, o["level"])
            else:
                key = (0, o["level"])
            if best is None or key > best[0]:
                best = (key, o)
        return best[1] if best else None

    # ----- sessions -----
    def login(self, p):
        rng = self.rng
        roster = p["roster"]
        below = [c for c in roster if c["level"] < 50]
        # add an alt (never replace) when everything is 50, or sometimes when the main is 50
        if len(roster) < self.o.get("max_roster", 3) and (not below or (rng.random() < self.o.get("alt_chance", 0.08) and roster[0]["level"] == 50)):
            if self.stats["characters_created"] < self.o.get("name_cap", 5700):
                self.new_char(p, 1)
                self.stats["alts_created"] += 1
                below = [c for c in roster if c["level"] < 50]
        if roster[0]["crafter"] and rng.random() < 0.7:
            ch = roster[0]                            # crafters mostly play their crafter
        elif below and rng.random() < 0.7:
            ch = below[-1]
        else:
            ch = rng.choice(roster)
        p["online"] = ch
        ch["state"] = "idle"
        ch["until"] = self.t

    def logout(self, p):
        ch = p["online"]
        if ch and ch["state"] == "hunt" and ch["camp"]:
            self.occupancy[ch["camp"]["id"]] -= 1
        if ch:
            ch["state"] = "off"
            ch["camp"] = None
        p["online"] = None
        # retirement: the whole player leaves; their characters stay in the world records
        if self.rng.random() < self.o.get("retire_chance", 0.004):
            p["retired"] = True
            self.stats["retired_players"] += 1
            q = dict(id=len(self.players), type=self.rng.choices(list(TYPES), weights=[TYPES[n][0] for n in TYPES])[0],
                     roster=[], gold=0.0, online=None, until=self.t + self.rng.randint(30, 240),
                     guild=(self.rng.randrange(max(1, self.o.get("n_personas", 1450) // 25)) if self.rng.random() < 0.5 else None),
                     retired=False, joined=self.t)
            self.players.append(q)
            if self.stats["characters_created"] < self.o.get("name_cap", 5700):
                self.new_char(q, 1, crafter=(q["type"] == "Crafter"))
                self.stats["new_players"] += 1

    def decide(self, b):
        rng = self.rng
        if b["state"] == "town" and b.get("act") is None:
            self.shop(b)
        if b["crafter"] and rng.random() < 0.5:
            dur = rng.randint(30, 90)
            b.update(state="town", act="craft", until=self.t + dur, zone="Jordheim", region=100)
            self.craft_session(b, dur)
            self.stats["craft_min"] += dur
            return
        w = [share / LW.ACT_MINUTES[a] for share, a in zip(b["budget"], ACTS)]
        act = rng.choices(ACTS, weights=w)[0]
        if act in ("craft", "social") or rng.random() < 0.12:     # town break: shop at a natural task break
            dur = rng.randint(20, 60)
            b.update(state="town", act=None, until=self.t + 6 + dur, zone="Jordheim", region=100)
            return
        if act == "explore":
            b.update(state="explore", act=None, until=self.t + rng.randint(40, 100))
            return
        if b["level"] == 50 and rng.random() < 0.4:
            b.update(state="rvr", act=None, until=self.t + rng.randint(45, 120), zone="Frontier", region=163)
            return
        camp = LW.choose_camp(b, self.camps_by_band, self.occupancy, self.zone_pop, self.t, rng, True)
        if camp is None:
            b.update(state="town", act=None, until=self.t + 10)
            return
        self.occupancy[camp["id"]] += 1
        b.update(state="hunt", act=None, camp=camp, zone=camp["zone"], region=camp["region"],
                 until=self.t + LW.travel_minutes(b["zone"], b["region"], camp) + LW.tenure(b, rng, True))
        b["visited"][camp["zone"]] = self.t

    # ----- main loop -----
    def run(self, hours):
        rng = self.rng
        self.t = 0
        for t in range(hours * 60):
            self.t = t
            online = [p for p in self.players if p["online"] is not None]
            if t % 5 == 0:
                self.zone_pop = collections.Counter(p["online"]["zone"] for p in online if p["online"]["state"] == "hunt")
            for p in self.players:
                if p["retired"]:
                    continue
                if p["online"] is None:
                    if t >= p["until"]:
                        self.login(p)
                        p["session_end"] = t + rng.randint(120, 300)
                    continue
                b = p["online"]
                if b["state"] == "hunt":
                    self.hunt_minute(b)
                if t >= b["until"]:
                    if b["state"] == "hunt" and b["camp"]:
                        self.occupancy[b["camp"]["id"]] -= 1
                        b["camp"] = None
                    if t >= p["session_end"]:
                        self.logout(p)
                        p["until"] = t + rng.randint(60, 240)
                        continue
                    self.decide(b)
            if self.player_me:
                me = self.player_me
                me["xp"] += 0.75 * self.o["player_xp"] / 60 / LW.hours_to_level(me["level"])
                while me["xp"] >= 1:
                    me["xp"] -= 1
                    me["level"] += 1
                    if me["level"] >= 50:
                        me["chars_at_50"] += 1
                        me.update(level=1, xp=0.0)
            if t % 30 == 0:
                self.guild_best = {}
                for p in self.players:
                    if not p["retired"] and p["guild"] is not None:
                        for c in p["roster"]:
                            if c["crafter"]:
                                self.guild_best[p["guild"]] = max(self.guild_best.get(p["guild"], 0), c["skill"])
                self.orders = [o for o in self.orders if t - o["t"] <= 12 * 60 or self.refund(o)]
                self.rare_market = [m for m in self.rare_market if t - m["t"] <= 24 * 60]
            if t % 60 == 59:
                self.hourly(online)
            if (t + 1) % (10 * 60) == 0:
                self.snapshot()
        return self.result()

    def refund(self, o):
        self.gold(o["char"], o["price"], "order_refunds")
        self.stats["orders_expired"] += 1
        return False

    def hourly(self, online):
        online = [p for p in self.players if p["online"] is not None]
        hunters = [p["online"] for p in online if p["online"]["state"] == "hunt"]
        zc = collections.Counter(b["zone"] for b in hunters)
        n = len(hunters) or 1
        me = self.player_me
        self.hour_rows.append(dict(
            hour=self.t // 60 + 1, online=len(online), hunters=len(hunters), zones=len(zc),
            top_zone_share=round(max(zc.values()) / n, 3) if zc else 0,
            crowded=round(sum(1 for b in hunters if self.occupancy[b["camp"]["id"]] > LW.CAPACITY_UNITS) / n, 3),
            online_bands=[sum(1 for p in online if a <= p["online"]["level"] <= a + 9) for a in (1, 11, 21, 31, 41)],
            near_me=(sum(1 for b in hunters if abs(b["level"] - me["level"]) <= 3) if me else None),
            me_level=(me["level"] if me else None)))

    def snapshot(self):
        active = [c for p in self.players if not p["retired"] for c in p["roster"]]
        lvl50 = [c for c in active if c["level"] == 50]
        crafters = [c for c in active if c["crafter"]]
        golds = [p["gold"] for p in self.players if not p["retired"]]
        self.snaps.append(dict(
            hour=self.t // 60 + 1,
            characters_total=len(self.chars), characters_active=len(active),
            players_active=sum(1 for p in self.players if not p["retired"]),
            roster_sizes=dict(collections.Counter(len(p["roster"]) for p in self.players if not p["retired"])),
            level_bands_all=[sum(1 for c in active if a <= c["level"] <= a + 9) for a in (1, 11, 21, 31, 41)],
            level50=len(lvl50), templated=sum(1 for c in lvl50 if c["templated"]),
            crafters=len(crafters), crafter_skill_median=(statistics.median(c["skill"] for c in crafters) if crafters else 0),
            legendary=sum(1 for c in crafters if c["skill"] >= 1000), skill_700_plus=sum(1 for c in crafters if c["skill"] >= 700),
            gold_total=round(sum(golds)), gold_median=round(statistics.median(golds)),
            open_orders=len(self.orders), rare_listings=len(self.rare_market)))

    def result(self):
        ev = self.template_events
        by_src = collections.defaultdict(list)
        for s, h in ev:
            by_src[s].append(h)
        crafters = [c for p in self.players if not p["retired"] for c in p["roster"] if c["crafter"]]
        cr_players = {id(c["player"]) for c in crafters}
        gold_cr = [p["gold"] for p in self.players if id(p) in cr_players and not p["retired"]]
        gold_other = [p["gold"] for p in self.players if id(p) not in cr_players and not p["retired"]]
        net50 = income_per_hour(50) * (1 - UPKEEP)
        template_price = 7 * (mats_cost(50) * CRAFT_MARKUP * PRICE_MULT + spellcraft_cost(50, 8))
        drops_needed = 7 * sum(1 / k for k in range(1, 8)) / (5 / 9)      # coupon collector, B >= 8
        farm_hours = drops_needed / (RARE_PER_HOUR * self.o.get("rare_mult", 1.0))
        shortcut = dict(buy_hunting_hours=round(template_price / net50, 1), farm_hunting_hours=round(farm_hours, 1),
                        ratio=round(template_price / net50 / farm_hours, 2))
        return dict(shortcut=shortcut, hourly=self.hour_rows, snaps=self.snaps, stats=dict(self.stats),
                    gold_in=dict(self.gold_in), gold_out=dict(self.gold_out),
                    templates={s: dict(n=len(v), median_hours=(statistics.median(v) if v else None)) for s, v in by_src.items()},
                    gold_crafter_players=round(statistics.median(gold_cr)) if gold_cr else 0,
                    gold_other_players=round(statistics.median(gold_other)) if gold_other else 0,
                    me=self.player_me)


World.hour_rows = None
World.guild_best = {}


def run(seed, hours, opts):
    w = World(seed, opts)
    w.hour_rows = []
    w.zone_pop = collections.Counter()
    return w.run(hours)


CASES = {
    "bots 2x": dict(bot_xp=2.0, player_xp=8),
    "bots 4x": dict(bot_xp=4.0, player_xp=8),
    "bots 2x, crafted gear 2.5x pricier": dict(bot_xp=2.0, player_xp=8, price_mult=2.5),
    "bots 2x, no alts": dict(bot_xp=2.0, player_xp=8, max_roster=1),
}


def _job(a):
    name, seed, hours = a
    return name, seed, run(seed, hours, CASES[name])


if __name__ == "__main__":
    seeds = [int(s) for s in (sys.argv[1] if len(sys.argv) > 1 else "1,2").split(",")]
    hours = int(sys.argv[2]) if len(sys.argv) > 2 else 120
    out = sys.argv[3] if len(sys.argv) > 3 else "persona_results.json"
    only = os.environ.get("PERSONA_ONLY")
    names = [n for n in CASES if not only or n in only.split("|")]
    with Pool(2) as pool:
        done = pool.map(_job, [(n, s, hours) for n in names for s in seeds])
    json.dump({n: [r for nn, s, r in done if nn == n] for n in names}, open(out, "w"))
    print("saved", out)
