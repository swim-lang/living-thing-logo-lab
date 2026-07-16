"""Render a seamlessly looping morph animation of the Living Thing logo organism.

Ports the shape math from living-thing-logo-lab.html 1:1. Every animated term
(drift, breath, and the slider morphs) is a sinusoid completing an integer
number of cycles over the loop, so frame 0 == frame N exactly.
"""
import math
import subprocess
import sys
from pathlib import Path

from PIL import Image, ImageDraw
from imageio_ffmpeg import get_ffmpeg_exe

TAU = math.tau

# --- genome (identical to ORIGIN_GENOME in the tool) ---
HARMONICS = [(2, 0.72, 1.15), (3, 1.00, 3.85), (5, 0.34, 0.90), (7, 0.16, 5.05)]
BUMPS = [(9, 0.62, 2.70), (13, 0.38, 0.60)]
ASYM_PHI = 2.40

PAPER = (253, 253, 252)
INK = (10, 10, 10)

T_SECONDS = 10.0
N_SAMPLES = 900  # contour samples per frame


PROFILE = 'calm'  # set via CLI: calm | dramatic


def morphed_params(u):
    """Slider values as loop-safe sinusoids around the tool's defaults."""
    if PROFILE == 'dramatic':
        return {
            'exp': 60 + 34 * math.sin(TAU * 1 * u + 0.7) + 8 * math.sin(TAU * 3 * u + 1.9),
            'com': 50 + 40 * math.sin(TAU * 2 * u + 4.0),
            'asy': 50 + 45 * math.sin(TAU * 2 * u + 2.1),
            'flo': 45 + 35 * math.sin(TAU * 2 * u + 1.2),
            'bmp': 45 + 40 * math.sin(TAU * 3 * u + 5.3),
        }
    return {
        'exp': 74 + 16 * math.sin(TAU * 1 * u + 0.7),
        'com': 38 + 20 * math.sin(TAU * 1 * u + 4.0),
        'asy': 30 + 20 * math.sin(TAU * 2 * u + 2.1),
        'flo': 55 + 16 * math.sin(TAU * 2 * u + 1.2),
        'bmp': 30 + 20 * math.sin(TAU * 2 * u + 5.3),
    }


def shape_radius(theta, u, p):
    A = 0.10 + (p['exp'] / 100) * 0.62
    c = p['com'] / 100
    breath = 1 + math.sin(TAU * 2 * u) * 0.045

    # No rotation: instead of a revolving phase drift, each gene's phase
    # sways around its home position (loop-safe, integer frequency).
    wob = 0.75 if PROFILE == 'dramatic' else 0.30

    def wobble(k):
        return wob * math.sin(TAU * u + k * 1.7)

    s = 0.0
    for k, w, phi in HARMONICS:
        wc = (1.15 - c * 0.45) if k <= 3 else (0.15 + c * 1.5)
        s += w * wc * math.sin(k * theta + phi + wobble(k))
    s += (p['asy'] / 100) * 0.85 * math.sin(theta + ASYM_PHI + wobble(1))

    flow_exp = 1.9 - (p['flo'] / 100) * 1.25
    s = math.copysign(abs(s * 0.5) ** flow_exp, s) * 2

    b = sum(gw * math.sin(gk * theta + gphi + wobble(gk)) for gk, gw, gphi in BUMPS)
    s += (p['bmp'] / 100) * 0.55 * b

    return max(0.12, 1 + A * s * 0.5) * breath


def unit_points(u):
    p = morphed_params(u)
    pts = []
    for i in range(N_SAMPLES):
        th = TAU * i / N_SAMPLES
        r = shape_radius(th, u, p)
        pts.append((math.cos(th) * r, math.sin(th) * r))
    return pts


def compute_fit(n_dense=600):
    """One transform for the whole loop: center of the union bounding box
    plus the max reach from it, so the mark stays inside a fixed safe
    square without per-frame re-zooming that would fight the breathing."""
    lo_x = lo_y = math.inf
    hi_x = hi_y = -math.inf
    frames = [unit_points(f / n_dense) for f in range(n_dense)]
    for pts in frames:
        for x, y in pts:
            lo_x, hi_x = min(lo_x, x), max(hi_x, x)
            lo_y, hi_y = min(lo_y, y), max(hi_y, y)
    cx, cy = (lo_x + hi_x) / 2, (lo_y + hi_y) / 2
    m = max(math.hypot(x - cx, y - cy) for pts in frames for x, y in pts)
    return cx, cy, m


def render_frame(u, size, fit, supersample=2):
    cx0, cy0, m = fit
    ss = size * supersample
    img = Image.new('RGB', (ss, ss), PAPER)
    draw = ImageDraw.Draw(img)
    k = ss * 0.42 / m  # mark reaches at most 84% of the square
    pts = [(ss / 2 + (x - cx0) * k, ss / 2 + (y - cy0) * k) for x, y in unit_points(u)]
    draw.polygon(pts, fill=INK)
    return img.resize((size, size), Image.LANCZOS)


def render_sequence(out_dir, size, fps, fit):
    out_dir.mkdir(parents=True, exist_ok=True)
    n = int(round(T_SECONDS * fps))
    for f in range(n):
        render_frame(f / n, size, fit).save(out_dir / f'{f:04d}.png')
        if f % 50 == 0:
            print(f'  frame {f}/{n}', flush=True)
    return n


def main():
    global PROFILE
    out = Path('/Users/kiraknoop/Desktop/Claude/LivingThing/exports')
    out.mkdir(parents=True, exist_ok=True)
    work = Path(sys.argv[1]) if len(sys.argv) > 1 else Path('.')
    PROFILE = sys.argv[2] if len(sys.argv) > 2 else 'calm'
    tag = '' if PROFILE == 'calm' else f'-{PROFILE}'
    print(f'profile: {PROFILE}')

    print('computing square fit across the loop...')
    fit = compute_fit()

    # --- MP4: 1080px @ 30fps ---
    print('rendering mp4 frames...')
    mp4_frames = work / f'frames_mp4{tag}'
    render_sequence(mp4_frames, 1080, 30, fit)
    ffmpeg = get_ffmpeg_exe()
    mp4_path = out / f'living-thing-morph-loop{tag}-1080.mp4'
    subprocess.run([
        ffmpeg, '-y', '-framerate', '30', '-i', str(mp4_frames / '%04d.png'),
        '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-crf', '18',
        '-movflags', '+faststart', str(mp4_path),
    ], check=True, capture_output=True)
    print('wrote', mp4_path)

    # --- GIF: 540px @ 25fps, infinite loop ---
    print('rendering gif frames...')
    n = int(round(T_SECONDS * 25))
    frames = [render_frame(f / n, 540, fit).convert('P', palette=Image.ADAPTIVE, colors=64)
              for f in range(n)]
    gif_path = out / f'living-thing-morph-loop{tag}-540.gif'
    frames[0].save(gif_path, save_all=True, append_images=frames[1:],
                   duration=40, loop=0, optimize=True)
    print('wrote', gif_path)


if __name__ == '__main__':
    main()
