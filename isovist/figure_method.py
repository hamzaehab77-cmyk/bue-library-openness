"""Method illustration for the paper: how isovist area and control are calculated for one seat.
usage: python figure_method.py plan.dxf seats.csv out.png [seat code]"""
import sys, math
import numpy as np, pandas as pd
import ezdxf
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon as MplPoly, FancyArrowPatch, Wedge, Rectangle
from matplotlib.lines import Line2D
from isovist import load_plan, isovist, wedge, in_window, polylines_of

dxf, seats_csv, out = sys.argv[1:4]
code = sys.argv[4] if len(sys.argv) > 4 else 'A-32'
plt.rcParams.update({'font.family': 'Arial', 'font.size': 8})

plan = load_plan(dxf, 'tall')
fp = plan['footprint']
doc = ezdxf.readfile(dxf)
low, glass = [], []
import standard_layout as SL                        # the standard tables replace the old study furniture
from ezdxf import bbox as _bbox
_cache = _bbox.Cache()
for e in doc.modelspace():
    if not in_window(e): continue
    try:
        _b = _bbox.extents([e], cache=_cache)
        if _b.has_data and SL.is_old_furniture(e, _b): continue
    except Exception:
        pass
    if e.dxf.layer == 'FUR':
        low += polylines_of([e])
    elif e.dxf.layer == 'p':          # p = glass partitions (lines) + room furniture/round tables
        (glass if e.dxftype() in ('LINE', 'LWPOLYLINE') else low).extend(polylines_of([e]))
for _t in SL.TABLES:
    low.append(SL.table_poly(*_t[1:]))
for _r in SL.build().itertuples():
    _sq, _back = SL.chair_poly(_r.x_m, _r.y_m, _r.facing_deg); low += [_sq, _back]
shelf_set = {tuple(map(tuple, p)) for p in plan['shelves']}
from shapely.geometry import Polygon as SPoly, LineString as SLine
from shapely.ops import unary_union as _uu
_shelf_area = _uu([SPoly(p).buffer(0.05) for p in plan['shelves']])
glass = [p for p in glass if not _shelf_area.contains(SLine(p))]   # centre lines drawn inside shelves

s = pd.read_csv(seats_csv).set_index('code').loc[code]
x, y, f = s.x_m, s.y_m, s.facing_deg
iso, ang, dist = isovist(x, y, plan['segments'], 3600)
iso = iso.intersection(fp)
front = iso.intersection(wedge(x, y, f))
A360, A170 = iso.area, front.area

C_WALL, C_SHELF, C_LOW, C_GLASS = '#1a1a1a', '#6b6b6b', '#c4c4c4', '#7fb3d5'
C_ISO, C_FRONT, C_RAY = '#9ecae1', '#f4a259', '#d62728'
X0, X1, Y0, Y1 = 783.5, 836, -1340, -1301.5


def base(ax, low_on=True):
    if low_on:
        for p in low:
            if tuple(p) in shelf_set: continue
            xs, ys = zip(*p); ax.plot(xs, ys, color=C_LOW if low_on != 'dark' else '#8a8a8a', lw=0.35, zorder=4)
        for p in glass:
            xs, ys = zip(*p); ax.plot(xs, ys, color=C_GLASS, lw=0.6, zorder=4)
    for p in plan['opaque']:
        xs, ys = zip(*p); ax.plot(xs, ys, color=C_WALL, lw=0.45, zorder=3)
    for a, b, c, d in plan['doors']:
        ax.plot([a, c], [b, d], color=C_WALL, lw=0.45, zorder=3)
    for p in plan['shelves']:
        ax.add_patch(MplPoly(p, closed=True, fc=C_SHELF, ec=C_SHELF, lw=0.3, zorder=3))
    ax.set_xlim(X0, X1); ax.set_ylim(Y0, Y1); ax.set_aspect('equal'); ax.axis('off')


def fill(ax, g, **kw):
    for part in getattr(g, 'geoms', [g]):
        if part.geom_type == 'Polygon' and not part.is_empty:
            ax.add_patch(MplPoly(np.array(part.exterior.coords), closed=True, **kw))


def seat(ax, arrow=True, size=4.5):
    ax.plot(x, y, 'o', ms=size, mfc='white', mec='k', mew=1.0, zorder=8)
    if arrow:
        r = math.radians(f)
        ax.add_patch(FancyArrowPatch((x, y), (x + 2.6 * math.cos(r), y + 2.6 * math.sin(r)),
                                     arrowstyle='-|>', mutation_scale=8, lw=1.1, color='k', zorder=9))


def scalebar(ax):
    ax.add_patch(Rectangle((784.3, -1337.0), 4, 0.35, fc='k', zorder=5))
    ax.add_patch(Rectangle((788.3, -1337.0), 4, 0.35, fc='white', ec='k', lw=0.6, zorder=5))
    for v, t in ((784.3, '0'), (788.3, '4'), (792.3, '8 m')):
        ax.text(v, -1337.4, t, ha='center', va='top', fontsize=6.5)


