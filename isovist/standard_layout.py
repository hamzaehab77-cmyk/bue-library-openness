"""Standard seating layout (site visit, Nov 2026): every table is a 1.6 x 1.1 m four-seater, two chairs on each long side.
Positions come from the hand-marked plan photo (fitted to the CAD with a homography on 15 columns, residual < 3.5 px)
and are then aligned and spaced evenly. Tables next to a window or the atrium edge keep 0.40 m clearance.

usage: python standard_layout.py <plan.dxf> <out_seats.csv> <preview.png>
writes the seat list (code, zone, x_m, y_m, facing_deg ...) and a preview of the coded plan."""
import sys, math
import numpy as np, pandas as pd

T_LONG, T_SHORT = 1.6, 1.1          # table size (m)
SEAT_ACROSS = T_SHORT / 2 + 0.25    # seat point = chair centre, 0.25 m off the long edge
SEAT_ALONG = 0.40                   # two chairs per side, +-0.40 m from the table centre
CLEAR = 0.40                        # clearance to windows / atrium edge

GRID_X = [797.73, 800.73, 803.73, 806.73]          # A and E: 3.0 m spacing, symmetric about the columns at 796.23/802.23/808.23
# inner face of the south facade behind area E (measured per table): it steps in by ~0.6 m behind the left pair,
# so the window row is two aligned pairs, each 0.40 m from its own facade face (matches the marked plan)
FACADE_E = {797.73: -1338.722, 800.73: -1338.722, 803.73: -1338.132, 806.73: -1338.132}
VOID_D = -1325.01                                   # edge of the atrium void beside area D
ROW_D = VOID_D - CLEAR - T_LONG / 2                 # = -1326.21, also the column line
VOID_D_N = -1318.77                                 # opposite (north) edge of the same void
ROW_D_N = VOID_D_N + CLEAR + T_LONG / 2             # mirror of the D row across the void (added on request)
# (zone, centre x, centre y, long axis 'y' or 'x')
TABLES = (
    [('A', x, -1317.86, 'y') for x in GRID_X] + [('A', x, -1320.46, 'y') for x in GRID_X] +
    [('B', x, -1317.26, 'x') for x in (818.24, 822.13, 824.24, 828.13, 830.24, 834.13)] +   # unchanged centres
    [('C', x, ROW_D, 'y') for x in (818.83, 821.63)] + [('C', x, -1323.50, 'y') for x in (818.83, 821.63, 824.43)] +
    [('D', x, ROW_D_N, 'y') for x in (810.01, 812.81, 815.61)] +
    [('D', x, ROW_D, 'y') for x in (810.01, 812.81, 815.61)] + [('D', 811.28, -1330.20, 'y')] +
    [('E', x, FACADE_E[x] + CLEAR + T_LONG / 2, 'y') for x in GRID_X] +
    [('E', x, -1332.70, 'y') for x in GRID_X] +
    [('E', x, -1330.20, 'y') for x in GRID_X]
)


def seats_of(zone, cx, cy, axis):
    out = []
    for side in (-1, 1):
        for along in (-SEAT_ALONG, SEAT_ALONG):
            if axis == 'y':   # long side runs along y, chairs left and right
                out.append((cx + side * SEAT_ACROSS, cy + along, 0.0 if side < 0 else 180.0))
            else:
                out.append((cx + along, cy + side * SEAT_ACROSS, 90.0 if side < 0 else 270.0))
    return out


def build():
    rows = []
    for t, (zone, cx, cy, axis) in enumerate(TABLES):
        for x, y, f in seats_of(zone, cx, cy, axis):
            rows.append(dict(zone=zone, table=t, x_m=round(x, 3), y_m=round(y, 3), facing_deg=f,
                             table_cx=cx, table_cy=round(cy, 3), table_axis=axis))
    s = pd.DataFrame(rows)
    out = []
    for zone, g in s.groupby('zone', sort=True):
        # numbering: rows of tables top to bottom (a row may be slightly staggered, as by the E facade);
        # within a row, the upper chairs of all its tables left to right, then the lower chairs
        g = g.copy()
        cys = sorted(g.table_cy.unique(), reverse=True); rid, cur, last = {}, -1, None
        for c in cys:
            if last is None or last - c > 1.0: cur += 1
            rid[c] = cur; last = c
        g['trow'] = g.table_cy.map(rid)
        g['upper'] = (g.y_m < g.table_cy).astype(int)          # 0 = upper chair (larger y), 1 = lower
        g = g.sort_values(['trow', 'upper', 'x_m']); g['n'] = range(1, len(g) + 1)
        out.append(g)
    s = pd.concat(out)
    s['code'] = s.zone + '-' + s.n.astype(str)
    s['zone_type'] = 'Open-plan'; s['furniture'] = 'table 1.6x1.1'
    r = np.radians(s.facing_deg); s['facing_dx'] = np.cos(r).round(3); s['facing_dy'] = np.sin(r).round(3)
    s['dist_to_table_m'] = 0.25
    return s[['code', 'zone', 'zone_type', 'x_m', 'y_m', 'furniture', 'facing_deg', 'facing_dx', 'facing_dy',
              'dist_to_table_m', 'table', 'table_cx', 'table_cy', 'table_axis']]


