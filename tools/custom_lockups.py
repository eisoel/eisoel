#!/usr/bin/env python3
"""요청 참고 이미지에 맞춘 기관상징 (가이드 치수와 다름).

각 줄의 잉크 상자를 참고 이미지에서 잰 값(문양 잉크 우단·상단 기준, r 단위)에 맞춘다.
  size  = "width"  : 잉크 폭이 x0~x1 이 되게 크기를 정함
          "height" : 잉크 높이가 y0~y1 이 되게 크기를 정하고, 글자 사이를 고르게 벌려 폭을 x0~x1 에 맞춤
세로 위치는 잉크 높이의 가운데를 (y0+y1)/2 에 맞춘다. 영문은 kern + 트래킹 −8/1000em.
문양·색·보호공간(좌우 8r, 상하 5r)·파일 형식은 build_gov_symbol.py 와 같다.

  python3 tools/custom_lockups.py --font path/to/정부상징체.ttf --out logos/기관별
"""

import argparse
import os

import build_gov_symbol as b

# (파일명, 제목, [(글자, 언어, 크기 기준, x0, x1, y0, y1)])  — 참고 이미지 실측 (r)
LOCKUPS = [
    ("국립외교원 로고", "국립외교원 Korea National Diplomatic Academy", [
        ("국립외교원", "kor", "height", 5.02, 53.87, 3.35, 11.38),
        ("Korea National Diplomatic Academy", "eng", "width", 5.35, 53.87, 12.71, 15.39)]),
    ("방위사업교육원 로고", "방위사업교육원 Defense Acquisition Program Training Institute", [
        ("방위사업교육원", "kor", "width", 3.88, 65.20, 3.10, 12.42),
        ("Defense Acquisition Program Training Institute", "eng", "width", 3.88, 65.20, 14.36, 16.69)]),
    ("정부합동민원센터 로고", "국민권익위원회가 운영하는 종합민원상담창구 정부합동민원센터", [
        ("국민권익위원회가 운영하는 종합민원상담창구", "kor", "width", 4.96, 73.11, 2.71, 6.77),
        ("정부합동민원센터", "kor", "width", 4.51, 59.12, 8.57, 15.79)]),
]
NOTE = " 참고 이미지에 맞춘 크기·간격·정렬(요청에 따른 가이드 예외)."


def place(font, text, lang, size, x0, x1, y0, y1, m):
    r, left, top = m["r"], m["ink"][2], m["ink"][3]
    track = [b.ENG_TRACKING * font.upm / 1000] * (len(text) - 1) if lang == "eng" else None

    def ink(scale, extra=None):
        g = b.set_line(font, text, 0, scale, extra_kern=extra or track, ink_left=0)
        return b.union([b.seg_bounds(s) for s in g])

    box = ink(1.0)                                         # 1 pt / unit 에서의 잉크 상자
    if size == "width":
        scale, extra = (x1 - x0) * r / (box[2] - box[0]), track
    else:
        scale = (y1 - y0) * r / (box[3] - box[1])
        natural = ink(scale)[2]
        gap = ((x1 - x0) * r - natural) / scale / (len(text) - 1)
        extra = [gap + (track[i] if track else 0) for i in range(len(text) - 1)]
    bx = ink(scale, extra)
    baseline = top - (y0 + y1) / 2 * r - (bx[1] + bx[3]) / 2
    return b.set_line(font, text, baseline, scale, extra_kern=extra, ink_left=left + x0 * r)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--font", required=True)
    ap.add_argument("--out", default="logos/기관별")
    ap.add_argument("--px-per-pt", type=float, default=8.0)
    args = ap.parse_args()
    font = b.Font(args.font)
    m = b.emblem_metrics()
    for d in ("svg", "pdf", "png"):
        os.makedirs(os.path.join(args.out, d), exist_ok=True)
    for base, title, lines in LOCKUPS:
        glyphs = [g for spec in lines for g in place(font, *spec, m)]
        kind = "국영B" if any(l[1] == "eng" for l in lines) else "A"
        geo = b.geometry(glyphs, kind)
        geo["note"] = NOTE
        svg = os.path.join(args.out, "svg", base + ".svg")
        W, _ = b.write_svg(svg, title, geo, glyphs)
        b.write_pdf(os.path.join(args.out, "pdf", base + ".pdf"), title, geo, glyphs)
        b.write_png(svg, os.path.join(args.out, "png", base + ".png"), W, args.px_per_pt)
        print(f"{title}: 캔버스 {W / m['r']:.2f}r x {(geo['canvas'][3] - geo['canvas'][1]) / m['r']:.2f}r")


if __name__ == "__main__":
    main()
