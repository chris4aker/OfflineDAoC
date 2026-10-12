# Living World data check (2026-10-11)

The simulators' biggest guesses, checked against the real 0.35 world database. The owner had not
installed the game yet, so the published release was downloaded into Claude's cloud workspace
instead.

## Method

- **Source:** the official v0.35b release.
  - Its 3 parts and the joined archive matched the release manifest's SHA-256 hashes.
  - Both world databases were read **read-only**: the 0.35 edition's (`feb4a511…`, matching the
    0.35 manifest) and 0.35b's.
  - The release database is clean: 0 accounts, 0 characters, 0 bots.
- **Nothing from the release is committed here.**
- **Server code read:** `LootGeneratorMoney`, `ROGMobGenerator` (`AtlasMobLoot.cs`),
  `GeneratedUniqueItem.CapUtility`, `Recipe.cs`, `GameMerchant`.
- **Not checked:** anything that needs a running server, such as kill speed, real XP per hour and
  bot behavior. Those still wait for the owner's PC.

## Findings

### 1. Random magic items already drop from every monster (the biggest correction)

- **The generator is live.** The `LootGenerator` table has `DOL.GS.ROGMobGenerator` active for all
  monsters, alongside coin, one-time drops and fixed loot tables.
- **The drop chance is high.** In `AtlasMobLoot.cs`:
  - a **solo** kill of a yellow-con monster rolls a class-appropriate random item at 14% + 10% solo
    bonus = **about 24% per kill**;
  - each con step adds 3%, and grey monsters drop nothing;
  - group kills roll per member, with lower chances above levels 27 and 40.
- **Autonomous gamebots receive these drops too** (`IsLootParticipant`).
- **Strength:** quality 95–99%.
  - The item-strength cap (`CapUtility`) for a level-50 monster's drop is about 33–47 "utility",
    with a floor of 15.
  - How that compares with a spellcrafted piece is not checked.
- **What it means:**
  - None of the persona models included this. They had about 1 common drop per hunting hour and
    rare drops at 0.08–0.25 per hour.
  - Real magic gear is far more plentiful, so "crafted gear is a costly shortcut over farming"
    competes with a steady stream of random drops.
  - The crafting-economy results (crafter income, demand for crafted sets) are **overstated** until
    the model includes this.
  - Tuning levers, all existing:
    - `BASE_ROG_CHANCE` (a code constant);
    - the solo bonus;
    - the `atlas_rog` server settings (quality, stat weights);
    - removing the generator row for some monsters.

### 2. Named monsters below level 51 have almost no signature loot

Monster spawns with capitalized names (a rough "named" filter that can include a few NPCs):

| Level band | Named spawns | With a loot table | With a fixed magic item | Epic-class |
|---|---|---|---|---|
| 1–19 | 303 | 137 | 2 | 0 |
| 20–34 | 211 | 86 | 0 | 0 |
| 35–50 | 343 | 136 | 2 | 0 |
| 51+ | 520 | 338 | 98 | 112 |

- **Below level 51**, named monsters drop the same random items as anything else.
- **Fixed, recognizable drops** exist almost only on the 51+ encounters (dragons, Darkness Falls,
  epic NPCs).
- "Holy-shit items at every level" is therefore genuinely new work: loot tables for some of the
  about 860 named spawns in levels 1–50.
- The hosts already exist, so **no new monsters are needed**.

### 3. The frontier already has PvE: bots just don't use it

- **Layout:** each realm's classic frontier is **4 zones with 9 keeps** (7 keeps + 2 relic castles),
  plus two enemy portal keeps in the border zone.
  - The 7 + 2 count matches the RvR model; its 5 zones per realm does not.
  - Albion: Hadrian's Wall (border, 1 keep), Pennine Mountains (middle, 4), Snowdonia and Forest
    Sauvage (inner, 2 each including a relic castle).
  - Midgard and Hibernia follow the same pattern.
  - Six relics in total.
- **Monsters:** about 4,400 neutral monsters across the 12 frontier zones.

| Zone | Ring | Monsters | Levels (10th/50th/90th percentile) | Named |
|---|---|---|---|---|
| Hadrian's Wall | border | 131 | 1 / 41 / 52 | 2 |
| Pennine Mountains | middle | 411 | 1 / 45 / 50 | 13 |
| Snowdonia | inner | 252 | 1 / 28 / 41 | 10 |
| Forest Sauvage | inner | 419 | 1 / 18 / 36 | 12 |
| Odin's Gate | border | 246 | 30 / 42 / 50 | 4 |
| Jamtland Mountains | middle | 675 | 1 / 40 / 50 | 3 |
| Uppland | inner | 823 | 21 / 31 / 44 | 7 |
| Yggdra Forest | inner | 748 | 24 / 30 / 42 | 6 |
| Emain Macha | border | 259 | 1 / 36 / 51 | 2 |
| Breifine | middle | 79 | 1 / 42 / 53 | 6 |
| Mount Collory | inner | 147 | 1 / 29 / 37 | 3 |
| Cruachan Gorge | inner | 188 | 1 / 34 / 39 | 5 |

