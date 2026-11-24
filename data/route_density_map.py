"""Walking-route density from the behavioural maps: lines crossing fixed count lines (gates), counted by eye on every sheet
(data/route_counts.csv; gates set in data/route_gates.py), split by pen colour (apparent gender) and with the direction of the
arrowheads seen near the gate. Lines drawn for a labelled group are counted as that many people. Staff lines are left out.
These are density markers, not exact counts: bundled lines can hide one another (about +/- 2 lines per gate).
usage: python route_density_map.py   -> results/figures/route_density.png, results/route_counts_summary.csv"""
import os, sys, re
import numpy as np, pandas as pd
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__)); W = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(W, 'isovist'))
import standard_layout as L
from matplotlib.patches import Polygon as MplPoly

plt.rcParams.update({'font.family': 'Arial', 'font.size': 8})
INK, INK2, GRID, SURF = '#0b0b0b', '#52514e', '#c9c8c3', '#fcfcfb'
CM, CF = '#2a78d6', '#eb6834'
# sheet borders (online_task/make_mapping_sheets_v3.py): east x 808.6-837.5, y -1312.5..-1334; west x 786.5-808.6, y -1312.5..-1340.5
SH = {'east': (808.6, 28.9, -1312.5, 21.5), 'west': (786.5, 22.1, -1312.5, 28.0)}
GATES = {  # same as route_gates.py: half, (u0, v0), (u1, v1), label
    'E1': ('east', (0.25, 0.09), (0.25, 0.23), 'North corridor (D)'),
    'E2': ('east', (0.25, 0.66), (0.25, 0.84), 'South corridor (D-C)'),
    'E3': ('east', (0.21, 0.45), (0.335, 0.45), 'Along the void'),
    'E4': ('east', (0.36, 0.40), (0.76, 0.40), 'B shelves <-> C'),
    'E5': ('east', (0.66, 0.60), (0.66, 0.92), 'East stairs'),
    # the north door (to the west stairs; not on the mapping sheets, at about x 793.6, y -1310.4 on the plan) is reached two
    # ways: through the bookshelves north of the A tables (W1a) or along the open strip by the north wall (W1b)
    'W1a': ('west', (0.385, 0.054), (0.50, 0.054), 'To north door via shelves'),
    'W1b': ('west', (0.52, -0.046), (0.52, 0.004), 'To north door, open side'),
    'W2': ('west', (0.97, 0.06), (0.97, 0.36), 'A <-> D (north)'),
    'W3': ('west', (0.97, 0.38), (0.97, 0.70), 'A/E <-> D/C'),
    'W4': ('west', (0.36, 0.45), (0.36, 0.66), 'To the toilets'),
    'W5': ('west', (0.38, 0.41), (0.96, 0.41), 'A <-> E'),
}


# centre lines of the walking routes on the plan (metres), traced from the bundles of lines on the sheets; each route carries
# the count of its count line. Drawn in one nominal direction; the arrow shows the main direction actually observed.
PATHS = {
    'E1': [(808.8, -1315.7), (814.0, -1315.6), (820.0, -1315.5), (824.2, -1315.6), (825.6, -1316.8)],   # north corridor -> B
    'E4': [(825.6, -1316.8), (826.1, -1319.5), (826.5, -1323.0), (827.0, -1326.0), (827.6, -1327.6)],   # B aisles -> C
    'E3': [(816.8, -1315.9), (817.0, -1319.0), (817.1, -1323.0), (817.3, -1326.5), (817.7, -1328.1)],   # along the void
    'E2': [(808.8, -1328.4), (813.0, -1328.4), (818.0, -1328.3), (823.0, -1328.3), (826.6, -1328.7)],   # south corridor
    'E5': [(826.6, -1328.7), (828.0, -1329.1), (829.4, -1329.9), (830.6, -1331.0)],                     # to the east stairs
    'W2': [(797.6, -1316.5), (801.0, -1316.4), (805.0, -1316.2), (808.8, -1315.7)],                     # A -> D, north
    'W3': [(799.6, -1326.3), (803.0, -1326.3), (806.0, -1326.6), (808.8, -1328.4)],                     # A/E -> south corridor
    'W4': [(799.6, -1326.3), (797.6, -1326.4), (795.8, -1326.9), (794.3, -1327.8)],                     # to the toilets
    'W5': [(807.0, -1320.2), (807.1, -1322.5), (807.0, -1324.5), (806.2, -1326.4)],                     # A <-> E
    'W1a': [(797.6, -1316.5), (796.4, -1315.0), (795.5, -1313.4), (794.6, -1311.6), (793.9, -1310.8)],  # through the shelves to the door
    'W1b': [(803.8, -1312.0), (800.5, -1311.8), (797.5, -1311.5), (795.4, -1311.0), (794.1, -1310.6)],  # open side to the door
}
LBL_OFF = {'E1': 1.3, 'E4': -2.6, 'E3': -2.2, 'E2': -1.4, 'E5': -1.6, 'W2': 1.3, 'W3': -1.5, 'W4': 1.6, 'W5': 2.6,
           'W1a': 2.4, 'W1b': 1.2}


