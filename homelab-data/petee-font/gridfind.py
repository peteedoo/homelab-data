#!/usr/bin/env python
"""Grid bbox from horizontal border lines; x-extent from their span. Overlay to verify."""
import cv2, numpy as np, os, sys, json
BUILD = os.path.expanduser("~/homelab-data/petee-font/build")

DIMS = {"page1.png": (6, 6), "page2.png": (7, 6), "kp.png": (1, 6)}

def hmask(gray):
    bw = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_MEAN_C,
                               cv2.THRESH_BINARY_INV, 41, 12)
    k = cv2.getStructuringElement(cv2.MORPH_RECT, (int(gray.shape[1]*0.3), 1))
    return cv2.morphologyEx(bw, cv2.MORPH_OPEN, k, 1)

def find(path):
    rows, cols = DIMS[path]
    img = cv2.imread(os.path.join(BUILD, path))
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    h, w = gray.shape
    mh = hmask(gray)
    rowsum = mh.sum(1)
    peak = rowsum.max()
    strong = rowsum > 0.45*peak
    ys = np.where(strong)[0]
    y0, y1 = int(ys.min()), int(ys.max())
    # x-extent from the strong horizontal lines' span
    band = mh[ys, :].any(0)
    xs = np.where(band)[0]
    x0, x1 = int(xs.min()), int(xs.max())
    grid = {"path": path, "rows": rows, "cols": cols,
            "x0": x0, "y0": y0, "x1": x1, "y1": y1}
    # overlay computed equal-division grid
    dbg = img.copy()
    for c in range(cols+1):
        x = int(x0 + (x1-x0)*c/cols)
        cv2.line(dbg, (x, y0), (x, y1), (0, 0, 255), 4)
    for r in range(rows+1):
        y = int(y0 + (y1-y0)*r/rows)
        cv2.line(dbg, (x0, y), (x1, y), (0, 0, 255), 4)
    cv2.imwrite(os.path.join(BUILD, path.replace(".png", "_grid.png")), dbg)
    print(f"{path}: x[{x0}-{x1}] y[{y0}-{y1}] cell {(x1-x0)/cols:.0f}x{(y1-y0)/rows:.0f}")
    return grid

grids = {p: find(p) for p in (sys.argv[1:] or DIMS.keys())}
json.dump(grids, open(os.path.join(BUILD, "grids.json"), "w"), indent=2)
