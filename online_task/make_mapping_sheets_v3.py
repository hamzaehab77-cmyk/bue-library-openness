"""Behavioural-mapping sheets v3 (18 Nov 2026): the WHOLE open floor, not only the seats.
Following the observation method of the module's lecture 4: who (actor), doing what (act), with whom, when, where, setting;
recorded with a map (symbols + letters), an observation table and observation notes, plus physical traces.

One map page per area (A-E). Each area now owns a territory of the floor: its seats AND the corridors, bookshelves and
open space around them, so every person on the floor belongs to exactly one sheet. The territory border is drawn on
each page; what lies outside it is faded (it belongs to another sheet).
Page 6 = observation table (one row per activity), page 7 = observation notes + physical traces checklist.
usage: python make_mapping_sheets_v3.py <isovist folder> <plan.dxf> <out.pdf> [preview_prefix]"""
import sys
import numpy as np
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.patches import Rectangle, Polygon as MplPoly, Circle, RegularPolygon, FancyArrowPatch

iso, dxf, out_pdf = sys.argv[1:4]
preview = sys.argv[4] if len(sys.argv) > 4 else None
sys.path.insert(0, iso)
import standard_layout as L

plt.rcParams.update({'font.family': 'Arial', 'font.size': 9})
seats = L.build()
BOX = 0.60
X0, X1, Y0, Y1 = 786.5, 837.5, -1340.5, -1312.5           # open floor (enclosed rooms to the north are not mapped)
XW, XE, YAE, YBC = 808.6, 817.2, -1326.0, -1322.6           # territory borders
TERR = {'A': (X0, XW, YAE, Y1), 'E': (X0, XW, Y0, YAE), 'D': (XW, XE, -1334.0, Y1),
        'B': (XE, X1, YBC, Y1), 'C': (XE, X1, -1334.0, YBC)}
AREA_LBL = {'A': (802.23, -1322.6), 'B': (826.2, -1314.4), 'C': (821.6, -1329.4), 'D': (814.3, -1321.0), 'E': (802.23, -1335.3)}
PAGES = [('A', 'land'), ('B', 'land'), ('C', 'land'), ('D', 'port'), ('E', 'land')]
BLUE, RED, INK, GREY = '#1f5fd0', '#d00000', '#111111', '#9a9a9a'


def zone_of(x, y):
    for z, (a, b, c, d) in TERR.items():
        if a <= x < b and c <= y <= d: return z
    return None


assert all(zone_of(r.x_m, r.y_m) == r.zone for r in seats.itertuples()), 'a seat lies outside its own territory'


# ---------- the symbol key (drawn in figure coordinates) ----------
def sym(fig, kind, x, y, r_in=0.095, letter=None, color=INK):
    """draw one symbol centred at (x, y) in figure fractions; r_in = half-size in inches (same size on every page)"""
    sx, s = r_in / fig.get_figwidth(), r_in / fig.get_figheight()
    T = fig.transFigure
    if kind == 'sit':
        from matplotlib.patches import Ellipse
        fig.add_artist(Ellipse((x, y), 2 * sx, 2 * s, transform=T, fill=False, ec=color, lw=1.1))
    elif kind == 'else':
        fig.add_artist(Rectangle((x - sx, y - s), 2 * sx, 2 * s, transform=T, fill=False, ec=color, lw=1.1))
    elif kind == 'stand':
        fig.add_artist(MplPoly([(x - sx * 1.1, y - s), (x + sx * 1.1, y - s), (x, y + s * 1.05)], transform=T, fill=False,
                               ec=color, lw=1.1))
    elif kind == 'walk':
        fig.add_artist(FancyArrowPatch((x - sx * 2.4, y), (x + sx * 2.4, y), transform=T, arrowstyle='-|>', mutation_scale=9,
                                       color=color, lw=1.2))
    if letter:
        fig.text(x, y - (s * 0.22 if kind == 'stand' else 0), letter, fontsize=7.5, weight='bold', color=color,
                 ha='center', va='center')


