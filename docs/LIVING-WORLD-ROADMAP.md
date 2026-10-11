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
| M1 | **Personalities, PvE-first** | Every gamebot has a persistent type and traits, including *curiosity*; zone memory; personality shifts PvE choices and chat. No RvR changes. |
| M2 | Living towns and chat | Downtime that looks human (inns, trading, idle chatter, emotes), type-voiced 2003-style chat, a safety blocklist |
| M3 | Reasons to explore PvE | HearthDAoC's quest indicators, epic chains and restored spawns; bots spread rumors about named monsters and unexplored places |
| M4 | Frontier PvE | Frontier dungeons and named monsters worth the trip; the player can read danger: scouting, warnings, signs of roaming groups |
| M5 | RvR alive | Group doctrines, observe-before-engage, danger memory, guild cohesion; roaming kill squads and big fights to avoid or join |
| M6 | RvR stakes | Keeps, relics, realm rank and frontier ownership that matter to PvE access and rewards |
| M7 | New content | Trials of Atlantis zones, Catacombs, then original dungeons for gaps in 1–50 |

## M1 specification: Personalities, PvE-first

### Scope

Autonomous gamebots only: not companions, not real players (see "Tell bot types apart"
in `AGENTS.md`). PvE decisions and chat only. RvR behavior is unchanged in M1.

### Identity

- **Types for M1 (PvE-relevant):**
  - **Leveler:** efficient; sticks to good XP.
  - **Explorer:** seeks unvisited zones and camps; takes longer trips.
  - **Casual:** frequent town breaks; crafts and trades.
  - **Socialite:** prefers groups; lingers in towns; chatty.
  - **Daredevil:** pulls harder camps; dives into dungeons; accepts more deaths.
  - RvR-leaning types (Hunter, Roamer, Keep warrior) are reserved for M5. Until then those
    bots behave as Hybrid/Leveler in PvE.
- **Traits** are small integer ranges, persisted per bot:
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

### Decisions (where personality plugs in)

`AutonomousBotDecisionEngine.Choose` today uses fixed numbers for every bot. M1 makes them
depend on traits, within bounds:

| Today | Change |
|---|---|
| Trainer visit chance 0.28 | Patience and type shift it |
| Craft chance 0.16 | Higher for Casual |
| Safe-town downtime 0.035 | Higher for Casual and Socialite; lower for Leveler |
| Safer camps after 2 deaths at a camp | Risk tolerance moves the threshold; Daredevils tolerate more |
| Camp choice: outdoor camps weighted by live spawns (`SelectByLiveSpawns`), dungeons balanced by region (`SelectWithinEnvironment`); nothing personal | Add personality weights on top: curiosity favors camps in unvisited zones; Leveler favors the shortest trip; Daredevil favors higher con |
| Dungeon preference permille (100 / 300 / 400) | Shifted by type and risk tolerance |

Hard rules stay hard: realm, reachability, level and con legality, recovery thresholds, the
full-backpack services, and the owner's gameplay rules.

### Zone memory

- Each bot remembers the zones it has hunted in, with last-visit time (bounded, for
  example the last 32 zones).
- Curiosity weights unvisited and long-unvisited zones. This is the driver for bots to
  spread across the world instead of piling into the same camps.
- It is stored compactly (a serialized column), updated at task boundaries, not on every
  AI tick.

### Chat

- `AutonomousBotChat` gets per-type phrase pools: Explorers talk about places, Socialites
  invite, Levelers ask for groups, Daredevils brag. Chattiness scales frequency within the
  existing rate limits.
- No profanity in M1. A blocklist check is applied to generated lines.

### Settings

- A server setting turns personalities on or off (default **off** until the playtest
  passes).
- Launcher exposure can wait for M2.

### Tests

- Unit tests extend `UT_AutonomousBotDecisionEngine`:
  - each type's choice distribution over many seeded draws stays within expected bands;
  - hard rules are never violated;
  - curiosity measurably widens zone spread.
- Persistence test: a bot's type and traits survive save and reload; an existing bot gets
  a stable type.

### Playtest checklist (owner, on the PC)

1. Back up the install. Deploy only the tested build.
2. Watch one realm's leveling zones for an hour.
   - Do bots spread out across zones instead of stacking?
   - Do towns have some life?
   - Is the chat varied and in character?
3. Check that nothing regressed: bots still level at a normal pace, no stuck groups, and
   no extra deaths beyond what Daredevils should take.
4. Record the result here before starting M2.

## Open questions

- Final type list and names: are these five PvE types right?
- How many bots should be Explorers?
- Should the player see a bot's personality, for example in `/who` or a `/bot` command?
- When should stefanrows' guild charters arrive: M2 or M5?

## Sources

- Original: https://github.com/shadowofze/OfflineDAoC
- stefanrows: https://github.com/stefanrows/OfflineDAoC (docs/AUTONOMOUS_BOT_ROADMAP.md,
  docs/AUTONOMOUS_BOT_M7_REVIEW.md, docs/CAMLANN.md, docs/RVR_GROUP_DOCTRINE.md)
- HearthDAoC: https://github.com/lometur/HearthDAoC
- scaleysandwich: https://github.com/scaleysandwich/OfflineDAoC-
- BeezKneezItem9: https://github.com/BeezKneezItem9/OfflineDAoC
