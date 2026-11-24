"""Seat isovists for the BUE library first floor.

For every seat in seat_codes_first_floor.csv this script
  1. traces sight lines (rays) from the seat point in all directions until they hit
     something that blocks the view at seated eye height (1.2 m),
  2. joins the ray end points into the isovist polygon and measures its area (A360, m2),
  3. keeps the part of that polygon inside a 170 degree wedge centred on the seat's
     facing direction (A170, m2), and
  4. reports control = A170 / A360.

What blocks the view (layers of "Library floor plans.dwg", exported to DXF):
  OPAQUE  wall, COL (columns), WIN / GLASS / HA / E1 (outer facade: the isovist stops at
          the building envelope), closed doors (one line across each door opening)
  SHELF   tall bookshelves = FUR rectangles 0.6 m deep and 2-4 m long. Opaque when
          --shelves tall (default), ignored when --shelves low. Height to be confirmed on site.
  IGNORED clear internal glazing (layer p), tables, chairs, desks, the round tables,
          the atrium edges (e2, low balustrade), stairs, sanitary fittings, text, hidden lines.
The visible area is also clipped to the building outline, so nothing outside the
facade is ever counted.

usage:
  python isovist.py plan.dxf seats.csv outdir [--shelves tall|low] [--rays 3600]
"""
import argparse, math, os, json
import numpy as np
import pandas as pd
import ezdxf
from ezdxf import bbox, disassemble
from shapely.geometry import LineString, Polygon, Point, MultiPolygon
from shapely.ops import unary_union, polygonize

WINDOW = (783.0, 838.0, -1342.0, -1300.0)          # first floor, DWG units = metres
OPAQUE_LAYERS = {'wall', 'COL', 'WIN', 'GLASS', 'HA', 'E1'}
ENVELOPE_LAYERS = {'wall', 'COL', 'WIN', 'GLASS', 'HA', 'E1'}
FOV = 170.0


# ---------------------------------------------------------------- geometry from the DXF
def in_window(e):
    try:
        b = bbox.extents([e], fast=True)
    except Exception:
        return False
    x0, x1, y0, y1 = WINDOW
    return b.has_data and b.extmin.x < x1 and b.extmax.x > x0 and b.extmin.y < y1 and b.extmax.y > y0


def polylines_of(entities):
    """Flatten entities (blocks exploded, arcs as short chords) to lists of (x, y)."""
    out = []
    for v in disassemble.recursive_decompose(entities):
        if v.dxftype() in ('TEXT', 'MTEXT', 'DIMENSION', 'HATCH', 'ATTRIB', 'ATTDEF', 'POINT'):
            continue
        for prim in disassemble.to_primitives([v], max_flattening_distance=0.01):
            try:
                pts = [(p.x, p.y) for p in prim.vertices()]
            except Exception:
                continue
            if len(pts) > 1:
                out.append(pts)
    return out


def segments_of(polys):
    s = []
    for pts in polys:
        for a, b in zip(pts[:-1], pts[1:]):
            if abs(a[0] - b[0]) + abs(a[1] - b[1]) > 1e-6:
                s.append((a[0], a[1], b[0], b[1]))
    return s


def door_closures(doc, inserts, wall_lines):
    """One line per door leaf in the CLOSED position (hinge -> arc end that lies in the wall line)."""
    walls = unary_union([LineString(p) for p in wall_lines])
    out = []
    for ins in inserts:
        for v in ins.virtual_entities():
            if v.dxftype() != 'ARC':
                continue
            c = v.ocs().to_wcs(v.dxf.center); r = v.dxf.radius     # mirrored doors use an OCS
            pts = list(v.flattening(0.01))
            ends = [pts[0], pts[-1]]
            closed = []
            for p in ends:
                ux, uy = (p.x - c.x) / r, (p.y - c.y) / r
                beyond = Point(c.x + ux * (r + 0.15), c.y + uy * (r + 0.15))   # just past the leaf tip
                if walls.distance(beyond) < 0.12:
                    closed.append(p)
            if len(closed) != 1:      # unclear: block both positions
                closed = ends
            for p in closed:
                out.append((c.x, c.y, p.x, p.y))
    return out


def load_plan(dxf_path, shelves):
    doc = ezdxf.readfile(dxf_path)
    msp = doc.modelspace()
    ents = [e for e in msp if in_window(e)]
    opaque, envelope, shelf_polys, door_inserts = [], [], [], []
    for e in ents:
        lay = e.dxf.layer
        if lay == 'E1' and e.dxftype() == 'LWPOLYLINE':
            continue        # edge of the entrance void (low balustrade): you see across it
        if lay in OPAQUE_LAYERS:
            pl = polylines_of([e])
            opaque += pl
            if lay in ENVELOPE_LAYERS:
                envelope += pl
        elif lay == 'dor' and e.dxftype() == 'INSERT':
            door_inserts.append(e)
        elif lay == 'FUR' and e.dxftype() == 'LWPOLYLINE' and e.closed:
            pts = [(p[0], p[1]) for p in e.get_points('xy')]
            poly = Polygon(pts)
            r = poly.minimum_rotated_rectangle
            xs, ys = r.exterior.coords.xy
            sides = sorted({round(math.dist((xs[i], ys[i]), (xs[i + 1], ys[i + 1])), 2) for i in range(4)})
            if len(sides) == 2 and 0.5 <= sides[0] <= 0.7 and 1.9 <= sides[1] <= 4.1:
                shelf_polys.append(pts + [pts[0]])
    doors = door_closures(doc, door_inserts, opaque)
    seg = segments_of(opaque) + doors
    if shelves == 'tall':
        seg += segments_of(shelf_polys)
    footprint = building_outline(envelope + [[(a, b), (c, d)] for a, b, c, d in doors])
    seg += segments_of([list(footprint.exterior.coords)])
    return dict(segments=np.array(seg, float), opaque=opaque, shelves=shelf_polys, doors=doors,
                footprint=footprint)


