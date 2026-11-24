"""Behavioural map of ONE observer's half of the floor for one mapping day (for individual marking): west = areas A and E
([researcher]), east = areas D, B and C ([researcher]). One panel per scan: every standard seat coloured by activity (letter inside),
extra chairs as +n badges, and under each panel an observation table (activity x apparent gender, people at the tables
plus people standing, walking or sitting elsewhere). The paper uses the merged whole-floor maps instead.
usage: python behaviour_map_side.py <date> <west|east> <out.png>"""
import os, sys
import numpy as np, pandas as pd
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, FancyBboxPatch, Polygon as MplPoly

date, side, out = sys.argv[1:4]
HERE = os.path.dirname(os.path.abspath(__file__)); W = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(W, 'isovist'))
import standard_layout as L

plt.rcParams.update({'font.family': 'Arial', 'font.size': 9})
INK, INK2, GRID, SURF = '#0b0b0b', '#52514e', '#c9c8c3', '#fcfcfb'
COL = {'S': '#2a78d6', 'T': '#eb6834', 'P': '#1baf7a', 'O': '#eda100', 'B': '#e87ba4', 'L': '#7f63d6', 'U': '#8a8984'}
ACT = {'S': 'Studying', 'T': 'Talking', 'P': 'On the phone', 'O': 'Other', 'L': 'Looking for books', 'U': 'Unreadable letter', '': 'Not recorded'}
SIDE = {'west': ('AE', '[researcher]', 'West half: areas A and E'), 'east': ('DBC', '[researcher]', 'East half: areas D, B and C')}
zones, observer, side_title = SIDE[side]
LBL = {'A': (802.23, -1315.4), 'B': (826.2, -1314.6), 'C': (821.23, -1328.3), 'D': (814.3, -1328.4), 'E': (802.23, -1335.0)}
BOX = 0.62

d = pd.read_csv(os.path.join(HERE, f'behaviour_mapping_{date}.csv'), dtype={'mark': str}, keep_default_na=False)
d = d[d.zone.isin(list(zones))]
assert len(d), f'no {side} data for {date} yet'
ex = pd.read_csv(os.path.join(HERE, f'behaviour_mapping_{date}_extras.csv'), keep_default_na=False)
seats = L.build().set_index('code')
ex = ex[ex.table_first_seat.map(lambda c: c[0] in zones)]
offf = os.path.join(HERE, f'behaviour_mapping_{date}_people_off_seats.csv')
off = pd.read_csv(offf, keep_default_na=False) if os.path.exists(offf) else pd.DataFrame(columns=['scan', 'area', 'posture', 'activity', 'gender', 'staff', 'count'])
off = off[off.area.isin(list(zones)) & (off.staff.astype(str).str.strip() != '1')]   # staff left out of the counts
sx = seats[seats.zone.isin(list(zones))]
WIN = (sx.x_m.min() - 2.6, sx.x_m.max() + 2.6, -1339.4, -1313.4)
bg = L.background(os.path.join(W, 'isovist', 'Library_floor_plans.dxf'), WIN)


def badge_pos(code, k):
    s = seats.loc[code]; cx, cy, ax = s.table_cx, s.table_cy, s.table_axis
    if ax == 'y': return cx - 0.55 + k * 1.15, cy + L.T_LONG / 2 + 0.5
    return cx + L.T_LONG / 2 + 0.75, cy + 0.45 - k * 0.75


def obs_table(scan):
    """counts by activity x gender: tables (standard + extra chairs) and elsewhere (standing, walking, sitting elsewhere)"""
    rows = []
    q = d[(d.scan == scan) & (d.occupied == 1)]
    for r in q.itertuples(): rows.append((r.mark, getattr(r, 'gender', '') or '', 1, 'table'))
    for r in ex[(ex.scan == scan) & ex.activity.isin(list('STPOLU'))].itertuples():
        g_ = getattr(r, 'gender', ''); rows.append((r.activity, g_ if g_ in ('M', 'F', 'U') else '', int(r.count), 'table'))
    for r in off[off.scan == scan].itertuples():
        rows.append((r.activity, r.gender, int(r.count), 'elsewhere'))
    t = pd.DataFrame(rows, columns=['act', 'g', 'n', 'where'])
    if t.empty: return t
    t['g'] = t.g.replace({'U': '?', '': '?'})
    return t


scans = sorted(d.scan.unique())
fig_w = 7.4 if side == 'west' else 9.6
panel_h = fig_w * 0.96 * (WIN[3] - WIN[2]) / (WIN[1] - WIN[0])
tab_h = 2.05
fig = plt.figure(figsize=(fig_w, (panel_h + tab_h) * len(scans) + 1.5), facecolor=SURF)
H = fig.get_figheight()
fig.text(0.02, 1 - 0.32 / H, f'Behavioural map · {side_title} · observer: {observer} · {pd.Timestamp(date):%A %d %B %Y}',
         fontsize=11, weight='bold', color=INK)
