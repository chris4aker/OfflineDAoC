# Living World roadmap (Chris's fork)

Status: **planning.** Nothing in this document is implemented yet.
Owner: Chris (`chris4aker/OfflineDAoC`). Started 2026-10-11.

## Current direction (after the audit of 2026-10-11)

This section is the up-to-date summary. The study sections further down are kept as a dated record;
where a later study or the audit overtook one, it says so at its heading. The audit itself is in
[LIVING-WORLD-AUDIT-2026-10-11.md](LIVING-WORLD-AUDIT-2026-10-11.md).

**The owner's decisions so far:**
- **Scale:** about 1,000 bots online per realm while he plays (the server only runs then).
- **Start:** a fresh world, everyone at level 1 without armor, with a **staggered launch** (about 40%
  on day one, the rest joining over about 12 weeks).
- **No-lifers:** about 4% of bots, always online, no alts, min-maxing, chasing epics, raids and RvR.
- **Bot players own characters:** up to 3 per bot player; alts are added, never rerolled; mains,
  guilds and gold persist; occasional retirement and new players.
- **XP shaped by level range:** owner 3× / 5× / 12× and bots 1.5× / 2.5× / 6× for levels 1–19 /
  20–34 / 35–50. The settings `xp_rate_by_level` and `bot_xp_rate_by_level` are written on
  `feature/xp-by-level-range` (off by default; not yet checked in game).
- **The owner:** about 5 hours a week, about 9 characters (3 per realm) with a favored main in each.
- **Grouping:** keep the server's default of 40% group goals; grouping is a big lever for company and
  leveling.
- **Economy:**
  - crafters about 7% of bot players, with realm commissions doubled;
  - small classic repair and potion costs that never punish the owner for skipping the economy;
  - a bot-only luxury sink that buys real things (houses, horse routes, dyes);
  - an Exchange tax on trades only;
  - named and epic drops at every level;
  - crafted, spellcrafted gear costing about half the time of farming drops;
  - **random magic drops stay at the current (Atlas) rate** (decided after the data check). The
    rerun shows this halves demand for crafted gear, so crafting has to matter through other
    things: commissions, repairs, consumables, siege, and goods only crafters make.
- **RvR:**
  - keep the three realms' bot counts equal;
  - build a guarded, depth-graded frontier with PvE worth the trip (the monsters exist; camps for
    bots and the guards are new);
  - no small-group RP bonus for now;
  - watch the relic bonus for snowballing.

**Still open:**
- Apprentice commissions for typical crafters (crafting income is winner-take-most, and random drops
  halve gear orders).
- A reward for stealth hunting. Less pressing after the rerun: with the real 4-zone frontier,
  stealthers earn about as much as siegers.
- How rare epics should stay at the top.
- Relic bonus size.

