#!/usr/bin/env python3
"""관세국경인재개발원 로고 (정부상징 밖 요청) — 좌: 관세청 엠블럼, 우: 영문 슬로건(위) / 국문 기관명(아래).

엠블럼은 '연수원.svg' 왼쪽의 관세청 엠블럼 벡터를 그대로 쓴다 (원본의 글자는 쓰지 않음).
구도 (요청 참고 이미지 실측, REF_*):
  * 국문은 정부상징체, 정부회색 #575757. 영문도 정부상징체, '연수원.svg' 의 영문 색 #2b609f
  * 영문 폭 = 국문 폭 (두 줄의 잉크 좌단·우단을 맞춤), 'CBHRDI' 는 볼드
    — 정부상징체는 R 한 굵기뿐이라 윤곽을 바깥으로 BOLD 만큼 두껍게 하고 그만큼 글자 폭을 늘린다
  * 줄의 높이 위치·엠블럼과의 간격은 참고 이미지대로, 바탕 여백 좌우 8r · 상하 5r (엠블럼 높이 = 20r)

  python3 tools/customs_lockup.py --font 정부상징체.ttf --emblem 연수원.svg --out logos/관세청
"""

import argparse
import os
from xml.etree import ElementTree as ET

import cairosvg
import pathops
import pymupdf
from fontTools.pens.boundsPen import BoundsPen
from fontTools.pens.recordingPen import RecordingPen
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.svgLib.path import parse_path

import build_gov_symbol as b

NS = "{http://www.w3.org/2000/svg}"
EMBLEM_FILLS = ("#2e5c97", "#383c6c", "#fff", "#f6a845", "#ee3731")   # 원본에서 엠블럼을 이루는 색
ENGLISH, KOREAN = "Smart Customs, Excellent CBHRDI", "관세국경인재개발원"
BOLD_WORD = "CBHRDI"
ENG_COLOR, KOR_COLOR = "#2B609F", b.COLORS["gray"][0]
BOLD = 60              # 볼드 두께 증가 (1/1000 em) — 참고 이미지의 볼드/보통 획 굵기 비 약 1.5 (R 기둥 115)
CLEAR_X, CLEAR_Y = 8, 5
# 참고 이미지 (500x133 px) 잉크 상자 (x0, y0, x1, y1 — 픽셀 가장자리), 영문은 대문자 위·아래(쉼표 꼬리 제외)
REF_EMBLEM = (16, 14, 104, 122)
REF_ENG_CAP = (32, 50)
REF_KOR = (113, 67, 472, 110)


def emblem_paths(path):
    """원본 SVG 에서 엠블럼 패스만 (색, 원본 좌표 RecordingPen). transform(scale) 은 좌표에 반영."""
    parts = []
    for el in ET.parse(path).getroot().iter(NS + "path"):
        style = dict(kv.split(":") for kv in el.get("style", "").split(";") if kv)
        fill = el.get("fill") or style.get("fill")
        if fill not in EMBLEM_FILLS:
            continue
        tr = el.get("transform", "")
        s = float(tr[tr.index("(") + 1:-1]) if tr.startswith("scale(") else 1.0
        rec = RecordingPen()
        parse_path(el.get("d"), TransformPen(rec, (s, 0, 0, s, 0, 0)))
        parts.append(("#FFFFFF" if fill == "#fff" else fill.upper(), rec))
    return parts


def to_pathops(segs):
    p = pathops.Path()
    for op, pts in segs:
        {"m": lambda: p.moveTo(*pts[0]), "l": lambda: p.lineTo(*pts[0]),
         "c": lambda: p.cubicTo(*pts[0], *pts[1], *pts[2]), "h": p.close}[op]()
    return p


