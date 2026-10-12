# Living World audit (2026-10-11)

The owner asked for a full audit before any game code is written. It covers the repository state, the
simulators against the server code, the corrections made during the day, what is verified versus
assumed, and what can realistically be built. The roadmap's "Current direction" section is the
up-to-date plan; this file is the evidence behind it.

Nothing in this audit changed the game, started a server, or touched a played install.

## 1. Repository state

| Branch | State | Note |
|---|---|---|
| `main` | Unchanged at `d121209` | Never touched |
| `living-world/trade-sim` | **Working branch**, 15 commits ahead of `main`, 0 behind | Contains everything below, including the CI workflow |
| `living-world/roadmap` | Stale: the first roadmap and simulator | A subset of `trade-sim` with the uncorrected first 20-hour numbers. Safe to delete once `trade-sim` is accepted. |
| `ci/github-actions` | Stale: the CI workflow alone | Also in `trade-sim` |
| `claude-push-test-20261011` | Leftover push test at `main`'s commit | The owner should delete it on github.com (Claude's delete attempts were refused). |

- **Authorship:** every commit is authored `chris4aker <chris4aker@users.noreply.github.com>`, with
  co-author attribution.
- **Automatic build (GitHub Actions):** every push to `trade-sim` built.
  - **Corrected 2026-10-12:** not every run passed the tests. Two runs, on documentation-only
    commits, each had one failing server test. The same code passed on rerun (3 more runs), so one
    existing test is intermittent ("flaky"). Its name is not known yet: the build now names failing
    tests, so the next failure will show it.
  - The number of tests that ran was never confirmed: run logs could not be read from the cloud
    workspace. **Later the same day:** a CI step now reports counts as notices. On
    `feature/xp-by-level-range`, 2,674 of 2,674 server tests ran and passed.
  - About 47 test classes that need installed game files are excluded on purpose
    (`.github/ci-excluded-tests.txt`).
- **Player data:** none committed. There is no database, `account.txt`, logs or credentials. The
  results folder holds about 7 MB of simulation output (JSON).
- **An incident:** two script files of unknown origin (`study_1500.py`, `summarize_1500.py`)
  appeared in the simulator folder and were committed by mistake once. They were removed in the next
  commit and moved out of the repository; they remain in the branch history. They did not match the
  simulator and were never used.
- **Project rules (`AGENTS.md`):** no server was started, nothing was deployed or copied over an
  install, old releases were not touched, and every report separated model results from real play.
  Nothing has been playtested.

## 2. Simulators checked against the server code

**Verified in code** (file and value):

| Rule used | Where in the server | Status |
|---|---|---|
| Bot goal mix: 60/40/0 (levels 1–19), 40/40/20 (20–49), 20/40/40 (50) solo/group/RvR | `BotGoalSettings.Defaults` | Matches |
| Between-task services: train 90%, unload when the bag is nearly full, 15% town break of 15–30 min | `AutonomousObjectiveAssignments`, `AutonomousTownDowntime` | Matches (after the first correction below) |
| Camp choice: environment, live-spawn weighting, safer camp after deaths | `SelectPveEnvironment`, `SelectWithinEnvironment`, `SelectSafestAvailableAfterDeath` | Live and used |
| Crafted quality 96–99%, 2% masterpiece at Legendary (1000) or for grey recipes, item-con thresholds | `AbstractCraftingSkill.GetQuality`, `GetItemCon` | Matches |
| Crafted sell price near 95% of materials | `crafting_sellback_percent` (95) in `Recipe.cs` | Applied only when `crafting_adjust_product_price` is on; actual item data not checked |
| Separate XP rates for the player and bots | `xp_rate`, `bot_xp_rate` | Exist, both 1× in the release |
| Siege scheduler chances, caps 128/240, 12-minute muster and cooldown | `AutonomousRvrEventLayer` | Matches |
| Sieges only by forces averaging level 50; relic raids about one in eight | `AutonomousRvrEventLayer.ChooseCore` | Matches (after the audit fix) |
| Defenders sent at 0.5× the army that marched (at least 8) | `RealmEventPolicy.DefenseRatio` | Matches (after the audit fix) |
| Realm points (pre-1.81 formula) and the realm-rank table | `AutonomousBotRealmPointRewards`, `GamePlayer.REALMPOINTS_FOR_LEVEL` | Matches (after the audit fix) |
| Relic bonus 10% per enemy relic | `relic_owning_bonus` | Matches (after the audit fix) |
| Bot groups track roles (tank, healer…) | `AutonomousBotGroupCoordinator` (`BotPveGroupRole`) | Exists; **not modeled** in the simulators |
| Bots' PvE camp catalog has no frontier zones | `data/capnbry_classic_si_goals.json` | Confirmed. The data check later found about 4,400 monsters already in the 12 frontier zones, so the camps for bots are new but the monsters are not |
| Today's bots never craft | No live caller for `AutonomousBotDecisionEngine.Choose`; only players' progress writes crafting skills | Confirmed |