def key(fig, top, left=0.03, right=0.97):
    """the symbol key; items wrap onto a new line when the page is too narrow. Returns the y below the key."""
    r = fig.canvas.get_renderer()
    line = 0.27 / fig.get_figheight()                       # line height, 0.27 in
    inch_x = 1 / fig.get_figwidth()

    def row(y, items, gap=0.14):
        x = left
        for kind, letter, txt, color in items:
            w0 = (0.55 if kind == 'walk' else 0.24) * inch_x if kind else (0.17 * inch_x if letter else 0)
            t = fig.text(0, 0, txt, fontsize=8.3)
            tw = t.get_window_extent(renderer=r).width / fig.bbox.width; t.remove()
            if x + w0 + tw > right and x > left: y -= line; x = left
            if kind:
                sym(fig, kind, x + w0 / 2, y, letter=letter, color=color)
            elif letter:
                fig.text(x, y, letter, fontsize=9.5, weight='bold', color=color, va='center')
            x += w0 + 0.05 * inch_x
            fig.text(x, y, txt, fontsize=8.3, va='center', color=INK)
            x += tw + gap * inch_x
        return y - line

    y = top
    for head, items in [
        ('SHAPE = where / posture', [('sit', None, 'sitting on a chair', INK),
                                     ('else', None, 'sitting elsewhere (floor, between shelves, ledge)', INK),
                                     ('stand', None, 'standing', INK), ('walk', None, 'walking (arrow = direction)', INK)]),
        ('LETTER inside the shape = activity', [(None, 'S', 'studying (reading, writing, laptop)', INK), (None, 'T', 'talking', INK),
                                                (None, 'P', 'on the phone', INK), (None, 'L', 'looking for books at shelves', INK),
                                                (None, 'O', 'other (eating, resting, sleeping)', INK),
                                                (None, 'B', 'belongings only, nobody there', INK)]),
        ('PEN COLOUR = gender, and other marks', [('sit', 'S', 'blue = male', BLUE), ('sit', 'S', 'red = female', RED),
                                                  ('sit', 'S', 'black = cannot tell', INK),
                                                  (None, '*', 'next to a symbol = staff or visitor', INK),
                                                  (None, '—', 'line joining symbols = group together', INK),
                                                  (None, 'X', 'on a chair box = chair missing', INK)])]:
        fig.text(left, y, head, fontsize=8.3, weight='bold', va='center')
        y = row(y - line, items)
    return y


def header(fig, title, sub):
    """title, one line of instructions, and the boxes for date, time, observer and head counts (sizes in inches)"""
    H, Wd = fig.get_figheight(), fig.get_figwidth()
    y = 1 - 0.38 / H
    fig.text(0.03, y, title, fontsize=14, weight='bold', va='center')
    y -= 0.27 / H
    fig.text(0.03, y, sub, fontsize=8.8, va='center', color='#333333')
    y -= 0.27 / H
    x = 0.03
    for label, w in [('Date', 1.1), ('Day', 0.8), ('Scan no.', 0.6), ('Start time', 0.75), ('End time', 0.75),
                     ('Observer', 0.95), ('People: male', 0.85), ('female', 0.65), ('total', 0.6)]:
        if x + w / Wd > 0.97: x = 0.03; y -= 0.55 / H
        fig.text(x, y, label, fontsize=7.8, color='#333333', va='center')
        fig.add_artist(Rectangle((x, y - 0.4 / H), w / Wd, 0.3 / H, transform=fig.transFigure, fill=False, lw=0.8))
        x += (w + 0.12) / Wd
    return y - 0.62 / H


