"""Llavero articulado "LIS" (print-in-place) -> STL para Ultimaker Cura.

Uso:  python3 make_llavero.py [TEXTO]      (por defecto LIS)
Salida: llavero_<TEXTO>.stl  (mm, impreso plano: z=0 es la cama)

Cada letra es una pieza; entre letras hay una bisagra con pin vertical que se
imprime ya montada (holgura CLEAR). Las letras giran en horizontal.
"""
import sys
import numpy as np
import trimesh
from shapely.geometry import Polygon, Point, box
from shapely.ops import unary_union
from matplotlib.textpath import TextPath
from matplotlib.font_manager import FontProperties

TEXT = (sys.argv[1] if len(sys.argv) > 1 else "LIS").upper()
FONT = "/usr/share/fonts/opentype/inter/Inter-Black.otf"

H = 20.0          # alto de letra (mm)
T = 6.0           # grosor total (mm)
GAP = 5.8         # separacion entre letras (mm)
CLEAR = 0.35      # holgura bisagra (mm)
PIN_R = 1.3       # radio del pin
RING_R = 2.6      # radio del anillo de la bisagra
TAB_LO = 2.6      # grosor de la pestana inferior (la que lleva el pin)
LAYER_GAP = 0.4   # aire entre pestana inferior y superior
LOOP_R, LOOP_HOLE, LOOP_T = 5.0, 2.3, 4.0


def glyph(ch):
    tp = TextPath((0, 0), ch, size=100, prop=FontProperties(fname=FONT))
    polys = [Polygon(p) for p in tp.to_polygons() if len(p) > 2]
    # el contorno mas grande es el exterior; los demas son agujeros
    polys.sort(key=lambda p: -p.area)
    shape = polys[0]
    for p in polys[1:]:
        shape = shape.difference(p) if shape.contains(p) else shape.union(p)
    minx, miny, maxx, maxy = shape.bounds
    s = H / (maxy - miny)
    from shapely import affinity
    shape = affinity.translate(shape, -minx, -miny)
    return affinity.scale(shape, s, s, origin=(0, 0))


def prism(geom, z0, z1):
    parts = geom.geoms if hasattr(geom, "geoms") else [geom]
    ms = []
    for g in parts:
        m = trimesh.creation.extrude_polygon(g, z1 - z0)
        m.apply_translation([0, 0, z0])
        ms.append(m)
    return trimesh.util.concatenate(ms)


def cyl(x, y, r, z0, z1, n=48):
    m = trimesh.creation.cylinder(radius=r, height=z1 - z0, sections=n)
    m.apply_translation([x, y, (z0 + z1) / 2])
    return m


def cone(x, y, r0, r1, z0, z1, n=48):
    # cono truncado construido a mano
    ang = np.linspace(0, 2 * np.pi, n, endpoint=False)
    bot = np.c_[x + r0 * np.cos(ang), y + r0 * np.sin(ang), np.full(n, z0)]
    top = np.c_[x + r1 * np.cos(ang), y + r1 * np.sin(ang), np.full(n, z1)]
    v = np.vstack([bot, top, [[x, y, z0]], [[x, y, z1]]])
    f = []
    for i in range(n):
        j = (i + 1) % n
        f += [[i, j, n + j], [i, n + j, n + i]]
        f += [[2 * n, j, i]]
        f += [[2 * n + 1, n + i, n + j]]
    return trimesh.Trimesh(v, f)


def union(meshes):
    return trimesh.boolean.union(meshes, engine="manifold")


def reach_x(shape, y, x_from, x_to, depth=1.5):
    """Recorre x desde x_from hacia x_to hasta tocar la letra a altura y;
    devuelve x metido 'depth' mm dentro."""
    step = 0.25 if x_to > x_from else -0.25
    x = x_from
    while (x - x_to) * step < 0:
        if shape.intersects(box(x - 0.1, y - 0.6, x + 0.1, y + 0.6)):
            return x + np.sign(step) * depth
        x += step
    return x_to


# --- colocar letras ---
shapes, x = [], 0.0
for ch in TEXT:
    g = glyph(ch)
    from shapely import affinity
    g = affinity.translate(g, x, 0)
    shapes.append(g)
    x = g.bounds[2] + GAP

YJ = H / 2
bodies = [[prism(g, 0, T)] for g in shapes]

for i in range(len(shapes) - 1):
    A, B = shapes[i], shapes[i + 1]
    xj = (A.bounds[2] + B.bounds[0]) / 2
    # pestana A (inferior, lleva el pin)
    xa = reach_x(A, YJ, xj, A.bounds[0])
    tabA = unary_union([box(xa, YJ - RING_R, xj, YJ + RING_R),
                        Point(xj, YJ).buffer(RING_R, 48)])
    bodies[i].append(prism(tabA, 0, TAB_LO))
    bodies[i].append(cyl(xj, YJ, PIN_R, 0, T))
    bodies[i].append(cone(xj, YJ, PIN_R, PIN_R + 1.0, T, T + 1.0))
    # pestana B (superior, con agujero)
    xb = reach_x(B, YJ, xj, B.bounds[2])
    zlo = TAB_LO + LAYER_GAP
    ring = cyl(xj, YJ, RING_R, zlo, T)
    bar = prism(box(xj, YJ - RING_R, xb, YJ + RING_R), zlo, T)
    tabB = union([ring, bar])
    hole = cyl(xj, YJ, PIN_R + CLEAR, zlo - 0.1, T + 0.1)
    tabB = trimesh.boolean.difference([tabB, hole], engine="manifold")
    bodies[i + 1].append(tabB)

# anilla para el aro (en la primera letra)
L = shapes[0]
cx, cy = L.bounds[0] - 3.2, H - 4.5
loop = trimesh.boolean.difference(
    [cyl(cx, cy, LOOP_R, 0, LOOP_T), cyl(cx, cy, LOOP_HOLE, -0.1, LOOP_T + 0.1)],
    engine="manifold")
bodies[0].append(loop)

letters = [union(b) for b in bodies]
final = trimesh.util.concatenate(letters)
# centrar en XY y apoyar en z=0
final.apply_translation([-final.centroid[0], -final.centroid[1], 0])
out = f"llavero_{TEXT}.stl"
final.export(out)

comps = final.split(only_watertight=False)
print(out, "dimensiones (mm):", np.round(final.extents, 1))
print("watertight por pieza:", [c.is_watertight for c in comps])
print("piezas independientes (esperado", len(TEXT), "):", len(comps))
