"""Check the script against depthmapX (validation pilot).

Both tools get exactly the same obstruction lines (exported here to a plain DXF), so the
check tests the isovist calculation itself, not the choice of layers.
depthmapXcli makes, for every seat, a full isovist (360°) and a partial isovist
(170° centred on the facing direction); its areas are compared with the script's.

usage: python validate_depthmapx.py plan.dxf seats.csv outdir depthmapXcli.exe [--shelves tall|low]
"""
import argparse, os, subprocess
import numpy as np, pandas as pd
import ezdxf
from shapely.geometry import Polygon, Point
from shapely.ops import unary_union
from isovist import load_plan

ap = argparse.ArgumentParser()
ap.add_argument('dxf'); ap.add_argument('seats'); ap.add_argument('outdir'); ap.add_argument('cli')
ap.add_argument('--shelves', choices=['tall', 'low'], default='tall')
a = ap.parse_args()
tag = f'shelves_{a.shelves}'
work = os.path.join(a.outdir, f'depthmapx_{tag}'); os.makedirs(work, exist_ok=True)

# 1. the obstruction lines the script uses, as a plain DXF
plan = load_plan(a.dxf, a.shelves)
doc = ezdxf.new('R2010'); msp = doc.modelspace()
for x1, y1, x2, y2 in plan['segments']:
    msp.add_line((x1, y1), (x2, y2), dxfattribs={'layer': 'OBSTRUCTION'})
lines_dxf = os.path.join(work, 'obstruction_lines.dxf'); doc.saveas(lines_dxf)

seats = pd.read_csv(a.seats)
res = pd.read_csv(os.path.join(a.outdir, f'isovist_results_{tag}.csv'))


def run(args):
    r = subprocess.run([a.cli] + args, capture_output=True, text=True)
    if r.returncode != 0:
        raise SystemExit(f'depthmapXcli failed: {" ".join(args)}\n{r.stdout}\n{r.stderr}')


def read_mif(path):
    """REGION polygons from a MapInfo MIF file, in file order."""
    lines = open(path).read().split('\n'); polys = []; i = 0
    while i < len(lines):
        t = lines[i].strip().split()
        if t and t[0].upper() == 'REGION':
            rings = []; i += 1
            for _ in range(int(t[1])):
                n = int(lines[i].strip()); i += 1
                rings.append([tuple(map(float, lines[i + k].split()[:2])) for k in range(n)]); i += n
            polys.append(unary_union([Polygon(r).buffer(0) for r in rings]))
        else:
            i += 1
    return polys


graph = os.path.join(work, 'plan.graph')
run(['-m', 'IMPORT', '-f', lines_dxf, '-o', graph])

out = {}
for kind in ('full', 'partial'):
    pts = pd.DataFrame({'x': seats.x_m, 'y': seats.y_m})
    if kind == 'partial':
        pts['angle'] = seats.facing_deg; pts['viewangle'] = 170
    pf = os.path.join(work, f'points_{kind}.csv'); pts.to_csv(pf, index=False)
    g = os.path.join(work, f'isovists_{kind}.graph')
    run(['-m', 'ISOVIST', '-f', graph, '-o', g, '-if', pf])
    # depthmapXcli cannot export an isovist map directly (it crashes), so the isovist
    # polygons are first converted to a convex map and exported as MapInfo (MIF)
    gc = os.path.join(work, f'isovists_{kind}_convex.graph')
    run(['-m', 'MAPCONVERT', '-f', g, '-o', gc, '-co', 'convex', '-con', f'isovists_{kind}'])
    mif = os.path.join(work, f'isovists_{kind}.mif')
    run(['-m', 'EXPORT', '-f', gc, '-o', mif, '-em', 'shapegraph-map-mif'])
    out[kind] = read_mif(mif)


def match(polys):
    """Polygons come out in the order of the points file (= seat order); check that each
    one contains its own seat point (or has it on its edge, for partial isovists)."""
    s = {}
    for (code, x, y), p in zip(seats[['code', 'x_m', 'y_m']].itertuples(index=False), polys):
        assert p.distance(Point(x, y)) < 0.05, f'polygon order mismatch at {code}'
        s[code] = p.area
    return pd.Series(s)


cmp = res.set_index('code')[['zone', 'isovist_area_m2', 'area_170_m2', 'control']].copy()
cmp['dmx_area_m2'] = match(out['full'])
cmp['dmx_area_170_m2'] = match(out['partial'])
cmp['dmx_control'] = cmp.dmx_area_170_m2 / cmp.dmx_area_m2
cmp['diff_area_pct'] = 100 * (cmp.isovist_area_m2 - cmp.dmx_area_m2) / cmp.dmx_area_m2
cmp['diff_control'] = cmp.control - cmp.dmx_control
cmp.round(4).to_csv(os.path.join(a.outdir, f'validation_depthmapx_{tag}.csv'))

r_area = np.corrcoef(cmp.isovist_area_m2, cmp.dmx_area_m2)[0, 1]
r_ctrl = np.corrcoef(cmp.control, cmp.dmx_control)[0, 1]
print(f'seats compared: {cmp.dmx_area_m2.notna().sum()}')
print(f'isovist area: mean abs difference {cmp.diff_area_pct.abs().mean():.2f}%  max {cmp.diff_area_pct.abs().max():.2f}%  r = {r_area:.4f}')
print(f'control:      mean abs difference {cmp.diff_control.abs().mean():.4f}  max {cmp.diff_control.abs().max():.4f}  r = {r_ctrl:.4f}')
print(cmp.sort_values('diff_area_pct', key=abs, ascending=False).head(8).round(3).to_string())
