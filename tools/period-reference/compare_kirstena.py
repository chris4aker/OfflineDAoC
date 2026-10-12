"""Compare Kirstena's 2002 monster tables with a world database (read-only).

  python tools/period-reference/compare_kirstena.py <world.db> [out.json]

For each monster on each map it reports one status:
  match          same name in the same zone, levels within 1 of the map
  level_differs  same name in the same zone, other levels
  elsewhere      the name exists, but in other zones
  missing        not spawned; then classified as a spelling variant, removed by the
                 release's 1.65 cleanup (offline_classic165_removed_mobs), template only, or absent
Monsters with level 0 in Mob take their level from NPCTemplate.Level.
"""
import collections
import difflib
import json
import re
import sqlite3
import sys
from pathlib import Path

TSV = Path(__file__).with_name('kirstena_2002_mobs.tsv')
ALIAS = {'Catacombs of Carvoda': 'Catacombs of Cardova', 'North Black Mountains': 'Black Mtns. North',
         'South Black Mountains': 'Black Mtns. South', 'Silvermine Mountains': 'Silvermine Mts.'}


def main():
    db = sys.argv[1]
    out = sys.argv[2] if len(sys.argv) > 2 else None
    c = sqlite3.connect(f'file:{db}?mode=ro', uri=True)
    zones = c.execute('select ZoneID,RegionID,Name,OffsetX,OffsetY,Width,Height from Zones').fetchall()

    def inside(z, x, y):
        return z[3] * 8192 <= x < (z[3] + z[5]) * 8192 and z[4] * 8192 <= y < (z[4] + z[6]) * 8192

    def zone_of(r, x, y):
        return next((z[2] for z in zones if z[1] == r and inside(z, x, y)), f'region {r}')

    tl = {}
    for tid, lv in c.execute('select TemplateId, Level from NPCTemplate'):
        nums = [int(v) for v in re.findall(r'\d+', str(lv or ''))]
        if nums:
            tl[tid] = (min(nums), max(nums))
    spawns = collections.defaultdict(list)
    for n, r, x, y, lv, tid in c.execute('select lower(Name),Region,X,Y,Level,NPCTemplateID from Mob'):
        for level in (tl[tid] if lv == 0 and tid in tl else (lv,)):
            spawns[n].append((r, x, y, level))
    names = sorted(spawns)
    removed = {n.lower() for (n,) in c.execute('select Name from offline_classic165_removed_mobs')}
    templates = {n.lower() for (n,) in c.execute('select Name from NPCTemplate')}

    data = collections.OrderedDict()
    for line in TSV.read_text(encoding='utf-8').splitlines():
        if line.startswith('#') or line.startswith('zone\t'):
            continue
        zone, date, note, n, lo, hi, t = line.split('\t')
        data.setdefault(zone, dict(date=date, note=note, mobs=[]))['mobs'].append((n, int(lo), int(hi)))

    report, totals = {}, collections.Counter()
    for zone, d in data.items():
        zs = [z for z in zones if z[2].lower() == ALIAS.get(zone, zone).lower()]
        rows = []
        for n, lo, hi in d['mobs']:
            hits = spawns.get(n.lower(), [])
            here = {}
            for z in zs:
                lv = [h[3] for h in hits if h[0] == z[1] and inside(z, h[1], h[2])]
                if lv:
                    here[z[1]] = lv
            if here:
                lv = here[sorted(here)[0]]
                ok = min(lv) <= hi + 1 and max(lv) >= lo - 1
                row = dict(name=n, kirstena=[lo, hi], db=[min(lv), max(lv)], status='match' if ok else 'level_differs')
            elif hits:
                where = collections.Counter(zone_of(*h[:3]) for h in hits[:200])
                row = dict(name=n, kirstena=[lo, hi], status='elsewhere', where=dict(where.most_common(3)))
            else:
                close = difflib.get_close_matches(n.lower(), names, n=1, cutoff=0.85)
                why = (f'spelled "{close[0]}"' if close else 'removed by the 1.65 cleanup' if n.lower() in removed
                       else 'template only' if n.lower() in templates else 'absent')
                row = dict(name=n, kirstena=[lo, hi], status='missing', resolution=why)
            rows.append(row)
            totals[row['status']] += 1
        report[zone] = dict(date=d['date'], note=d['note'], rows=rows,
                            counts=dict(collections.Counter(r['status'] for r in rows)))
    print('total', sum(totals.values()), dict(totals))
    for zone, r in report.items():
        print(f'  {zone:24s} {r["counts"]}')
    if out:
        Path(out).write_text(json.dumps(dict(totals=totals, zones=report), indent=1), encoding='utf-8')


if __name__ == '__main__':
    main()
