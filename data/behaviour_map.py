"""Behavioural map of one mapping day: one panel per scan, every standard seat coloured by what its occupant was doing
(letter inside, so colour is never the only cue), empty and missing chairs shown, extra chairs as '+n' badges at
their table.  Colours: reference categorical palette, slots 1-5 in fixed order (S, T, P, O, B).
usage: python behaviour_map.py <date, e.g. 2026-11-17> <out.png>"""
import os, sys
import numpy as np, pandas as pd
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, FancyBboxPatch, Polygon as MplPoly

date, out = sys.argv[1:3]
HERE = os.path.dirname(os.path.abspath(__file__)); W = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(W, 'isovist'))
import standard_layout as L

plt.rcParams.update({'font.family': 'Arial', 'font.size': 9})
INK, INK2, GRID, SURF = '#0b0b0b', '#52514e', '#c9c8c3', '#fcfcfb'
COL = {'S': '#2a78d6', 'T': '#eb6834', 'P': '#1baf7a', 'O': '#eda100', 'B': '#e87ba4', 'U': '#8a8984', 'L': '#7f63d6'}
NAME = {'S': 'Studying', 'T': 'Talking', 'P': 'On the phone', 'O': 'Other', 'B': 'Belongings only', 'U': 'Letter unreadable', 'L': 'Looking for books'}
LBL = {'A': (802.23, -1315.4), 'B': (826.2, -1314.6), 'C': (821.23, -1328.3), 'D': (814.3, -1328.4), 'E': (802.23, -1335.0)}
BOX = 0.62

d = pd.read_csv(os.path.join(HERE, f'behaviour_mapping_{date}.csv'))
ex = pd.read_csv(os.path.join(HERE, f'behaviour_mapping_{date}_extras.csv'))
seats = L.build().set_index('code')
WIN = (794.6, 836.4, -1339.4, -1313.4)
bg = L.background(os.path.join(W, 'isovist', 'Library_floor_plans.dxf'), WIN)


def table_badge_pos(code, k):
    s = seats.loc[code]; cx, cy, ax = s.table_cx, s.table_cy, s.table_axis
    if ax == 'y':
        return cx - 0.55 + k * 1.15, cy + L.T_LONG / 2 + 0.5
    return cx + L.T_LONG / 2 + 0.75, cy + 0.45 - k * 0.75


scans = sorted(d.scan.unique())
fig_w = 12.0; panel_h = fig_w * (WIN[3] - WIN[2]) / (WIN[1] - WIN[0])
fig = plt.figure(figsize=(fig_w, panel_h * len(scans) + 1.6), facecolor=SURF)
H = fig.get_figheight()
for i, scan in enumerate(scans):
    q = d[d.scan == scan].set_index('seat')
    e = ex[ex.scan == scan]
    on_seats = int(q.mark.isin(['S', 'T', 'P', 'O', 'L', 'U']).sum())
    on_extra = int(e[e.activity.isin(['S', 'T', 'P', 'O', 'L', 'U'])]['count'].sum())
    bottom = 1.35 + (len(scans) - 1 - i) * panel_h
    ax = fig.add_axes([0.01, bottom / H, 0.98, (panel_h - 0.35) / H]); ax.set_facecolor(SURF)
    for a in bg:
        ax.plot(a[:, 0], a[:, 1], color=GRID, lw=0.35, zorder=1)
    for t in L.TABLES:
        ax.add_patch(MplPoly(np.array(L.table_poly(*t[1:])), closed=True, fc='white', ec='#8a8984', lw=0.7, zorder=2))
    for code, r in q.iterrows():
        s = seats.loc[code]; f = np.radians(s.facing_deg)
        out_ = BOX / 2 - 0.25; x, y = s.x_m - np.cos(f) * out_, s.y_m - np.sin(f) * out_
        m = r.mark if isinstance(r.mark, str) else ''
        if m == 'X':
            ax.add_patch(Rectangle((x - BOX / 2, y - BOX / 2), BOX, BOX, fill=False, ec='#b5b4ae', lw=0.6, ls=(0, (2, 1.5)), zorder=3))
            ax.plot([x - 0.17, x + 0.17], [y - 0.17, y + 0.17], color='#b5b4ae', lw=0.7, zorder=3)
            ax.plot([x - 0.17, x + 0.17], [y + 0.17, y - 0.17], color='#b5b4ae', lw=0.7, zorder=3)
        elif m in COL:
            ax.add_patch(Rectangle((x - BOX / 2, y - BOX / 2), BOX, BOX, fc=COL[m], ec=SURF, lw=1.0, zorder=3))
            ax.text(x, y, m, ha='center', va='center', fontsize=6.5, weight='bold', color='white' if m in 'STP' else INK, zorder=4)
        else:
            ax.add_patch(Rectangle((x - BOX / 2, y - BOX / 2), BOX, BOX, fc='white', ec='#8a8984', lw=0.6, zorder=3))
    for code, g in e.groupby('table_first_seat', sort=False):
        for k, r in enumerate(g.itertuples()):
            bx, by = table_badge_pos(code, k)
            act = r.activity if isinstance(r.activity, str) else ''
            a0 = act[:1]
            fc = COL.get(a0, 'white'); tc = 'white' if a0 in 'STP' and a0 else INK2
            txt = f'+{int(r.count)}' + (f' {a0}' if a0 else '')
            ax.add_patch(FancyBboxPatch((bx - 0.5, by - 0.28), 1.0, 0.56, boxstyle='round,pad=0.02,rounding_size=0.18',
                                        fc=fc, ec='#8a8984' if not a0 else SURF, lw=0.7, ls='-' if a0 else (0, (2, 1.5)), zorder=5))
            ax.text(bx, by, txt, ha='center', va='center', fontsize=6, weight='bold', color=tc, zorder=6)
    for z, (lx, ly) in LBL.items():
        ax.text(lx, ly, z, ha='center', va='center', fontsize=16, weight='bold', color=INK2, zorder=6)
    st, en = q.start.min(), q.end.max()
    ax.set_title(f'Scan {scan}  ·  {pd.Timestamp(date):%a %d %b %Y}, {st}–{en}  ·  {on_seats + on_extra} people '
                 f'({on_seats} on plan seats, {on_extra} on extra chairs)', loc='left', fontsize=10.5, color=INK, pad=4)
    ax.set_xlim(WIN[0], WIN[1]); ax.set_ylim(WIN[2], WIN[3]); ax.set_aspect('equal'); ax.axis('off')

