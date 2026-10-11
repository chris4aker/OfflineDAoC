"""Crafting and trade layer for the Living World simulator (a PROPOSED system, not today's game).

Today's autonomous bots never craft: nothing gives them crafting skills, and the "Craft" rule in
AutonomousBotDecisionEngine.Choose has no live caller. This module models what would happen IF
bots had a crafting economy, so the design can be tested before any server code is written.

Everything here is an assumption, labelled ASSUMPTION. Compare runs; do not trust absolute numbers.
"""
import collections, random, statistics

SLOTS = 7                      # helm, chest, arms, legs, hands, boots, weapon (ASSUMPTION)
BANDS = 5                      # level bands 1-10, 11-20 ... 41-50


def band(level):
    return min(BANDS - 1, max(0, (level - 1) // 10))


def item_price(level, q):      # coins. ASSUMPTION: a level-20 piece ~ 1-2 hours of income
    return 4.0 * level * (1 + (q - 85) / 40.0)


def income_per_hour(level):    # coins per hunting hour. ASSUMPTION
    return 3.0 * level


def craft_minutes(level):      # ASSUMPTION
    return 8 + 0.4 * level


def mats_needed(level):        # material units, from the item's own level band. ASSUMPTION
    return 3 + level // 4


MAT_BUY, MAT_SELL = 3.0, 1.5   # coins per unit: crafter buys from the market / hunter sells to it
MATS_PER_HUNT_MIN = 8 / 60.0   # units a hunting bot gathers per minute, in its camp's level band
LOOT_PER_HOUR = 2.0            # equipment drops per hunting hour
ORDER_LIFETIME = 8 * 60        # minutes an unfilled order stays open
LISTING_LIFETIME = 12 * 60


class Econ:
    def __init__(self, rng, craft_enabled, opts=None):
        self.rng = rng
        self.craft_enabled = craft_enabled
        o = opts or {}
        self.quality_bonus = o.get("quality_bonus", 0.0)   # sensitivity: easier high quality
        self.mat_rate = o.get("mat_rate", 1.0)             # sensitivity: material supply
        self.loot_rate = o.get("loot_rate", 1.0)
        self.listings = []            # dict(slot, level, q, price, seller, for_bot, src, t)
        self.orders = []              # dict(buyer, slot, level, max_price, t, claimed)
        self.mat_stock = [0.0] * BANDS
        self.stats = collections.Counter()
        self.band_orders = collections.Counter()
        self.band_filled = collections.Counter()
        self.fill_wait = []
        self.snap = []                # periodic snapshots

    # ---------- gear ----------
    @staticmethod
    def score(item):
        return 0.0 if item is None else item["level"] * item["q"] / 100.0

    def fit(self, b):
        L = max(1, b["level"])
        return sum(min(1.0, self.score(it) / L) for it in b["gear"]) / SLOTS

    def init_bot(self, b, established):
        b["gear"] = [None] * SLOTS
        b["gold"] = 0.0
        b["skill"] = 1.0
        b["emats"] = [0.0] * BANDS
        b["bag"] = []
        b["crafts"] = b["crafts_orders"] = b["crafts_stock"] = b["craft_fail"] = b["craft_blocked"] = 0
        b["craft_idle_min"] = 0
        b["sales"] = 0.0
        b["bought_crafted"] = b["bought_other"] = 0
        if established:
            L = b["level"]
            b["skill"] = max(1.0, 0.8 * L)   # ASSUMPTION: established crafters already trained to ~80% of their level
            b["gold"] = 15.0 * L
            for i in range(SLOTS):
                if self.rng.random() < 0.5:
                    b["gear"][i] = dict(level=max(1, L - self.rng.randint(0, 6)),
                                        q=min(100, max(75, self.rng.gauss(88, 4))), src="loot", by=None)
        b["fit"] = self.fit(b)

    def reset_alt(self, b):
        b["gear"] = [None] * SLOTS
        b["gold"] *= 0.3
        b["skill"] = 1.0
        b["emats"] = [0.0] * BANDS
        b["bag"] = []
        b["fit"] = 0.0

    def try_equip(self, b, item, slot):
        cur = b["gear"][slot]
        if item["level"] <= b["level"] and self.score(item) > self.score(cur):
            b["gear"][slot] = item
            if cur is not None:
                b["bag"].append((slot, cur))
            b["fit"] = self.fit(b)
            return True
        return False

    # ---------- hunting ----------
    def hunt_minute(self, b, camp_level, eff):
        rng = self.rng
        b["gold"] += income_per_hour(b["level"]) * eff / 60.0
        b["emats"][band(camp_level)] += MATS_PER_HUNT_MIN * self.mat_rate
        if rng.random() < LOOT_PER_HOUR * self.loot_rate / 60.0:
            item = dict(level=max(1, camp_level + rng.randint(-1, 1)),
                        q=min(100.0, max(75.0, rng.gauss(88, 4))), src="loot", by=None)
            slot = rng.randrange(SLOTS)
            if not self.try_equip(b, item, slot):
                b["bag"].append((slot, item))
            self.stats["loot_drops"] += 1

    # ---------- town ----------
    def needy_slots(self, b):
        L = b["level"]
        if L < 8:
            return []
        out = []
        for i, it in enumerate(b["gear"]):
            have = 0 if it is None else it["level"]
            if it is None or have < L - 4:
                out.append((L - have, i))
        return [i for _, i in sorted(out, reverse=True)]

    def town_visit(self, b, t, is_crafter):
        rng = self.rng
        # sell gathered materials (crafters keep theirs)
        if not (is_crafter and self.craft_enabled):
            for k in range(BANDS):
                if b["emats"][k] > 0:
                    b["gold"] += b["emats"][k] * MAT_SELL
                    self.mat_stock[k] += b["emats"][k]
                    b["emats"][k] = 0.0
        # surplus loot: list good pieces on the exchange, vendor the rest
        mine = sum(1 for l in self.listings if l["seller"] == b["id"])
        for slot, it in b["bag"]:
            price = item_price(it["level"], it["q"])
            if it["q"] >= 85 and mine < 3 and rng.random() < 0.5:
                self.listings.append(dict(slot=slot, level=it["level"], q=it["q"], price=price * 0.9,
                                          seller=b["id"], for_bot=None, src=it["src"], by=it.get("by"), t=t))
                mine += 1
            else:
                b["gold"] += price * 0.25
        b["bag"] = []
        self.shop(b, t)

    def shop(self, b, t):
        L = b["level"]
        for slot in self.needy_slots(b):
            best = None
            for l in self.listings:
                if l["slot"] != slot or l["seller"] == b["id"]:
                    continue
                if not (L - 5 <= l["level"] <= L) or l["price"] > b["gold"]:
                    continue
                if l["for_bot"] not in (None, b["id"]):
                    continue
                key = (l["for_bot"] == b["id"], self.score(l))
                if best is None or key > best[0]:
                    best = (key, l)
            if best:
                l = best[1]
                b["gold"] -= l["price"]
                self.listings.remove(l)
                seller = self.by_id.get(l["seller"])
                if seller is not None:
                    seller["gold"] += l["price"]
                    seller["sales"] += l["price"] if l["src"] == "crafted" else 0.0
                if l["for_bot"] == b["id"]:
                    self.stats["reserved_claimed"] += 1
                item = dict(level=l["level"], q=l["q"], src=l["src"], by=l.get("by"))
                self.try_equip(b, item, slot)
                self.stats["purchases"] += 1
                if l["src"] == "crafted":
                    b["bought_crafted"] += 1
                    self.stats["purchases_crafted"] += 1
                    self.band_filled[band(L)] += 1
                else:
                    b["bought_other"] += 1
            elif not any(o["buyer"] == b["id"] and o["slot"] == slot for o in self.orders):
                self.orders.append(dict(buyer=b["id"], slot=slot, level=L, t=t,
                                        max_price=item_price(L, 96) * 1.2, claimed=None))
                self.stats["orders_posted"] += 1
                self.band_orders[band(L)] += 1

    # ---------- crafting ----------
    def available_mats(self, b, lvl):
        k = band(lvl)
        return b["emats"][k] + self.mat_stock[k]

    def take_mats(self, b, lvl):
        k, need = band(lvl), mats_needed(lvl)
        own = min(b["emats"][k], need)
        b["emats"][k] -= own
        rest = need - own
        if rest > 0:
            self.mat_stock[k] -= rest
            b["gold"] -= rest * MAT_BUY

    def craft_session(self, b, minutes, t):
        if not self.craft_enabled:
            b["craft_idle_min"] += minutes
            return
        rng = self.rng
        left = minutes
        while True:
            job = self.pick_job(b)
            if job is None:
                break
            lvl = job["level"]
            ct = craft_minutes(lvl)
            if ct > left:
                break
            left -= ct
            if self.available_mats(b, lvl) < mats_needed(lvl):
                b["craft_blocked"] += 1
                self.stats["craft_blocked_mats"] += 1
                break
            self.take_mats(b, lvl)
            S = b["skill"]
            fail = 0.05 * max(0.0, lvl - S)
            if rng.random() < fail:
                b["craft_fail"] += 1
                self.stats["craft_failed"] += 1
                continue
            q = max(80.0, min(100.0, 86.0 + (S - lvl + 4) + self.quality_bonus + rng.gauss(0, 2)))
            gain = 0.45 if lvl >= S else (0.25 if lvl >= S - 5 else 0.05)
            b["skill"] = min(50.0, S + gain)
            b["crafts"] += 1
            self.stats["crafts"] += 1
            price = item_price(lvl, q)
            if job["order"] is not None:
                o = job["order"]
                self.orders.remove(o)
                buyer = self.by_id.get(o["buyer"])
                if o["buyer"] == b["id"]:
                    self.try_equip(b, dict(level=lvl, q=q, src="crafted", by=b["id"]), o["slot"])
                else:
                    self.listings.append(dict(slot=o["slot"], level=lvl, q=q, price=min(price, o["max_price"]),
                                              seller=b["id"], for_bot=o["buyer"], src="crafted", by=b["id"], t=t))
                b["crafts_orders"] += 1
                self.stats["orders_filled_by_craft"] += 1
                self.fill_wait.append(t - o["t"])
            else:
                self.listings.append(dict(slot=rng.randrange(SLOTS), level=lvl, q=q, price=price * 0.95,
                                          seller=b["id"], for_bot=None, src="crafted", by=b["id"], t=t))
                b["crafts_stock"] += 1
            self.stats["perfect_pieces"] += 1 if q >= 96 else 0
        b["craft_idle_min"] += left

    def order_valid(self, o):
        buyer = self.by_id.get(o["buyer"])
        if buyer is None:
            return False
        it = buyer["gear"][o["slot"]]
        return it is None or it["level"] < buyer["level"] - 4     # buyer still needs this slot

    def pick_job(self, b):
        S = b["skill"]
        # own needs first, then open orders the crafter can make with little risk (level <= skill+2),
        # highest level first; riskier orders (up to skill+5) only if nothing safer; else stock for skill-up
        own = [o for o in self.orders if o["buyer"] == b["id"] and self.order_valid(o)]
        if own:
            o = max(own, key=lambda o: o["level"])
            return dict(level=o["level"], order=o)
        cand = [o for o in self.orders if o["buyer"] != b["id"] and o["level"] <= S + 5 and self.order_valid(o)]
        safe = [o for o in cand if o["level"] <= S + 2] or cand
        safe = [o for o in safe if self.available_mats(b, o["level"]) >= mats_needed(o["level"])] or safe
        if safe:
            o = max(safe, key=lambda o: o["level"])
            return dict(level=o["level"], order=o)
        return dict(level=max(1, int(S)), order=None)

    # ---------- bookkeeping ----------
    def expire(self, t):
        keep = []
        for o in self.orders:
            if not self.order_valid(o):
                self.stats["orders_voided_by_other_gear"] += 1
            elif t - o["t"] > ORDER_LIFETIME:
                self.stats["orders_expired"] += 1
            else:
                keep.append(o)
        self.orders = keep
        live = []
        for l in self.listings:
            if t - l["t"] > LISTING_LIFETIME:
                self.stats["listings_expired_" + l["src"]] += 1
                continue
            if l["for_bot"] is not None and t - l["t"] > 360:
                l["for_bot"] = None                      # reservation released after 6 h
                self.stats["reservations_released"] += 1
            live.append(l)
        self.listings = live

    def sets(self, bots):
        res = dict(n=0, full=0, perfect=0, crafted_full=0, crafted_pieces=0, worn=0, empty=0, fit=0.0)
        for b in bots:
            if b["level"] < 10:
                continue
            res["n"] += 1
            L = b["level"]
            gear = b["gear"]
            filled = [it for it in gear if it is not None and it["level"] >= L - 5]
            res["fit"] += b["fit"]
            res["empty"] += sum(1 for it in gear if it is None)
            res["worn"] += sum(1 for it in gear if it is not None)
            res["crafted_pieces"] += sum(1 for it in gear if it is not None and it["src"] == "crafted")
            if len(filled) == SLOTS:
                res["full"] += 1
                if all(it["q"] >= 96 for it in filled):
                    res["perfect"] += 1
                if all(it["src"] == "crafted" for it in filled):
                    res["crafted_full"] += 1
        return res