**Assumptions that are not verified** (they drive the numbers; calibrate before relying on them):
- **Leveling:** the XP curve (fitted to classic pacing, about 190 hours to 50 at 1×), kill speed,
  camp capacity and the level-35+ share of the population.
- **Economy:** coin income per hour, drop rates, prices, material costs, spellcraft costs, repair
  and potion shares, luxury thresholds and commission volume.
- **Groups:** a group XP bonus of 1.4× and 0.4× deaths.
- **Owner model:** hunting 75% of his play time; the 9-character rotation.
- **RvR:** meeting, spotting and ambush rates; Lanchester-style fight odds; guard factors; the frontier
  layout (5 zones with 7 keeps and 2 relic keeps per realm, not checked against the world database);
  the role split.
- **Sessions:** 2–5 hours on, 1–4 hours off; how often live bots actually reach the Exchange.
- **Scale:** whether the owner's PC can run about 3,000 bots online at once (unknown; the project's
  own docs warn about lag above 1,000 per realm).

## 3. Corrections made during the day

Each of these changed a result that had been reported to the owner:

1. **Non-live rules.** The first model used the trainer, craft and 3.5% downtime rules from
   `AutonomousBotDecisionEngine.Choose`, which no live code calls. Replaced with the live between-task
   rules; the 20-hour study was rerun (directions held).
2. **Zone count:** 25 Midgard zones and dungeons, not 24.
3. **Personality types:** the tested design had 5 types (Crafter replaced Casual), not a sixth type.
4. **Crafting quality.** The first trade model invented a quality formula. Replaced with the server's
   rule; earlier "perfect set" results are withdrawn.
5. **Practice-craft sellback.** It was assumed to be 50%; the server has a 95% setting. Runs at 90%
   followed.
6. **Crafter "cheap practice craft" loop.** It drained crafters a little at a time. Fixed.
7. **Unneeded salvage purchases** by crafters. Fixed.
8. **Banking "half the profit"** actually banked half of revenue (which includes materials). Fixed
   to net profit.
9. **Luxury threshold** used the crafter character's level, taxing crafters early. Fixed to the bot
   player's highest-level character (after the crafter-alt runs).
10. **RvR model (found in this audit):** it let low-level bots siege, sent defenders at 0.8× instead
    of 0.5×, gated relic raids behind an invented rule, used a 5% relic bonus instead of 10%, and had
    a mistyped rank table. Corrected and rerun.
    - **Withdrawn:** "zerging pays 2.5× more than roaming" and "relics barely move".
    - **Corrected:** sieges and roaming pay about the same, relics move about once per 14 hours, and
      the relic bonus can snowball.
    - **Also corrected:** the earlier recommendation of a small-group RP bonus. It is no longer
      recommended.

## 4. Reproducibility

Each results file was produced by the simulator code committed alongside it. Several later commits
changed the code (crafter fixes, the luxury threshold, the RvR audit fixes), so older persona-model
result files may not reproduce exactly with today's code. The two RvR result files were regenerated in
this audit and match today's code. From now on, each results file should record the commit that made
it.

## 5. What can realistically be built

- **Codeable on the server:**
  - XP by level range;
  - population (sessions, staggered launch, no-lifers, bot players with rosters: new tables, since
    bots are not player accounts);
  - personalities;
  - economy rules (Exchange tax, repair fees, commissions, discounts, premiums, luxury spending that
    buys real things);
  - RvR tuning (relic bonus, warnings through the existing announcements, the existing keep guard
    patrols);
  - named and epic drops built on the existing random-item generator (`AtlasROGManager`) and on
    existing models and effects.
