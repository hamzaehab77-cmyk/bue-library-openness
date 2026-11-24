"""Paper Figure 3 (v24, 18 Nov 2026, supervisor comment 1): first-floor plan with the seat codes AND each area shaded,
so the borders of the five areas are clear. The areas are the same territories as on the behavioural-mapping sheets v3
(online_task/make_mapping_sheets_v3.py): each area = its seats + the corridors and shelves around them.
usage: python figure3_zones.py <out.png>"""
import os, sys
import numpy as np
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Polygon as MplPoly

HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import standard_layout as L

out = sys.argv[1]
plt.rcParams.update({'font.family': 'Arial', 'font.size': 9})
X0, X1, Y0, Y1 = 786.5, 837.5, -1340.5, -1312.5
XW, XE, YAE, YBC = 808.6, 817.2, -1326.0, -1322.6
TERR = {'A': (X0, XW, YAE, Y1), 'E': (X0, XW, Y0, YAE), 'D': (XW, XE, -1334.0, Y1),
        'B': (XE, X1, YBC, Y1), 'C': (XE, X1, -1334.0, YBC)}
COL = {'A': '#2a78d6', 'B': '#eb6834', 'C': '#1baf7a', 'D': '#eda100', 'E': '#e87ba4'}    # reference categorical palette
LBL = {'A': (802.2, -1322.6), 'B': (826.2, -1314.2), 'C': (821.6, -1329.6), 'D': (814.3, -1321.0), 'E': (802.2, -1335.4)}
INK, INK2 = '#0b0b0b', '#52514e'

seats = L.build()
bg = L.background(os.path.join(HERE, 'Library_floor_plans.dxf'), (X0 - 2, X1 + 2, Y0 - 2, Y1 + 2))
n_by = seats.groupby('zone').size()

fig = plt.figure(figsize=(12, 7.2), facecolor='white')
ax = fig.add_axes([0.01, 0.06, 0.98, 0.93])
for z, (a, b, c, d) in TERR.items():
    ax.add_patch(Rectangle((a, c), b - a, d - c, fc=COL[z], ec='none', alpha=0.13, zorder=0))
for arr in bg:
    ax.plot(arr[:, 0], arr[:, 1], color='#8c8c8c', lw=0.4, zorder=1)
for z, (a, b, c, d) in TERR.items():
    ax.add_patch(Rectangle((a, c), b - a, d - c, fill=False, ec=COL[z], lw=2.0, zorder=6))
for tz, cx, cy, axis in L.TABLES:
    ax.add_patch(MplPoly(np.array(L.table_poly(cx, cy, axis)), closed=True, fc='white', ec=INK, lw=0.7, zorder=3))
for r in seats.itertuples():
    f = np.radians(r.facing_deg); ux, uy = np.cos(f), np.sin(f)
    ax.add_patch(Rectangle((r.x_m - ux * 0.05 - 0.27, r.y_m - uy * 0.05 - 0.27), 0.54, 0.54, fc='white', ec=INK2, lw=0.5, zorder=4))
    ax.text(r.x_m - ux * 0.05, r.y_m - uy * 0.05, r.code.split('-')[1], fontsize=4.6, color='#c00000', weight='bold',
            ha='center', va='center', zorder=5)
for z, (lx, ly) in LBL.items():
    ax.text(lx, ly, z, fontsize=22, weight='bold', color=COL[z], ha='center', va='center', zorder=7,
            bbox=dict(fc='white', ec='none', alpha=0.75, pad=1))
ax.set_xlim(X0 - 0.4, X1 + 0.4); ax.set_ylim(Y0 - 0.4, Y1 + 0.4); ax.set_aspect('equal'); ax.axis('off')
# legend + scale bar
lg = fig.add_axes([0.02, 0.0, 0.96, 0.055]); lg.axis('off'); lg.set_xlim(0, 100); lg.set_ylim(0, 10)
x = 0
for z in 'ABCDE':
    lg.add_patch(Rectangle((x, 3), 2.2, 4.5, fc=COL[z], alpha=0.35, ec=COL[z], lw=1.5))
    lg.text(x + 3, 5.2, f'Area {z} ({n_by[z]} seats)', va='center', fontsize=9, color=INK)
    x += 14
lg.text(x + 1, 5.2, 'Red numbers = seat numbers (code = area + number, e.g. A-12)', va='center', fontsize=8.5, color=INK2)
sb = fig.add_axes([0.85, 0.075, 0.12, 0.02]); sb.axis('off'); sb.set_xlim(0, 5.6); sb.set_ylim(0, 1)
sb.add_patch(Rectangle((0, 0.45), 5, 0.25, fc=INK)); sb.text(0, 0.0, '0', fontsize=7.5, ha='center'); sb.text(5, 0.0, '5 m', fontsize=7.5, ha='center')
fig.savefig(out, dpi=220)
print('written', out)
