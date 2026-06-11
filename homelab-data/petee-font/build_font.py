#!/usr/bin/env fontforge -script
# Assemble PeteeHand.ttf from traced glyph PNGs. Run: fontforge -script build_font.py
import fontforge, psMat, glob, os

ROOT = os.path.expanduser("~/homelab-data/petee-font")
SVG = ROOT + "/glyphs/svg"
EM, ASCENT, DESCENT = 1000, 800, 200
SB = 33            # side bearing (tightened)
CAP, ASC, XH, DROP = 700, 730, 545, -205

# per-class vertical span [bottom, top] in em units
ASCENDERS = set("bdfhklt")
XHEIGHT   = set("acemnorsuvwxz")
DESCEND   = set("gpqy")
SPAN = {}
for c in "ABCDEFGHIJKLMNOPQRSTUVWXYZ": SPAN[c] = (0, CAP)
for c in "0123456789":                SPAN[c] = (0, 680)
for c in ASCENDERS: SPAN[c] = (0, ASC)
for c in XHEIGHT:   SPAN[c] = (0, XH)
for c in DESCEND:   SPAN[c] = (DROP, XH)
SPAN["i"] = (0, CAP); SPAN["j"] = (DROP, CAP)
SPAN["!"] = (0, CAP); SPAN["?"] = (0, CAP); SPAN["("] = (-160, CAP)
SPAN["#"] = (0, 560); SPAN["$"] = (-60, 720); SPAN["@"] = (-40, 560)
SPAN["."]=(0,90); SPAN[","]=(-120,70); SPAN["'"]=(540,720); SPAN['"']=(540,720)
SPAN[":"]=(0,500); SPAN[";"]=(-120,500); SPAN["-"]=(230,300); SPAN["/"]=(-120,700)
SPAN["&"]=(0,700); SPAN[")"]=(-160,700)


font = fontforge.font()
font.em = EM; font.ascent = ASCENT; font.descent = DESCENT
font.familyname = "Petee Hand"
font.fontname = "PeteeHand-Regular"
font.fullname = "Petee Hand"
font.copyright = "Petee's handwriting, 2026."
font.version = "001.000"

made = []
for svg in sorted(glob.glob(SVG + "/u*.svg")):
    cp = int(os.path.basename(svg)[1:5], 16)
    ch = chr(cp)
    g = font.createChar(cp)
    g.importOutlines(svg)
    g.removeOverlap(); g.simplify(1.0); g.round()
    bb = g.boundingBox()              # (xmin, ymin, xmax, ymax)
    gw, gh = bb[2]-bb[0], bb[3]-bb[1]
    if gh <= 0 or gw <= 0:
        font.removeGlyph(g); continue
    bottom, top = SPAN.get(ch, (0, 650))
    s = (top - bottom) / gh
    g.transform(psMat.scale(s))
    bb = g.boundingBox()
    g.transform(psMat.translate(SB - bb[0], bottom - bb[1]))
    bb = g.boundingBox()
    if (bb[2] - bb[0]) > 1.3 * EM:        # stray far fragment survived — skip, don't poison the font
        print("SKIP oversized", ch)
        font.removeGlyph(g); continue
    g.width = int(bb[2] + SB)
    g.removeOverlap(); g.round()
    made.append(ch)

sp = font.createChar(32); sp.width = 300
font.createChar(160).width = 300     # nbsp

out = ROOT + "/build/PeteeHand.ttf"
font.generate(out)
print("glyphs:", "".join(sorted(made)))
print("wrote", out, "(", len(made), "glyphs )")
