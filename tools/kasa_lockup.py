#!/usr/bin/env python3
"""우주항공청 소속기관 로고 (정부상징 밖 요청) — 좌: KASA 마크, 우: 본부명/기관명 (A type 비율, 검은색).

KASA 마크는 '우주항공청 로고.svg' 의 벡터를 그대로 쓴다 (KASA 글자·궤도·별, 아래 '우주항공청'·영문 줄은 제외).
구도 ('우주환경센터.webp' 참고):
  * 글자 영역 위 = 마크(별) 위, 글자 영역 아래 = KASA 글자 기준선 — 그 높이를 A type 15.4r(5.5r/2.4r/7.5r)로 나눔
  * 마크와 글자 사이 5.5r, 바탕 여백 좌우 8r · 상하 5r
  * 글자는 정부상징체, 검은색 (#000000 / K100)

  python3 tools/kasa_lockup.py --font 정부상징체.ttf --kasa '우주항공청 로고.svg' --out logos/우주항공청 \\
      "우주항공청|우주환경센터"
"""

import argparse
import os
from xml.etree import ElementTree as ET

import cairosvg
import pymupdf
from fontTools.pens.boundsPen import BoundsPen
from fontTools.pens.recordingPen import RecordingPen, replayRecording
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.svgLib.path import parse_path

import build_gov_symbol as b

NS = "{http://www.w3.org/2000/svg}"
MARK_LETTER_BOTTOM = 202.17     # KASA 글자 기준선 (원본 좌표)
LINES = ((5.5, 0.0), (7.5, 5.5 + 2.4))   # (글자 높이, 글자 영역 위에서 거리) r — A type
GAP, CLEAR_X, CLEAR_Y = 5.5, 8, 5


def kasa_mark(path):
    """원본 SVG 에서 KASA 마크 부분만: (translate, defs xml, [(fill, d)], 마크 상자)."""
    root = ET.parse(path).getroot()
    defs = ET.tostring(root.find(NS + "defs"), encoding="unicode").replace("ns0:", "").replace(":ns0", "")
    parts, box = [], None
    for el in root.iter(NS + "path"):
        rec = RecordingPen()
        parse_path(el.get("d"), rec)
        subs, cur = [], []
        for op, a in rec.value:
            cur.append((op, a))
            if op in ("closePath", "endPath"):
                subs.append(cur)
                cur = []
        keep = []
        for s in subs:
            bp = BoundsPen(None)
            replayRecording(s, bp)
            if bp.bounds[3] <= MARK_LETTER_BOTTOM + 0.5:      # 마크 (글자 줄 아래는 제외)
                keep.append(s)
                box = bp.bounds if box is None else b.union([box, bp.bounds])
        pen = SVGPathPen(None)
        for s in keep:
            replayRecording(s, pen)
        fill = el.get("fill") or "url(#a)"
        parts.append((fill, pen.getCommands()))
        tr = el.get("transform")
    return tr, defs, parts, box


def build(font, kasa, parent, name, out, base, png_height):
    tr, defs, parts, box = kasa_mark(kasa)
    tx, ty = (float(v) for v in tr[tr.index("(") + 1:-1].split())     # translate(tx ty)
    x0, y0, x1 = box[0] + tx, box[1] + ty, box[2] + tx
    h = MARK_LETTER_BOTTOM + ty - y0
    r = h / sum(LINES[-1])                                  # 글자 영역 15.4r = 마크 높이
    # 글자: y 위쪽 증가 좌표 (원본 y 를 뒤집음, 마크 위 = h)
    glyphs = []
    for text, (lh, t) in zip((parent, name), LINES):
        em = lh * r / (b.BOX_TOP - b.BOX_BOTTOM)
        baseline = h - (t + lh) * r - b.BOX_BOTTOM * em
        glyphs += b.set_line(font, text, baseline, em / font.upm, ink_left=(x1 - x0) + GAP * r)
    tb = b.union([b.seg_bounds(g) for g in glyphs])
    left, right = -CLEAR_X * r, max(x1 - x0, tb[2]) + CLEAR_X * r
    top, bottom = max(h, tb[3]) + CLEAR_Y * r, min(0, tb[1]) - CLEAR_Y * r
    W, H = right - left, top - bottom

    def tf(p):
        return (p[0] - left, top - p[1])

    mx, my = -left - x0, top - h - y0                       # 원본 마크 좌표 → 캔버스
    out_svg = ['<?xml version="1.0" encoding="UTF-8"?>',
               f'<svg xmlns="http://www.w3.org/2000/svg" width="{b.fmt(W)}" height="{b.fmt(H)}" '
               f'viewBox="0 0 {b.fmt(W)} {b.fmt(H)}">',
               f"<title>{parent} {name}</title>",
               "<desc>우주항공청 KASA 마크 + 정부상징체 기관명 (정부상징 밖 요청 로고). 바탕 여백 좌우 8r, 상하 5r 포함.</desc>",
               defs,
               f'<g id="kasa" transform="translate({b.fmt(mx)} {b.fmt(my)}) {tr}">']
    out_svg += [f'<path fill="{f}" d="{d}"/>' for f, d in parts if d]
    out_svg += ["</g>", '<g id="name" fill="#000000">']
    out_svg += [f'<path d="{b.svg_path(g, tf)}"/>' for g in glyphs]
    out_svg += ["</g>", "</svg>"]
    for d in ("svg", "pdf", "png"):
        os.makedirs(os.path.join(out, d), exist_ok=True)
    svg = os.path.join(out, "svg", base + ".svg")
    with open(svg, "w", encoding="utf-8") as f:
        f.write("\n".join(out_svg) + "\n")
    doc = pymupdf.open("pdf", cairosvg.svg2pdf(url=svg))
    # 메타데이터 고정 (생성 시각을 빼서 다시 만들어도 같은 파일)
    doc.set_metadata({"title": f"{parent} {name}", "subject": "우주항공청 KASA 마크 + 정부상징체 기관명",
                      "producer": "", "creator": "", "creationDate": "", "modDate": ""})
    doc.save(os.path.join(out, "pdf", base + ".pdf"), garbage=3, deflate=True, no_new_id=True)
    b.write_png(svg, os.path.join(out, "png", base + ".png"), W, png_height / H)
    print(f"{parent} / {name}: 캔버스 {W / r:.2f}r x {H / r:.2f}r (r = {r:.3f})")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--font", required=True)
    ap.add_argument("--kasa", required=True, help="우주항공청 로고.svg")
    ap.add_argument("--out", default="logos/우주항공청")
    ap.add_argument("--filename", default="{name} 로고")
    ap.add_argument("--png-height", type=int, default=710, help="PNG 높이 (px, 다른 로고와 같은 710)")
    ap.add_argument("names", nargs="+", help="'본부명|기관명'")
    args = ap.parse_args()
    font = b.Font(args.font)
    for n in args.names:
        parent, name = n.split("|")
        build(font, args.kasa, parent, name, args.out, args.filename.format(name=name), args.png_height)


if __name__ == "__main__":
    main()