def smooth(pts, it=4):
    """Chaikin corner cutting: a smooth curve through the route's control points (ends kept)"""
    P = np.asarray(pts, float)
    for _ in range(it):
        Q = [P[0]]
        for a, b in zip(P[:-1], P[1:]): Q += [0.75 * a + 0.25 * b, 0.25 * a + 0.75 * b]
        Q.append(P[-1]); P = np.array(Q)
    return P


def plan(half, u, v):
    x0, wx, y0, hy = SH[half]; return x0 + u * wx, y0 - v * hy


def arrows(s):
    out = {}
    for tok in str(s).split():
        m = re.match(r'([NSEW])(\d*)$', tok)
        if m: out[m.group(1)] = out.get(m.group(1), 0) + int(m.group(2) or 1)
    return out


d = pd.read_csv(os.path.join(HERE, 'route_counts.csv'), keep_default_na=False)
summ = d.groupby(['date', 'gate'])[['male', 'female']].sum().reset_index()
summ['scans'] = d.groupby(['date', 'gate']).scan.nunique().values
summ['per_scan'] = ((summ.male + summ.female) / summ.scans).round(1)
summ['female_share'] = (summ.female / (summ.male + summ.female)).round(2)


def main_dir(sub):
    tot = {}
    for col in ('arrows_male', 'arrows_female'):
        for s in sub[col]:
            for k, v in arrows(s).items(): tot[k] = tot.get(k, 0) + v
    if not tot: return ''
    k = max(tot, key=tot.get); opp = {'N': 'S', 'S': 'N', 'E': 'W', 'W': 'E'}[k]
    return k if tot[k] >= 2 * tot.get(opp, 0) and tot[k] >= 2 else 'both'


summ['main_direction'] = [main_dir(d[(d.date == r.date) & (d.gate == r.gate)]) for r in summ.itertuples()]
summ['label'] = summ.gate.map(lambda g: GATES[g][3])
os.makedirs(os.path.join(W, 'results', 'figures'), exist_ok=True)
summ.to_csv(os.path.join(W, 'results', 'route_counts_summary.csv'), index=False)
print(summ.to_string(index=False))