- **The depth grading already exists in the monster levels.** The border and middle zones hold the
  level 40–50 monsters; the inner zones nearer home hold levels 20–40.
- **What changes in the plan:**
  - "Frontier PvE for bots" is mainly adding these existing camps to the bots' camp catalog
    (`capnbry_classic_si_goals.json` has none), not building new content.
  - Named frontier monsters (for example Draco Magnificens, the Green Knight, Thorkatla) are ready
    hosts for signature drops.
- **Oddity:** Uppland contains Atlas-era training dummies ("Hitback Dummy", "Total: 0 DPS: 0") that
  are not period content.

### 4. Crafting costs track monster coin closely

- **Coin per kill** (`LootGeneratorMoney`) is 2 + (level+1)³/8 copper, times 1–1.5. At
  `money_drop` 1 that is about 2 gold at level 50 and about 15 silver at level 20.
- **Recipe materials** come from `CraftedItem`/`CraftedXItem` × `ItemTemplate.Price`. The table
  shows medians by product level, where "kills" means the same-level monster's average coin.

| Level | Armor materials | = kills | Weapon materials | = kills |
|---|---|---|---|---|
| 10 | 0.50 g | 24 | 0.85 g | 40 |
| 20 | 4.9 g | 34 | 7.6 g | 53 |
| 30 | 18 g | 39 | 35 g | 75 |
| 40 | 41 g | 38 | 83 g | 77 |
| 50 | 97 g | 47 | 200 g | 97 |

- **The model's shape holds.** It assumed materials cost 0.125·√level hours of hunting. That rises
  about 2.2× from level 10 to 50; the real armor ratio rises 2.0× and weapons 2.4×.
- **Absolute hours** still depend on kill speed, which is not measured.
- Of 8,479 recipes, 1,606 were skipped because an ingredient or product row is missing.

### 5. Practice-craft sellback is 50% in the release, not 95%

- **Release settings:** `crafting_adjust_product_price` is **False** and `item_sell_ratio` is 50.
- **What that means:**
  - A crafted item's price is its template price, which is about its material cost.
  - A merchant pays half of that, so selling practice crafts returns about **50% of materials**.
- **The 95% rule applies only when the setting is turned on** (`Recipe.cs` sets the price to
  materials × 2 × 95%, and the merchant pays half).
- The v4 plan assumed 90%, so it **needs that one setting turned on**. It is a server setting,
  not code.

### 6. Atlas daily-quest givers are not in the world database

- **None of the 21 named givers** in `scripts/quests/AtlasQuests` (Herou, Haszan, Kelteen, Rey,
  Succi and others) has a row in `Mob`.
  - The only matches are two existing classic NPCs that share their names: Ellyn Weyland and Sir
    Lukas.
- **What the code says:**
  - It would create the givers at startup when `load_quests` is on, and it is on.
  - The quest NPC save setting is also on.
  - Yet the development install this release was taken from never saved them.
- **Most likely** they do not appear in play, but the reason was not found. One look in game (for
  example at Svasud Faste) settles it.

### 7. Other facts

- **XP:** `xp_rate`, `bot_xp_rate`, `rvr_zones_xp_rate` and `money_drop` are all 1.
  `XP_Cap_Percent` is 125.
- **Relics:** `relic_owning_bonus` is 10.
- **Edition:** in the 0.35 edition database, `enable_sluaghbinder` is False.
- **Housing:** 1,800 lots per realm.
  - A new lot starts at 95,000 gold and falls by 1,200 gold per hour to a 300-gold floor.
  - Weekly rent is 20 gold (cottage) to 100 gold (mansion).
  - A finite, real luxury sink is already there.
- **Realm Exchange:** one broker per capital and real items and coin only (`offline_auction_settings`).
  No fee setting exists. The housing market search charges 20%.
- **Population settings:** a startup ramp of 15 minutes. `BackgroundProgression` is false and
  `WorldActorOnly` is true (bots only progress while loaded in the world).

## What to change next

1. **Add random item drops to the persona model** and rerun the v4 economy case. Expect lower
   crafter income and a smaller premium for crafted sets.
2. **Decide the gear-flow policy (owner):**
   - keep Atlas-rate random drops (plentiful gear, weaker crafting); or
   - lower them toward classic rates so crafting matters (for example a lower base chance, no solo
     bonus, or random drops only from named monsters).
3. **Fix the RvR model's zone count** (4 per realm, not 5) and rerun. The keep count was right.
4. **Frontier PvE for bots:** plan it as a camp-catalog extension over existing monsters.
5. **Named drops:** plan them as loot tables on existing named spawns in levels 1–50.
6. **Turn on `crafting_adjust_product_price`** if the owner keeps the 90–95% practice-craft
   sellback.
7. **Atlas quest givers and Uppland's training dummies:** one in-game look, then keep or remove.
