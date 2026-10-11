# Living World roadmap (Chris's fork)

Status: **planning.** Nothing in this document is implemented yet.
Owner: Chris (`chris4aker/OfflineDAoC`). Started 2026-10-11.

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
| `lometur/HearthDAoC` | 260 | Close to the original (4 commits behind, 176 files differ); a shared multiplayer server | Quest indicators, epic quest chains with period dialogue, restored leveling spawns, monster period corrections |
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
- **Type-voiced chat in 2003 style**, with a safety blocklist (`AutonomousChatSafetyPolicy`).
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
| M1 | **Population flow + personalities, PvE-first** | A world that starts and stays spread across levels (established start, play sessions, new characters and alts); every gamebot has a persistent type, traits and a **time budget** (hunt / craft-trade / social / explore); zone memory; personality-voiced chat. No RvR changes. |
| M2 | Living towns and chat | Downtime that looks human (inns, trading, idle chatter, emotes), type-voiced 2003-style chat, a safety blocklist |
| M3 | Reasons to explore PvE | HearthDAoC's quest indicators, epic chains and restored spawns; bots spread rumors about named monsters and unexplored places |
| M4 | Frontier PvE | Frontier dungeons and named monsters worth the trip; the player can read danger: scouting, warnings, signs of roaming groups |
| M5 | RvR alive | Group doctrines, observe-before-engage, danger memory, guild cohesion; roaming kill squads and big fights to avoid or join |
| M6 | RvR stakes | Keeps, relics, realm rank and frontier ownership that matter to PvE access and rewards |
| M7 | New content | Trials of Atlantis zones, Catacombs, then original dungeons for gaps in 1–50 |

## M1 specification: Population flow + personalities, PvE-first

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
- **New characters and alts:** a steady trickle of new level-1 characters. In the
  simulation, one every 15 minutes per 300 bots: an offline bot of level 30 or higher
  starts an alt. This is the owner's choice of "replace" or "add".
- **Check what exists first.** `AutonomousPopulationController`, `AutonomousPopulationRamp`
  and `offline_population_settings` already manage population. stefanrows' roadmap
  milestone M5 ("Established-server generator and alts") is the reference design to
  review before building.

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
    and vendor trading at natural breaks.
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

| Today | Change |
|---|---|
| Trainer visit chance 0.28 | Unchanged |
| Craft chance 0.16 | Replaced by the craft/trade budget |
| Safe-town downtime 0.035 | Replaced by the social budget |
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

- `AutonomousBotChat` gets per-type phrase pools:
  - Explorers talk about places.
  - Crafters talk about prices and orders.
  - Socialites invite.
  - Levelers ask for groups.
  - Daredevils brag.
- Chattiness scales frequency within the existing rate limits.
- No profanity in M1. A blocklist check is applied to generated lines.

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

Run with `tools/living-world-sim`: 300 Midgard bots, 20 hours, 5 seeds, using the real camp
catalog (4,003 camps, 25 zones). This is a design model with stated assumptions. **Trust the
directions, not the exact numbers.**

| At hours 17–20 | Today | Mild personalities | **Strong (time budgets)** |
|---|---|---|---|
| Fresh: level spread (std. dev.) | 1.3 | 1.3 | **3.6** |
| Fresh: bots in level 11–20 | 0 | 0 | **46** |
| Fresh: zones with someone hunting or exploring | 11 | 11 | **19** |
| Fresh: bots at overcrowded camps | 40% | 30% | **16%** |
| Fresh: share of bots in town / exploring | 8% / 0% | 10% / 0% | **26% / 12%** |
| Established: bots in level 1–10 | 16 | 16 | **33** |
| Established: zones with someone present | 19 | 20 | **21** |
| Established: bots at overcrowded camps | 12% | 5% | **2.5%** |
| Established: hunters near a level-45 player | 9 | 10 | **6** |

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

## Open questions

- Final type list, names and time budgets.
- Bot population size: more bots offset the thinner high-level zones.
- Alts: replace offline high-level bots, or add new ones?
- Should the player see a bot's personality, for example in `/who` or a `/bot` command?
- When should stefanrows' guild charters arrive: M2 or M5?

## Sources

- Original: https://github.com/shadowofze/OfflineDAoC
- stefanrows: https://github.com/stefanrows/OfflineDAoC (docs/AUTONOMOUS_BOT_ROADMAP.md,
  docs/AUTONOMOUS_BOT_M7_REVIEW.md, docs/CAMLANN.md, docs/RVR_GROUP_DOCTRINE.md)
- HearthDAoC: https://github.com/lometur/HearthDAoC
- scaleysandwich: https://github.com/scaleysandwich/OfflineDAoC-
- BeezKneezItem9: https://github.com/BeezKneezItem9/OfflineDAoC