# legend
lg = fig.add_axes([0.02, 0.15 / H, 0.96, 0.95 / H]); lg.axis('off'); lg.set_xlim(0, 100); lg.set_ylim(0, 10)
items = [(COL[k], k, NAME[k], 'fill') for k in 'STPOB'] + [('white', '', 'Chair there, empty', 'empty'),
                                                          ('', '', 'Chair missing', 'missing'), ('white', '+n', 'Extra chairs (n) at a table', 'badge')]
x = 0
for i, (c, l, n, kind) in enumerate(items):
    yy = 6.6 if i < 5 else 2.2; x = (i if i < 5 else i - 5) * 20
    if kind == 'missing':
        lg.add_patch(Rectangle((x, yy - 1.4), 1.6, 2.8, fill=False, ec='#b5b4ae', lw=0.8, ls=(0, (2, 1.5))))
        lg.plot([x + 0.35, x + 1.25], [yy - 0.8, yy + 0.8], color='#b5b4ae', lw=0.8); lg.plot([x + 0.35, x + 1.25], [yy + 0.8, yy - 0.8], color='#b5b4ae', lw=0.8)
    elif kind == 'badge':
        lg.add_patch(FancyBboxPatch((x, yy - 1.3), 3.2, 2.6, boxstyle='round,pad=0.05,rounding_size=0.8', fc='white', ec='#8a8984', lw=0.8))
        lg.text(x + 1.6, yy, '+n', ha='center', va='center', fontsize=7, weight='bold', color=INK2)
    else:
        lg.add_patch(Rectangle((x, yy - 1.4), 1.6, 2.8, fc=c, ec='#8a8984' if kind == 'empty' else SURF, lw=0.8))
        if l: lg.text(x + 0.8, yy, l, ha='center', va='center', fontsize=7, weight='bold', color='white' if l in 'STP' else INK)
    lg.text(x + (4.0 if kind == 'badge' else 2.4), yy, n, va='center', fontsize=9, color=INK)
lg.text(100, 2.2, 'Extra chairs: a filled badge shows what the people on them were doing; outlined = empty.',
        ha='right', va='center', fontsize=8, color=INK2)
fig.savefig(out, dpi=220, facecolor=SURF)
print('written', out)
for scan in scans:
    q = d[d.scan == scan]; e = ex[ex.scan == scan]
    print(scan, q.mark.value_counts().to_dict(), '| extras with people', int(e[e.activity.isin(list('STPOL'))]['count'].sum()))