**First code (2026-10-11):** XP by level range is written on the branch `feature/xp-by-level-range`.
It adds the settings `xp_rate_by_level` and `bot_xp_rate_by_level`, off by default, with a helper
script and [a how-to](https://github.com/chris4aker/OfflineDAoC/blob/feature/xp-by-level-range/docs/XP-BY-LEVEL-RANGE.md).
- **Automated:** the build and all tests pass on GitHub.
- **In-game:** not yet checked.

**Next step:** move from simulation to real code on the owner's PC: set up the build, load-test
1,000 bots per realm, and calibrate the models from real logs before building features.

**Redundancy check (2026-10-11, after the audit):** the plan was checked against this fork's code
and the original's latest `main` (`1cabc77`, 0.36 in progress). Two planned pieces were already
done upstream and were dropped, and several others now extend existing systems instead of adding
new ones. See "What the base already has" below; the milestones and the M1 specification were
revised to match.

## What the base already has

Checked in the code on 2026-10-11 (file names under `source/server/GameServer`). "In the world" means
whether it is actually live in a played install, which has not been checked unless stated.

| Planned | Already in the base | Plan now |
|---|---|---|
| Port HearthDAoC quest indicators, epic chains and restored spawns (old M3) | 0.35 ships 448 classic 1.65/SI quests including class epics, red map markers, the Quest Guide, and period monster populations; 0.36 adds 940 quest reward items | **Dropped.** Compare HearthDAoC item by item only for specific missing quests or spawns. |
| Personality-voiced chat with a safety blocklist (old M2) | `AutonomousBotChat` (lines assembled from parts), `AutonomousBotChatCoordinator` (short, rare conversations), `AutonomousChatIntentModel` (small classifier for player questions), `AutonomousChatKnowledge` (places and spells), `RealmEventBanter` | **Shrunk:** add personality flavor to the existing chat. No blocklist: nothing is generated freely, all text is pre-written. |
| Named and epic drops at every level | `Managers/RandomObjectGeneration/AtlasROGManager` (random items, 95–99% quality, stat weights as `atlas_rog` settings). **Live on every monster** through `ROGMobGenerator`: about 24% per solo yellow kill (data check, 2026-10-11). Named monsters in levels 1–50 have almost no fixed signature loot. | **Extend:** loot tables on existing named spawns in levels 1–50; **decide** the random-drop rate first (it competes with crafting) |
| PvE reasons in every zone | **Bounty Masters** (`scripts/quests/Bounty`): repeatable hunts of named monster types and epic named spawns across the home realm, dungeons and DF; equipment and XP rewards; map markers | **Extend** bounties to every level band and later to the frontier |
| Frontier PvE reasons | Atlas daily, weekly and monthly quests (`scripts/quests/AtlasQuests`), e.g. "kill 25 yellow-or-higher monsters in any RvR zone" (levels 10–50; XP, coin, a random item and a jewel). Their givers create themselves at startup when `load_quests` is on. Also `rvr_zones_xp_rate`. | **Check first:** the givers are **not** in the 0.35 world database (data check), so they most likely don't appear; one look in game settles it. Whether these Atlas-era quests fit the classic feel is the owner's call. **Also:** the 12 frontier zones already hold about 4,400 monsters, most of them levels 20–50, with named ones; bots' camp catalog just doesn't include them. |
| Bots crafting | `AutonomousBotDecisionEngine` has a "craft at a station with owned materials" activity (16% with 3+ material stacks), but nothing calls `Choose` | **Wire up and finish** the existing activity |
| Luxury spending | Housing, consignment merchants, market search (`market_fee_percent` 20) | Bots spend through the **real** housing system |
| RvR warnings | `GameWideAnnouncements`, `RealmEventNotices` (siege, relic and raid lines on screen) | **Extend** with frontier-danger warnings |
| Guard patrols | `keeps/Gameobjects/Guards/Patrol.cs` | **Tune** by frontier depth |
| Staggered launch | `AutonomousPopulationRamp` staggers only the startup (the whole roster loads over about 15 minutes); `AutonomousRealmLoginBalancer`; an `IsRetired` flag | **Extend** `AutonomousPopulationController`, no parallel system |

**Genuinely new** (no fork has done these better for this base):
- XP by level range (now written on `feature/xp-by-level-range`);
- bot play sessions, rosters of up to 3 characters per bot player, and alts (today every non-retired bot is online whenever the server runs);
- bot guilds (`GameBot.Guild` exists, but nothing assigns one);
- personalities and time budgets (stefanrows' design is the reference);
- RvR group doctrines, danger memory and observe-before-engaging (from stefanrows);
- the crafter economy: commissions, discounts and an Exchange tax (no fee was found on the Realm Exchange);
- a guarded, depth-graded frontier with PvE camps for bots (the monsters exist; the camps for bots
  are new).

**Data check (2026-10-11):** the release's world database was checked against the simulators'
guesses. See [LIVING-WORLD-DATA-CHECK-2026-10-11.md](LIVING-WORLD-DATA-CHECK-2026-10-11.md). The
biggest results:
- random magic items drop from every monster, which the persona models left out, so their crafting
  income is overstated;
- named monsters in levels 1–50 have almost no signature loot;
- the frontier is 4 zones per realm (the RvR model used 5) and already full of monsters;
- practice-craft sellback is 50% unless `crafting_adjust_product_price` is turned on.

## Vision

Playing should feel like logging into a classic three-realm server at its peak in
2003:

- **PvE is worth doing everywhere, from level 1 to 50.** Leveling zones are busy with
  bots that have their own habits, moods and reasons to be there. Every bracket has
  places worth exploring.
- **The frontier is dangerous and rewarding.** There are good PvE reasons to travel deep
  into it: dungeons, named monsters and loot. Doing that means watching for, and
  slipping past, roaming kill squads and the big battles.
- **RvR has real stakes.** Groups play like real groups. Keeps, relics and realm rank
  matter, and the frontier changes hands.
- **Bots are people, not machines.** Each one has a persistent personality that shapes
  where it goes, what it does, who it groups with, and how it talks.
- **Later:** new zones and dungeons keep PvE interesting through the whole 1–50 range.

## Foundation and sync policy

- **Base:** this fork of the original, `shadowofze/OfflineDAoC`. It keeps the classic
  three-realm rules and is actively maintained.
- **Stay mergeable.** Regularly merge the original's `main` into this fork. Prefer
  additive changes (new files, new settings, new columns) over rewriting shared code, so
  upstream updates keep merging cleanly.
- **Check upstream before each feature.** The original ships about weekly (0.36 was in progress
  on 2026-10-11). Before starting a milestone, merge its `main` and read its `CHANGELOG.md`, so
  nothing is built that it has just shipped.
- **Other forks are sources of ideas and code, not bases.** Their work is ported feature
  by feature onto this base. All of it is GPL-3; keep upstream attribution and each
  source's license notices, and credit the fork in commit messages and in this file.
- **The owner's gameplay rules in `AGENTS.md` still apply** unless Chris changes them:
  real loot, the Realm Exchange, stablemaster routes, gamebots earn their armor,
  Darkness Falls stays open to solo bots.
- **Three-realm rules stay.** Leveling zones are safe from other realms. PvP happens in
  the frontier, battlegrounds and Darkness Falls, as on a normal classic server.

## Sources from other forks

These are surveyed as of 2026-10-11. "Own commits" counts commits that the original does not contain.

| Fork | Own commits | Relationship to the original | What to take |
|---|---|---|---|
| `stefanrows/OfflineDAoC` | 449 | Split 2026-09-16; 118 of the original's commits missing; 1,277 files differ; **replaced three-realm RvR with Camlann-style PvP** (see its `docs/CAMLANN.md`) | Ideas and selected code, adapted to three-realm rules (below) |
| `lometur/HearthDAoC` | 260 | Close to the original (4 commits behind, 176 files differ); a shared multiplayer server | Mostly covered by the original's 0.35/0.36 (classic quests with markers, epics, period spawns, reward items). Only specific missing quests or spawns, after an item-by-item comparison. |
| `scaleysandwich/OfflineDAoC-` | 7 | Early work | Trials of Atlantis (Oceanus) and Catacombs restoration plan (`docs/GOAL2-TOA-MIGRATION.md`) |
| `BeezKneezItem9/OfflineDAoC` | 20 | Recent | Two-way bind portals, buff stones, configurable RvR XP (later, if wanted) |
| `BlakeFL`, `ThatFontGuy`, `catastrophic-impact` | 1–7 | Small | LAN/hosting/Linux tooling; not part of this vision |

The original reports 13 forks. 4 could not be identified from this workspace.

### From stefanrows (adapt, don't merge)

Its `docs/AUTONOMOUS_BOT_ROADMAP.md` is the best existing design for bot identity. What to
borrow:

- **Persistent player types plus traits.** It has six types: Leveler, Casual, Hybrid,
  Hunter, Roamer and Keep warrior. It has five traits: aggression, risk tolerance,
  sociability, patience and chattiness. Types are assigned deterministically, with no
  runtime re-rolls, and are shifted by class: stealthers lean Hunter, healers lean
  Leveler. Its finding F8 ("no identity or intent") matches this fork today.
- **Guild charters:** hunting, RvR, keep, leveling and social guilds, with member mixes
  and invented names.
- **Type-voiced chat in 2003 style.** Only the per-type flavor: this base already has its own chat
  system (see "What the base already has"), so its chat engine and blocklist
  (`AutonomousChatSafetyPolicy`) are not needed.
- **RvR group behavior:** group doctrines with habits (`AutonomousRvrDoctrine`,
  `AutonomousRvrCombatHabits`); weighted roaming toward recent fights (`AutonomousRvrHeat`);
  **danger memory** of where a group died, which cautious and bold leaders treat
  differently (`AutonomousRvrDangerMemory`); **observe before engaging**
  (`AutonomousRvrObserve`); guild cohesion and encounter memory.
- **Solo confidence** that recovers after kills (`AutonomousSoloConfidence`).

**Their lessons** (`docs/AUTONOMOUS_BOT_M7_REVIEW.md`): the first live playtest found
several problems:

- low-level bots killed each other at the stables;
- solo camp choice ignored travel time;
- pickup groups never found camps;
- grudge writes stalled the server tick;
- after two hours, bots were still level 1–8.

So every milestone here is small, ships behind a setting, and gets a real playtest before
the next one starts.

**Not taken:** the Camlann PvP ruleset, Hunters ganking in leveling zones, and the
cross-realm PvE rules.

## Milestones

Each milestone must be playable on its own, sit behind a server setting where practical,
and pass the existing test suite plus new unit tests. Automated tests and real in-game
checks are reported separately.

| # | Milestone | Outcome |
|---|---|---|
| M1 | **Population flow + personalities, PvE-first** | A world that starts and stays spread across levels (established start, play sessions, new characters and alts); every gamebot has a persistent type, traits and a **time budget** (hunt / craft-trade / social / explore); zone memory; personality flavor in the existing chat. No RvR changes. |
| M2 | Living towns | Downtime that looks human (inns, trading, idle chatter, emotes); bot guilds; personality flavor added to the **existing** chat system (no new chat engine) |
| M3 | Reasons to explore PvE | Built on what exists: Bounty Masters extended to every level band, named and epic drops through the existing random-item generator, the crafter economy; bots spread rumors about named monsters and unexplored places. (The classic quests, markers, epics and period spawns are already in the base.) |
| M4 | Frontier PvE | Frontier dungeons and named monsters worth the trip, starting from the existing frontier daily quests and `rvr_zones_xp_rate` if the owner keeps them; frontier PvE camps for bots (new); the player can read danger: scouting, warnings through the existing announcement channel, signs of roaming groups |
| M5 | RvR alive | Group doctrines, observe-before-engage, danger memory, guild cohesion; roaming kill squads and big fights to avoid or join |
| M6 | RvR stakes | Keeps, relics, realm rank and frontier ownership that matter to PvE access and rewards; existing keep guard patrols tuned by frontier depth |
| M7 | New content | New monsters, named spawns, quests and loot in existing zones and dungeons for gaps in 1–50. Truly new 3D zones are not realistic to build here. Trials of Atlantis or Catacombs zones only if the client supports them (not checked). |

## M1 specification: Population flow + personalities, PvE-first

> **Partly superseded:** see "Current direction". The owner chose a fresh start with a staggered launch (not an established start), alts that are added to a bot player's roster, 7% crafters, shaped XP and no-lifers.

Updated 2026-10-11 after simulation (see "Simulation findings" below).

### Scope

Autonomous gamebots only: not companions, not real players (see "Tell bot types apart"
in `AGENTS.md`). PvE, town life and chat only. RvR behavior is unchanged in M1.

### Part A: Population flow

The simulation shows population flow matters more than personality for "is anyone near
me?". With everyone starting at level 1, the population moves as one wave: level 1–10
zones are empty by hour 3, and everyone is level 21–30 by hour 20.

- **Established start:** an option to generate the starting population with a level
  spread (for example evenly over 1–50) instead of all level 1. Existing saves are not
  touched.
- **Play sessions:** bots log in for 2–5 hours and log off for 1–4 hours. That is about 60%
  online at a time. Prime-time shaping can come later.
- **New characters and alts:** a steady trickle of new level-1 characters. The 60-hour
  study tested the rate: one alt every 15 minutes per 300 bots drains the high levels (levels
  41–50 fall from 43 bots to 1 by hour 60); no alts empties levels 1–10 by hour 40; **one alt per
  hour per 300 bots kept every level band populated for 60 hours.** Start there and tune in
  playtest. "Replace" or "add" is still the owner's choice.
- **Build on what exists (checked 2026-10-11).** `AutonomousPopulationController` loads
  launcher-created characters and never creates any itself; `AutonomousPopulationRamp` staggers
  only the startup (the whole non-retired roster is the target, loaded over about 15 minutes);
  `AutonomousRealmLoginBalancer` picks the next login by realm load; `offline_world_bots` has an
  `IsRetired` flag. There are no play sessions, rosters or alts. Sessions, rosters and the
  staggered launch extend the controller and the ramp; they are not a parallel system.
  stefanrows' roadmap milestone M5 ("Established-server generator and alts") is the reference
  design to review before building.

### Part B: Personalities with time budgets

Personality is mainly **how a bot spends its time**, not just which camp it picks. Different
budgets make bots level at different speeds, so slow types stay behind in mid-level zones
while fast types move on. That spreads the world out.

| Type | Share | Hunt | Craft/trade | Social | Explore | Character |
|---|---|---|---|---|---|---|
| **Leveler** | 30% | 88% | 4% | 4% | 4% | Efficient; good XP; short trips |
| **Crafter** | 15% | 35% | 55% | 7% | 3% | Lives at the forge and the Realm Exchange; levels slowly |
| **Socialite** | 20% | 50% | 5% | 30% | 15% | Groups, trades, hangs out in town, wanders |
| **Explorer** | 15% | 45% | 2% | 8% | 45% | Wants to see every inch; visits unvisited zones, some above its level |
| **Daredevil** | 20% | 85% | 2% | 8% | 5% | Pulls harder monsters; dives into dungeons; brags |

These are starting targets, to be tuned in playtest. "Casual" from the first draft is
folded into Crafter and Socialite. RvR-leaning types (Hunter, Roamer, Keep warrior) are
reserved for M5.

- **Activities:** each one goes through normal game systems, per the owner's rules:
  - **Hunt:** the existing PvE flow, with personality weights.
  - **Craft/trade:** real crafting at stations with owned materials, plus Realm Exchange
    and vendor trading at natural breaks. Start from the existing, unused `Craft` activity in
    `AutonomousBotDecisionEngine` (station lookup, owned-material check) rather than a new one.
  - **Social:** time in town (bind point, inn, trainers), emotes, chat, forming groups.
  - **Explore:** travel to a zone the bot hasn't seen recently, with typical monster
    levels up to about 6 above its own, for 30–90 minutes. It kills monsters along the
    way and faces real death risk.
- **Choosing:** at each task boundary, after the existing services (full backpack,
  trainer), the bot picks its next activity. The odds are its budget share divided by
  the activity's typical length.
- **Traits** are small integer ranges, persisted per bot, that shape behavior within a
  type:
  - curiosity (new for this fork)
  - risk tolerance
  - sociability
  - patience
  - chattiness
  - aggression (stored now, used from M5)
- **Assignment** is deterministic from bot id, class and realm, like stefanrows'
  `AutonomousBotIdentity.TypeFor`. Existing bots get a type on first load without losing
  level, items or money.
- **Storage:** new columns on `offline_world_bots` (`OfflineWorldBotRecord` in
  `AutonomousBotEconomy.cs`). The schema reconciler adds new `DataElement` columns at
  startup, so the change is additive.

### Decisions inside "hunt"

Corrected 2026-10-11: this table first listed the 0.28 / 0.16 / 0.035 chances from
`AutonomousBotDecisionEngine.Choose`, which nothing calls. The live rules are below.

| Today (live) | Change |
|---|---|
| Train 90% of the time when points are unspent (`AutonomousObjectiveAssignments`) | Unchanged |
| No crafting (the `Craft` activity exists but is unused) | Craft/trade budget, wiring up the existing activity |
| Town break: 15% chance at a task boundary, 15–30 minutes (`AutonomousTownDowntime`) | Replaced by the social budget |
| Safer camps after 2 deaths at a camp | Risk tolerance moves the threshold; Daredevils tolerate more |
| Camp choice: outdoor camps weighted by live spawns (`SelectByLiveSpawns`), dungeons balanced by region (`SelectWithinEnvironment`); nothing personal | Add personality weights on top: curiosity favors unvisited zones; Leveler favors short trips; Daredevil favors higher con; sociability favors zones with people |
| Dungeon preference permille (100 / 300 / 400) | Shifted by type and risk tolerance |

Hard rules stay hard: realm, reachability, level and con legality, recovery thresholds, the
full-backpack services, and the owner's gameplay rules.

**Tuning note:** in the simulation, Daredevils spent more time on orange and red monsters
(21–29% versus 13–19%) but barely died more. If they should feel different, their weights
need to be stronger.

### Zone memory

- Each bot remembers the zones it has hunted in or explored, with last-visit time
  (bounded, for example the last 32 zones).
- Curiosity weights unvisited and long-unvisited zones.
- It is stored compactly (a serialized column), updated at task boundaries, not on every
  AI tick.

### Chat

- The base already has a full chat system: `AutonomousBotChat` assembles lines from parts,
  `AutonomousBotChatCoordinator` keeps conversations short and rare, `AutonomousChatIntentModel`
  recognizes player questions and `AutonomousChatKnowledge` answers about places and spells. M1
  only adds flavor to it.
- Per-type phrase parts added to the existing pools:
  - Explorers talk about places.
  - Crafters talk about prices and orders.
  - Socialites invite.
  - Levelers ask for groups.
  - Daredevils brag.
- Chattiness scales frequency within the coordinator's existing rate limits.
- No profanity in the new parts. No blocklist is needed: every line is pre-written, nothing is
  generated freely.

### Settings

- Server settings turn each part on or off: established start, sessions, alts, and
  personalities. The default is **off** until the playtest passes.
- Launcher exposure can wait for M2.

### Tests

- Unit tests extend `UT_AutonomousBotDecisionEngine`:
  - realized time shares per type stay within bands over many seeded draws;
  - hard rules are never violated;
  - curiosity measurably widens zone spread.
- Persistence test: a bot's type, traits and zone memory survive save and reload; an
  existing bot gets a stable type.
- Re-run `tools/living-world-sim` after any change to budgets or weights, and record the
  results below.

### Playtest checklist (owner, on the PC)

1. Back up the install. Deploy only the tested build.
2. Watch one realm for an hour, then check again a few hours later.
   - Is there company near a new level-5 character, and near levels 15, 25, 35 and 45?
   - Are towns lively but not packed? The simulation predicts 16–26% of bots in town.
   - Do Crafters actually craft and trade? Do Explorers turn up in unexpected places?
   - Is the chat varied and in character?
3. Check that nothing regressed: no stuck groups, normal server tick, and deaths only where
   expected.
4. Record the result here before starting M2.

## Simulation findings (2026-10-11)

> Directions still hold. Numbers are from the small 300-bot model; the full-scale model (bot players with rosters) supersedes them.

Run with `tools/living-world-sim`: 300 Midgard bots, 20 hours, 5 seeds, using the real camp
catalog (4,003 camps, 25 zones). This is a design model with stated assumptions. **Trust the
directions, not the exact numbers.**

| At hours 17–20 | Today | Mild personalities | **Strong (time budgets)** |
|---|---|---|---|
| Fresh: level spread (std. dev.) | 1.2 | 1.3 | **3.4** |
| Fresh: bots in level 11–20 | 0 | 0 | **46** |
| Fresh: zones with someone hunting or exploring | 11 | 12 | **19** |
| Fresh: bots at overcrowded camps | 35% | 28% | **13%** |
| Fresh: share of bots in town / exploring | 14% / 0% | 16% / 0% | **29% / 12%** |
| Established: bots in level 1–10 | 18 | 17 | **33** |
| Established: zones with someone present | 20 | 20 | **20** |
| Established: bots at overcrowded camps | 9% | 4% | **1.3%** |
| Established: hunters near a level-45 player | 8 | 8 | **4** |

**Correction (2026-10-11).** The first version of this table used some rules from
`AutonomousBotDecisionEngine.Choose` (trainer trips, crafting trips, a 3.5% town break). The
live bots do not call that function. The table above uses the live between-task rules
instead (`AutonomousObjectiveAssignments`: train 90%, unload when the bag is nearly full, and
a 15% chance of a 15–30 minute town break at each solo task boundary). The directions did not
change; the numbers moved a little. Camp selection, which is live, was modeled correctly.

Takeaways:

1. **Population flow is the biggest lever.** A fresh start empties the low-level zones within
   hours whatever the personalities are.
2. **Time budgets are what make personalities matter.** Slow types stay behind in mid-level
   zones. Explorers see about 11 zones in 20 hours versus 7 for Levelers. Towns fill up.
3. **Trade-offs:**
   - towns may be too busy;
   - high-level zones get thinner as more time goes to crafting, socializing and
     exploring;
   - everyone levels about 10% slower.
   
   Tune these in playtest, and consider a larger bot population.
4. **Today, one zone (Munin Sound) holds a quarter of all hunters** in the established
   scenario. The catalog lists its camps across levels 7–48, which may be real or a data
   quirk; it needs checking in game.

## Trade study (2026-10-11): do crafters make sets for others?

> **Superseded:** this model invented its own crafting-quality formula. The server's real rule (96–99%, a 2% masterpiece only at Legendary or for grey recipes) is used from the full-scale study on, so the "perfect set" numbers here do not apply.

**Today: no.** Autonomous bots never craft. Nothing gives them crafting skills (only real players'
progress writes `SerializedCraftingSkills`), the "Craft" rule in `Choose` has no live caller, and no
code makes an item for a bot. Bots do buy and sell through the Realm Exchange, but only loot and
vendor goods. So every number below is about a **proposed** crafting economy, in the model of
`tools/living-world-sim/lw_economy.py`.

40 hours, 300 bots, 5 seeds. All economy numbers (drop rates, prices, material needs, quality
formula, how gear changes leveling) are labelled assumptions. Compare rows; do not trust absolutes.
"Full set" = all 7 slots filled with items within 5 levels of the bot. "Perfect" = full set, every
piece quality 96 or better.

| Fresh world, level 10+ bots at hour 40 | Full set | Crafted share of worn gear | Crafts per crafter | Crafter skill vs bots |
|---|---|---|---|---|
| A: today's rules, gear from loot only | 60% | 0% | n/a | n/a |
| B: strong personalities, crafting does not exist | 62% | 0% | 0 | crafters idle: level 24 vs 30 |
| **C: strong personalities + crafting economy** | **81%** | **16%** | **53** | skill 23, p90 bot level 33 |
| F: B with scarce loot (40%) | 6% | 0% | 0 | n/a |
| **D: C with scarce loot (40%)** | **26%** | **29%** | **51** | skill 22, p90 bot level 33 |
| H: C with 8% crafters | 68% | 8% | 55 | skill 24 |
| G: C with 25% crafters | 88% | 21% | 47 | skill 20 |
| I: C with scarce materials (30%) | 63% | 3% | 16 | skill 7 |
| Established world, scarce loot, no crafting | 2% | 0% | 0 | n/a |
| **Established world, scarce loot, crafting** | **29%** | **42%** | **32** | skill 19, tracks their level |

Takeaways:

1. **Crafters do help others, and more so when loot is scarce.** With 40% loot, crafting lifts full
   sets from 6% to 26% (fresh) and from 2% to 29% (established). With plentiful loot, crafters
   add 18 points of full sets (62% to 81%) but supply only 16% of what is worn.
2. **"Amazing perfect sets" do not appear in the first 40 hours.** Perfect sets: 0% in every
   case, and fewer than 1 fully crafted set per 300 bots (3 to 6 in the scarce-loot cases).
   Reason: quality depends on crafter skill versus item level, and crafters lag the bots who need
   gear. At hour 40 the best crafter has skill 34 and the average 23, while bots are level 30 to 33.
   Easy high-quality crafting (+6) did not change this. Crafters would need to be ahead of demand,
   not behind it.
3. **Crafters pay for their time in levels.** They finish about 6 levels behind others (24 vs 30),
   because 55% of their time is crafting. In return they earn more gold than a crafter with
   nothing to craft (1,170 vs 420), but less than hunters unless loot is scarce (established world:
   crafters are the richest group).
4. **Materials are a hard dependency.** At 30% material supply, crafting nearly stops (16 crafts
   per crafter, skill 7). Hunters must sell materials to the Exchange, or crafters must hunt for
   them. At the normal rate, stock piled up unused (about 20,000 units).
5. **Demand outruns supply when crafters are few or skill lags.** With scarce loot, 60% of orders
   went unfilled at 15% crafters. At 25% crafters, only 7% went unfilled in the plentiful-loot
   case. Median wait for an order was about 5 hours, and a quarter to a third of crafted pieces
   were never bought because the buyer had moved on or found gear elsewhere.
6. **Crafting barely changes leveling speed in this model** (about 0.1 level over 40 hours). Gear
   effects on XP and deaths are guesses. The payoff of a trade economy here is identity, economy
   and reasons to interact, not speed.

Design implications for a future milestone (not approved yet):
- Start crafters with skill matched to demand, or give them a faster early skill curve, so
  perfect gear exists for the levels bots are actually at.
- Make material flow explicit: hunters sell materials at natural task breaks; crafters hunt a
  little for rare ones.
- Let orders carry a deadline and let crafters pick them by profit, with a visible Exchange
  board, so waiting is not 5 hours.
- Keep the owner's rules: real loot, real items, the Realm Exchange, selling only at natural
  breaks, and gamebots earning their armor.

Not modeled: which gear is actually best for a class, group buffs and dyes, price changes from
supply and demand, crafters trading with each other, and how often live bots reach the
Exchange. How often bots shop depends on live between-task visits, which this model only
approximates.

## 60-hour study (2026-10-11): leveling, zones and crafting together

> **Partly superseded:** alts here replace (reroll) a character, which drained the high levels. The current design adds alts to a bot player's roster. The "no one reaches 50 in 60 hours" finding is about the XP curve and still informs the shaped-XP decision.

Same model, 60 hours, 5 seeds, with the corrected live rules. Results are in
`tools/living-world-sim/results/trade_60h_*.json`; `summarize_population.py` prints them.

**Fresh start (everyone level 1):**

| At hour 60 | Today's rules | Strong personalities | + crafting |
|---|---|---|---|
| Mean level | 34.6 | 32.9 | 33.1 |
| Bots by level band 1–10 / 11–20 / 21–30 / 31–40 / 41–50 | 0 / 0 / 0 / 300 / 0 | 0 / 1 / 63 / 236 / 0 | 0 / 2 / 61 / 237 / 0 |
| Zones with someone present (of 25) | 12 | 20 | 20 |
| Share of hunters in the busiest zone | 35% | 29% | 27% |
| Hunters at overcrowded camps | 30% | 15% | 14% |

- Today's rules march everyone together: at hour 20 all 300 bots are level 21–30, at hour 60 all
  are 31–40. Personalities keep a trailing group behind (about 60 bots still in 21–30).
- **Nobody reaches level 41 in 60 hours from a fresh start**, so the level 41–50 zones stay empty.
  This depends on the assumed XP curve; it is the strongest reason to use an established start.

**Established start (levels spread over 1–50, sessions and alts on):**

| At hour 60 | Alt every 15 min | **Alt every hour** | No alts |
|---|---|---|---|
| Bots by level band 1–10 / 11–20 / 21–30 / 31–40 / 41–50 | 30 / 71 / 183 / 15 / 1 | **10 / 19 / 90 / 132 / 49** | 0 / 4 / 58 / 163 / 75 |
| Full gear sets (level 10+) | 25% | **85%** | 90% |
| Crafted share of worn gear | 44% | **47%** | 41% |

(All three with strong personalities, crafting and scarce loot. Today's rules with the
15-minute alt rate drain the same way: levels 41–50 fall from 44 to 3.)

**Crafting at hour 60:**
- Crafters slowly catch up. In a fresh world the average crafter's skill is 29 and the best 39,
  against bots at level 33–37. In the healthy established world (alt every hour) the best crafters
  reach skill 48.
- Crafters end 3 to 7 levels behind other bots, but when loot is scarce they become the richest
  group (about 2,300–3,600 gold against 800–2,400).
- With scarce loot, crafting lifts full sets from 22% to 83% in a fresh world by hour 60.
- **Perfect sets are still essentially absent** (at most 0.2 per 300 bots, in the alt-every-hour
  world). The bar is high: all 7 pieces quality 96+ and within 5 levels of the wearer. Fully
  crafted sets stay rare (at most about 8 per 300 bots). In a fresh world they peak early, on
  low-level characters, and then fall, because crafters cannot keep the top of the population
  supplied.

What this changes in the plan:
1. **Set the alt rate deliberately** (Part A above). It is the biggest single lever in the
   established world, bigger than personalities or crafting.
2. **Use an established start** if the owner wants level 41–50 zones alive early.
3. **If "amazing crafted sets" are a goal, crafting needs its own design**: faster crafter skill,
   or crafters who specialize in a level range, or quality that is easier to reach. The current
   proposal makes crafters useful, not legendary.

## XP-rate study (2026-10-11): the owner at 8×, 5 hours a week

> **Superseded:** flat rates were replaced by XP shaped by level range (model v4).

The owner plays about 5 hours a week and wants fast leveling. The server already has two
separate dials: `xp_rate` (the real player only) and `bot_xp_rate` (autonomous gamebots only),
both 1× in the release. Bots only live while the server runs, so 120 server hours is about
24 weeks of the owner's play. Established start, strong personalities, crafting, scarce loot;
300 Midgard bots, 3 seeds. Script: `tools/living-world-sim/xp_study.py`.

- **The owner at 8×:** about 31 hours of play per character to 50 (about 6 weeks), so about
  3 characters at 50 in 24 weeks. Levels 41–50 take about two-thirds of that time.
- **Company:** in every case, an average of 13 to 27 bots were hunting within 3 levels of the
  owner, and fewer than 3 of them in at most 3% of hours. The established start does this.

| At week 24 | Bots by level band 1–10 / 11–20 / 21–30 / 31–40 / 41–50 | Full gear sets |
|---|---|---|
| Bots 1×, alt every 60 min | 9 / 20 / 52 / 166 / 54 | 91% |
| **Bots 2×, alt every 30 min** | **14 / 26 / 61 / 103 / 97** | **70%** |
| Bots 4×, alt every 60 min | 3 / 9 / 23 / 46 / 220 | 82% |
| **Bots 4×, alt every 30 min** | **8 / 15 / 44 / 68 / 164** | **61%** |
| Bots 4×, alt every 15 min | 15 / 29 / 76 / 107 / 74 | 19% |
| Bots 6×, alt every 10 min | 18 / 29 / 85 / 108 / 59 | 4% |

(Alt rates are per 300 bots; scale them with the bot count.)

Takeaways:
1. **Faster bots need faster alts**, or the world piles up at 50 and the low zones empty.
2. **But fast churn breaks the economy.** Characters that are replaced quickly never get geared:
   at 6× with an alt every 10 minutes, only 4% wear a full set.
3. **Balanced picks:** bots at 2× with an alt every 30 minutes keeps every band alive with a
   working economy. Bots at 4× with an alt every 30 minutes gives a busier endgame (more level
   50s for RvR and groups) with thinner low zones. Both are starting points for playtest.
4. Assumptions: the owner hunts 75% of the time at even-con camps; the XP curve is fitted to
   classic pacing (about 190 hours to 50 at 1×), not measured on this server. Measure real bot
   leveling from the `AUTONOMOUS_XP_PROGRESS` log lines before tuning.

## Full-scale study (2026-10-11): bot players with rosters at 1,000 online

Target from the owner: about 1,000 bots online per realm while he plays (the server only runs
then, so every session is "peak"). `tools/living-world-sim/persona_sim.py` models Midgard alone at
that size: 1,450 bot players, about 900 online at a time, 120 server hours (about 24 weeks at
5 hours a week), the owner at 8×, 2 seeds per case.

What is new in this model (design proposals, not built):
- **A bot player owns up to 3 characters.** The main is never deleted; alts are added. All
  characters share the player's gold (the server already has an account vault).
- **Guilds:** 75% of players are in one; orders wait up to 2 hours for a capable guild crafter.
- **Retirement:** about 7% of players leave over 24 weeks and new players join with a level-1 main.
  Retired characters stay in the records.
- **Real crafting rules** from `AbstractCraftingSkill.GetQuality`: crafted items are 96–99%, and a
  100% masterpiece is a 2% chance only for a Legendary crafter (1000) or a grey recipe. (Earlier
  models in this document used an invented quality formula; their "perfect set" numbers do not
  apply to this server.)
- **Vendor materials** as a gold sink; **spellcrafting** adds bonus stats; **rare drops** compete.

| At week 24 | Bots 2× | Bots 4× | Bots 2×, crafted gear 2.5× pricier | Bots 2×, no alts |
|---|---|---|---|---|
| Online by level band 1–10 / 11–20 / 21–30 / 31–40 / 41–50 | 12 / 31 / 84 / 311 / 462 | 21 / 49 / 84 / 204 / 557 | 8 / 30 / 78 / 315 / 479 | 4 / 7 / 24 / 214 / 667 |
| Zones with hunters (of 25) | 25 | 25 | 24 | 20 |
| Hunters at overcrowded camps (hours 24–120) | 26% | 23% | 26% | 27% |
| Characters created (name ceiling about 5,700) | 2,440 | 2,770 | 2,420 | 1,770 |
| Level-50 characters with a full template | 9% | 6% | 7% | 46% |
| Templates bought / farmed | 41 / 0 | 51 / 0 | 34 / 0 | 221 / 0 |
| Buy vs farm cost (hunting hours) | 23 vs 131 | 23 vs 131 | 59 vs 131 | 23 vs 131 |
| Gold in the economy, hour 20 → 120 | +120% | +130% | +113% | +140% |
| Median gold: crafter players vs others | 2,200 vs 22,900 | 2,200 vs 25,500 | 2,400 vs 16,400 | 2,200 vs 24,200 |

Takeaways:
1. **Rosters protect legacy.** Mains, guilds and gold persist; alts are added. Characters stay well
   under the name ceiling for 24 weeks. At about 4–8 new characters per server hour, the ceiling
   is about 1.5–3 years of the owner's play away.
2. **The owner is never alone:** on average 127–153 bots hunt within 3 levels of him, and fewer
   than 3 in under 0.5% of hours.
3. **The world still drifts toward 50.** Alts keep about 40–70 bots online in levels 1–20, not
   more. Without alts, the low zones nearly empty and only 20 zones have hunters.
4. **At 1,000 online, Midgard's camps get crowded:** about a quarter of hunters share a camp
   beyond the assumed capacity. More spawns, more use of dungeons and the frontier, or a capacity
   check in camp choice will matter at this scale. (Capacity per camp is an assumption.)
5. **The economy does not meet the owner's goal yet:**
   - **Crafters are poor and idle** (about 93% of crafting time has no order, and their median
     gold is about a tenth of everyone else's). Skill-ups burn their money.
   - **Gold inflates** (more than doubles in 100 hours): hunting income outruns the sinks.
   - **Farming never completes a template** in 24 weeks (0 farmed in every case), so rare drops
     are not a real alternative. Buying is far cheaper than farming at today's prices (0.18);
     2.5× pricier crafted gear brings it to 0.45, inside the owner's "costly shortcut" target.
   - **Alts slow endgame gear:** with no alts 46% of level 50s finish a template; with alts, 6–9%,
     because gold and play time are split across characters.

Design levers to test next (not approved yet): crafted gear priced at about 40–60% of farming
time; rare drops about twice as common so farming can finish; crafter players with a hunting
main for income (crafter as an alt); stronger gold sinks (Exchange tax, repairs, consumables);
and spawn capacity at 1,000 online.

## Economy package study (2026-10-11): epic drops at every level and a richer crafter

> Crafter wealth here uses a fixed 15,000-gold cushion. Later studies changed crafter spending rules and found model leaks; compare crafter numbers only within a study.

The owner's goals: "holy shit" items and sets from monsters at all levels; crafting as important
as PvE; crafted gear a clear but costly shortcut over farming; crafters level more slowly but are
richer than anyone except the top farmers. Same full-scale model (1,450 bot players, about 900
Midgard bots online, 24 weeks of the owner's play, 2 seeds), with a package of changes
(`econ2` in `persona_sim.py`; all numbers are assumptions):

- **Named drops** (bonus 10–14, beats spellcraft's 8) and **epic drops** (bonus 15–20) at every
  level; anything not worn is sold on the Exchange, at any level (alts buy them).
- Rare drops twice as common; **crafted gear 1.3× pricier**, so a crafted template costs about
  **half the farming time** (33 vs 65 hunting hours) once repairs and consumables are paid.
- **Materials discount** for 99% (10%) and 100% (25%) items on the crafter's next purchase.
- **Bounded realm commissions:** 30 NPC orders per hour for the realm at 3× materials.
- **Repairs** (6% of income, done by a crafter 60% of the time), **consumables** (4%, half to an
  alchemist), **salvage** (crafters buy junk loot for materials credit), a **masterpiece premium**
  (+10% for 99%, +50% for 100%) and a **5% Exchange tax**.
- Crafters keep a 15,000-gold cushion before spending on skill-ups.

| At week 24 (bots 2×) | Old economy | **Package** | Package without commissions |
|---|---|---|---|
| Median gold: crafter players | 2,200 | **7,900** | 3,000 |
| Median gold: other players | 23,400 | 20,300 | 20,300 |
| Median gold: top 5% farmers (by Exchange sales) | 46,400 | **49,700** | 50,300 |
| Top 5% farmers' Exchange income | 3,100 | **25,300** | 26,500 |
| Level-50 characters with a full template | 10% | **16%** | 17% |
| Templates bought / mixed / farmed | 36 / 17 / 0 | **42 / 33 / 6** | 45 / 36 / 7 |
| Named drops / epic drops in 24 weeks | 0 / 0 | **1,670 / 217** | 1,660 / 219 |
| Characters wearing a named or epic piece, levels 1–10 / 11–20 / 21–30 / 31–40 / 41–50 | 0 | **4% / 11% / 19% / 33% / 45%** | 0% / 12% / 16% / 32% / 44% |
| Gold in the economy, hour 20 → 120 | +121% | +111% | +105% |
| Crafter characters' mean level vs others | 38.5 vs 39.4 | 37.9 vs 39.3 | 38.1 vs 39.3 |

(Bots at 4× behave the same way: crafters 7,500 vs others 22,100; 16 farmed templates.)

What worked:
- **Holy-shit drops exist at every level** and are rare: about 2 epics per server hour across a
  realm of 900 online, and most characters below level 30 have never worn one.
- **Farming became a real path:** the first fully farmed templates appear, and the top 5% of
  farmers earn about 8× more from the Exchange. They are the richest group.
- **Crafting got 3.6× richer,** mostly from realm commissions (without them, crafters stay poor).

What did not:
1. **Crafters are still poorer than ordinary hunters** (7,900 vs 20,300), not richer. The cause is
   **too many crafters for the demand:** about 210 crafters share about 100 orders an hour, and 94%
   of their forge time has nothing to make. Next: fewer crafters (about 8% of players), or crafter
   players who keep a hunting main and craft on an alt, plus more commissions.
2. **Gold still doubles in 24 weeks.** The new sinks are too small. Next: stronger sinks (higher
   repair and consumable costs at high levels, guild and housing costs) or fewer coin drops.
3. **Crafters barely level slower** (about 1.4 levels behind) because the established start dominates.
4. **Named and epic pieces pile up at the top:** 45% of level 41–50 characters wear one by week
   24. Either that is the endgame chase working, or high-level rates should be lower so they stay
   special. The owner's call.

## Fresh-start study (2026-10-11): everyone at level 1, the owner's economy plan

> **Crafter wealth numbers here are unreliable:** this study's "cheap practice craft" rule drained crafters, a leak found and fixed in model v4. The leveling, loneliness and staggered-launch findings stand.

The owner chose a fresh start: every bot begins at level 1 with no armor. Plan (`PLAN` in
`persona_sim.py`): 7% crafters, realm commissions doubled (60 per hour), small classic repair
(2%) and potion (1%) costs that do not punish a player who stays out of the economy, an Exchange
tax only on trades, and **bot-only luxury spending** (rich bots spend part of their surplus on
houses, guild costs, dyes and horse routes) as the main gold sink. 1,450 bot players, about 900
Midgard bots online, the owner at 8× for 24 weeks of 5 hours, 2 seeds per case.

**A model correction found here.** The server has a `crafting_sellback_percent` setting (default
95) that can set crafted items' vendor price near their material cost (it is applied by
`Recipe.cs` only when `crafting_adjust_product_price` is on, so what your item data pays today is
not verified). The earlier runs assumed practice crafts sell back at 50%. The follow-up runs use 90%.

| At week 24 | Plan, bots 2× (50% sellback) | Plan, bots 2× (90%) | Plan, bots 4× (90%) | Plan, bots 4× (90%), staggered launch |
|---|---|---|---|---|
| Bots at level 50 | 0 | 0 | 213 | 164 |
| Crafter skill: median / 700+ / Legendary | 363 / 7 / 0 | 453 / 20 / 13 | 547 / 26 / 14 | 460 / 19 / 9 |
| Crafting orders that expired unfilled | 42% | 5% | 13% | 17% |
| Median gold: crafter players / others / top 5% farmers | 110 / 11,300 / 22,800 | 121 / 10,340 / 21,000 | 320 / 13,800 / 27,000 | 166 / 11,500 / 27,700 |
| Crafter characters' mean level vs others | 28.9 vs 39.5 | 27.8 vs 39.5 | 34.4 vs 42.6 | 31.9 vs 42.1 |
| Hours with fewer than 3 bots near the owner: weeks 1–5 / 5–12 / 12–24 | 100% / 69% / 12% | 100% / 68% / 10% | 100% / 19% / 2% | 100% / 19% / 0% |
| Bots online in levels 1–20 at week 5 / 12 / 24 | 300 / 27 / 10 | 287 / 28 / 16 | 97 / 12 / 42 | 121 / 107 / 44 |
| Level 41–50 characters wearing a named or epic piece | 59% | 61% | 47% | 49% |

Takeaways:
1. **Bots at 2× are too slow for a fresh start:** none reach 50 in 24 weeks, so no alts start
   and the low zones empty after about week 6. **Bots at 4×** reach 50 from about week 18.
2. **The owner at 8× is alone for the first ~5 weeks** in every case, because he outlevels a
   fresh world. Options: start the owner slower until the bots catch up, or add a small group of
   "hardcore" bots (a few percent) that level at the owner's pace, as real servers had.
3. **A staggered launch keeps low zones alive:** with 40% of bots at launch and the rest joining
   over about 12 weeks, levels 1–20 keep about 110 bots online at week 12 instead of 12.
4. **Generous sellback lets crafters keep up with demand** (expired orders fall from 42% to 5–17%,
   and Legendary crafters appear), but **crafters are still broke.** The bots reinvest every coin in
   skill-ups. Crafter wealth is now a bot spending-policy question: for example, crafters invest
   at most half their profit in skill-ups and keep the rest.
5. **Crafters do level much more slowly** (8–12 levels behind), as the owner wanted.
6. **The luxury sink barely matters in a fresh start** (bots are not rich yet). Median gold per bot stays
   around 20–30 hours of hunting income. Inflation is a later-server problem here.

## Model v4 (2026-10-11): shaped XP, the owner's 9 characters, grouping, no-lifers

> **Economy numbers overstated:** this model left out random magic drops. See "Rerun with the data-check corrections". The XP, company and grouping results are unaffected.

The owner's direction:
- **9 characters**, 3 per realm, with a favored main in each realm.
- **Do not skip low levels:** keep 1–35 worth exploring, and compress the 35–50 grind instead.
- **Grouping matters.**
- **A staggered launch.**
- **4% no-lifers:** no alts, always online, min-maxing gear, chasing epics, raids and RvR.

Model (`V4` in `persona_sim.py`): everyone starts at level 1, 40% of bots at launch and the rest
join over about 12 weeks. The owner's Midgard time is a third of his play, in 60–120 minute
blocks, 60% on his main. XP by level range (needs a small server change; today the server has
one flat `xp_rate` and one `bot_xp_rate`):

| Levels | Owner | Bots |
|---|---|---|
| 1–19 | 3× | 1.5× |
| 20–34 | 5× | 2.5× |
| 35–50 | 12× | 6× |

Grouping follows the server default of 40% group goals (no-lifers 70%, socialites 50%), groups of
4–8 within 4 levels, a 20-minute matchmaking timeout, and a group XP bonus of 1.4× with fewer
deaths. The bonus is an assumption; the server's XP code has group and camp bonuses. Crafters
bank half their crafting profit; practice crafts sell back at 90%. 24 weeks of the owner's play,
2 seeds per case.

| Week 24 | **Shaped XP** | Flat XP (owner 10×, bots 5×) | Shaped, no grouping |
|---|---|---|---|
| Owner's hours in Midgard levels 1–10 / 11–20 / 21–30 / 31–40 / 41–50 | **1.1 / 3.2 / 7.4 / 11.3 / 20.4** | 0.4 / 1.1 / 3.3 / 10.3 / 22.9 | 1.3 / 4.2 / 7.5 / 9.7 / 11.4 |
| Owner's three Midgard characters | 50 (week 17–19), ~38, ~39 | 50 (week 15–20), ~34, ~45 | ~47, ~33, ~27 |
| Hours with fewer than 3 bots near the owner | **3–5%** | 4–11% | 0–1% |
| Hours the owner could form a group | **91–93%** | 91–94% | n/a |
| Bots online by level range at week 24 (1–10 / 11–20 / 21–30 / 31–40 / 41–50) | 37 / 95 / 159 / 172 / 478 | 18 / 44 / 96 / 211 / 570 | 34 / 63 / 103 / 228 / 500 |
| Bots that reached 50 / alts started | 598 / 596 | 658 / 660 | 367 / 294 |
| Hunters at crowded camps | 13% | 11% | 21% |
| Share of hunting time in groups, levels 11–20 / 21–30 / 31–40 / 41–50 | 32% / 40% / 41% / 45% | 9% / 34% / 42% / 45% | 0 |
| No-lifers at 50 / with a full top set | 97% / about 45% | 97% / about 43% | 93% / about 36% |

Takeaways:
1. **Shaped XP keeps the low levels alive for the owner:** about 12 hours in levels 1–30 against
   about 5 at a flat 10×, with the main still reaching 50 in about 4–5 months.
2. **Grouping is a big lever:** almost always a group available, twice as many bots reaching 50
   (and starting alts), and less crowding, because a group shares one camp.
3. **The world stays spread** across all level ranges through week 24 (staggered launch plus alts).
4. **Crafters are still the poorest group.** A model leak was found and fixed (a "cheap practice
   craft" rule drained them; they bought salvage they did not need). After the fix, crafter median
   gold rose from about 200 to about 1,800, still far below other players (about 11,100). Crafters
   level much slower (27 vs 38.5), and hunting income grows with level while craft margins are
   fixed per piece. Closing the gap needs bigger margins or more paid work, not more tuning of sinks.

### Follow-up: does "hunting main + crafter alt" make crafters rich? (2026-10-11)

Small test on the v4 world (2 seeds, 24 weeks): 80% of crafter players hunt on a main and craft on an
alt (shared purse), 20% stay pure crafters. Another model flaw was found and fixed first: "bank half
the profit" was banking half of *revenue* (which includes materials), so crafters spent about 90% of
their profit on skill-ups.

| Week 24 | Pure crafters | Main + crafter alt |
|---|---|---|
| Median gold: crafter players vs others | 2,970 vs 11,190 | 2,810 vs 10,880 |
| Crafter skill median / Legendary | 538 / 11 | 481 / 13 |
| Orders expired | 2% | 4% |

**The alt alone does not close the gap.** A 90-hour ledger trace (1 seed) shows why: crafting income is
**concentrated at the top.** The top fifth of crafters (skill about 780) hold a median of about 13,600
gold, richer than the median hunter (about 7,100). The other four-fifths (skill about 370) hold about
1,300. The average crafter player (about 10,900) is slightly richer than the average other player
(about 9,800). Two causes: high-level orders and commissions pay far more and go to the best
crafters, and the luxury sink was scaled to the crafter character's (low) level, taxing crafters
early. The luxury threshold now uses the player's highest-level character (fixed after these runs).

Options if the owner wants the *typical* crafter rich, not only the famous ones: apprentice-level paid
work (commissions sized to the crafter's skill, paid for time rather than item value), or fewer
crafters sharing the same work.

## RvR study (2026-10-11, corrected by the audit): three realms, keeps, relics, roaming, frontier PvE

> **Superseded:** this model used 5 frontier zones per realm; the real frontier has 4. See "Rerun with the data-check corrections" for the current numbers.

**What already exists in the server (read from the code, not playtested here):**
- **Bot RvR objectives:** regroup, hunt enemies, defend a keep under attack, and assault keeps
  (`AutonomousRvrDirector`).
- **Organized sieges** (`AutonomousRvrEventLayer`, `RealmEventPolicy`):
  - Each one goes muster → march → battle within a 4-hour window.
  - Only forces averaging level 50 start sieges.
  - Defenders answer the army that marched at `DefenseRatio` 0.5 (at least 8).
  - Up to 128 attackers (240 for relic raids).
  - A level-50 force picks a relic keep about one time in eight.
  - The scheduler keeps about one siege running at almost all times.
- **Realm raids into Darkness Falls and Summoner's Hall.** Their raid AI is not described here as
  working; see `AGENTS.md`.
- **Realm points for bots** use the pre-1.81 formula. RR2 is 7,125 RP, RR3 61,750, RR4 213,875 and
  RR5 513,500.
- **Settings:** `rp_rate`, `relic_owning_bonus` (10% per enemy relic),
  `relic_players_required_on_pad` (16), `Relic_Return_Time` (20 minutes) and
  `keep_balance_multiplier`.
- **A gap:** the bots' PvE camp catalog has no frontier zones, so bots do not level or farm in the
  frontier today. Frontier PvE would be new content.

**Model** (`tools/living-world-sim/rvr_sim.py`):
- Three frontiers of 5 zones (2 border, 2 middle, 1 inner), each with 7 keeps and 2 relic keeps.
- 400 RvR-capable characters per 1,000 online in each realm. Roles: 45% join sieges, 43% roam in
  8s, 12% stealth; 10% are no-lifers.
- 8% of level 35+ PvE bots farm their own frontier (proposed content).
- 120 server hours, 3 seeds. Meeting, spotting and fight odds are assumptions.

**Audit correction:** the first version of this study let low-level bots siege, sent defenders at
0.8× instead of the server's 0.5×, gated relic raids behind an invented rule, used a 5% relic bonus
instead of 10%, and had a mistyped realm-rank table. Those runs said "zerging pays 2.5× more" and
"relics barely move". Both were artifacts and are withdrawn. The numbers below are the corrected runs.

| Per hour of server time | Balanced | Hibernia at 750 | Hibernia 750 + 15% underdog bonus | Balanced, no relic bonus |
|---|---|---|---|---|
| Sieges / keep flips | 2.1 / 1.1 | 2.1 / 1.2 | 2.1 / 1.2 | 2.1 / 1.2 |
| Open-field fights / RvR deaths | 34 / 243 | 30 / 215 | 30 / 215 | 34 / 239 |
| Relic raids / relic captures | 0.18 / 0.07 | 0.15 / 0.06 | 0.17 / 0.06 | 0.14 / 0.05 |
| Darkness Falls access (Alb / Mid / Hib) | 19% / 20% / 60% | 84% / 7% / 8% | 42% / 40% / 17% | 28% / 27% / 44% |
| Most relics held by one realm at the end (of 6, per seed) | 2, 5, 5 | 3, 3, 3 | 4, 3, 6 | 3, 3, 2 |

- **RP per active hour (balanced):** sieges about 460, roaming about 460, stealth about 320.
- **Deaths per active hour (balanced):** sieges 0.18, roaming 0.57, stealth 0.09.
- **Ranks after 24 weeks:** about 88% of RvR-capable bots reach RR2 and about 10% RR3; none reach RR4.
  No-lifers reach a median of about 57,000 RP (just under RR3).
- **Frontier PvE deaths per hour** (proposed): border 0.79, middle 0.79, inner 0.73. Without enemy
  warnings, 1.13 / 1.01 / 0.90.

Takeaways:
1. **The frontier is busy:** about one keep flip and 34 small fights an hour.
2. **Sieges and roaming pay about the same** under the server's real siege rules. There is no zerg
   problem to fix in this model.
3. **Relics do move** (about one capture per 14 hours), and **the 10% relic bonus can snowball:** in
   two of three balanced runs one realm ended with 5 of the 6 relics, and Darkness Falls access was
   lopsided. Without the bonus, access is more even. Worth watching in playtest; options are a smaller
   bonus, a cap, or relics that drift home.
4. **Population balance decides Darkness Falls:** a realm with 25% fewer bots holds it about 8% of the
   time; a 15% underdog bonus lifts that to 17%. Keep the three realms equal.
5. **Deep-frontier PvE is too deadly and not graded by depth** without new design (next section).
6. **Realm ranks are a long climb** at `rp_rate` 1: RR3 is rare after 24 weeks.

### RvR fix run (2026-10-11, corrected by the audit)

> **Superseded** by the 4-zone rerun below.

Options (`RVR_SET=fix`):
- **Adaptive roles:** at half of their logins, bots re-pick their role weighted by their realm's
  recent RP per hour.
- **Small-group bonus:** open-field kills by 8 or fewer pay 1.5×, and outnumbered kills up to 2× more.
- **Guarded, graded frontier:** guards cut enemy reach to 60% in middle zones and 25% in inner zones,
  and wear down enemy groups inside. Proposed rewards are 2.0× / 1.5× / 1.2× a home zone.

| | Baseline | Adaptive roles | + small-group bonus | Guarded frontier | Both + adaptive roles |
|---|---|---|---|---|---|
| Time in sieges / roaming / stealth | 46% / 44% / 11% | 34% / 56% / 11% | 25% / 67% / 9% | 46% / 44% / 11% | 24% / 70% / 6% |
| RP per hour: siege / roam / stealth | 464 / 461 / 324 | 360 / 534 / 321 | 304 / 892 / 323 | 449 / 455 / 231 | 287 / 902 / 233 |
| Open-field fights per hour | 34 | 52 | 68 | 34 | 72 |
| Frontier PvE deaths/hour: border / middle / inner | 0.79 / 0.79 / 0.73 | 0.82 / 0.82 / 0.81 | 0.76 / 0.76 / 0.66 | **0.81 / 0.49 / 0.17** | 0.65 / 0.38 / 0.13 |
| Frontier PvE value vs home: border / middle / inner | 1.69 / 1.27 / 1.03 | 1.68 / 1.26 / 1.01 | 1.70 / 1.28 / 1.04 | **1.68 / 1.35 / 1.16** | 1.74 / 1.38 / 1.16 |

Takeaways:
1. **Left to choose, bots drift toward roaming** (56%), and open-field fights rise to about 52 an hour.
2. **A small-group RP bonus is not needed** and would push roaming to about 70% and sieges to about
   24%, which risks thin sieges. Hold it until a playtest shows a zerg problem.
3. **The guarded, graded frontier works on its own:** frontier PvE deaths fall from 0.81 an hour at the
   border to 0.49 in the middle and 0.17 inner. Every ring stays worth more than home PvE.
4. **Stealthers earn the least** and shrink when guards are added. Stealth hunting needs its own
   reward if it should stay a common play style.

## Rerun with the data-check corrections (2026-10-11)

After the [data check](LIVING-WORLD-DATA-CHECK-2026-10-11.md), both models were corrected and rerun.
The owner chose to keep random magic drops at the current rate.

### Economy: random magic drops added (`persona_sim.py`, v4, 120 hours, 2 seeds)

**What the model now includes:**
- Random class items from ordinary kills: 24% per solo kill, group rolls per member as in the server.
  - Strength from the server's utility cap.
  - Sold at about 0.55 of a kill's coin when not used.
- **Assumptions:**
  - 40 kills per hunting hour, not measured;
  - a spellcrafted piece is worth about 35 utility;
  - "weak" and "strong" cases: 60% or 85% of a random item's utility is useful.

| | Before (no random drops) | Random drops, weak items | Random drops, strong items |
|---|---|---|---|
| Crafted-gear orders | 6,015 | 3,159 (-47%) | 2,920 (-51%) |
| Crafters' income from orders | 5.1 M | 2.6 M | 2.2 M |
| Median gold: crafter players / others | 3,250 / 12,010 | 4,551 / 17,316 | 4,164 / 16,848 |
| Bots reaching level 50 | 613 | 650 | 662 |
| Level-50 sets completed from drops (median hours at 50) | 30 (37 h) | 28 (36 h) | 89 (16 h) |
| Sets completed mostly from bought crafted gear | 0 | 0 | 0 |

**Takeaways:**
1. **Random drops roughly halve the demand for crafted gear.** Leveling slots fill themselves, so bots
   order far fewer pieces.
2. **Everyone else gets about 40% richer**, and crafters stay at about a quarter of others' median gold.
   The winner-take-most pattern is unchanged.
3. **Whether drops replace crafted level-50 sets depends on how useful random stat lines are.**
   - With strong items, finished sets come three times as often and three times as fast.
   - With weak items, nothing changes at level 50.
   - This is the biggest unknown; in-game logs of what bots actually wear will settle it.
4. **Even before this change, no bot finished a set mostly from bought crafted gear.** The "crafted
   set as a costly shortcut" never happened in the model.
5. **What follows for "crafting as important as PvE":** with the current drop rate, crafting needs
   value that drops can't supply:
   - commissions (including apprentice orders);
   - repairs, potions, poisons and arrows;
   - siege engines;
   - spellcrafting on top of found items;
   - dyes and housing goods.

### RvR: the real 4-zone frontier (`rvr_sim.py`, 120 hours, 3 seeds)

| Per hour, balanced 1000/1000/1000 | Before (5 zones) | Now (4 zones) |
|---|---|---|
| Open-field fights / RvR deaths | 34 / 243 | 51 / 309 |
| Sieges / keep flips | 2.1 / 1.1 | 2.1 / 1.2 |
| Relic captures | 0.07 | 0.06 |
| RP per active hour: siege / roam / stealth | 464 / 461 / 324 | 463 / 634 / 463 |
| Ranks after 24 weeks: RR2+ / RR3+ | 88% / about 10% | 89% / 18% |
| Frontier PvE deaths per hour: border / middle / inner (unguarded) | 0.79 / 0.79 / 0.73 | 1.46 / 1.51 / 0.37 |

**Fix options on the 4-zone layout:**

| | Baseline | Adaptive roles | + small-group bonus | Guarded frontier | Both + adaptive roles |
|---|---|---|---|---|---|
| Time in sieges / roaming / stealth | 46% / 44% / 11% | 27% / 61% / 12% | 19% / 71% / 9% | 46% / 44% / 11% | 19% / 73% / 8% |
| RP per hour: siege / roam / stealth | 463 / 634 / 463 | 316 / 738 / 439 | 277 / 1,202 / 455 | 446 / 637 / 367 | 271 / 1,195 / 356 |
| Open-field fights per hour | 51 | 84 | 104 | 51 | 109 |
| Frontier PvE deaths/hour: border / middle / inner | 1.46 / 1.51 / 0.37 | 1.62 / 1.71 / 0.42 | 1.40 / 1.50 / 0.36 | **1.46 / 0.92 / 0.09** | 1.25 / 0.84 / 0.08 |
| Frontier PvE value vs home: border / middle / inner | 1.49 / 1.11 / 1.10 | 1.45 / 1.07 / 1.09 | 1.51 / 1.11 / 1.11 | **1.49 / 1.23 / 1.18** | 1.55 / 1.26 / 1.18 |

**Takeaways (these replace the earlier RvR takeaways):**
1. **The real frontier is more crowded.** Fewer zones mean groups meet more: about 51 fights an hour
   instead of 34.
2. **Roaming now pays about 1.4× more than sieges.** Left to choose, bots drift to 61% roaming.
   - A small-group bonus is still not wanted: it would cut sieges to 19% of RvR time.
   - This result depends on the meeting rate, which is an assumption.
3. **Stealthers earn about as much as siegers** (463 RP an hour), so a separate stealth reward is less
   needed.
4. **Relics still snowball:**
   - in two of three balanced runs one realm ended with all 6 relics;
   - Hibernia held Darkness Falls 56% of the time in the balanced case;
   - with Hibernia at 750 bots, it holds Darkness Falls 16% of the time; a 15% underdog bonus lifts
     that to 37%.
5. **The unguarded frontier is too deadly** in the border and middle zones (about 1.5 deaths an
   hour).
   - The guarded, graded design brings the middle to 0.92 and the inner zones to 0.09.
   - The border stays dangerous, which is the intended graded feel.
   - Every ring stays worth more than home PvE.
6. **Ranks:** RR3 is reached by about 18% of RvR bots after 24 weeks. No bot reaches RR4.

## Open questions

- Apprentice commissions: should typical crafters earn a living, or is winner-take-most right?
- Stealth hunting: give stealthers their own reward, or let them stay rare?
- Epic and named drops: how rare at levels 41–50?
- Relic bonus: keep 10% per relic, lower it, or cap it?
- Can the owner's PC run about 3,000 bots online at once? (Load test before building features.)
- How useful are random drops' stat lines in practice (weak or strong case)? In-game logs of what
  bots wear will tell. (The drop rate itself is decided: keep the current rate.)
- Are the Atlas daily, weekly and monthly quest givers (for example Herou at Svasud Faste) actually
  in the 0.35 world? They are not in the database; one look in game settles it.
- Do those Atlas-era quests fit the classic feel, or should frontier PvE reasons come only from
  extended Bounty Masters and named monsters?
- Should the Realm Exchange get a fee? None was found in the code; the housing market search
  already charges 20%.

## Graphics (tabled, 2026-10-11)

Tabled until after the current sprint, except two client-side add-ons to try on a test copy:
- **ReShade** (post-processing such as ambient shadows, sharpening and color grading).
- **NVIDIA RTX Remix** (path-traced lighting and asset replacement for old DirectX 8/9 games).
  Compatibility with this client is unknown.

Facts that bear on both:
- The client draws with **DirectX 9**.
- The original's 0.36 runs the client on Vulkan through DXVK 3.1.1. That is two files in the
  client folder (`d3d9.dll`, `dxvk.conf`), and deleting them goes back to DirectX 9.
- RTX Remix probably cannot run alongside DXVK and would replace it. This is an inference, not
  tested.

Neither add-on touches `game.dll`, so the hash guards are unaffected.

Later options:
- Recolored and reshaped private art (`tools/pet-art`).
- An HD-texture test on one skin.
- Extra foliage and props added through zone `fixtures.csv` rows: `si_portal_visuals.py` is the
  precedent. Non-solid objects are safe; solid ones need that zone's navmesh rebuilt.

## Sources

- Original: https://github.com/shadowofze/OfflineDAoC (its `CHANGELOG.md` lists what each
  upcoming version adds; checked at `1cabc77` on 2026-10-11)
- stefanrows: https://github.com/stefanrows/OfflineDAoC (docs/AUTONOMOUS_BOT_ROADMAP.md,
  docs/AUTONOMOUS_BOT_M7_REVIEW.md, docs/CAMLANN.md, docs/RVR_GROUP_DOCTRINE.md)
- HearthDAoC: https://github.com/lometur/HearthDAoC
- scaleysandwich: https://github.com/scaleysandwich/OfflineDAoC-
- BeezKneezItem9: https://github.com/BeezKneezItem9/OfflineDAoC
