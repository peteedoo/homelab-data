#!/usr/bin/env python
"""Stage 1: rotate, find the page sheet, perspective-correct to a flat portrait rectangle.
Saves the warped page + a debug overlay so we can verify before segmenting."""
import cv2, numpy as np, sys, os

def order_quad(pts):
    pts = np.array(pts, dtype="float32").reshape(4, 2)
    s = pts.sum(1); d = np.diff(pts, axis=1).ravel()
    return np.array([pts[np.argmin(s)],      # tl
                     pts[np.argmin(d)],      # tr
                     pts[np.argmax(s)],      # br
                     pts[np.argmax(d)]],     # bl
                    dtype="float32")

def find_page(img):
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    gray = cv2.GaussianBlur(gray, (7, 7), 0)
    # paper is the bright region on a darker background
    _, th = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    th = cv2.morphologyEx(th, cv2.MORPH_CLOSE, np.ones((25, 25), np.uint8))
    cnts, _ = cv2.findContours(th, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    c = max(cnts, key=cv2.contourArea)
    peri = cv2.arcLength(c, True)
    approx = cv2.approxPolyDP(c, 0.02 * peri, True)
    if len(approx) == 4:
        quad = approx.reshape(4, 2)
    else:
        quad = cv2.boxPoints(cv2.minAreaRect(c))
    return order_quad(quad), c

def main():
    path, rot, out = sys.argv[1], int(sys.argv[2]), sys.argv[3]
    img = cv2.imread(path)
    rotmap = {0: None, 90: cv2.ROTATE_90_CLOCKWISE,
              180: cv2.ROTATE_180, 270: cv2.ROTATE_90_COUNTERCLOCKWISE}
    if rotmap[rot] is not None:
        img = cv2.rotate(img, rotmap[rot])
    quad, c = find_page(img)
    (tl, tr, br, bl) = quad
    wA = np.linalg.norm(br - bl); wB = np.linalg.norm(tr - tl)
    hA = np.linalg.norm(tr - br); hB = np.linalg.norm(tl - bl)
    W, H = int(max(wA, wB)), int(max(hA, hB))
    dst = np.array([[0, 0], [W-1, 0], [W-1, H-1], [0, H-1]], dtype="float32")
    M = cv2.getPerspectiveTransform(quad, dst)
    warp = cv2.warpPerspective(img, M, (W, H))
    cv2.imwrite(out, warp)
    dbg = img.copy()
    cv2.drawContours(dbg, [quad.astype(int)], -1, (0, 0, 255), 6)
    cv2.imwrite(out.replace(".png", "_dbg.png"), dbg)
    print(f"{os.path.basename(path)}  rot={rot}  page {W}x{H}  -> {out}")

if __name__ == "__main__":
    main()
