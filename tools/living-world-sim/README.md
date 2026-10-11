# Living World simulator

A small design model for testing bot-population ideas before writing server code. It
answers questions like:

- Where are the bots after 20 hours?
- Do personalities spread them out?
- Does a new player find anyone to play with?

**It is not the game.** Trust the directions and comparisons between runs, not the exact
numbers. Real validation is an in-game playtest. See
[docs/LIVING-WORLD-ROADMAP.md](../../docs/LIVING-WORLD-ROADMAP.md).

## Run

```bash
python3 tools/living-world-sim/living_world_sim.py            # 5 seeds, all scenarios and modes
python3 tools/living-world-sim/living_world_sim.py "" 1        # one seed, quick check
python3 tools/living-world-sim/living_world_sim.py "" 1,2,3 out.json
```

- Needs Python 3 only.
- A full run (2 scenarios × 3 modes × 5 seeds) takes about a minute.
- Results print to the console and are saved as JSON (default `sim_results.json`).

## What it models

- **Population:** 300 Midgard autonomous gamebots for 20 game hours, in one-minute steps.
- **World:** the real camp catalog `capnbry_classic_si_goals.json`.
  - 4,003 Midgard camps across 25 zones and dungeons (Darkness Falls included).
  - The camp level is the median listed monster level.
  - Albion and Hibernia coverage in this file is thin, so only Midgard is modeled.
- **Scenarios:**
  - `fresh`: everyone starts at level 1 within the first hour and plays continuously.
  - `established`: levels are spread evenly over 1–50. Bots play 2–5 hour sessions and
    are offline 1–4 hours between them. Every 15 minutes, one offline bot of level 30 or
    higher starts over as a new level-1 character (an alt).
- **Modes:**
  - `baseline`: today's decision rules.
  - `mild`: personalities as small weight changes.
  - `strong`: personalities with **time budgets** for hunting, crafting/trading,
    socializing and exploring.

### Taken from the code

| Rule | Source |
|---|---|
| Goal mix 60/40/0 (levels 1–19), 40/40/20 (20–49), 20/40/40 (50) solo/group/RvR | `BotGoalSettings.Defaults` |
| PvE tenure 45–120 min; group matchmaking timeout 20 min | `AutonomousObjectiveAssignments` |
| Train at 90% of task boundaries when points are unspent; unload when the bag is nearly full; 15% chance of a 15–30 min town break at each solo task boundary | `AutonomousObjectiveAssignments`, `AutonomousTownDowntime` |
| Safer (green) camps after 2 deaths at a camp | `SelectSafestAvailableAfterDeath` (live) |
| Dungeon preference 100 / 300 / 400 permille (solo / group / group at 50) | `SelectPveEnvironment` (live) |
| Outdoor camps weighted by live spawns (sightings used as the proxy) | `SelectWithinEnvironment` (live) |

**Not live, so not used:** the trainer 0.28 / craft 0.16 / downtime 0.035 rules in `AutonomousBotDecisionEngine.Choose`.
Only tests call that function, and nothing runs its "Craft" result. Today's autonomous bots never craft.
An earlier version of this simulator used those numbers; it was corrected on 2026-10-11.

### Assumptions (change these to test sensitivity)

- **XP:** hours per level at yellow = `0.045 × 1.135^level`, so roughly level 25 after 20
  efficient hours. The XP multiplier by con is green 0.45, blue 0.75, yellow 1.0,
  orange 1.25, red 1.45. Groups get ×1.15.
- **Deaths per hour (solo):** green 0.01, blue 0.03, yellow 0.07, orange 0.18, red 0.45.
  Groups take ×0.4. Exploring a zone whose median level is more than 5 above yours:
  0.25 per hour.
- **Camp capacity:** 2 pulling units per camp cell; a group counts as one unit. Beyond
  that, XP efficiency falls proportionally.
- **Travel:** same zone 2 min, same region 7 min, other region 14 min; dungeons +3 min.
  A town trip is 6 min.
