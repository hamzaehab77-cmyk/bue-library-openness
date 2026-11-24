"""Working map (not a paper figure): which seats already have a valid answer, and which seats still need one so the
answers cover the whole range of isovist area.

Rule used: split the isovist-area range of the 152 seats into 50 m2 bands; every band should have at least TARGET
valid answers so the scatter plots have no empty stretch along the x-axis. For a band that is short, the suggested
seats are the unanswered seats of that band, picked to spread over control (low / middle / high); the other
unanswered seats of the band are backups.

Reads:  data/responses.csv + data/exclusions.csv (valid answers, via load_responses() in run_analysis.py),
        isovist/output/isovist_results_shelves_tall.csv, drafts/figures/seat_codes_first_floor.csv
Writes: drafts/Seat_coverage_map.png / .pdf, results/seat_coverage_needed.csv
No outcome data (time, quality, BIS) is used here - only where people sat."""
import os, sys, json
import numpy as np, pandas as pd
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon as MplPoly, Rectangle
from matplotlib.colors import LinearSegmentedColormap, Normalize

W = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(W, 'isovist'))
import standard_layout as L

TARGET, STEP = 3, 50
PAPER = '--paper' in sys.argv                         # appendix version: no 'needed' marks, no titles
INK, INK2, SURF, GRID = '#1f1e1b', '#5f5e5a', '#ffffff', '#d9d8d3'
NEED_C = '#d9480f'                                       # orange = seat still needed

seats = pd.read_csv(os.path.join(W, 'drafts', 'figures', 'seat_codes_first_floor.csv'))
iso = pd.read_csv(os.path.join(W, 'isovist', 'output', 'isovist_results_shelves_tall.csv'))[['code', 'isovist_area_m2', 'control']]
sys.path.insert(0, os.path.join(W, 'analysis'))
from run_analysis import load_responses                  # same exclusion rules; does not rerun the analysis
r_all, _ = load_responses()
p = r_all[r_all.category == 'valid']
s = seats[['code', 'zone', 'x_m', 'y_m', 'table_cy']].merge(iso, on='code')
s['n'] = s.code.map(p.seat.value_counts()).fillna(0).astype(int)
lo_edge = np.floor(s.isovist_area_m2.min() / STEP) * STEP
edges = np.arange(lo_edge, s.isovist_area_m2.max() + STEP, STEP)
s['band'] = pd.cut(s.isovist_area_m2, edges, right=False)

# ---- pick the seats still needed ----
s['status'] = np.where(s.n > 0, 'answered', 'other')
bands = []
for b, g in s.groupby('band', observed=True):
    have = int(g.n.sum()); short = max(0, TARGET - have)
    free = g[g.n == 0].sort_values('control')
    if PAPER: short = 0
    if short and len(free):
        idx = np.unique(np.round(np.linspace(0, len(free) - 1, min(short, len(free)))).astype(int))
        need = free.iloc[idx].code
        s.loc[s.code.isin(need), 'status'] = 'needed'
        s.loc[s.code.isin(free.code) & ~s.code.isin(need), 'status'] = 'backup'
    bands.append(dict(band=f'{int(b.left)}-{int(b.right)}', seats=len(g), answers=have, short=short,
                      needed=', '.join(s[(s.band == b) & (s.status == 'needed')].code),
                      backups=', '.join(s[(s.band == b) & (s.status == 'backup')].code)))
bands = pd.DataFrame(bands)
if not PAPER: bands.to_csv(os.path.join(W, 'results', 'seat_coverage_needed.csv'), index=False)
print(bands.to_string(index=False))

# ---- map ----
WIN = (786.0, 836.6, -1340.0, -1302.0)
bg = L.background(os.path.join(W, 'isovist', 'Library_floor_plans.dxf'), WIN)
cmap = LinearSegmentedColormap.from_list('blue', ['#cde2fb', '#86b6ef', '#3987e5', '#1c5cab', '#0d366b'])
norm = Normalize(s.isovist_area_m2.min(), s.isovist_area_m2.max())

fig = plt.figure(figsize=(11.7, 13.2), facecolor=SURF)
if not PAPER: fig.text(0.02, 0.975, 'Seats with a valid answer so far, and seats still needed', fontsize=14, color=INK, weight='bold')
if not PAPER: fig.text(0.02, 0.957, f'{len(p)} valid answers at {int((s.n > 0).sum())} seats. Blue = isovist area of an answered seat '
         f'(darker = more open). Goal: at least {TARGET} answers in every {STEP} m² band of isovist area.', fontsize=9.5, color=INK2)
ax = fig.add_axes([0.01, 0.36, 0.98, 0.59]); ax.set_facecolor(SURF)
for a in bg: ax.plot(a[:, 0], a[:, 1], color='#c9c8c3', lw=0.35, zorder=1)
for t in L.TABLES: ax.add_patch(MplPoly(np.array(L.table_poly(*t[1:])), closed=True, fc='white', ec='#8a8984', lw=0.6, zorder=2))
for r in s.itertuples():
    x, y = r.x_m, r.y_m
    if r.status == 'answered':
        ax.add_patch(Rectangle((x - 0.32, y - 0.32), 0.64, 0.64, fc=cmap(norm(r.isovist_area_m2)), ec=INK, lw=0.6, zorder=5))
        if r.n > 1: ax.text(x, y, str(r.n), ha='center', va='center', fontsize=5.5, color='white', weight='bold', zorder=6)
    else:
        ax.add_patch(Rectangle((x - 0.22, y - 0.22), 0.44, 0.44, fc='#e6e5e0', ec='#b4b2a9', lw=0.4, zorder=4))
    if r.status == 'needed':
        ax.add_patch(Rectangle((x - 0.45, y - 0.45), 0.9, 0.9, fill=False, ec=NEED_C, lw=1.8, zorder=9))
    elif r.status == 'backup':
        ax.add_patch(Rectangle((x - 0.4, y - 0.4), 0.8, 0.8, fill=False, ec=NEED_C, lw=0.8, ls=(0, (2, 1.5)), zorder=6))
    if r.status in ('answered', 'needed'):                  # label on the side away from the table
        up = y > r.table_cy
        ax.text(x, y + (0.42 if up else -0.42), r.code, ha='center', va='bottom' if up else 'top', fontsize=5.6, zorder=8,
                bbox=dict(fc='white', ec='none', pad=0.4, alpha=0.9),
                color=NEED_C if r.status == 'needed' else INK, weight='bold' if r.status == 'needed' else 'normal')
