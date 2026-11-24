"""Merged behavioural map: all scans of all mapping days in one figure (for the paper; the per-day maps go in the appendix).
(a) how often each seat was occupied = occupied scans / scans with the chair present;
(b) of those occupied scans, the share in which the occupant was studying (S).
Reads results/mapping_per_seat.csv (written by analysis/run_analysis.py) and data/*_extras.csv.
usage: python behaviour_map_merged.py <out.png>"""
import os, sys, glob
import numpy as np, pandas as pd
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, FancyBboxPatch, Polygon as MplPoly
from matplotlib.colors import LinearSegmentedColormap, Normalize

out = sys.argv[1]
HERE = os.path.dirname(os.path.abspath(__file__)); W = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(W, 'isovist'))
import standard_layout as L

plt.rcParams.update({'font.family': 'Arial', 'font.size': 9})
INK, INK2, GRID, SURF = '#0b0b0b', '#52514e', '#c9c8c3', '#fcfcfb'
CMAP = LinearSegmentedColormap.from_list('blue', ['#bcd5f5', '#86b6ef', '#3987e5', '#1c5cab', '#0d366b'])
LBL = {'A': (802.23, -1315.4), 'B': (826.2, -1314.6), 'C': (821.23, -1328.3), 'D': (814.3, -1328.4), 'E': (802.23, -1335.0)}
BOX = 0.62
WIN = (794.6, 836.4, -1339.4, -1313.4)

ps = pd.read_csv(os.path.join(W, 'results', 'mapping_per_seat.csv')).set_index('seat')
seats = L.build().set_index('code')
bg = L.background(os.path.join(W, 'isovist', 'Library_floor_plans.dxf'), WIN)
ex = [pd.read_csv(f, keep_default_na=False) for f in glob.glob(os.path.join(HERE, '*_extras.csv'))]
ex = pd.concat(ex, ignore_index=True) if ex else pd.DataFrame(columns=['table_first_seat', 'count', 'activity'])
ex['count'] = pd.to_numeric(ex['count'], errors='coerce').fillna(0)
people_extra = ex[ex.activity.astype(str).str.strip().isin(list('STPOLU'))].groupby('table_first_seat')['count'].sum()
n_scans = int(ps.scans.max())
norm = Normalize(0, 1)


def badge_pos(code):
    s = seats.loc[code]; cx, cy, ax = s.table_cx, s.table_cy, s.table_axis
    return (cx, cy + L.T_LONG / 2 + 0.5) if ax == 'y' else (cx + L.T_LONG / 2 + 0.75, cy)


fig_w = 12.0; panel_h = fig_w * (WIN[3] - WIN[2]) / (WIN[1] - WIN[0])
fig = plt.figure(figsize=(fig_w, panel_h * 2 + 1.5), facecolor=SURF); H = fig.get_figheight()
panels = [('occupancy_rate', f'(a) How often each seat was occupied (share of the {n_scans} scans in which its chair was there)', True),
          ('study_share', '(b) Of the scans in which the seat was occupied (activity readable), the share spent studying', False)]
for i, (col, title, badges) in enumerate(panels):
    bottom = 1.25 + (1 - i) * panel_h
    ax = fig.add_axes([0.01, bottom / H, 0.98, (panel_h - 0.35) / H]); ax.set_facecolor(SURF)
    for a in bg: ax.plot(a[:, 0], a[:, 1], color=GRID, lw=0.35, zorder=1)
    for t in L.TABLES:
        ax.add_patch(MplPoly(np.array(L.table_poly(*t[1:])), closed=True, fc='white', ec='#8a8984', lw=0.7, zorder=2))
    for code, s in seats.iterrows():
        f = np.radians(s.facing_deg); o = BOX / 2 - 0.25
        x, y = s.x_m - np.cos(f) * o, s.y_m - np.sin(f) * o
        r = ps.loc[code] if code in ps.index else None
        val = np.nan if r is None else r[col]
        if r is None or r.present == 0:                                   # chair missing in every scan
            ax.add_patch(Rectangle((x - BOX / 2, y - BOX / 2), BOX, BOX, fill=False, ec='#b5b4ae', lw=0.6, ls=(0, (2, 1.5)), zorder=3))
        elif pd.isna(val):                                                # (b) never occupied
            ax.add_patch(Rectangle((x - BOX / 2, y - BOX / 2), BOX, BOX, fc='white', ec='#b5b4ae', lw=0.6, zorder=3))
        else:
            ax.add_patch(Rectangle((x - BOX / 2, y - BOX / 2), BOX, BOX, fc=CMAP(norm(val)), ec='#8a8984' if val == 0 else SURF, lw=0.8, zorder=3))
    if badges:
        for code, nppl in people_extra.items():
            bx, by = badge_pos(code)
            ax.add_patch(FancyBboxPatch((bx - 0.5, by - 0.28), 1.0, 0.56, boxstyle='round,pad=0.02,rounding_size=0.18',
                                        fc='white', ec=INK2, lw=0.7, zorder=5))
            ax.text(bx, by, f'+{int(nppl)}', ha='center', va='center', fontsize=6, weight='bold', color=INK, zorder=6)
    for z, (lx, ly) in LBL.items():
        ax.text(lx, ly, z, ha='center', va='center', fontsize=16, weight='bold', color=INK2, zorder=6)
    ax.set_title(title, loc='left', fontsize=10.5, color=INK, pad=4)
    ax.set_xlim(WIN[0], WIN[1]); ax.set_ylim(WIN[2], WIN[3]); ax.set_aspect('equal'); ax.axis('off')

cax = fig.add_axes([0.03, 0.62 / H, 0.32, 0.16 / H])
cb = fig.colorbar(plt.cm.ScalarMappable(norm=norm, cmap=CMAP), cax=cax, orientation='horizontal')
cb.set_label('Share of scans (0 = never, 1 = every scan)', fontsize=8.5, color=INK2)
cb.ax.tick_params(labelsize=8, colors=INK2); cb.outline.set_visible(False)
lg = fig.add_axes([0.40, 0.25 / H, 0.58, 0.8 / H]); lg.axis('off'); lg.set_xlim(0, 100); lg.set_ylim(0, 10)
lg.add_patch(Rectangle((0, 6.0), 1.6, 2.8, fc='white', ec='#b5b4ae', lw=0.8)); lg.text(2.4, 7.4, '(b) never occupied', va='center', fontsize=9, color=INK)
lg.add_patch(Rectangle((30, 6.0), 1.6, 2.8, fill=False, ec='#b5b4ae', lw=0.8, ls=(0, (2, 1.5)))); lg.text(32.4, 7.4, 'chair missing in every scan', va='center', fontsize=9, color=INK)
lg.add_patch(FancyBboxPatch((0, 0.9), 3.2, 2.6, boxstyle='round,pad=0.05,rounding_size=0.8', fc='white', ec=INK2, lw=0.8))
lg.text(1.6, 2.2, '+n', ha='center', va='center', fontsize=7, weight='bold', color=INK)
lg.text(4.0, 2.2, '(a) people on extra chairs brought to that table, all scans together', va='center', fontsize=9, color=INK)
fig.savefig(out, dpi=220, facecolor=SURF)
print('written', out, '| seats', len(ps), '| scans', n_scans)