- **Strong-mode time budgets** (hunt / craft-trade / social / explore):

  | Type | Share of bots | Hunt | Craft/trade | Social | Explore |
  |---|---|---|---|---|---|
  | Leveler | 30% | 88% | 4% | 4% | 4% |
  | Crafter | 15% | 35% | 55% | 7% | 3% |
  | Socialite | 20% | 50% | 5% | 30% | 15% |
  | Explorer | 15% | 45% | 2% | 8% | 45% |
  | Daredevil | 20% | 85% | 2% | 8% | 5% |

  These are target shares. Services and travel make the realized shares lower.
- **RvR** is only time away from PvE. It is not modeled.

## Metrics

| Metric | Meaning |
|---|---|
| `online` | Bots logged in |
| `zones` | Zones with at least one bot hunting |
| `present_zones` | Zones with at least one bot hunting or exploring |
| `evenness` | How evenly hunters spread over zones. 0 means everyone is in one zone; 1 means a perfectly even spread. Normalized Shannon entropy. |
| `crowded` | Share of hunters at camps over capacity |
| `town` / `exploring` | Share of all bots in town / exploring |
| near a level-X player | Bots hunting within 3 levels of X: who a player at that level would see |
| per type | Average level, zones seen, deaths per hour, time shares, share of time on orange/red monsters |

## Crafting and trade study (40 hours)

A separate layer, `lw_economy.py`, models a **proposed** crafting economy: loot, materials, crafting
skill, orders, Exchange listings, gear quality and how gear changes leveling. It does not describe
today's game. See the "Trade study" section of the roadmap.

```bash
python3 tools/living-world-sim/trade_study.py 1,2,3,4,5 out.json     # 11 cases, about 5 minutes
TRADE_ONLY=C,D python3 tools/living-world-sim/trade_study.py 1,2,3 out.json   # chosen cases only
python3 tools/living-world-sim/summarize_trade.py out.json            # summary table
```

Cases: A today's rules + loot only; B personalities without crafting; C personalities + crafting;
D to I sensitivity (scarce loot, easy quality, 25% / 8% crafters, scarce materials);
J and K an established world. Saved results are in `results/`.

Assumptions in `lw_economy.py` are labelled `ASSUMPTION`: prices, drop rates, material needs,
the quality formula, and the effect of gear on XP and deaths. The gear effect on leveling is a
guess. Change them to test sensitivity.

## Full-scale model: bot players with rosters (`persona_sim.py`)

Bot players own up to 3 characters (mains kept, alts added), share gold, belong to guilds and
sometimes retire. Crafting follows the server's real quality rule. About 900 Midgard bots online.

```bash
python3 tools/living-world-sim/persona_sim.py 1,2 120 out.json      # 4 cases, about 25 minutes on 2 cores
python3 tools/living-world-sim/summarize_persona.py out.json
```

## Results recorded so far

- `results/v2_20h_results.json`: the 20-hour personality study, corrected to the live rules.
- `results/trade_40h_results.json`: the 40-hour trade study (5 seeds).
- `results/trade_60h_results.json` and `trade_60h_extra.json`: the 60-hour study with hourly data
  (`TRADE_HOURS=60 TRADE_KEEP_HOURLY=1 python3 tools/living-world-sim/trade_study.py ...`;
  summarize with `python3 tools/living-world-sim/summarize_population.py <file>`). Cases M and N
  test the alt rate (`alt_every` option: minutes between alts, 0 = none).
- `results/xp_study_120h.json`: the owner at 8× XP for 24 weeks of 5 hours, bots at 1×–6× with
  several alt rates (`python3 tools/living-world-sim/xp_study.py 1,2,3 120 out.json`, then
  `summarize_xp.py out.json`). Options: `bot_xp` (bot_xp_rate) and `player_xp` (xp_rate).

- `results/persona_120h.json`: the full-scale model, 24 weeks of the owner's play.

Summaries are in the roadmap ("Simulation findings" and "Trade study").