def map_page(pdf, n, zones, orient, bg, title):
    """one A3 map page covering several areas; the key goes on top (portrait) or in a right-hand column (landscape)"""
    figsize = (16.54, 11.69) if orient == 'land' else (11.69, 16.54)
    fig = plt.figure(figsize=figsize)
    a = min(TERR[z][0] for z in zones); b = max(TERR[z][1] for z in zones)
    c = min(TERR[z][2] for z in zones); d = max(TERR[z][3] for z in zones)
    top = header(fig, f'Behavioural mapping: {title}  (sheet {n} of 3)',
                 'Map EVERY person inside the blue borders: at the seats, in corridors, between shelves, standing or walking.')
    bottom = 0.06
    if orient == 'land':
        key(fig, top - 0.01, left=0.745, right=0.985)
        ax = fig.add_axes([0.02, bottom, 0.71, top - bottom])
    else:
        top = key(fig, top) - 0.005
        ax = fig.add_axes([0.03, bottom, 0.94, top - bottom])
    m = 0.9
    x0, x1, y0, y1 = a - m, b + m, c - m, d + 0.3
    for arr in bg:
        if arr[:, 0].max() < x0 - 1 or arr[:, 0].min() > x1 + 1 or arr[:, 1].max() < y0 - 1 or arr[:, 1].min() > y1 + 1: continue
        ax.plot(arr[:, 0], arr[:, 1], color='#8c8c8c', lw=0.45, zorder=1)
    for t, (tz, cx, cy, axis) in enumerate(L.TABLES):
        ax.add_patch(MplPoly(np.array(L.table_poly(cx, cy, axis)), closed=True, fc='white', ec='black', lw=0.9, zorder=3))
    for r in seats.itertuples():
        f = np.radians(r.facing_deg); ux, uy = np.cos(f), np.sin(f)
        o = BOX / 2 - 0.25; bx, by = r.x_m - ux * o, r.y_m - uy * o
        ax.add_patch(Rectangle((bx - BOX / 2, by - BOX / 2), BOX, BOX, fc='white', ec='#555555', lw=0.6, zorder=4))
        if r.zone in zones:
            ax.text(r.x_m + ux * 0.53, r.y_m + uy * 0.53, r.code.split('-')[1], color=RED, fontsize=7, weight='bold',
                    ha='center', va='center', zorder=5)
    # fade everything outside this sheet (it belongs to the other sheet)
    for rx, ry, rw, rh in ((x0, y0, a - x0, y1 - y0), (b, y0, x1 - b, y1 - y0), (a, y0, b - a, c - y0), (a, d, b - a, y1 - d)):
        if rw > 0 and rh > 0:
            ax.add_patch(Rectangle((rx, ry), rw, rh, fc='white', ec='none', alpha=0.72, zorder=7))
    for z in zones:
        za, zb, zc, zd = TERR[z]
        ax.add_patch(Rectangle((za, zc), zb - za, zd - zc, fill=False, ec=BLUE, lw=2.2, zorder=8))
    for nz, (lx, ly) in AREA_LBL.items():
        if x0 <= lx <= x1 and y0 <= ly <= y1:
            own = nz in zones
            ax.text(lx, ly, nz if own else f'{nz}\n(other sheet)', color=BLUE if own else GREY, fontsize=28 if own else 10,
                    weight='bold', ha='center', va='center', zorder=9)
    ax.set_xlim(x0, x1); ax.set_ylim(y0, y1); ax.set_aspect('equal', anchor='C'); ax.axis('off')
    fig.text(0.03, 0.035, 'Notes (crowding, event, closed part, noise, moved furniture):', fontsize=9)
    fig.add_artist(plt.Line2D([0.03, 0.97], [0.015, 0.015], transform=fig.transFigure, lw=0.6, color='#555555'))
    fig.text(0.97, 0.003, 'Draw the symbol where the person is. Standard chairs: draw it in the chair box. Seat numbers in red. '
             'Print on A3.', fontsize=7.5, ha='right', color='#666666')
    pdf.savefig(fig)
    if preview: fig.savefig(f'{preview}_{n}.png', dpi=100)
    plt.close(fig)


