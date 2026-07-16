"""Export bred specimens of the Living Thing logo as SVGs.

Ports the tool's math 1:1 (index.html): the fixed genome defines the species,
each specimen is one Variation-button breed away from the origin. Seeded RNG
so the set is reproducible. Every mark is centered and square-constrained
(max reach 84% of the viewBox), solid #0a0a0a fill.

Usage: python3 generate_specimens.py [count]
"""
import copy
import math
import random
import sys
from pathlib import Path

TAU = math.tau

ORIGIN_GENOME = {
    'harmonics': [[2, 0.72, 1.15], [3, 1.00, 3.85], [5, 0.34, 0.90], [7, 0.16, 5.05]],
    'bumps': [[9, 0.62, 2.70], [13, 0.38, 0.60]],
    'asymPhi': 2.40,
}
PARAMS = {'exp': 74, 'com': 38, 'asy': 30, 'flo': 55, 'bmp': 30}
SIZE = 512
N_SAMPLES = 180


def breed(rng):
    g = copy.deepcopy(ORIGIN_GENOME)
    for h in g['harmonics']:
        h[2] += (rng.random() - 0.5) * 0.8
        h[1] = max(0.08, h[1] * (0.88 + rng.random() * 0.24))
    for b in g['bumps']:
        b[2] += (rng.random() - 0.5) * 0.9
        b[1] = max(0.08, b[1] * (0.88 + rng.random() * 0.24))
    g['asymPhi'] += (rng.random() - 0.5) * 1.1
    return g


def shape_radius(theta, g):
    A = 0.10 + PARAMS['exp'] / 100 * 0.62
    c = PARAMS['com'] / 100
    s = 0.0
    for k, w, phi in g['harmonics']:
        wc = (1.15 - c * 0.45) if k <= 3 else (0.15 + c * 1.5)
        s += w * wc * math.sin(k * theta + phi)
    s += PARAMS['asy'] / 100 * 0.85 * math.sin(theta + g['asymPhi'])
    flow_exp = 1.9 - PARAMS['flo'] / 100 * 1.25
    s = math.copysign(abs(s * 0.5) ** flow_exp, s) * 2
    b = sum(w * math.sin(k * theta + phi) for k, w, phi in g['bumps'])
    s += PARAMS['bmp'] / 100 * 0.55 * b
    return max(0.12, 1 + A * s * 0.5)


def specimen_points(g):
    pts = []
    for i in range(N_SAMPLES):
        th = TAU * i / N_SAMPLES
        r = shape_radius(th, g)
        pts.append((math.cos(th) * r, math.sin(th) * r))
    return pts


def square_fit(pts):
    xs, ys = [p[0] for p in pts], [p[1] for p in pts]
    cx, cy = (min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2
    m = max(math.hypot(x - cx, y - cy) for x, y in pts)
    return cx, cy, m


def path_data(pts):
    """Catmull-Rom -> cubic bezier through the closed loop (same as the tool)."""
    n = len(pts)
    f = lambda v: f'{v:.2f}'
    d = f'M {f(pts[0][0])} {f(pts[0][1])} '
    for i in range(n):
        p0, p1, p2, p3 = pts[i - 1], pts[i], pts[(i + 1) % n], pts[(i + 2) % n]
        d += (f'C {f(p1[0] + (p2[0] - p0[0]) / 6)} {f(p1[1] + (p2[1] - p0[1]) / 6)} '
              f'{f(p2[0] - (p3[0] - p1[0]) / 6)} {f(p2[1] - (p3[1] - p1[1]) / 6)} '
              f'{f(p2[0])} {f(p2[1])} ')
    return d + 'Z'


def specimen_svg(g):
    pts = specimen_points(g)
    cx, cy, m = square_fit(pts)
    k = SIZE * 0.42 / m
    px = [((x - cx) * k + SIZE / 2, (y - cy) * k + SIZE / 2) for x, y in pts]
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {SIZE} {SIZE}" '
            f'width="{SIZE}" height="{SIZE}"><path fill="#0a0a0a" d="{path_data(px)}"/></svg>')


def main():
    count = int(sys.argv[1]) if len(sys.argv) > 1 else 10
    out = Path(__file__).parent / 'exports' / 'specimens'
    out.mkdir(parents=True, exist_ok=True)
    for i in range(1, count + 1):
        rng = random.Random(100 + i)
        svg = specimen_svg(breed(rng))
        path = out / f'living-thing-specimen-{i:02d}.svg'
        path.write_text(svg)
        print('wrote', path.name)


if __name__ == '__main__':
    main()
