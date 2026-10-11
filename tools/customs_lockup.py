#!/usr/bin/env python3
"""관세국경인재개발원 로고 (정부상징 밖 요청) — 좌: 관세청 엠블럼, 우: 영문 슬로건(위) / 국문 기관명(아래).

엠블럼과 영문은 '연수원.svg' 의 벡터를 그대로 쓴다.
  * 엠블럼: 원본 왼쪽의 관세청 엠블럼
  * 영문: 원본 슬로건 'Smart Customs, Excellent CBCTI' 에서 'Smart Customs, Excellent' 는 그대로,
    볼드 단어는 원본의 C·B·I 를 쓰고, 원본에 없는 H·R·D 는 원본 볼드 획 굵기로 만들되 비율은
    요청 참고 이미지(15.png, 같은 계열 서체의 CBHRDI)에서 잰 값을 따른다
      H  기둥 두 개 + 가로획 (가운데보다 조금 위)
      R·D  곧은 기둥·가로획·다리 + 참고 글자 윤곽에 맞춘 매끄러운 곡선 (R_*, D_*)
    글자 사이도 참고 이미지의 간격을 따른다
  * 색: 영문 #2B609F (원본), 국문 정부상징체 정부회색 #575757
구도 (요청 참고 이미지 실측, REF_*): 영문 잉크 폭 = 국문 잉크 폭, 줄 높이·엠블럼과의 간격은 참고 이미지대로,
바탕 여백 좌우 8r · 상하 5r (엠블럼 높이 = 20r).

  python3 tools/customs_lockup.py --font 정부상징체.ttf --emblem 연수원.svg --out logos/관세국경인재개발원
"""

import argparse
import math
import os
from xml.etree import ElementTree as ET

import cairosvg
import pathops
import pymupdf
from fontTools.misc.transform import Transform
from fontTools.pens.boundsPen import BoundsPen
from fontTools.pens.recordingPen import RecordingPen
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.svgLib.path import parse_path

import build_gov_symbol as b

NS = "{http://www.w3.org/2000/svg}"
EMBLEM_FILLS = ("#2e5c97", "#383c6c", "#fff", "#f6a845", "#ee3731")   # 원본에서 엠블럼을 이루는 색
ENG_FILL = "#2b609f"
ENGLISH, KOREAN = "Smart Customs, Excellent CBHRDI", "관세국경인재개발원"
ENG_COLOR, KOR_COLOR = "#2B609F", b.COLORS["gray"][0]
CLEAR_X, CLEAR_Y = 8, 5
# 참고 이미지 (500x133 px) 잉크 상자 (x0, y0, x1, y1 — 픽셀 가장자리), 영문은 대문자 위·아래(쉼표 꼬리 제외)
REF_EMBLEM = (16, 14, 104, 122)
REF_ENG_CAP = (32, 50)
REF_KOR = (113, 67, 472, 110)

