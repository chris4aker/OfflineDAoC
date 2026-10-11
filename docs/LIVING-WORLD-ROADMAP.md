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
- **New characters and alts:** a steady trickle of new level-1 characters. The 60-hour
  study tested the rate: one alt every 15 minutes per 300 bots drains the high levels (levels
  41–50 fall from 43 bots to 1 by hour 60); no alts empties levels 1–10 by hour 40; **one alt per
  hour per 300 bots kept every level band populated for 60 hours.** Start there and tune in
  playtest. "Replace" or "add" is still the owner's choice.
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