def from_pathops(p):
    segs = []
    for verb, pts in p:
        if verb == pathops.PathVerb.MOVE:
            segs.append(("m", [pts[0]]))
        elif verb == pathops.PathVerb.LINE:
            segs.append(("l", [pts[0]]))
        elif verb == pathops.PathVerb.CUBIC:
            segs.append(("c", list(pts)))
        elif verb == pathops.PathVerb.QUAD:
            cur = segs[-1][1][-1]
            q, e = pts
            segs.append(("c", [(cur[0] + 2 / 3 * (q[0] - cur[0]), cur[1] + 2 / 3 * (q[1] - cur[1])),
                               (e[0] + 2 / 3 * (q[0] - e[0]), e[1] + 2 / 3 * (q[1] - e[1])), e]))
        elif verb == pathops.PathVerb.CLOSE:
            segs.append(("h", []))
    return segs


def embolden(segs, width):
    """윤곽을 바깥쪽으로 width/2 만큼 키운 채움 윤곽 (획 + 원래 윤곽의 합집합)."""
    fill = to_pathops(segs)
    stroke = to_pathops(segs)
    stroke.stroke(width, pathops.LineCap.BUTT_CAP, pathops.LineJoin.MITER_JOIN, 4)
    return from_pathops(pathops.op(fill, stroke, pathops.PathOp.UNION, fix_winding=True))


def english_line(font, scale, ink_left, baseline):
    """영문 줄: 트래킹 −8/1000 em, BOLD_WORD 는 윤곽을 BOLD 만큼 두껍게 하고 글자마다 BOLD 만큼 넓힌다."""
    i0 = ENGLISH.index(BOLD_WORD)
    bold = set(range(i0, i0 + len(BOLD_WORD)))
    track = [b.ENG_TRACKING * font.upm / 1000 + (BOLD * font.upm / 1000 if i in bold else 0)
             for i in range(len(ENGLISH) - 1)]
    glyphs, k = [], 0
    raw = b.set_line(font, ENGLISH, baseline, scale, extra_kern=track, ink_left=ink_left)
    for i, ch in enumerate(ENGLISH):
        if ch == " ":
            continue
        g = raw[k]
        k += 1
        if i in bold:
            # 두께의 절반만큼 오른쪽으로 옮겨 키우면 왼쪽 잉크 끝은 그대로, 오른쪽은 w 만큼 (다음 글자는 w 만큼 밀림)
            # 키운 뒤 세로는 원래 잉크 높이로 되돌려 대문자 높이·기준선을 유지
            w = BOLD * font.upm / 1000 * scale
            y0, y1 = b.seg_bounds(g)[1::2]
            g = embolden([(op, [(x + w / 2, y) for x, y in pts]) for op, pts in g], w)
            sy = (y1 - y0) / (y1 - y0 + w)
            g = [(op, [(x, y0 + (y - y0 + w / 2) * sy) for x, y in pts]) for op, pts in g]
        glyphs.append(g)
    return glyphs