- **Codeable but hard and slow:**
  - bots crafting through the real crafting system (it is written for players; an unused `Craft`
    activity in `AutonomousBotDecisionEngine` is the starting point);
  - frontier PvE camps for bots (needs the world database);
  - human-looking bot tactics (needs many playtest rounds);
  - 3,000 bots online (performance unknown);
  - raid bosses.
- **Not realistic here:**
  - new 3D zones or dungeons (reuse existing ones instead);
  - wholly new models, skeletons, animations or sound files. Recolored and reshaped private copies
    of existing art are possible (`tools/pet-art`), as are extra props from existing models in a
    zone's `fixtures.csv`;
  - client features beyond small, hash-guarded patches;
  - seeing or playing the game, which needs the owner as playtester;
  - building .NET in the cloud workspace (GitHub Actions and the owner's PC do that).

## 6. Recommendations before writing game code

1. **Set up the owner's PC:**
   - the Claude desktop app, Git, the .NET 10 SDK and Python;
   - a separate code folder;
   - a test copy of the playable install.
2. **Load-test first:** run 1,000 bots per realm on the test copy, with the owner's permission, and
   measure lag before building features that depend on that scale.
3. **Calibrate:** use one play session's logs (`AUTONOMOUS_XP_PROGRESS` and others) and the item
   database to replace the biggest assumptions (XP pace, income, prices).
4. **Get an independent review:** a reviewer that has not seen this work checks the simulators against
   the server code once more. This audit was done by the same author as the models.
5. **Consolidate branches:** accept `living-world/trade-sim` as the planning branch, delete the stale
   ones, and start feature work on new branches from `main`.
6. **The first real code task:** XP by level range (a small, testable server setting), followed by
   the population pieces of milestone 1.

## 7. Redundancy check (added later the same day)

The plan was checked against this fork's code and the original's latest `main` (`1cabc77`, with
0.36 in progress) for work that already exists.

**Dropped because it already exists:**
- **Porting HearthDAoC's quests and spawns.** 0.35 has 448 classic quests with map markers and the
  Quest Guide, the class epics and period monster populations; 0.36 adds 940 quest reward items.
- **A new chat engine and blocklist.** The base has assembled chat, a conversation coordinator, a
  question classifier and world knowledge; all text is pre-written.

**Changed from "build" to "extend":**
- named and epic drops: the random-item generator;
- PvE reasons: Bounty Masters;
- frontier PvE: Atlas frontier daily quests and `rvr_zones_xp_rate` (whether they are in the world
  is not checked);
- bot crafting: the unused `Craft` activity;
- luxury spending: housing;
- RvR warnings: the announcements;
- guard patrols: the keep patrols;
- staggered launch: the population ramp.

**Also corrected:** the M1 specification's "Decisions inside hunt" table still listed the non-live
`Choose` chances (correction 1 above had missed it). It now lists the live rules.

**Process:** the original ships about weekly, so its `main` is merged and its changelog read before
each milestone.

**Not compared:** HearthDAoC item by item; the forks that could not be identified.

The roadmap's "What the base already has" section holds the full table.

## 8. Data check (added later the same day)

The release's world database was read in the cloud workspace and compared with the simulators. The
full results are in [LIVING-WORLD-DATA-CHECK-2026-10-11.md](LIVING-WORLD-DATA-CHECK-2026-10-11.md).

**Corrections to the models:**
- **Random magic item drops are live on every monster.** They run about 24% per solo yellow kill, and
  the persona models left them out, so crafting income is overstated.
- **The frontier is 4 zones per realm, not 5.** The keep count of 7 plus 2 relic castles was right.
- **Practice-craft sellback is 50%** in the release settings. The 95% rule needs
  `crafting_adjust_product_price` turned on.

**Confirmed:** the cost of crafting materials scales with monster coin in the shape the economy model
assumed.

**What changes for the reported results:**
- The persona models' crafting-income results were overstated without random drops.
- The RvR model needed a rerun with 4 zones per realm.

Both reruns were done the same day; the roadmap's "Rerun with the data-check corrections" section has the
results. The owner decided to keep the current random-drop rate.