# 원본 영문 (원본 SVG 좌표, y 아래쪽 증가)
SRC_REGULAR_END = 1080        # 'Smart Customs, Excellent' 의 오른쪽 끝 이후 (볼드 단어 시작 전)
SRC_BOLD = {"C": (1094.2, 1134.7), "B": (1140.2, 1177.5), "I": (1271.6, 1280.6)}   # 'CBCTI' 의 글자 x 범위
CAP_TOP, BASE = 50.6, 101.8   # 볼드 대문자 위·기준선
STEM = 8.8                    # 볼드 기둥 굵기 (B 8.8, I 9.0)
# 볼드 단어 배치: (글자, 앞 글자 잉크와의 간격, 원본 좌표). 참고 이미지(15.png) 잉크 간격
# (C→B 13 px, B→H 15, H→R 15, R→D 11, D→I 14) 을 대문자 높이(87 px = 51.2)로 맞춘 값
_PX = (BASE - CAP_TOP) / 87
# 참고 이미지(15.png) R·D 의 곡선 — 참고 글자 윤곽을 8배 확대해 벡터로 딴 점들에 맞춘 3차 곡선 (원본 좌표, 왼쪽 끝 0,
# 따낸 윤곽의 위·아래 끝 50.62 / 101.65 기준; 최대 오차 0.17 = 참고 이미지 0.3 px).
#   (a, R, b, k1, c, e, k2): 위 모서리는 (a, 위) 에서 수평으로 시작해 (R, b) 에서 수직으로, b~c 는 곧은 세로,
#   아래 모서리는 (R, c) 에서 수직으로 시작해 (e, 아래) 에서 수평으로. 손잡이는 모서리 가로·세로 길이의 k 배
D_OUTER = (18.16, 39.31, 72.10, 0.601, 77.80, 17.25, 0.580)       # 위·아래 50.62 / 101.65
D_INNER = (15.46, 30.99, 74.32, 0.657, 75.74, 16.71, 0.610)       # 위·아래 57.68 / 94.59
R_INNER = (15.91, 26.84, 66.10, 0.652, 67.04, 17.14, 0.557)       # 위·아래 57.85 / 74.90
# R 바깥: 위 모서리 (a, R, b, k1) 뒤 아래 곡선은 (R, b) 에서 수직으로 시작해 꼭짓점 R_APEX 로, 손잡이 k2, 끝 방향 각 th
R_OUTER = (18.60, 35.25, 64.76, 0.589, 0.651, 0.564)               # 위 50.62
R_APEX = (25.55, 80.56)       # 볼 바깥 곡선과 다리 오른쪽 직선이 만나는 꼭짓점
R_LEG = ((14.1, 0.5857), (22.66, 0.635))     # 다리 왼쪽·오른쪽 직선: y=76 에서의 x, 기울기 (dx/dy)
R_BAR_BOTTOM = 82.15          # 볼 아래 가로획 아래 (기둥 쪽)
BOLD_WORD = (("C", 0), ("B", 13 * _PX), ("H", 15 * _PX), ("R", 15 * _PX), ("D", 11 * _PX), ("I", 14 * _PX))


def _transform(s):
    if not s:
        return Transform()
    v = [float(x) for x in s[s.index("(") + 1:-1].replace(",", " ").split()]
    if s.startswith("matrix"):
        return Transform(*v)
    if s.startswith("scale"):
        return Transform(v[0], 0, 0, v[-1], 0, 0)
    raise ValueError(s)


def source_subpaths(path):
    """원본 SVG 의 모든 패스를 하위 윤곽 단위로: [(색, 상자, RecordingPen 값)] — transform 은 좌표에 반영."""
    out = []

    def walk(el, t, fill):
        for c in el:
            tag = c.tag[len(NS):]
            if tag in ("defs", "clipPath"):
                continue
            ct = t.transform(_transform(c.get("transform")))
            style = dict(kv.split(":") for kv in c.get("style", "").split(";") if kv)
            f = c.get("fill") or style.get("fill") or fill
            if tag == "g":
                walk(c, ct, f)
            elif tag == "path":
                rec = RecordingPen()
                parse_path(c.get("d"), TransformPen(rec, ct))
                cur = []
                for op, a in rec.value:
                    cur.append((op, a))
                    if op in ("closePath", "endPath"):
                        bp = BoundsPen(None)
                        for o, aa in cur:
                            getattr(bp, o)(*aa)
                        out.append((f, bp.bounds, cur))
                        cur = []

    walk(ET.parse(path).getroot(), Transform(), None)
    return out


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


# --- pathops 도우미 ---
UNION, INTER, DIFF = pathops.PathOp.UNION, pathops.PathOp.INTERSECTION, pathops.PathOp.DIFFERENCE


def op(a, c, o):
    return pathops.op(a, c, o, fix_winding=True)


def rect(x0, y0, x1, y1):
    p = pathops.Path()
    p.moveTo(x0, y0)
    p.lineTo(x1, y0)
    p.lineTo(x1, y1)
    p.lineTo(x0, y1)
    p.close()
    return p


def poly(*pts):
    p = pathops.Path()
    p.moveTo(*pts[0])
    for q in pts[1:]:
        p.lineTo(*q)
    p.close()
    return p


def xf(p, t):
    q = pathops.Path()
    p.draw(TransformPen(q.getPen(), t))
    return q