def build(font, emblem_svg, out, base, png_height):
    parts = emblem_paths(emblem_svg)
    eb = None
    for _, rec in parts:
        bp = BoundsPen(None)
        rec.replay(bp)
        eb = bp.bounds if eb is None else b.union([eb, bp.bounds])
    ex0, ey0, ex1, ey1 = eb                                  # 원본 좌표 (y 아래쪽 증가)
    eh = ey1 - ey0
    r = eh / 20
    k = eh / (REF_EMBLEM[3] - REF_EMBLEM[1])                 # 참고 이미지 1 px → 원본 좌표
    # 글자 좌표: y 위쪽 증가, 엠블럼 좌상단 = (0, eh)
    def px(x):
        return (x - REF_EMBLEM[0]) * k

    def py(y):
        return eh - (y - REF_EMBLEM[1]) * k

    # 국문: 참고 이미지 잉크 폭에 맞춰 크기, 잉크 높이 가운데를 참고 이미지 줄 가운데에
    kb = b.union([b.seg_bounds(g) for g in b.set_line(font, KOREAN, 0, 1.0, ink_left=0)])
    ks = (px(REF_KOR[2]) - px(REF_KOR[0])) / (kb[2] - kb[0])
    kor = b.set_line(font, KOREAN, py((REF_KOR[1] + REF_KOR[3]) / 2) - (kb[1] + kb[3]) / 2 * ks, ks,
                     ink_left=px(REF_KOR[0]))
    kbox = b.union([b.seg_bounds(g) for g in kor])
    # 영문: 잉크 좌단·우단을 국문과 같게 (볼드 포함 폭으로 크기를 맞춘 뒤 한 번 더 보정)
    s = 1.0
    for _ in range(4):
        eb_ = b.union([b.seg_bounds(g) for g in english_line(font, s, 0, 0)])
        s *= (kbox[2] - kbox[0]) / (eb_[2] - eb_[0])
    # 세로: 대문자 높이 가운데를 참고 이미지 영문 대문자 줄(31~50 px) 가운데에 — 쉼표 꼬리는 빼고 잼
    cap = b.ENG_CAP[1] * font.upm * s
    baseline = (py(REF_ENG_CAP[0]) + py(REF_ENG_CAP[1])) / 2 - cap / 2
    eng = english_line(font, s, kbox[0], baseline)
    ebox = b.union([b.seg_bounds(g) for g in eng])

    tb = b.union([ebox, kbox])
    left, right = -CLEAR_X * r, max(ex1 - ex0, tb[2]) + CLEAR_X * r
    top, bottom = max(eh, tb[3]) + CLEAR_Y * r, min(0, tb[1]) - CLEAR_Y * r
    W, H = right - left, top - bottom

    def tf(p):
        return (p[0] - left, top - p[1])

    mx, my = -left - ex0, top - eh - ey0                    # 원본 엠블럼 좌표 → 캔버스
    f = b.sfmt
    svg = ['<?xml version="1.0" encoding="UTF-8"?>',
           f'<svg xmlns="http://www.w3.org/2000/svg" width="{f(W)}" height="{f(H)}" viewBox="0 0 {f(W)} {f(H)}">',
           f"<title>{KOREAN} {ENGLISH}</title>", '<g id="emblem">']
    for fill, rec in parts:
        pen = SVGPathPen(None, ntos=f)
        rec.replay(TransformPen(pen, (1, 0, 0, 1, mx, my)))
        svg.append(f'<path fill="{fill}" d="{pen.getCommands()}"/>')
    svg += ["</g>", f'<g id="english" fill="{ENG_COLOR}">']
    svg += [f'<path d="{b.svg_path(g, tf)}"/>' for g in eng]
    svg += ["</g>", f'<g id="name" fill="{KOR_COLOR}">']
    svg += [f'<path d="{b.svg_path(g, tf)}"/>' for g in kor]
    svg += ["</g>", "</svg>"]
    for d in ("svg", "pdf", "png"):
        os.makedirs(os.path.join(out, d), exist_ok=True)
    path = os.path.join(out, "svg", base + ".svg")
    with open(path, "w", encoding="utf-8") as fh:
        fh.write("\n".join(svg) + "\n")
    doc = pymupdf.open("pdf", cairosvg.svg2pdf(url=path))
    doc.set_metadata({"title": f"{KOREAN} {ENGLISH}", "subject": "관세청 엠블럼 + 정부상징체 기관명·영문 슬로건",
                      "producer": "", "creator": "", "creationDate": "", "modDate": ""})
    doc.save(os.path.join(out, "pdf", base + ".pdf"), garbage=3, deflate=True, no_new_id=True)
    b.write_png(path, os.path.join(out, "png", base + ".png"), W, png_height / H)
    print(f"{KOREAN}: 캔버스 {W / r:.2f}r x {H / r:.2f}r, 국문 폭 {(kbox[2] - kbox[0]) / r:.3f}r, "
          f"영문 폭 {(ebox[2] - ebox[0]) / r:.3f}r")



def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--font", required=True)
    ap.add_argument("--emblem", required=True, help="연수원.svg (관세청 엠블럼이 왼쪽에 있는 원본)")
    ap.add_argument("--out", default="logos/관세청")
    ap.add_argument("--filename", default="관세국경인재개발원 로고")
    ap.add_argument("--png-height", type=int, default=710, help="PNG 높이 (px, 다른 로고와 같은 710)")
    args = ap.parse_args()
    build(b.Font(args.font), args.emblem, args.out, args.filename, args.png_height)


if __name__ == "__main__":
    main()
