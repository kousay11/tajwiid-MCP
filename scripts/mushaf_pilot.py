#!/usr/bin/env python3
"""Pilot: find coloured letter blobs on scanned pages of the coloured Hannibal mushaf.

Reads the PDF read-only, decodes the embedded page JPEG losslessly with `pdfimages -png`,
masks the ornamental frame and verse rings, and lists red / orange / grey blobs with their
bounding boxes. All outputs go to the git-ignored `.work/mushaf_pilot/` directory; nothing
derived from the scan is ever committed. This script does not map blobs to letters.
"""

import argparse
import hashlib
import json
import subprocess
import sys
import tempfile
from pathlib import Path

import cv2
import numpy as np

EXTRACTOR_VERSION = "mushaf-pilot-0.1"
MIN_BLOB_PIXELS = 30


def extract_page(pdf: Path, page: int, workdir: Path) -> tuple[np.ndarray, str]:
    with tempfile.TemporaryDirectory(dir=workdir) as tmp:
        subprocess.run(
            ["pdfimages", "-png", "-f", str(page), "-l", str(page), str(pdf), f"{tmp}/img"],
            check=True,
            capture_output=True,
        )
        files = sorted(Path(tmp).glob("img-*.png"), key=lambda p: p.stat().st_size, reverse=True)
        raw = files[0].read_bytes()
    image = cv2.imdecode(np.frombuffer(raw, np.uint8), cv2.IMREAD_COLOR)
    return image, hashlib.sha256(raw).hexdigest()


def _clusters(flags: np.ndarray) -> list[tuple[int, int]]:
    out, start = [], None
    for i, flag in enumerate(flags):
        if flag and start is None:
            start = i
        elif not flag and start is not None:
            out.append((start, i - 1))
            start = None
    if start is not None:
        out.append((start, len(flags) - 1))
    return out


def text_box(image: np.ndarray) -> tuple[int, int, int, int]:
    """Inner rectangle of the double black frame: the clusters nearest the page centre."""
    h, w = image.shape[:2]
    dark = (cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) < 90).astype(np.uint8)
    rows = _clusters(dark.sum(1) > 0.5 * w)
    cols = _clusters(dark.sum(0) > 0.5 * h)
    top = [c for c in rows if c[1] < h * 0.35]
    bottom = [c for c in rows if c[0] > h * 0.65]
    left = [c for c in cols if c[1] < w * 0.35]
    right = [c for c in cols if c[0] > w * 0.65]
    if not (top and bottom and left and right):
        return int(w * 0.1), int(h * 0.08), int(w * 0.9), int(h * 0.92)
    return left[-1][1] + 4, top[-1][1] + 4, right[0][0] - 4, bottom[0][0] - 4


def find_rings(image: np.ndarray) -> list[tuple[int, int, int]]:
    """Verse-end rings: dark circular components. Returned as (cx, cy, radius)."""
    small = cv2.resize(cv2.cvtColor(image, cv2.COLOR_BGR2GRAY), None, fx=0.5, fy=0.5)
    circles = cv2.HoughCircles(
        cv2.medianBlur(small, 5),
        cv2.HOUGH_GRADIENT,
        dp=1.2,
        minDist=40,
        param1=120,
        param2=34,
        minRadius=18,
        maxRadius=34,
    )
    if circles is None:
        return []
    return [(int(x * 2), int(y * 2), int(r * 2)) for x, y, r in circles[0]]


def blobs(mask: np.ndarray, box: tuple[int, int, int, int]) -> list[dict]:
    x0, y0, x1, y1 = box
    count, _lab, stats, centroids = cv2.connectedComponentsWithStats(mask.astype(np.uint8), 8)
    found = []
    for i in range(1, count):
        x, y, w, h, area = (int(v) for v in stats[i])
        cx, cy = centroids[i]
        if area >= MIN_BLOB_PIXELS and x0 <= cx <= x1 and y0 <= cy <= y1:
            found.append({"bbox": [x, y, x + w, y + h], "area": area, "cx": int(cx), "cy": int(cy)})
    return found


def analyse(image: np.ndarray) -> dict:
    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    hue, sat, val = (hsv[..., i].astype(int) for i in range(3))
    box = text_box(image)
    saturated = (sat > 110) & (val > 80)
    # Legend swatches measured on page م11 (pdf 616): "red" is pure red (hue 0); the swatch
    # the book calls orange is a crimson (hue ~173). Ornament pink sits near hue 165.
    masks = {
        "red": saturated & (hue <= 6),
        "orange": saturated & (hue >= 170) & (sat > 150),
    }
    # Grey letters are printed as a halftone hatch, so blur first; the erosion then drops the
    # thin mid-grey rims that surround black strokes.
    blurred = cv2.GaussianBlur(cv2.cvtColor(image, cv2.COLOR_BGR2GRAY), (0, 0), 3)
    grey = ((blurred > 105) & (blurred < 190) & (sat < 60)).astype(np.uint8)
    masks["grey"] = cv2.erode(grey, np.ones((5, 5), np.uint8)) > 0
    rings = find_rings(image)
    result = {"text_box": list(box), "rings": len(rings), "blobs": {}, "on_ring": {}}
    for name, mask in masks.items():
        kept, on_ring = [], 0
        for blob in blobs(mask, box):
            near = any(
                (blob["cx"] - cx) ** 2 + (blob["cy"] - cy) ** 2 <= (r * 1.35) ** 2
                for cx, cy, r in rings
            )
            if near:
                on_ring += 1
            else:
                kept.append(blob)
        result["blobs"][name] = kept
        result["on_ring"][name] = on_ring
    result["_rings"] = rings
    return result


def overlay(image: np.ndarray, result: dict) -> np.ndarray:
    out = image.copy()
    colors = {"red": (0, 0, 255), "orange": (0, 165, 255), "grey": (255, 0, 0)}
    x0, y0, x1, y1 = result["text_box"]
    cv2.rectangle(out, (x0, y0), (x1, y1), (0, 200, 0), 3)
    for cx, cy, r in result["_rings"]:
        cv2.circle(out, (cx, cy), int(r * 1.35), (255, 0, 255), 3)
    for name, items in result["blobs"].items():
        for number, blob in enumerate(items, 1):
            bx0, by0, bx1, by1 = blob["bbox"]
            cv2.rectangle(out, (bx0 - 4, by0 - 4), (bx1 + 4, by1 + 4), colors[name], 3)
            cv2.putText(out, str(number), (bx0, by0 - 8), 0, 0.9, colors[name], 2)
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pdf", type=Path)
    parser.add_argument("pages", type=int, nargs="+", help="pdf page numbers (1-based)")
    parser.add_argument("--out", type=Path, default=Path(".work/mushaf_pilot"))
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    for page in args.pages:
        target = args.out / f"page{page:04d}.json"
        if target.exists():
            print(f"page {page}: already done")
            continue
        try:
            image, sha = extract_page(args.pdf, page, args.out)
            result = analyse(image)
            cv2.imwrite(str(args.out / f"page{page:04d}_overlay.png"), overlay(image, result))
            result.pop("_rings")
            result.update(pdf_page=page, image_sha256=sha, extractor_version=EXTRACTOR_VERSION)
            target.write_text(json.dumps(result, indent=1), encoding="utf-8")
            counts = {k: len(v) for k, v in result["blobs"].items()}
            print(f"page {page}: {counts} on_ring={result['on_ring']} rings={result['rings']}")
        except Exception as exc:  # a page failure is logged, never fatal to the batch
            print(f"page {page}: FAILED {type(exc).__name__}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