def note(ax, text):
    ax.text(0.5, -0.03, text, transform=ax.transAxes, ha='center', va='top', fontsize=8)


fig, axs = plt.subplots(2, 2, figsize=(6.3, 6.3))
(a, b), (c, d) = axs

# (a) sight lines
base(a)
for k in range(0, 3600, 50):                      # every 5 degrees
    t = ang[k]; r = dist[k]
    a.plot([x, x + r * math.cos(t)], [y, y + r * math.sin(t)], color=C_RAY, lw=0.4, alpha=0.85, zorder=4)
    a.plot(x + r * math.cos(t), y + r * math.sin(t), 'o', ms=1.3, color=C_RAY, zorder=5)
seat(a, arrow=False)
a.set_title('(a) Sight lines traced from the seat', fontsize=8.5, loc='left')
note(a, 'Each line stops at the first object that blocks the view')
scalebar(a)

# (b) isovist area
base(b)
fill(b, iso, fc=C_ISO, ec='#3d7fb5', lw=0.6, alpha=0.85, zorder=2)
seat(b, arrow=False)
b.set_title('(b) Isovist area', fontsize=8.5, loc='left')
note(b, f'Area reached by the sight lines: A$_{{360}}$ = {A360:.0f} m²')

# (c) control
from shapely.geometry import LineString
base(c)
fill(c, iso, fc=C_ISO, ec='none', alpha=0.85, zorder=2)
fill(c, front, fc=C_FRONT, ec='#c0631f', lw=0.6, alpha=0.9, zorder=2)
for side in (-85, 85):
    r = math.radians(f + side)
    ln = LineString([(x, y), (x + 60 * math.cos(r), y + 60 * math.sin(r))]).intersection(fp)
    for part in getattr(ln, 'geoms', [ln]):
        c.plot(*part.xy, '--', color='k', lw=0.6, zorder=6)
seat(c)
c.set_title('(c) Control', fontsize=8.5, loc='left')
note(c, f'Control = A$_{{170}}$ ÷ A$_{{360}}$ = {A170:.0f} ÷ {A360:.0f} = {A170 / A360:.2f}')

# (d) close-up of the seat: facing direction and the 170 degree field
base(d, low_on='dark')
fill(d, iso, fc=C_ISO, ec='none', alpha=0.6, zorder=2)
fill(d, front, fc=C_FRONT, ec='none', alpha=0.6, zorder=2)
d.add_patch(Wedge((x, y), 1.6, f - 85, f + 85, fc='none', ec='k', lw=0.7, ls='--', zorder=7))
seat(d, size=6)
r = math.radians(f)
d.text(x + 1.1 * math.cos(r), y + 1.1 * math.sin(r) + 0.12, 'facing\ndirection', ha='center', va='bottom', fontsize=6.5, zorder=10,
       bbox=dict(fc='white', ec='none', pad=0.5, alpha=0.8))
for sgn in (1, -1):
    d.text(x + 1.95 * math.cos(r + sgn * math.radians(55)), y + 1.95 * math.sin(r + sgn * math.radians(55)), '85°',
           fontsize=6.5, ha='center', va='center', zorder=10, bbox=dict(fc='white', ec='none', pad=0.5, alpha=0.8))
d.set_xlim(x - 4.2, x + 3.2); d.set_ylim(y - 2.9, y + 2.9)
d.set_title('(d) Close-up of the seat', fontsize=8.5, loc='left')
note(d, 'The 170° field: 85° either side of the facing direction')
d.axis('on'); d.set_xticks([]); d.set_yticks([])
for sp in d.spines.values(): sp.set_linewidth(0.6)

handles = [Line2D([], [], color=C_WALL, lw=1.2, label='Walls, columns, facade, doors (block view)'),
           MplPoly([[0, 0]], fc=C_SHELF, label='Bookshelves taller than 1.2 m (block view)'),
           Line2D([], [], color=C_LOW, lw=1.2, label='Tables, chairs, desks below 1.2 m (ignored)'),
           Line2D([], [], color=C_GLASS, lw=1.2, label='Clear glazing (transparent)'),
           Line2D([], [], marker='o', ls='', mfc='white', mec='k', label=f'Seat {code} and facing direction'),
           MplPoly([[0, 0]], fc=C_ISO, label='Visible area (A$_{360}$)'),
           MplPoly([[0, 0]], fc=C_FRONT, label='Visible area in front (A$_{170}$)')]
fig.legend(handles=handles, loc='lower center', ncol=2, fontsize=7, frameon=False, bbox_to_anchor=(0.5, -0.005))
fig.tight_layout(rect=(0, 0.12, 1, 1), h_pad=2.2, w_pad=0.6)
fig.savefig(out, dpi=400)
print(f'{code}: A360 {A360:.1f}  A170 {A170:.1f}  control {A170 / A360:.3f}')