def building_outline(lines):
    """Outline of the floor: wall/facade lines thickened by 0.4 m (closes window and door gaps),
    merged, outer edge taken (all holes filled), then shrunk back by 0.4 m."""
    net = unary_union([LineString(p).buffer(0.4) for p in lines if len(p) > 1])
    if isinstance(net, MultiPolygon):
        net = max(net.geoms, key=lambda g: g.area)
    return Polygon(net.exterior).buffer(-0.4)


# ---------------------------------------------------------------- isovists
def isovist(x, y, seg, n_rays, rmax=80.0):
    ang = np.linspace(0, 2 * np.pi, n_rays, endpoint=False)
    dx, dy = np.cos(ang), np.sin(ang)
    ax_, ay_, bx_, by_ = seg.T
    ex, ey = bx_ - ax_, by_ - ay_
    wx, wy = ax_ - x, ay_ - y
    dist = np.full(n_rays, rmax)
    for k in range(0, n_rays, 400):
        rx, ry = dx[k:k + 400, None], dy[k:k + 400, None]
        den = rx * ey - ry * ex
        with np.errstate(divide='ignore', invalid='ignore'):
            t = (wx * ey - wy * ex) / den
            u = (wx * ry - wy * rx) / den
        ok = (np.abs(den) > 1e-12) & (t > 1e-6) & (u >= -1e-9) & (u <= 1 + 1e-9)
        t = np.where(ok, t, np.inf)
        dist[k:k + 400] = np.minimum(dist[k:k + 400], t.min(axis=1))
    pts = np.column_stack([x + dx * dist, y + dy * dist])
    return Polygon(pts).buffer(0), ang, dist


def wedge(x, y, facing_deg, fov=FOV, r=80.0, n=180):
    a0 = math.radians(facing_deg - fov / 2); a1 = math.radians(facing_deg + fov / 2)
    arc = [(x + r * math.cos(a), y + r * math.sin(a)) for a in np.linspace(a0, a1, n)]
    return Polygon([(x, y)] + arc)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('dxf'); ap.add_argument('seats'); ap.add_argument('outdir')
    ap.add_argument('--shelves', choices=['tall', 'low'], default='tall')
    ap.add_argument('--rays', type=int, default=3600)
    a = ap.parse_args()
    os.makedirs(a.outdir, exist_ok=True)
    plan = load_plan(a.dxf, a.shelves)
    fp = plan['footprint']
    seats = pd.read_csv(a.seats)
    rows, polys = [], {}
    for s in seats.itertuples():
        iso, ang, dist = isovist(s.x_m, s.y_m, plan['segments'], a.rays)
        iso = iso.intersection(fp)
        front = iso.intersection(wedge(s.x_m, s.y_m, s.facing_deg))
        A360, A170 = iso.area, front.area
        rows.append(dict(code=s.code, zone=s.zone, x_m=s.x_m, y_m=s.y_m, facing_deg=s.facing_deg,
                         isovist_area_m2=round(A360, 2), area_170_m2=round(A170, 2),
                         control=round(A170 / A360, 4) if A360 > 0 else None,
                         max_radial_m=round(float(dist.max()), 2), mean_radial_m=round(float(dist.mean()), 2)))
        polys[s.code] = iso
    df = pd.DataFrame(rows)
    tag = f'shelves_{a.shelves}'
    df.to_csv(os.path.join(a.outdir, f'isovist_results_{tag}.csv'), index=False)
    with open(os.path.join(a.outdir, f'isovist_polygons_{tag}.geojson'), 'w') as f:
        json.dump({'type': 'FeatureCollection', 'features': [
            {'type': 'Feature', 'properties': {'code': k}, 'geometry': v.__geo_interface__} for k, v in polys.items()]}, f)
    import pickle
    with open(os.path.join(a.outdir, f'plan_{tag}.pkl'), 'wb') as f:
        pickle.dump({k: plan[k] for k in ('opaque', 'shelves', 'doors', 'footprint')}, f)
    print(f'{len(df)} seats  footprint {fp.area:.1f} m2  shelves found {len(plan["shelves"])}  doors {len(plan["doors"])}')
    print(df.groupby('zone')[['isovist_area_m2', 'control']].describe().round(2).to_string())


if __name__ == '__main__':
    main()