def table_poly(cx, cy, axis):
    a, b = (T_SHORT / 2, T_LONG / 2) if axis == 'y' else (T_LONG / 2, T_SHORT / 2)
    return [(cx - a, cy - b), (cx + a, cy - b), (cx + a, cy + b), (cx - a, cy + b), (cx - a, cy - b)]


def chair_poly(x, y, facing, w=0.42, d=0.42):
    """square chair centred on the seat point, back line on the side away from the table."""
    r = math.radians(facing); ux, uy = math.cos(r), math.sin(r); vx, vy = -uy, ux
    pts = [(x + ux * i * d / 2 + vx * j * w / 2, y + uy * i * d / 2 + vy * j * w / 2) for i, j in ((-1, -1), (1, -1), (1, 1), (-1, 1), (-1, -1))]
    back = [(x - ux * (d / 2 - 0.07) + vx * w / 2, y - uy * (d / 2 - 0.07) + vy * w / 2),
            (x - ux * (d / 2 - 0.07) - vx * w / 2, y - uy * (d / 2 - 0.07) - vy * w / 2)]
    return pts, back


# old study furniture in these boxes is replaced by the standard tables
REGIONS = {'A': (796.6, 809.2, -1321.5, -1316.9), 'B': (816.5, 835.0, -1318.6, -1315.9),
           'C': (817.5, 825.5, -1328.0, -1322.5), 'D': (809.5, 816.5, -1332.5, -1325.1), 'E': (795.6, 808.4, -1339.0, -1327.8)}


def is_old_furniture(e, b):
    c = b.center
    if not any(x0 <= c.x <= x1 and y0 <= c.y <= y1 for x0, x1, y0, y1 in REGIONS.values()):
        return False
    if e.dxftype() == 'INSERT' and e.dxf.layer == 'FUR' and e.dxf.name in ('tttttt', 'COMPUTER  TABLE'):
        return True
    x0, x1, y0, y1 = REGIONS['C']      # round tables and their chairs in C
    return e.dxf.layer == 'p' and e.dxftype() in ('CIRCLE', 'ARC', 'LWPOLYLINE') and x0 <= c.x <= x1 and y0 <= c.y <= y1


def background(dxf, W):
    """plan linework inside window W = (x0, x1, y0, y1), without dimensions, text and the old study furniture."""
    import ezdxf
    from ezdxf import bbox
    sys.path.insert(0, __file__.rsplit('\\', 1)[0])
    from isovist import polylines_of
    doc = ezdxf.readfile(dxf); cache = bbox.Cache(); out = []
    for e in doc.modelspace():
        if e.dxf.layer in ('dim-in', 'ax', 'hid', 'TXT', 'Defpoints'): continue
        try:
            b = bbox.extents([e], cache=cache)
        except Exception:
            continue
        if not b.has_data or b.extmax.x < W[0] or b.extmin.x > W[1] or b.extmax.y < W[2] or b.extmin.y > W[3]: continue
        if is_old_furniture(e, b): continue
        try:
            ps = polylines_of([e])
        except Exception:
            continue
        out += [np.array(p) for p in ps if len(p) > 1]
    return out


if __name__ == '__main__':
    dxf, out_csv, out_png = sys.argv[1:4]
    s = build()
    s.to_csv(out_csv, index=False)
    print(s.groupby('zone').size().to_dict(), 'total', len(s))

    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    W = (786, 836.5, -1340.2, -1302)
    fig, ax = plt.subplots(figsize=(16, 12.3))
    for a in background(dxf, W):
        ax.plot(a[:, 0], a[:, 1], color='#9a9a9a', lw=0.45)
    for t in TABLES:
        a = np.array(table_poly(*t[1:])); ax.plot(a[:, 0], a[:, 1], color='k', lw=0.8)
    for _, r in s.iterrows():
        c, back = chair_poly(r.x_m, r.y_m, r.facing_deg)
        a = np.array(c); ax.plot(a[:, 0], a[:, 1], color='#555555', lw=0.5)
        a = np.array(back); ax.plot(a[:, 0], a[:, 1], color='#555555', lw=0.9)
        ax.text(r.x_m, r.y_m, r.code.split('-')[1], color='red', fontsize=6.3, ha='center', va='center', weight='bold', zorder=5)
    for z, g in s.groupby('zone'):
        lx, ly = {'A': (802.2, -1315.6), 'B': (826.2, -1314.9), 'C': (821.2, -1328.2), 'D': (812.8, -1328.4), 'E': (802.2, -1334.6)}[z]
        ax.text(lx, ly, z, color='blue', fontsize=20, weight='bold', ha='center', va='center')
    ax.set_xlim(W[0], W[1]); ax.set_ylim(W[2], W[3]); ax.set_aspect('equal'); ax.axis('off')
    fig.savefig(out_png, dpi=150, bbox_inches='tight')
