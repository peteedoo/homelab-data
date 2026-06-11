# petee-hand

Petee's handwriting turned into a font, built entirely locally (no third-party services).

## Pipeline
1. **`template.html` / `template2.html`** — printable character sheets. Fill in black pen, photograph flat & overhead with the four corner marks in frame.
2. **`dewarp.py`** — rotate, find the page, perspective-correct to a flat upright rectangle.
3. **`segment.py`** — threshold the ink, cluster it onto the row/column grid, cut and clean each cell into a glyph bitmap (`glyphs/u*.pbm`).
4. **potrace** — vectorize each glyph to SVG.
5. **`build_font.py`** — assemble `PeteeHand.ttf` with fontforge (per-class vertical metrics: caps, x-height, ascenders, descenders).

Env: `~/.venvs/petefont` (opencv, numpy, pillow). Tools: potrace, fontforge, imagemagick (brew).

Run: `python segment.py && (cd glyphs && for f in *.pbm; do potrace -s "$f" -o "svg/${f%.pbm}.svg"; done) && fontforge -script build_font.py`

## Status
- **`build/PeteeHand.ttf` / `.woff2`** — the live font: A–Z, a–z, 0–9, `! ? ( # $ @`. Installed at `~/Library/Fonts/`, served on petee.me, applied to the salutation + signature.
- **Don't put printed guide letters inside the writing cells** (the v2 `template2.html` did, and they bled into the ink and scrambled the scan). Faint blue *lines* are fine; gray *letters* are not.
- Parked: a v3 sheet (grid + lines only + a center tick, no printed letters) would beat v1 and finally land the period/comma/apostrophe.