def to_path(subs):
    """원본 하위 윤곽 모음 → 겹침·구멍을 정리한 하나의 윤곽 (원본은 nonzero 채움)."""
    p = pathops.Path()
    pen = p.getPen()
    for s in subs:
        for o, a in s:
            getattr(pen, o)(*a)
    p.simplify(fix_winding=True)
    return p


def bold_glyphs(subs):
    """볼드 단어 글자: 원본 C·B·I + 원본 볼드 획으로 만든 H·R·D (원본 좌표, y 아래쪽 증가, 왼쪽 끝 x=0).

    H 는 참고 이미지(15.png, 같은 계열 서체의 CBHRDI)를 대문자 높이로 맞춰 잰 비율, R·D 는 참고 이미지 윤곽을
    벡터로 딴 것 (참고 글자의 획 굵기가 원본 볼드와 같다: 기둥 8.8).
    """
    blue = [(bx, s) for f, bx, s in subs if f == ENG_FILL]

    def src(x0, x1, start=None):
        """x0~x1 안의 볼드 글자 (start 가 있으면 왼쪽 위가 그 점인 윤곽 하나만), 왼쪽 끝을 x=0 으로."""
        sel = [s for bx, s in blue if bx[0] >= x0 - 0.1 and bx[2] <= x1 + 0.1
               and (start is None or (abs(bx[0] - start[0]) < 0.1 and abs(bx[1] - start[1]) < 0.1))]
        return xf(to_path(sel), (1, 0, 0, 1, -x0, 0))

    G = {k: src(*v) for k, v in SRC_BOLD.items()}
    stem = rect(0, CAP_TOP, STEM, BASE)
    # H: 폭 38.8, 가로획 70.6~78.3 (가운데보다 조금 위)
    hw = 38.8
    G["H"] = op(op(stem, rect(hw - STEM, CAP_TOP, hw, BASE), UNION), rect(0, 70.6, hw, 78.3), UNION)

    # R·D: 참고 이미지 글자의 곡선 (R_*, D_*) — 곧은 기둥·가로획·다리 + 매끄러운 3차 곡선 모서리
    def contour(pts):
        """[(x, y) | ((x1, y1), (x2, y2), (x3, y3))] → 닫힌 윤곽."""
        p = pathops.Path()
        p.moveTo(*pts[0])
        for q in pts[1:]:
            if isinstance(q[0], tuple):
                p.cubicTo(*q[0], *q[1], *q[2])
            else:
                p.lineTo(*q)
        p.close()
        return p

    def round_side(prm, top, bottom):
        """위 모서리 → 곧은 오른쪽 세로 → 아래 모서리 (왼쪽 위에서 시계 방향, 시작·끝 점 제외)."""
        a, rx, b, k1, c, e, k2 = prm
        c = max(b, c)
        return [(a, top), ((a + k1 * (rx - a), top), (rx, b - k1 * (b - top)), (rx, b)), (rx, c),
                ((rx, c + k2 * (bottom - c)), (e + k2 * (rx - e), bottom), (e, bottom))]

    def fit_cap(p, y0, y1):
        """참고 글자 기준 위·아래(y0, y1)를 대문자 높이 CAP_TOP~BASE 로."""
        k = (BASE - CAP_TOP) / (y1 - y0)
        return xf(p, (1, 0, 0, k, 0, CAP_TOP - y0 * k))

    T, B = 50.62, 101.65
    d = op(contour([(0, T)] + round_side(D_OUTER, T, B) + [(0, B)]),
           contour([(STEM, 57.68)] + round_side(D_INNER, 57.68, 94.59) + [(STEM, 94.59)]), DIFF)
    G["D"] = fit_cap(d, T, B)

    a, rx, b, k1, k2, th = R_OUTER
    ax, ay = R_APEX
    (l0, ls), (r0, rs) = R_LEG
    bar_x = l0 + ls * (R_BAR_BOTTOM - 76)                 # 다리 왼쪽 직선이 가로획 아래와 만나는 점
    h4 = k2 * (rx - ax)
    outer = contour([(0, T), (a, T), ((a + k1 * (rx - a), T), (rx, b - k1 * (b - T)), (rx, b)),
                     ((rx, b + k2 * (ay - b)), (ax + h4 * math.cos(th), ay - h4 * math.sin(th)), (ax, ay)),
                     (r0 + rs * (B - 76), B), (l0 + ls * (B - 76), B), (bar_x, R_BAR_BOTTOM),
                     (STEM, R_BAR_BOTTOM), (STEM, B), (0, B)])
    counter = contour([(STEM, 57.85)] + round_side(R_INNER, 57.85, 74.90) + [(STEM, 74.90)])
    G["R"] = fit_cap(op(outer, counter, DIFF), T, B)
    return G