seats = L.build()
bg = L.background(os.path.join(W, 'isovist', 'Library_floor_plans.dxf'), (785, 839, -1341.5, -1307.5))
dates = sorted(d.date.unique())
fig, axs = plt.subplots(len(dates), 1, figsize=(10.5, 7.1 * len(dates)), facecolor=SURF)
for ax, date in zip(np.atleast_1d(axs), dates):
    ax.set_facecolor(SURF)
    for a in bg: ax.plot(a[:, 0], a[:, 1], color=GRID, lw=0.35, zorder=1)
    for t in L.TABLES: ax.add_patch(MplPoly(np.array(L.table_poly(*t[1:])), closed=True, fc='white', ec='#8a8984', lw=0.6, zorder=2))
    ax.plot([808.6, 808.6], [-1312.5, -1340.5], color='#b5b4ae', lw=0.8, ls=(0, (4, 3)), zorder=2)
    nsc = d[d.date == date].scan.nunique()
    for r in summ[summ.date == date].itertuples():
        P = smooth(PATHS[r.gate])
        tang = np.gradient(P, axis=0); tang /= np.linalg.norm(tang, axis=1, keepdims=True)
        nrm = np.c_[-tang[:, 1], tang[:, 0]]
        wm, wf = r.male / nsc, r.female / nsc
        sm, sf = max(0.7, wm * 1.5), max(0.7, wf * 1.5)          # stroke widths in points
        gap = 0.16 + 0.012 * (sm + sf)                            # metres between the two strands
        for val, col, sgn, sw in ((wm, CM, 1, sm), (wf, CF, -1, sf)):
            if val <= 0: continue
            S = P + nrm * sgn * gap / 2
            ax.plot(S[:, 0], S[:, 1], color=col, lw=sw, solid_capstyle='round', solid_joinstyle='round', alpha=0.88, zorder=4)
        # direction: compare the main direction with the way the path is drawn
        k = len(P) // 2; t = tang[k]
        if r.main_direction in ('N', 'S', 'E', 'W'):
            v = np.array({'N': (0, 1), 'S': (0, -1), 'E': (1, 0), 'W': (-1, 0)}[r.main_direction])
            s = 1 if np.dot(t, v) >= 0 else -1
            ax.annotate('', xy=P[k] + s * t * 0.9, xytext=P[k] - s * t * 0.9,
                        arrowprops=dict(arrowstyle='-|>', color=INK, lw=1.1, mutation_scale=11), zorder=6)
        elif r.main_direction == 'both':
            ax.annotate('', xy=P[k] + t * 1.0, xytext=P[k] - t * 1.0,
                        arrowprops=dict(arrowstyle='<|-|>', color=INK, lw=1.0, mutation_scale=9), zorder=6)
        lx, ly = P[k] + nrm[k] * LBL_OFF.get(r.gate, 1.3)
        ax.text(lx, ly, f'{r.label}\n{wm:.1f} m · {wf:.1f} f', fontsize=6.5, color=INK, ha='center', va='center', zorder=7,
                bbox=dict(fc='white', ec='none', alpha=0.82, pad=0.5))
    ax.plot([793.2, 794.0], [-1310.4, -1310.4], color=INK, lw=2.4, zorder=6)
    ax.text(793.6, -1309.6, 'North door\n(to stairs)', fontsize=6.8, ha='center', va='bottom', color=INK, zorder=7)
    for z, (lx, ly) in {'A': (802.2, -1322.6), 'B': (826.2, -1314.4), 'C': (821.6, -1330.5), 'D': (814.3, -1321.0), 'E': (802.2, -1336.2)}.items():
        ax.text(lx, ly, z, fontsize=16, weight='bold', color='#d0cfca', ha='center', va='center', zorder=2)
    ax.set_title(f'{pd.Timestamp(date):%A %d %B %Y}: walking routes, people per scan ({nsc} scans)',
                 loc='left', fontsize=10, color=INK)
    ax.set_xlim(785, 839); ax.set_ylim(-1341.5, -1307.8); ax.set_aspect('equal'); ax.axis('off')
fig.text(0.02, 0.012, 'Line thickness = people per scan on each walking route (blue = male, orange = female, from pen colour); '
         'black arrow = main direction of the arrowheads (double arrow = both ways). Counted by eye from the hand-drawn sheets: density '
         'markers, about +/- 2 lines per count line.', fontsize=7, color=INK2, wrap=True)
fig.tight_layout(rect=(0, 0.03, 1, 1))
out = os.path.join(W, 'results', 'figures', 'route_density.png'); fig.savefig(out, dpi=180, facecolor=SURF); print('written', out)