for z, (x0, x1, y0, y1) in L.REGIONS.items():
    ax.text(x0, y1 + 1.1, f'Area {z}', fontsize=10, color=INK2, weight='bold', zorder=7)
ax.set_xlim(WIN[0], WIN[1]); ax.set_ylim(WIN[2], WIN[3]); ax.set_aspect('equal'); ax.axis('off')

# legend + colour bar
cax = fig.add_axes([0.05, 0.345, 0.32, 0.012])
cb = fig.colorbar(plt.cm.ScalarMappable(norm=norm, cmap=cmap), cax=cax, orientation='horizontal')
cb.set_label('Isovist area of an answered seat (m²)', fontsize=8.5, color=INK2); cb.ax.tick_params(labelsize=8, colors=INK2); cb.outline.set_visible(False)
lg = fig.add_axes([0.42, 0.33, 0.56, 0.035]); lg.axis('off'); lg.set_xlim(0, 100); lg.set_ylim(0, 10)
items = [('ans', 'Answered (number = answers if >1)'), ('need', 'Needed next'), ('backup', 'Backup in same band'), ('none', 'No answer, band already covered')]
if PAPER: items = [('ans', 'Seat of a participant (number = participants if >1)'), ('none', 'No participant')]
for i, (k, txt) in enumerate(items):
    x0 = [0, 52, 0, 52][i]; y0 = 7 if i in (0, 1) else 1.5
    if k == 'ans': lg.add_patch(Rectangle((x0, y0 - 1.6), 2.4, 3.2, fc='#3987e5', ec=INK, lw=0.6))
    if k == 'need': lg.add_patch(Rectangle((x0, y0 - 1.6), 2.4, 3.2, fc='#e6e5e0', ec=NEED_C, lw=1.8))
    if k == 'backup': lg.add_patch(Rectangle((x0, y0 - 1.6), 2.4, 3.2, fc='#e6e5e0', ec=NEED_C, lw=0.8, ls=(0, (2, 1.5))))
    if k == 'none': lg.add_patch(Rectangle((x0 + 0.3, y0 - 1.1), 1.8, 2.2, fc='#e6e5e0', ec='#b4b2a9', lw=0.4))
    lg.text(x0 + 3.4, y0, txt, va='center', fontsize=8.5, color=INK)

# band chart: answers per isovist-area band
bx = fig.add_axes([0.08, 0.06, 0.88, 0.22])
xs = np.arange(len(bands))
cols = [cmap(norm(min(max((e + STEP / 2), s.isovist_area_m2.min()), s.isovist_area_m2.max()))) for e in edges[:-1]]
bx.bar(xs, bands.answers, color=cols, ec=INK, lw=0.5, width=0.62, zorder=3)
if not PAPER: bx.bar(xs, bands.short, bottom=bands.answers, color='none', ec=NEED_C, lw=1.4, ls='--', width=0.62, zorder=3)
if not PAPER: bx.axhline(TARGET, color=NEED_C, lw=0.9, ls=':', zorder=2)
for i, r in bands.iterrows():
    bx.text(i, r.answers + r.short + 0.3, f'{r.answers}', ha='center', fontsize=9, color=INK, weight='bold')
    bx.text(i, -1.4, f'{r.seats} seats', ha='center', fontsize=7.5, color=INK2)
    if r.needed:
        bx.text(i, max(r.answers + r.short, TARGET) + 1.6, r.needed.replace(', ', '\n'), ha='center', va='bottom', fontsize=7.5, color=NEED_C, weight='bold')
bx.set_xticks(xs, [f'{b} m²' for b in bands.band], fontsize=8.5, color=INK2)
bx.set_ylim(0, max(bands.answers.max(), TARGET) + 6)
bx.set_ylabel('Participants' if PAPER else 'Valid answers', fontsize=9, color=INK2)
if PAPER: bx.set_title(f'Participants in each {STEP} m² band of isovist area', fontsize=9.5, color=INK, loc='left')
else: bx.set_title(f'Answers in each band of isovist area (dotted line = goal of {TARGET}; dashed boxes = answers still missing; codes = seats needed next)',
             fontsize=9.5, color=INK, loc='left')
bx.grid(axis='y', color=GRID, lw=0.5, zorder=0)
for sp in ('top', 'right'): bx.spines[sp].set_visible(False)
for sp in ('left', 'bottom'): bx.spines[sp].set_color(GRID)
bx.tick_params(colors=INK2, labelsize=8)
bx.xaxis.set_tick_params(pad=14)

out = os.path.join(W, 'results', 'figures', 'seat_coverage_paper') if PAPER else os.path.join(W, 'drafts', 'Seat_coverage_map')
fig.savefig(out + '.png', dpi=200, facecolor=SURF); fig.savefig(out + '.pdf', facecolor=SURF); plt.close(fig)
print('saved', out + '.png')
