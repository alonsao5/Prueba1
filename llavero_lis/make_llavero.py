"""Llavero articulado 3D "LIS" (letras gruesas, de pie, print-in-place) -> STL.

Uso:  python3 make_llavero.py [TEXTO]      (por defecto LIS)

- Cada letra es un bloque grueso que se imprime DE PIE (z = altura de la letra).
- Entre letras, detras, hay una bisagra de pin VERTICAL: el llavero se curva en horizontal.
- La bisagra se imprime ya montada (holgura CLEAR). Sin soportes.
"""
import sys
import numpy as np
import trimesh
from shapely import affinity
from shapely.geometry import Polygon, box
from matplotlib.textpath import TextPath
from matplotlib.font_manager import FontProperties

TEXT = (sys.argv[1] if len(sys.argv) > 1 else "LIS").upper()
FONT = "/usr/share/fonts/opentype/inter/Inter-Black.otf"

H = 24.0          # alto de letra (mm)
D = 11.0          # profundidad / grosor de la letra (mm)
GAP = 1.6         # hueco entre letras (mm)
FLAT = 0.8        # base plana: recorta la parte curva inferior
CLEAR = 0.35      # holgura bisagra
PIN_R = 1.3
RING_R = 2.6
POCKET_R = RING_R + 0.4
YP = D - 4.0      # posicion del pin en profundidad (cerca de la parte trasera)
Z_A1 = 4.0        # pestana A (con pin): z 0..4
Z_B0, Z_B1 = 4.4, 9.0   # pestana B (con agujero): z 4.4..9
Z_HEAD = 10.2     # tope del pin
LOOP_R, LOOP_HOLE, LOOP_T = 5.0, 2.3, 4.0


def glyph(ch):
    tp = TextPath((0, 0), ch, size=100, prop=FontProperties(fname=FONT))
    polys = sorted((Polygon(p) for p in tp.to_polygons() if len(p) > 2), key=lambda p: -p.area)
    shape = polys[0]
    for p in polys[1:]:
        shape = shape.difference(p) if shape.contains(p) else shape.union(p)
    minx, miny, maxx, maxy = shape.bounds
    s = (H + FLAT) / (maxy - miny)
    shape = affinity.scale(affinity.translate(shape, -minx, -miny), s, s, origin=(0, 0))
    shape = shape.intersection(box(-1e3, FLAT, 1e3, 1e3))       # base plana
    return affinity.translate(shape, 0, -FLAT)


def block(shape):
    """Silueta (x, z) extruida en profundidad: cara frontal en y=0, trasera en y=D."""
    parts = shape.geoms if hasattr(shape, "geoms") else [shape]
    ms = [trimesh.creation.extrude_polygon(g, D) for g in parts]
    m = trimesh.util.concatenate(ms)
    m.apply_transform(trimesh.transformations.rotation_matrix(np.pi / 2, [1, 0, 0]))  # (x,y,z)->(x,-z,y)
    m.apply_translation([0, D, 0])
    return m


def cyl(x, y, r, z0, z1, n=48):
    m = trimesh.creation.cylinder(radius=r, height=z1 - z0, sections=n)
    m.apply_translation([x, y, (z0 + z1) / 2])
    return m


def cone(x, y, r0, r1, z0, z1, n=48):
    ang = np.linspace(0, 2 * np.pi, n, endpoint=False)
    bot = np.c_[x + r0 * np.cos(ang), y + r0 * np.sin(ang), np.full(n, z0)]
    top = np.c_[x + r1 * np.cos(ang), y + r1 * np.sin(ang), np.full(n, z1)]
    v = np.vstack([bot, top, [[x, y, z0]], [[x, y, z1]]])
    f = []
    for i in range(n):
        j = (i + 1) % n
        f += [[i, j, n + j], [i, n + j, n + i], [2 * n, j, i], [2 * n + 1, n + i, n + j]]
    return trimesh.Trimesh(v, f)


def union(ms):
    return trimesh.boolean.union(ms, engine="manifold")


def diff(a, *bs):
    return trimesh.boolean.difference([a, *bs], engine="manifold")


# --- colocar letras en x ---
shapes, x = [], 0.0
for ch in TEXT:
    g = glyph(ch)
    g = affinity.translate(g, x, 0)
    shapes.append(g)
    x = g.bounds[2] + GAP

n = len(shapes)
xj = [(shapes[i].bounds[2] + shapes[i + 1].bounds[0]) / 2 for i in range(n - 1)]

letters = []
for i, g in enumerate(shapes):
    m = block(g)
    # 1) huecos (bolsillos) para la bisagra vecina
    if i < n - 1:       # soy A en la bisagra i: bolsillo sobre mi pestana
        m = diff(m, cyl(xj[i], YP, POCKET_R, Z_A1, Z_HEAD + 0.6))
    if i > 0:           # soy B en la bisagra i-1: bolsillos bajo y sobre mi pestana
        m = diff(m, cyl(xj[i - 1], YP, POCKET_R, -0.1, Z_B0),
                 cyl(xj[i - 1], YP, POCKET_R, Z_B1, Z_HEAD + 0.6))
    # 2) pestanas
    add = [m]
    if i < n - 1:       # A: disco + pin + cabeza
        add += [cyl(xj[i], YP, RING_R, 0, Z_A1), cyl(xj[i], YP, PIN_R, 0, Z_B1 + 0.1),
                cone(xj[i], YP, PIN_R, PIN_R + 1.0, Z_B1, Z_HEAD)]
    if i > 0:           # B: anillo
        add += [cyl(xj[i - 1], YP, RING_R, Z_B0, Z_B1)]
    m = union(add)
    if i > 0:           # agujero del pin (con holgura)
        m = diff(m, cyl(xj[i - 1], YP, PIN_R + CLEAR, Z_B0 - 0.1, Z_B1 + 0.1))
    letters.append(m)

# anilla del llavero (en la primera letra, a la izquierda, arriba)
b0 = shapes[0].bounds
cx, cz = b0[0] - 3.2, H - 5.2
loop = cyl(0, 0, LOOP_R, 0, LOOP_T)
loop.apply_transform(trimesh.transformations.rotation_matrix(np.pi / 2, [1, 0, 0]))
hole = cyl(0, 0, LOOP_HOLE, -0.1, LOOP_T + 0.1)
hole.apply_transform(trimesh.transformations.rotation_matrix(np.pi / 2, [1, 0, 0]))
loop = diff(loop, hole)
loop.apply_translation([cx, D / 2 + LOOP_T / 2 - 1.0, cz])
letters[0] = union([letters[0], loop])

final = trimesh.util.concatenate(letters)
final.apply_translation([-final.centroid[0], -final.centroid[1], -final.bounds[0][2]])
out = f"llavero_{TEXT}.stl"
final.export(out)

comps = final.split(only_watertight=False)
print(out, "dimensiones (mm):", np.round(final.extents, 1))
print("letras:", [tuple(np.round(np.diff(np.array(s.bounds).reshape(2, 2), axis=0)[0], 1)) for s in shapes])
print("watertight por pieza:", [c.is_watertight for c in comps])
print("piezas independientes (esperado", n, "):", len(comps))
