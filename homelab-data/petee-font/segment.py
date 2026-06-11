#!/usr/bin/env python
"""Segment by mass-weighted clustering: cluster every ink pixel's x onto `cols`
column centers and y onto `rows` row centers, cut cells at the midpoints."""
import cv2, numpy as np, os, json

ROOT = os.path.expanduser("~/homelab-data/petee-font")
BUILD, OUT = ROOT + "/build", ROOT + "/glyphs"
os.makedirs(OUT, exist_ok=True)

INK_T = 95
PAD = 0.18

# (top_frac, bottom_frac, rows, cols, layout)
JOBS = {
    "p1.png": (0.300, 0.83, 7, 6, ["ABCDEF","GHIJKL","MNOPQR","STUVWX","YZabcd","efghij","klmnop"]),
    "p2.png": (0.055, 0.86, 6, 6, ["qrstuv","wxyz01","234567",
                                   list("89.,'\""), list("!?-:;("),
                                   [")","&","/","@",None,None]]),
}

KEEP_LARGEST = set("y4D")   # single-stroke glyphs that dragged a far fragment

def clean_cell(sub, ch):
    """keep the main pen stroke + compact pieces sitting over it (i/j dots);
    drop thin guide fragments and stray marks. Some single-stroke glyphs that
    pick up a far fragment use largest-component-only."""
    n, lab, st, cen = cv2.connectedComponentsWithStats(sub, 8)
    H, W = sub.shape
    area = H * W
    cand = [i for i in range(1, n) if st[i, cv2.CC_STAT_AREA] >= 0.0006*area]
    if not cand:
        return None
    main = max(cand, key=lambda i: st[i, cv2.CC_STAT_AREA])
    if ch in KEEP_LARGEST:
        mask = (lab == main).astype(np.uint8)
        ys, xs = np.where(mask)
        return mask, ys.min(), ys.max(), xs.min(), xs.max()
    mx0, my0 = st[main, cv2.CC_STAT_LEFT], st[main, cv2.CC_STAT_TOP]
    mx1 = mx0 + st[main, cv2.CC_STAT_WIDTH]
    my1 = my0 + st[main, cv2.CC_STAT_HEIGHT]
    keep = [main]
    for i in cand:
        if i == main:
            continue
        w, h = st[i, cv2.CC_STAT_WIDTH], st[i, cv2.CC_STAT_HEIGHT]
        a = st[i, cv2.CC_STAT_AREA]
        thin = min(w, h) < 0.035*max(H, W) and max(w, h) > 4*min(w, h)
        fill = a / float(w*h + 1)
        if thin or fill < 0.30:
            continue
        x0, y0 = st[i, cv2.CC_STAT_LEFT], st[i, cv2.CC_STAT_TOP]
        pcx = x0 + w/2.0
        gap_y = max(my0 - (y0+h), y0 - my1, 0)
        over = (mx0 - 0.05*W) <= pcx <= (mx1 + 0.05*W)
        if over and gap_y < 0.25*H:
            keep.append(i)
    mask = np.isin(lab, keep).astype(np.uint8)
    ys, xs = np.where(mask)
    return mask, ys.min(), ys.max(), xs.min(), xs.max()

def kmeans1d(vals, k, iters=60):
    vals = np.asarray(vals, float)
    c = np.quantile(vals, np.linspace(0.5/k, 1-0.5/k, k))
    for _ in range(iters):
        lab = np.argmin(np.abs(vals[:, None] - c[None, :]), 1)
        for j in range(k):
            if (lab == j).any(): c[j] = vals[lab == j].mean()
    return np.sort(c)

def bounds(centers, lo, hi):
    mids = [(centers[i]+centers[i+1])/2 for i in range(len(centers)-1)]
    edges = [lo] + mids + [hi]
    return [int(round(e)) for e in edges]

def main():
    mapping, tiles, gridmaps = {}, [], {}
    for fname, (topf, botf, rows, cols, layout) in JOBS.items():
        img = cv2.imread(f"{BUILD}/{fname}")
        H = img.shape[0]
        img = img[int(H*topf):int(H*botf), :]
        h, w = img.shape[:2]
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        ink = (gray < INK_T).astype(np.uint8)
        ink = (cv2.medianBlur(ink*255, 3) // 255).astype(np.uint8)
        ink = cv2.morphologyEx(ink, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))  # kill thin guide lines
        ys, xs = np.where(ink)
        cys = kmeans1d(ys, rows) if rows > 1 else np.array([h/2.0])
        yb = bounds(cys, 0, h) if rows > 1 else [0, h]
        # Columns are identical for every row (template geometry). Compute ONE stable
        # set as the median of column centers over the complete rows -> immune to a
        # faint/missing glyph shifting any single row.
        center_sets = []
        for r in range(rows):
            if any(layout[r][c] is None for c in range(cols)):
                continue
            rx = np.where(ink[yb[r]:yb[r+1], :])[1]
            if len(rx) < 100:
                continue
            center_sets.append(kmeans1d(rx, cols))
        med = np.median(np.array(center_sets), axis=0) if center_sets else kmeans1d(xs, cols)
        xbf = bounds(med, 0, w)
        gm = [["·"]*cols for _ in range(rows)]
        for r in range(rows):
            for c in range(cols):
                ch = layout[r][c] if c < len(layout[r]) else None
                if ch is None: continue
                sub = ink[yb[r]:yb[r+1], xbf[c]:xbf[c+1]]
                cleaned = clean_cell(sub, ch)
                if cleaned is None: continue
                mask, gy0, gy1, gx0, gx1 = cleaned
                g = (1 - mask[gy0:gy1+1, gx0:gx1+1]) * 255
                gh, gw = g.shape; pad = int(max(gh, gw)*PAD)
                o = np.full((gh+2*pad, gw+2*pad), 255, np.uint8)
                o[pad:pad+gh, pad:pad+gw] = g
                cp = ord(ch)
                cv2.imwrite(f"{OUT}/u{cp:04X}.pbm", o.astype(np.uint8))
                mapping[f"{cp:04X}"] = {"char": ch}
                tiles.append((ch, o.astype(np.uint8)))
                gm[r][c] = ch
        gridmaps[fname] = gm
        print(f"{fname}:")
        for row in gm: print("   ", " ".join(row))
    json.dump(mapping, open(f"{OUT}/map.json", "w"), indent=2)
    cols, cs = 12, 140
    rws = (len(tiles)+cols-1)//cols
    sheet = np.full((rws*cs, cols*cs, 3), 255, np.uint8)
    for i, (ch, g) in enumerate(tiles):
        r, c = divmod(i, cols)
        gg = cv2.cvtColor(g, cv2.COLOR_GRAY2BGR)
        sc = min((cs-30)/gg.shape[1], (cs-30)/gg.shape[0])
        gg = cv2.resize(gg, (max(1,int(gg.shape[1]*sc)), max(1,int(gg.shape[0]*sc))))
        yo, xo = r*cs+(cs-gg.shape[0])//2, c*cs+(cs-gg.shape[1])//2
        sheet[yo:yo+gg.shape[0], xo:xo+gg.shape[1]] = gg
        cv2.rectangle(sheet,(c*cs,r*cs),(c*cs+cs-1,r*cs+cs-1),(225,225,225),1)
        cv2.putText(sheet,ch,(c*cs+4,r*cs+19),cv2.FONT_HERSHEY_SIMPLEX,0.55,(0,0,210),2)
    cv2.imwrite(f"{BUILD}/contact.png", sheet)
    print(f"total {len(tiles)} glyphs -> build/contact.png")

if __name__ == "__main__":
    main()
