# Living Thing — Logo Organism

An interactive, black-and-white generative logo lab for the Living Thing brand.

The mark has a fixed "genome" of radial harmonics that defines its identity; the
sliders (Expression, Complexity, Asymmetry, Flow, Bump, Breath, Drift) only change
how that genome is expressed — so every pose is a different individual of the same
species. Click the organism (or **Variation**) to breed a new specimen; **Origin**
returns to the canonical form. Every pose is centered and constrained to a square,
and exports as print-ready SVG or 1024px PNG.

**Use it:** open `index.html` in any browser — no build, no dependencies.

`render_morph_loop.py` renders the seamlessly looping morph animation in
`exports/` (requires Pillow + imageio-ffmpeg).
