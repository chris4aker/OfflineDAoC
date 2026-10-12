# Period reference: Kirstena's Atlas (2002)

Kirstena's Atlas is a set of hand-drawn DAoC maps from 2001–2003, with a monster table on each
map. It is mirrored at <https://www.moose.at/kirstena/>. This note records what the site holds and
how its monster tables compare with the 0.35 world database.

- **Data:** [tools/period-reference/kirstena_2002_mobs.tsv](../tools/period-reference/kirstena_2002_mobs.tsv)
  (1,685 monster entries from 42 maps; the keep and relic pages have no monster table).
- **Check:** `python tools/period-reference/compare_kirstena.py <world.db> [out.json]` (read-only).

The maps are © Kirstena. Only facts are kept here: names, levels and types, which the maps credit
to Illia's Beastiary and Prima's *Atlas of Dark Age of Camelot*. The images and PDFs are not copied.

## 1. What the site holds (coverage)

| Part | Count | Read |
|---|---|---|
| Index page (map list, credits, period links) | 1 | yes |
| Albion zone maps and frontier overview | 16 + 2 | yes, all |
| Albion dungeons (Catacombs, Keltoi Fogou, Stonehenge Barrows, Tepok's Mine, Tomb of Mithra) | 5 | yes, all |
| Darkness Falls | 1 | yes |
| Hibernia zone maps and frontier overview | 11 + 1 | yes, all |
| Hibernia dungeon (Muire Tomb) | 1 | yes |
| Midgard zone maps and frontier overview | 10 + 1 | yes, all |
| "Albion all" combined PDF | 1 | yes: the same Albion maps, with no extra pages |

**Not read, and why:**
- **The GIFs:** each is an image of the same map as its PDF.
- **Probes for unlinked files:** a directory listing and Hibernia/Midgard combined PDFs. All were
  refused or don't exist.
- **The rest of moose.at:** an unrelated Austrian search engine, now shut down.
- **External links** (the 3D DF model; Camelot Vault, Allakhazam, Camelot Herald): other sites
  from 2002–2003, mostly reachable only through the Wayback Machine, which is blocked here.

Map dates run from 5-2-2002 to 9-7-2002; the author stopped updating on 1-29-2003.

**Map pages without a monster table:** the Albion, Hibernia and Midgard frontier overviews only
show keeps and relics, and Tepok's Mine lists names without levels.

**Method:** text was pulled from the PDFs by an automated reader. Single entries can carry
transcription errors; the comparison below shows where.

## 2. Match with the 0.35 world database (verified by query)

| Result | Entries | Share |
|---|---|---|
| Same name, same zone, level within 1 | 1,098 | 65% |
| Same name, same zone, different level | 179 | 11% |
| Name exists, but in other zones | 214 | 13% |
| Not spawned | 194 | 12% |

The 0.35 and 0.35b databases give identical results.

**The "not spawned" entries break down as:**
- **46 spelling variants:** for example Chaosian, Fomorian, Giant Lusus and Wood Ogre Berserker.
  These exist, so the true match rate is higher.
- **69 removed by the release's own cleanup.** See section 3.
- **31 that exist only as NPC templates,** with no spawn.
- **48 that aren't in the database at all.** Some are probably misreadings.

**About "elsewhere":** these are mostly frontier names. In the database they sit in Jamtland,
Breifine or Mount Collory rather than the zone the 2002 map shows.

## 3. Finding: period monsters removed by the 1.65 cleanup

The release's table `offline_classic165_removed_mobs` holds 58,528 spawns that were taken out of
the world. For 58,521 of them the stated reason is "Post-legacy generic neutral spawn excluded
from the server 1.65 authority".

Kirstena's 2002 maps list 59 of those monster names in the same zones. In those zones that is
about 1,160 removed spawns (1,290 across the whole world):

**Home realms (about 380 spawns):**

| Zone | Removed monsters (spawns in that zone) |
|---|---|
| Bog of Cullen | Siabra Guardian, Siabra Archmagi (167) |
| Lyonesse | Lesser, Medial and Greater Telamon, Bean-Nighe, Danaoin Commander, Woodeworm (97) |
| Shannon Estuary | Lesser Zephyr, Weldo (69) |
| Stonehenge Barrows | Decayed Barbarian Chieftain, Echo of Life, Grave Goblin Crueler (9) |
| Cursed Forest, Skona Ravine | Grand Pooka (6); Werewolf Commander (6) |
| Cornwall | the four Yarley brothers, Lesser Telamon, Lone Wolf (5) |
| Salisbury Plains | Slave Master, Slave Master Bodyguard, Grunk (5) |
| Dartmoor | Clud, Clywd, Grimbuld, Granite Giant Earthmagi (4) |
| East Svealand | Jabrylla, Mourn, Plague Rat Scout (4) |
| Others, 1–2 each | Shale, Welsh Hobgoblin Chief, Hill Chief, Murgar, Straw, Hellhag, Scorpionida Regina, Blodfelag Livvakt |

**Old frontier zones (about 780 spawns):**
- **Hadrian's Wall:** Pictish Warrior, Pictish Druid, Priestess, Albion Waylayer (240).
- **Snowdonia:** Shadowhunter, Shadowhunter She-Wolf, Sprawling Arachnid, Howling Knifeman (178).
- **Midgard frontier** (Yggdra Forest, Odin's Gate, Uppland): Fenrir Guard, Bone-eater Clanmother,
  Ghastly Albion and Ghostly Hibernian Invaders (236).
- **Cruachan Gorge and Mount Collory:** Faeghoul, Bocaidhe, Curmudgeon Ratoner (123).
- **Pennine Mountains:** Barguest, Mountain Grim, Scorned Bwca (50).

**What is verified and what isn't:**
- **Verified:** these monsters existed in these zones in mid-2002, and the cleanup removed them as
  "post-legacy".
- **Not verified:** whether each one was still there in 1.65 (late 2003). Mythic changed zones in
  between (see section 4), so a 2002 map alone doesn't prove the cleanup wrong.
- **Earlier restorations:** the release already restored 2,273 spawns in two migrations
  (`classic165-conservative-frontier-albion-spawns-v1` and `classic165-period-map-frontier-albion-spawns-v2`).
  None of the names above was restored (checked by query).

**Use:** this list is the evidence for a possible third restoration pass, zone by zone. It needs
a second source from 2003, and the owner's decision.

## 4. Finding: zones whose levels changed after 2002

In some zones the database levels are well above Kirstena's. Median shifts, for zones with at
least 5 differences:

| Zone | Differ | Median shift | Map date |
|---|---|---|---|
| Myrkwood Forest | 26 of 52 | +13 | 5-18-2002 |
| Lough Gur | 15 of 28 | +12 | 8-17-2002 |
| Shannon Estuary | 6 of 21 | +12 | 5-16-2002 |
| Campacorentin Forest | 5 of 51 | +12 | 8-20-2002 |
| Bog of Cullen | 9 of 24 | +10 | 8-17-2002 |
| Silvermine Mountains | 9 of 27 | +10 | 5-2-2002 |
| Gotar | 18 of 47 | +10 | 5-17-2002 |
| Skona Ravine | 14 of 38 | +6 | 7-14-2002 |
| East Svealand | 9 of 32 | +5 | 5-17-2002 |
| Lough Derg, Vale of Mularn | 6 of 49, 7 of 36 | −6, −4 | 6-2002, 5-2002 |

**Inference:** the pattern looks like a later live revision that raised several Midgard and
Hibernia zones, rather than errors on either side. Which patch did it isn't verified.

**Rule for our work:** bot lines and camp choices follow the **database** levels, not the 2002
maps.

## 5. Dungeon level ranges (Kirstena 2002 vs database)

| Dungeon | Kirstena | Database (non-realm spawns) |
|---|---|---|
| Tomb of Mithra | 7–17 | 8–16 |
| Muire Tomb | 12–20 | 10–24 |
| Nisse's Lair | 8–21 | up to 29 |
| Spraggon Den | 15–24 | 17–35 |
| Tepok's Mine | 16–21 ("16–40ish") | 15–43 |
| Cursed Tomb | 18–28 | 19–27 |
| Keltoi Fogou | 19–28 | 20–28 |
| Koalinth Tribal Caverns | 20–30 | 18–31 |
| Vendo Caverns | 20–35 | 16–36 |
| Catacombs of Cardova | 24–42 | 29–40 |
| Varulvhamn | 25–38 | up to 46 |
| Treibh Caillte | 27–36 | 28–51 |
| Coruscating Mine | 30–40 | 35–56 |
| Spindelhalla | 33–45 | up to 53 |
| Stonehenge Barrows | 36–50 | 28–54 |
| Darkness Falls | 20–50 (25–50 on some maps) | — |

**The bot-voices corpus agrees with both columns:**
- the 15–25 Spraggon Den/Muire Tomb debate;
- the 38–50 Spindelhalla/Varulvhamn and Barrows debates;
- Mithra as a first dungeon;
- the 51 draugr spawns in Cursed Tomb.

No line needs a change.

## 6. Relics (from the frontier maps)

| Realm | Strength relic | Power relic |
|---|---|---|
| Albion | Scabbard, Castle Excalibur | Staff, Castle Myrddin |
| Hibernia | Spear, Dun Lamfhota | Cauldron, Dun Dagda |
| Midgard | Hammer, Mjollner Faste | Horn, Grallarhorn Faste |

The Darkness Falls map notes that the entrance opens only for the realm holding most of the
frontier keeps.

## 7. Period details worth turning into bot lines

These are paraphrased from the maps' notes. Check each against the database first: the Yarleys,
for instance, are removed today.

- **Dartmoor:** giant herdsmen are social and call their ponies and each other for help; the
  ponies are otherwise neutral; spawns repop fast.
- **Catacombs of Cardova:** a trapped "fireball run" hall where fireballs hit for anything from a
  little to a lot; pulls of 3–4 are common, and aggro seems to favor wizards.
- **Tepok's Mine:** the Whisperer, about level 40, comes with lions; juggernauts can be single
  pulls.
- **Llyn Barfog:** the merchants dislike you hunting their kin but appreciate dead hobgoblins.
  The epic monsters take one to three balanced groups.
- **Myrkwood Forest:** Svartalf Watchers spawn behind trees near the road.
- **Camelot Hills:** bandits on the road north of the bridge.
- **Salisbury Plains:** a guard at the southwest guard tower is also a merchant.
- **Snowdonia:** Fell Creature teeth are turned in at Snowdonia Fortress.

## 8. Next steps (none started)

1. **Removed spawns:** decide whether to look for a 2003 source for section 3, zone by zone,
   starting with Bog of Cullen, Lyonesse and Shannon Estuary.
2. **Bot lines:** turn section 7 into corpus lines, after a database check of each fact.
3. **Owner's saved threads:** use the same comparison script on any forum threads or atlas pages
   the owner saves.