def english_word(subs):
    """영문 한 줄: 원본 'Smart Customs, Excellent' + 볼드 'CBHRDI' (원본 좌표, y 아래쪽 증가)."""
    blue = [(bx, s) for f, bx, s in subs if f == ENG_FILL]
    regular = to_path([s for bx, s in blue if bx[2] < SRC_REGULAR_END])
    G = bold_glyphs(subs)

    out, x = regular, SRC_BOLD["C"][0] - BOLD_WORD[0][1]
    for ch, gap in BOLD_WORD:
        x += gap
        g = xf(G[ch], (1, 0, 0, 1, x - G[ch].bounds[0], 0))
        out = op(out, g, UNION)
        x = g.bounds[2]
    return out


def build(font, src_svg, out, base, png_height):
    subs = source_subpaths(src_svg)
    parts = emblem_paths(src_svg)
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
    # 영문: 원본 벡터를 잉크 폭이 국문 폭과 같게 키우고, 대문자 높이 가운데를 참고 이미지 대문자 줄 가운데에
    eng = english_word(subs)
    sx0, _, sx1, _ = eng.bounds
    s = (kbox[2] - kbox[0]) / (sx1 - sx0)
    yc = (py(REF_ENG_CAP[0]) + py(REF_ENG_CAP[1])) / 2
    eng = xf(eng, (s, 0, 0, -s, kbox[0] - sx0 * s, yc + (CAP_TOP + BASE) / 2 * s))
    ebox = eng.bounds

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
    pen = SVGPathPen(None, ntos=f)
    eng.draw(TransformPen(pen, (1, 0, 0, -1, -left, top)))
    svg += ["</g>", f'<path id="english" fill="{ENG_COLOR}" d="{pen.getCommands()}"/>',
            f'<g id="name" fill="{KOR_COLOR}">']
    svg += [f'<path d="{b.svg_path(g, tf)}"/>' for g in kor]
    svg += ["</g>", "</svg>"]
    for d in ("svg", "pdf", "png"):
        os.makedirs(os.path.join(out, d), exist_ok=True)
    path = os.path.join(out, "svg", base + ".svg")
    with open(path, "w", encoding="utf-8") as fh:
        fh.write("\n".join(svg) + "\n")
    doc = pymupdf.open("pdf", cairosvg.svg2pdf(url=path))
    doc.set_metadata({"title": f"{KOREAN} {ENGLISH}", "subject": "관세청 엠블럼 + 영문 슬로건 + 정부상징체 기관명",
                      "producer": "", "creator": "", "creationDate": "", "modDate": ""})
    doc.save(os.path.join(out, "pdf", base + ".pdf"), garbage=3, deflate=True, no_new_id=True)
    b.write_png(path, os.path.join(out, "png", base + ".png"), W, png_height / H)
    print(f"{KOREAN}: 캔버스 {W / r:.2f}r x {H / r:.2f}r, 국문 폭 {(kbox[2] - kbox[0]) / r:.3f}r, "
          f"영문 폭 {(ebox[2] - ebox[0]) / r:.3f}r")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--font", required=True)
    ap.add_argument("--emblem", required=True, help="연수원.svg (관세청 엠블럼·영문 슬로건 원본)")
    ap.add_argument("--out", default="logos/관세국경인재개발원")
    ap.add_argument("--filename", default="관세국경인재개발원 로고")
    ap.add_argument("--png-height", type=int, default=710, help="PNG 높이 (px, 다른 로고와 같은 710)")
    args = ap.parse_args()
    build(b.Font(args.font), args.emblem, args.out, args.filename, args.png_height)


if __name__ == "__main__":
    main()