def table_page(pdf, n):
    fig = plt.figure(figsize=(16.54, 11.69))
    top = header(fig, f'Observation table  (sheet {n} of 3)', 'Fill in once per scan, for the whole floor. One row per activity seen.')
    cols = [('Activity / behaviour', 0.17), ('Number\n(count)', 0.07), ('Actor type\n(student, staff,\nvisitor)', 0.10),
            ('Gender\n(M / F)', 0.08), ('Age group\n(estimate)', 0.08), ('Timing\n(clock time)', 0.08),
            ('Duration\n(seen in how\nmany scans)', 0.09), ('Where\n(area + spot)', 0.12), ('Notes and pictures\n(photo no.)', 0.15)]
    acts = ['Studying (S)', 'Talking (T)', 'On the phone (P)', 'Looking for books (L)', 'Other: eating, resting (O)',
            'Belongings only (B)', 'Walking through', 'Standing / waiting', 'Sitting on the floor / between shelves', 'Group work',
            '', '', '']
    x0, ytop, rh = 0.03, top, 0.05
    x = x0
    for name, w in cols:
        fig.add_artist(Rectangle((x, ytop - 0.07), w, 0.07, transform=fig.transFigure, fc='#e8eef9', ec='black', lw=0.7))
        fig.text(x + 0.004, ytop - 0.035, name, fontsize=9.5, weight='bold', va='center')
        x += w
    for i, a in enumerate(acts):
        y = ytop - 0.07 - (i + 1) * rh; x = x0
        for j, (name, w) in enumerate(cols):
            fig.add_artist(Rectangle((x, y), w, rh, transform=fig.transFigure, fill=False, ec='black', lw=0.6))
            if j == 0 and a: fig.text(x + 0.004, y + rh / 2, a, fontsize=10, va='center')
            x += w
    fig.text(0.03, 0.03, 'Example: Talking | 4 | students | 3 M, 1 F | 18-25 | 14:10 | 2 scans | B, between shelves near B-6 | photo 12 '
             '(no faces)', fontsize=9.5, color='#444444')
    pdf.savefig(fig)
    if preview: fig.savefig(f'{preview}_{n}.png', dpi=100)
    plt.close(fig)


def notes_page(pdf, n):
    fig = plt.figure(figsize=(8.27, 11.69))
    top = header(fig, f'Observation notes and physical traces  (sheet {n} of 7)', 'Once per scan, for the whole floor.')
    fig.text(0.03, top, 'A. What happened (short sentences, in time order)', fontsize=10, weight='bold', va='center')
    fig.text(0.53, top, 'Question / comment: why might this happen?\nWhat does it say about the space?', fontsize=8.3, weight='bold',
             va='center')
    for i in range(13):
        y = top - 0.035 - i * 0.026
        fig.add_artist(plt.Line2D([0.03, 0.49], [y, y], transform=fig.transFigure, lw=0.5, color='#777777'))
        fig.add_artist(plt.Line2D([0.53, 0.97], [y, y], transform=fig.transFigure, lw=0.5, color='#777777'))
    fig.text(0.03, 0.435, 'B. Physical traces: tick what you see, write where, and photograph it (no faces)', fontsize=10, weight='bold')
    traces = [('By-products of use', [('Leftovers', 'cups, food, rubbish left on tables'), ('Erosion', 'worn or damaged furniture, '
                                                                                                         'marks on the floor'),
                                      ('Missing traces', 'places nobody seems to use')]),
              ('Adaptations for use', [('Props', 'chargers, extension leads, cushions brought in'),
                                       ('Separations', 'bags or books used as a barrier between people'),
                                       ('Connections', 'chairs moved, tables pushed together')]),
              ('Displays of self', [('Personalisation / territory', 'jackets, bags or books left to keep a seat'),
                                    ('Group membership', 'the same group at the same tables')]),
              ('Public messages', [('Official', 'library signs, e.g. "quiet area"'), ('Unofficial', 'notes left by students'),
                                   ('Illegitimate', 'writing on tables or walls')])]
    y = 0.405
    for head, items in traces:
        fig.text(0.03, y, head, fontsize=9, weight='bold', color=BLUE); y -= 0.024
        for name, ex in items:
            fig.add_artist(Rectangle((0.035, y - 0.008), 0.013, 0.013 * 0.707, transform=fig.transFigure, fill=False, lw=0.8))
            fig.text(0.055, y, f'{name}: ', fontsize=8.5, weight='bold', va='center')
            fig.text(0.24, y, ex, fontsize=8.3, va='center', color='#333333')
            fig.text(0.62, y, 'where: ____________________  photo no.: ______', fontsize=8.3, va='center')
            y -= 0.022
        y -= 0.006
    pdf.savefig(fig)
    if preview: fig.savefig(f'{preview}_{n}.png', dpi=100)
    plt.close(fig)


bg = L.background(dxf, (X0 - 2, X1 + 2, Y0 - 2, Y1 + 2))
pdf = PdfPages(out_pdf)
map_page(pdf, 1, ['A', 'E'], 'port', bg, 'west half, areas A and E')
map_page(pdf, 2, ['D', 'B', 'C'], 'land', bg, 'east half, areas D, B and C')
table_page(pdf, 3)
pdf.close()
print('written', out_pdf)