has_gender = 'gender' in d.columns and (d.gender != '').any()
for i, scan in enumerate(scans):
    q = d[d.scan == scan].set_index('seat'); e = ex[ex.scan == scan]
    top = H - 0.55 - i * (panel_h + tab_h)
    ax = fig.add_axes([0.02, (top - panel_h) / H, 0.96, (panel_h - 0.3) / H]); ax.set_facecolor(SURF)
    for a in bg: ax.plot(a[:, 0], a[:, 1], color=GRID, lw=0.35, zorder=1)
    for t in L.TABLES:
        if t[0][0] in zones: ax.add_patch(MplPoly(np.array(L.table_poly(*t[1:])), closed=True, fc='white', ec='#8a8984', lw=0.7, zorder=2))
    for code, r in q.iterrows():
        s = seats.loc[code]; f = np.radians(s.facing_deg); o_ = BOX / 2 - 0.25
        x, y = s.x_m - np.cos(f) * o_, s.y_m - np.sin(f) * o_; m = r.mark
        if m == 'X':
            ax.add_patch(Rectangle((x - BOX / 2, y - BOX / 2), BOX, BOX, fill=False, ec='#b5b4ae', lw=0.6, ls=(0, (2, 1.5)), zorder=3))
            ax.plot([x - .17, x + .17], [y - .17, y + .17], color='#b5b4ae', lw=.7, zorder=3); ax.plot([x - .17, x + .17], [y + .17, y - .17], color='#b5b4ae', lw=.7, zorder=3)
        elif m in COL:
            ax.add_patch(Rectangle((x - BOX / 2, y - BOX / 2), BOX, BOX, fc=COL[m], ec=SURF, lw=1.0, zorder=3))
            g = r.get('gender', '') if has_gender else ''
            ax.text(x, y, m + ({'M': 'm', 'F': 'f'}.get(g, '') if m != 'B' else ''), ha='center', va='center', fontsize=5.6,
                    weight='bold', color='white' if m in 'STPLU' else INK, zorder=4)
        else:
            ax.add_patch(Rectangle((x - BOX / 2, y - BOX / 2), BOX, BOX, fc='white', ec='#8a8984', lw=0.6, zorder=3))
    for code, g in e.groupby('table_first_seat', sort=False):
        for k, r in enumerate(g.itertuples()):
            bx, by = badge_pos(code, k); a0 = (r.activity or '')[:1]
            ax.add_patch(FancyBboxPatch((bx - .5, by - .28), 1.0, .56, boxstyle='round,pad=0.02,rounding_size=0.18', fc=COL.get(a0, 'white'),
                                        ec='#8a8984' if not a0 else SURF, lw=.7, ls='-' if a0 else (0, (2, 1.5)), zorder=5))
            ax.text(bx, by, f'+{int(r.count)}' + (f' {a0}' if a0 else ''), ha='center', va='center', fontsize=5.8, weight='bold',
                    color='white' if a0 in ('S', 'T', 'P', 'L') else INK2, zorder=6)
    for z in zones: ax.text(*LBL[z], z, ha='center', va='center', fontsize=15, weight='bold', color=INK2, zorder=6)
    st, en = q.start.min(), q.end.max()
    t = obs_table(scan)
    n_tab = int(t[t['where'] == 'table'].n.sum()) if len(t) else 0; n_else = int(t[t['where'] == 'elsewhere'].n.sum()) if len(t) else 0
    ax.set_title(f'Scan {scan}, {st}–{en}: {n_tab} people at the tables' + (f', {n_else} standing, walking or sitting elsewhere' if len(off) else ''),
                 loc='left', fontsize=9.5, color=INK, pad=3)
    ax.set_xlim(WIN[0], WIN[1]); ax.set_ylim(WIN[2], WIN[3]); ax.set_aspect('equal'); ax.axis('off')
    # observation table
    tx = fig.add_axes([0.04, (top - panel_h - tab_h + 0.12) / H, 0.92, (tab_h - 0.25) / H]); tx.axis('off')
    if len(t):
        acts = [a for a in 'STPOLU' if (t.act == a).any()] + ([''] if (t.act == '').any() else [])
        cols = ['M', 'F', '?'] if has_gender else ['?']
        cell = [[ACT[a]] + [str(int(t[(t.act == a) & (t.g == g)].n.sum())) for g in cols] + [str(int(t[t.act == a].n.sum()))] for a in acts]
        cell.append(['Total'] + [str(int(t[t.g == g].n.sum())) for g in cols] + [str(int(t.n.sum()))])
        head = ['Activity'] + (['Male', 'Female', "Can't tell"] if has_gender else ['Gender not recorded']) + ['Total']
        tb = tx.table(cellText=cell, colLabels=head, loc='upper left', cellLoc='center', colLoc='center',
                      colWidths=[0.3] + [0.15] * len(cols) + [0.15])
        tb.auto_set_font_size(False); tb.set_fontsize(7.5); tb.scale(1, 1.05)
        for (rr, cc), c in tb.get_celld().items():
            c.set_edgecolor(GRID); c.set_linewidth(0.5)
            if rr == 0 or rr == len(cell): c.set_text_props(weight='bold')
lg = fig.add_axes([0.02, 0.1 / H, 0.96, 0.75 / H]); lg.axis('off'); lg.set_xlim(0, 100); lg.set_ylim(0, 10)
for k, (a, n_) in enumerate([(a, ACT.get(a, '')) for a in 'STPOB']):
    x = k * 19; lg.add_patch(Rectangle((x, 5), 2.2, 3.4, fc=COL[a], ec=SURF)); lg.text(x + 1.1, 6.7, a, ha='center', va='center', fontsize=7, weight='bold', color='white' if a in 'STP' else INK)
    lg.text(x + 3, 6.7, n_ if a != 'B' else 'Belongings only', va='center', fontsize=8, color=INK)
lg.text(0, 1.6, ('Small m / f after the letter = apparent gender (male / female). ' if has_gender else '') +
        '+n = people on extra chairs at that table; dashed box = chair missing.', fontsize=7.5, color=INK2, va='center')
fig.savefig(out, dpi=200, facecolor=SURF); plt.close(fig)
print('written', out)
