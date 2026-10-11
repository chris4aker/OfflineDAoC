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
| Trainer 0.28, craft 0.16, safe-town downtime 0.035; services first | `AutonomousBotDecisionEngine.Choose` |
| Safer (green) camps after 2 deaths at a camp | same |
| Dungeon preference 100 / 300 / 400 permille (solo / group / group at 50) | same |
| Outdoor camps weighted by live spawns (sightings used as the proxy) | `SelectWithinEnvironment` |

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

## Results recorded so far (2026-10-11, 5 seeds)

See the "Simulation findings" section of the roadmap.
