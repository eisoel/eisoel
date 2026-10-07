#!/usr/bin/env python3
"""대한민국 정부상징 기관상징 생성기 — 국문 가로조합 (좌: 정부상징 문양, 우: 기관명).

조합 형식
  1행     기관명 한 줄                                     (BS 3-1-02, BS 3-3-01)
  A       본부 병기형 2행: 본부명 5.5r / 소속기관명 7.5r    (BS 3-3-05 가로조합 A type)
  B       본부 병기형 2행: 본부명 7r / 소속기관명 7r        (BS 3-3-05 가로조합 B type)

근거 자료
  * 정부상징 디자인 가이드 (2017 개정판)
      BS 1-01  보호공간: 가로조합 좌우 8r, 상하 5r (r = 문양 반지름 R 의 1/10)
      BS 1-03  상징색상: 정부청색 / 정부적색 / 정부회색(기관명)
      BS 1-04  정부상징 문양 기본형은 백색배경(0.6r)을 포함
      BS 3-1-02, BS 3-3-01  1차 소속기관 국문 가로조합
               문양 2R, 문양-기관명 간격 5.5r, 기관명 10r (상하 5r), 기관명 좌측정렬,
               문양 중심축 = 기관명 중심축
      BS 3-1-03/04  1행은 4~9자가 기본 크기 (3자 이하 110%, 10자 이상 85% — 범위 밖)
      BS 3-3-05  본부 병기형 가로조합 — 문양 상단부터
               A type: 2.3r / 본부명 5.5r / 2.4r / 소속기관명 7.5r / 2.3r
               B type: 1.7r / 본부명 7r / 2.6r / 소속기관명 7r / 1.7r
  * 대한민국정부_국문_좌우_1행.ai
      정부상징 문양 벡터(아래 EMBLEM)는 이 파일의 콘텐츠 스트림을 그대로 옮긴 값이다.
      기관명의 글자 크기·기준선·시작 위치도 같은 파일의 '대한민국정부' 아웃라인을
      정부상징체.ttf 글리프와 대조해 얻은 값을 쓴다 (FONT_SCALE, BASELINE_Y, TEXT_INK_LEFT).
  * 정부상징체.ttf — 기관명 글리프 아웃라인. 자간은 서체 기본값(추가 조정 없음, BS 서론 p.7).

글자 높이 규정(10r, 7.5r ...)은 글리프 높이 기준 795 ~ -97 font unit 구간에 해당한다.
'대한민국정부' AI 대조(10r = 892 unit)와 가이드 BS 3-3-05 도면의 치수선(오차 0.07pt 이내)으로 확인했다.

좌표계는 원본 AI 문서의 PDF 좌표(pt, y 위쪽 증가)를 그대로 사용한다.

사용법
  python3 tools/build_gov_symbol.py --font path/to/정부상징체.ttf --out logos
  python3 tools/build_gov_symbol.py --font path/to/정부상징체.ttf --out logos/고용노동부 \\
      --type A --parent 고용노동부 --filename "{name} 로고" 광주지방고용노동청 ...
필요 패키지: fonttools, cairosvg (PNG), pillow (미리보기)
"""

import argparse
import os

from fontTools.misc.bezierTools import calcCubicBounds
from fontTools.pens.basePen import BasePen
from fontTools.ttLib import TTFont

NAMES = [
    "서울지방국세청",
    "인천지방국세청",
    "부산지방국세청",
    "대구지방국세청",
    "광주지방국세청",
    "중부지방국세청",
    "대전지방국세청",
]

# ---------------------------------------------------------------------------
# 정부상징 문양 — 대한민국정부_국문_좌우_1행.ai 콘텐츠 스트림 원본 값 (cm 이동량, 경로)
# ---------------------------------------------------------------------------
EMBLEM = [
    ("white", 214.6348, 137.3472, """
0 0 m
0 -17.658 -14.316 -31.974 -31.973 -31.974 c
-49.632 -31.974 -63.947 -17.658 -63.947 0 c
-63.947 17.657 -49.632 31.973 -31.973 31.973 c
-14.316 31.973 0 17.657 0 0 c
f"""),
    ("blue", 197.6914, 139.5767, """
0 0 m
-5.088 3.458 -11.603 2.05 -15.028 -3.149 c
-17.877 -7.495 -22.189 -8.036 -23.85 -8.036 c
-29.298 -8.036 -33.016 -4.206 -34.121 -0.246 c
-34.124 -0.246 l
-34.137 -0.203 -34.145 -0.168 -34.155 -0.133 c
-34.167 -0.088 -34.174 -0.045 -34.188 0 c
-34.623 1.656 -34.732 2.442 -34.732 4.199 c
-34.732 13.665 -25.013 24.209 -11.025 24.209 c
3.305 24.209 11.506 13.301 13.625 7.237 c
13.583 7.351 13.548 7.453 13.513 7.56 c
9.448 19.419 -1.796 27.943 -15.042 27.943 c
-31.696 27.943 -45.206 14.44 -45.206 -2.229 c
-45.206 -17.124 -34.463 -29.873 -19.558 -29.873 c
-7.676 -29.873 0.312 -23.211 3.972 -14.025 c
5.983 -9 4.563 -3.099 0 0 c
f"""),
    ("red", 211.501, 146.228, """
0 0 m
-1.767 5.916 -10.021 17.558 -24.835 17.558 c
-38.822 17.558 -48.542 7.014 -48.542 -2.453 c
-48.542 -4.209 -48.433 -4.996 -47.998 -6.651 c
-48.18 -5.926 -48.272 -5.205 -48.272 -4.499 c
-48.272 5.363 -38.401 12.194 -28.252 12.194 c
-14.511 12.194 -3.373 1.056 -3.373 -12.68 c
-3.373 -23.448 -9.571 -32.774 -18.573 -37.251 c
-18.573 -37.26 l
-6.965 -33.056 1.324 -21.937 1.324 -8.88 c
1.324 -5.79 0.91 -3.064 0 0 c
f"""),
]

# 원본 AI의 '대한민국정부' 아웃라인을 정부상징체.ttf와 대조해 얻은 값
FONT_SCALE = 0.033844      # pt / font unit (가로·세로 동일, 34.656pt) — 기관명 높이 10r
BASELINE_Y = 125.4431      # 1행 기준선 y (pt)
TEXT_INK_LEFT = 229.4574   # 첫 글자 잉크 좌단 x (pt) — 문양 우단에서 5.5r

# 글자 높이 규정이 가리키는 글리프 구간 (font unit)
BOX_TOP, BOX_BOTTOM = 795, -97

# 조합 형식: 줄마다 (글자 높이 h, 문양 상단에서 글자 영역 상단까지 거리 t), 단위 r
TYPES = {
    "1행": ((10.0, 5.0),),
    "A": ((5.5, 2.3), (7.5, 2.3 + 5.5 + 2.4)),
    "B": ((7.0, 1.7), (7.0, 1.7 + 7.0 + 2.6)),
}
TYPE_LABEL = {"1행": "국문 가로조합 1행", "A": "본부 병기형 국문 가로조합 A type (2행)",
              "B": "본부 병기형 국문 가로조합 B type (2행)"}

# 상징색상 (BS 1-03)
COLORS = {
    #         RGB (화면용)  CMYK (인쇄용)                 별색 이름
    "white": ("#FFFFFF", (0, 0, 0, 0), None),
    "blue": ("#003764", (1, 0.7, 0.2, 0.4), "GOK_Blue"),   # 정부청색 PANTONE 2955 C
    "red": ("#E4032E", (0, 1, 0.8, 0), "GOK_Red"),         # 정부적색 PANTONE 1935 C
    "gray": ("#575757", (0, 0, 0, 0.8), None),             # 정부회색 K80 (기관명)
}

CLEAR_X = 8   # 보호공간 좌우 (r)
CLEAR_Y = 5   # 보호공간 상하 (r)


def parse_ops(tx, ty, ops):
    """AI 경로 연산자를 절대 좌표 세그먼트 목록으로 변환."""
    segs, nums = [], []
    for tok in ops.split():
        if tok in ("m", "l", "c"):
            pts = [(nums[i] + tx, nums[i + 1] + ty) for i in range(0, len(nums), 2)]
            segs.append((tok, pts))
            nums = []
        elif tok == "h":
            segs.append(("h", []))
        elif tok == "f":
            pass
        else:
            nums.append(float(tok))
    return segs


class SegmentPen(BasePen):
    """글리프 아웃라인을 페이지 좌표 세그먼트로 기록 (2차 곡선은 3차로 정확 변환)."""

    def __init__(self, glyphset, ox, oy, scale):
        super().__init__(glyphset)
        self.ox, self.oy, self.s = ox, oy, scale
        self.segs = []

    def _t(self, p):
        return (self.ox + p[0] * self.s, self.oy + p[1] * self.s)

    def _moveTo(self, p):
        self.segs.append(("m", [self._t(p)]))

    def _lineTo(self, p):
        self.segs.append(("l", [self._t(p)]))

    def _curveToOne(self, p1, p2, p3):
        self.segs.append(("c", [self._t(p1), self._t(p2), self._t(p3)]))

    def _closePath(self):
        self.segs.append(("h", []))


def seg_bounds(segs):
    xs, ys, cur = [], [], None
    for op, pts in segs:
        if op == "c":
            x0, y0, x1, y1 = calcCubicBounds(cur, *pts)
            xs += [x0, x1]
            ys += [y0, y1]
        for p in pts:
            if op != "c":
                xs.append(p[0])
                ys.append(p[1])
        if pts:
            cur = pts[-1]
    return min(xs), min(ys), max(xs), max(ys)


def union(boxes):
    return (min(b[0] for b in boxes), min(b[1] for b in boxes),
            max(b[2] for b in boxes), max(b[3] for b in boxes))


class Font:
    def __init__(self, path):
        self.tt = TTFont(path)
        self.gs = self.tt.getGlyphSet()
        self.cmap = self.tt.getBestCmap()
        self.hmtx = self.tt["hmtx"]
        kern = self.tt["kern"].kernTables[0].kernTable if "kern" in self.tt else {}
        self.kern = kern

    def glyph(self, ch):
        if ord(ch) not in self.cmap:
            raise SystemExit(f"정부상징체에 '{ch}' 글리프가 없습니다.")
        return self.cmap[ord(ch)]

    def outline(self, gname, ox, oy, scale=FONT_SCALE):
        pen = SegmentPen(self.gs, ox, oy, scale)
        self.gs[gname].draw(pen)
        return pen.segs


def set_line(font, text, baseline, scale=FONT_SCALE, extra_kern=None):
    """한 줄 배치. 첫 글자 잉크 좌단을 TEXT_INK_LEFT 에 맞추고 서체 기본 자간으로 배열."""
    gnames = [font.glyph(ch) for ch in text]
    first = font.outline(gnames[0], 0, 0, scale)
    x = TEXT_INK_LEFT - seg_bounds(first)[0]
    glyphs = []
    for i, g in enumerate(gnames):
        if i:
            adv = font.hmtx[gnames[i - 1]][0] + font.kern.get((gnames[i - 1], g), 0)
            if extra_kern:
                adv += extra_kern[i - 1]
            x += adv * scale
        glyphs.append(font.outline(g, x, baseline, scale))
    return glyphs


def layout(font, name, extra_kern=None):
    """1행 기관명 — 기준선은 원본 AI 값."""
    return set_line(font, name, BASELINE_Y, extra_kern=extra_kern)


def layout_lines(font, lines, kind):
    """2행 본부 병기형 — 줄마다 글자 높이 h r, 문양 상단에서 t r 아래에 글자 영역을 둔다."""
    m = emblem_metrics()
    top, r = m["cy"] + m["R"], m["r"]
    glyphs = []
    for text, (h, t) in zip(lines, TYPES[kind]):
        scale = FONT_SCALE * h / 10
        baseline = top - (t + h) * r - BOX_BOTTOM * scale
        glyphs += set_line(font, text, baseline, scale)
    return glyphs


def emblem():
    return [(color, parse_ops(tx, ty, ops)) for color, tx, ty, ops in EMBLEM]


def emblem_metrics():
    """문양 기준값: 중심, 반지름 R, r = R/10, 청·홍 잉크 영역."""
    shapes = emblem()
    white = seg_bounds(shapes[0][1])
    cx, cy = (white[0] + white[2]) / 2, (white[1] + white[3]) / 2
    ink = union([seg_bounds(s) for c, s in shapes if c != "white"])   # 청·홍 문양 잉크 영역
    R = ((cx - ink[0]) + (ink[3] - cy)) / 2                           # 좌단·상단 기준 반지름
    return dict(shapes=shapes, cx=cx, cy=cy, R=R, r=R / 10, ink=ink)


def geometry(glyphs, kind="1행"):
    """보호공간을 포함한 캔버스 계산."""
    geo = emblem_metrics()
    r, ink = geo["r"], geo["ink"]
    text = union([seg_bounds(g) for g in glyphs])
    canvas = (ink[0] - CLEAR_X * r, ink[1] - CLEAR_Y * r,
              text[2] + CLEAR_X * r, ink[3] + CLEAR_Y * r)
    geo.update(text=text, canvas=canvas, kind=kind)
    return geo


def fmt(v):
    s = f"{v:.4f}".rstrip("0").rstrip(".")
    return "0" if s in ("-0", "") else s


def svg_path(segs, tf):
    out = []
    for op, pts in segs:
        if op == "h":
            out.append("Z")
            continue
        cmd = {"m": "M", "l": "L", "c": "C"}[op]
        out.append(cmd + " ".join(f"{fmt(x)} {fmt(y)}" for x, y in map(tf, pts)))
    return "".join(out)


def pdf_path(segs, tf):
    out = []
    for op, pts in segs:
        if op == "h":
            out.append("h")
            continue
        out.append(" ".join(f"{fmt(x)} {fmt(y)}" for x, y in map(tf, pts)) + " " + op)
    return "\n".join(out) + "\nf"


def write_svg(path, title, geo, glyphs, guides=False):
    x0, y0, x1, y1 = geo["canvas"]
    W, H = x1 - x0, y1 - y0

    def tf(p):
        return (p[0] - x0, y1 - p[1])

    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{fmt(W)}pt" height="{fmt(H)}pt" '
        f'viewBox="0 0 {fmt(W)} {fmt(H)}">',
        f"<title>{title}</title>",
        f"<desc>대한민국 정부상징 — {TYPE_LABEL[geo['kind']]}. "
        "캔버스는 보호공간(좌우 8r, 상하 5r)을 포함.</desc>",
        '<g id="emblem">',
    ]
    for color, segs in geo["shapes"]:
        lines.append(f'<path fill="{COLORS[color][0]}" d="{svg_path(segs, tf)}"/>')
    lines.append("</g>")
    lines.append(f'<g id="name" fill="{COLORS["gray"][0]}">')
    for g in glyphs:
        lines.append(f'<path d="{svg_path(g, tf)}"/>')
    lines.append("</g>")
    if guides:
        lines += guide_overlay(geo, tf, W, H)
    lines.append("</svg>")
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    return W, H


def guide_overlay(geo, tf, W, H):
    """가이드 BS 3-3-01 / 3-3-05 형식의 규정선(검증용)."""
    r, R, cx, cy, ink, text = geo["r"], geo["R"], geo["cx"], geo["cy"], geo["ink"], geo["text"]
    c = "#00ADEF"
    sw = 0.25
    out = [f'<g id="guides" fill="none" stroke="{c}" stroke-width="{sw}">']

    def line(a, b, dash=True):
        (ax, ay), (bx, by) = tf(a), tf(b)
        d = ' stroke-dasharray="1.6 2.1"' if dash else ""
        out.append(f'<line x1="{fmt(ax)}" y1="{fmt(ay)}" x2="{fmt(bx)}" y2="{fmt(by)}"{d}/>')

    left, right = cx - R, cx + R
    top = cy + R
    x_text = right + 5.5 * r
    # 글자 영역 경계 (문양 상단에서 아래로, r 단위)
    marks = [0.0]
    for h, t in TYPES[geo["kind"]]:
        marks += [t, t + h]
    marks.append(20.0)
    X0, Y0, X1, Y1 = geo["canvas"]
    for x in (left, right, x_text):
        line((x, Y0), (x, Y1))
    for m in marks:
        line((X0, top - m * r), (X1, top - m * r))
    if geo["kind"] == "1행":
        line((X0, cy), (X1, cy))
    # 보호공간 경계
    (ax, ay), (bx, by) = tf((ink[0], ink[3])), tf((text[2], ink[1]))
    out.append(f'<rect x="{fmt(ax)}" y="{fmt(ay)}" width="{fmt(bx - ax)}" height="{fmt(by - ay)}"/>')
    out.append(f'<rect x="0" y="0" width="{fmt(W)}" height="{fmt(H)}" stroke-dasharray="1.6 2.1"/>')
    # 원
    px, py = tf((cx, cy))
    out.append(f'<circle cx="{fmt(px)}" cy="{fmt(py)}" r="{fmt(R)}" stroke-dasharray="1.6 2.1"/>')
    out.append("</g>")
    # 치수 라벨
    fs = 2.4 * r * 0.55
    if geo["kind"] == "1행":
        y_left = cy + 2.5 * r
    else:                                        # 규정선과 겹치지 않도록 가장 넓은 칸 가운데
        a, b = max(zip(marks, marks[1:]), key=lambda ab: ab[1] - ab[0])
        y_left = top - (a + b) / 2 * r
    lab = [
        ((cx, (top + Y1) / 2), "2R (R=10r)"),
        (((right + x_text) / 2, (top + Y1) / 2), "5.5r"),
        (((X0 + ink[0]) / 2, y_left), "8r"),
        (((text[2] + X1) / 2 - 0.8 * r, cy - 2.5 * r), "8r"),
        (((X0 + ink[0]) / 2, (ink[3] + Y1) / 2), "5r"),
        (((X0 + ink[0]) / 2, (ink[1] + Y0) / 2), "5r"),
    ]
    for a, b in zip(marks, marks[1:]):
        y = top - (a + b) / 2 * r
        if geo["kind"] == "1행" and a == 5.0:
            y = cy + 2.5 * r                     # 중심축 선과 겹치지 않게
        lab.append(((X1 - 1.6 * r, y), f"{fmt(b - a)}r"))
    out.append(f'<g fill="{c}" font-family="sans-serif" font-size="{fmt(fs)}" text-anchor="middle">')
    for p, t in lab:
        x, y = tf(p)
        out.append(f'<text x="{fmt(x)}" y="{fmt(y + fs * 0.35)}">{t}</text>')
    out.append("</g>")
    return out


def pdf_text_string(s):
    return "<FEFF" + s.encode("utf-16-be").hex().upper() + ">"


def write_pdf(path, title, geo, glyphs):
    """인쇄용 PDF: 정부청색·정부적색은 원본 AI와 같은 별색(Separation), 기관명은 K80."""
    x0, y0, x1, y1 = geo["canvas"]
    W, H = x1 - x0, y1 - y0

    def tf(p):
        return (p[0] - x0, p[1] - y0)

    body = []
    for color, segs in geo["shapes"]:
        _, cmyk, spot = COLORS[color]
        if spot:
            body.append(f"/{spot} cs 1 scn")
        else:
            body.append("{} {} {} {} k".format(*map(fmt, cmyk)))
        body.append(pdf_path(segs, tf))
    body.append("{} {} {} {} k".format(*map(fmt, COLORS["gray"][1])))
    for g in glyphs:
        body.append(pdf_path(g, tf))
    content = ("\n".join(body) + "\n").encode("ascii")

    def sep(spot, cmyk):
        return (f"[/Separation /{spot} /DeviceCMYK << /FunctionType 2 /Domain [0 1] "
                f"/C0 [0 0 0 0] /C1 [{' '.join(map(fmt, cmyk))}] /N 1 >>]").encode()

    box = f"[0 0 {fmt(W)} {fmt(H)}]"
    objs = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        (f"<< /Type /Page /Parent 2 0 R /MediaBox {box} /TrimBox {box} "
         f"/Resources << /ColorSpace << /GOK_Blue 4 0 R /GOK_Red 5 0 R >> >> "
         f"/Contents 6 0 R >>").encode(),
        sep("GOK_Blue", COLORS["blue"][1]),
        sep("GOK_Red", COLORS["red"][1]),
        b"<< /Length %d >>\nstream\n" % len(content) + content + b"endstream",
        (f"<< /Title {pdf_text_string(title)} "
         f"/Subject {pdf_text_string('대한민국 정부상징 ' + TYPE_LABEL[geo['kind']])} >>").encode(),
    ]
    data = bytearray(b"%PDF-1.5\n%\xe2\xe3\xcf\xd3\n")
    offsets = []
    for i, o in enumerate(objs, 1):
        offsets.append(len(data))
        data += b"%d 0 obj\n" % i + o + b"\nendobj\n"
    xref = len(data)
    data += b"xref\n0 %d\n0000000000 65535 f \n" % (len(objs) + 1)
    for off in offsets:
        data += b"%010d 00000 n \n" % off
    data += b"trailer\n<< /Size %d /Root 1 0 R /Info 7 0 R >>\nstartxref\n%d\n%%%%EOF\n" % (
        len(objs) + 1, xref)
    with open(path, "wb") as f:
        f.write(data)


def write_png(svg, png, width_pt, px_per_pt):
    """백색배경(기본형 원칙)의 불투명 PNG."""
    import io

    import cairosvg
    from PIL import Image
    data = cairosvg.svg2png(url=svg, output_width=round(width_pt * px_per_pt))
    im = Image.open(io.BytesIO(data)).convert("RGBA")
    flat = Image.new("RGB", im.size, "white")
    flat.paste(im, mask=im.getchannel("A"))
    flat.save(png, dpi=(72 * px_per_pt, 72 * px_per_pt))


def write_preview(pngs, path, gap=24):
    from PIL import Image
    ims = [Image.open(p) for p in pngs]
    w = max(i.width for i in ims)
    h = sum(i.height for i in ims) + gap * (len(ims) - 1)
    sheet = Image.new("RGB", (w, h), "white")
    y = 0
    for i, im in enumerate(ims):
        sheet.paste(im, (0, y))
        y += im.height
        if i < len(ims) - 1:
            sheet.paste((225, 225, 225), (0, y + gap // 2, w, y + gap // 2 + 2))
            y += gap
    sheet.save(path)


def build(font, name, kind, parent):
    """(제목, 글리프, 기하) — kind 가 1행이면 기관명만, A/B 이면 본부명/기관명 2행."""
    if kind == "1행":
        n = len(name)
        if n <= 3 or n >= 10:
            raise SystemExit(f"{name}: {n}자 — 3자 이하(110%)/10자 이상(85%) 규정은 이 스크립트 범위 밖입니다.")
        glyphs = layout(font, name)
        title = name
    else:
        if not parent:
            raise SystemExit(f"{kind} type 은 --parent(본부명)가 필요합니다.")
        glyphs = layout_lines(font, [parent, name], kind)
        title = f"{parent} {name}"
    return title, glyphs, geometry(glyphs, kind)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--font", required=True, help="정부상징체.ttf 경로")
    ap.add_argument("--out", default="logos", help="출력 폴더")
    ap.add_argument("--type", default="1행", choices=sorted(TYPES), help="조합 형식 (기본: 1행)")
    ap.add_argument("--parent", help="본부명 (A/B type 1행째, 예: 고용노동부)")
    ap.add_argument("--filename", help="파일명 형식 (기본: 1행 '{name}_국문_좌우_1행', 2행 '{name}_국문_좌우_2행')")
    ap.add_argument("--px-per-pt", type=float, default=8.0, help="PNG 해상도 (pt 당 픽셀)")
    ap.add_argument("names", nargs="*", default=NAMES, help="기관명 (기본: 지방국세청 7곳)")
    args = ap.parse_args()

    font = Font(args.font)
    pattern = args.filename or ("{name}_국문_좌우_1행" if args.type == "1행" else "{name}_국문_좌우_2행")
    for d in ("svg", "pdf", "png"):
        os.makedirs(os.path.join(args.out, d), exist_ok=True)

    pngs = []
    for name in args.names:
        title, glyphs, geo = build(font, name, args.type, args.parent)
        base = pattern.format(name=name)
        svg = os.path.join(args.out, "svg", base + ".svg")
        W, _ = write_svg(svg, title, geo, glyphs)
        write_pdf(os.path.join(args.out, "pdf", base + ".pdf"), title, geo, glyphs)
        png = os.path.join(args.out, "png", base + ".png")
        write_png(svg, png, W, args.px_per_pt)
        pngs.append(png)
        r = geo["r"]
        t = geo["text"]
        print(f"{title}: 캔버스 {W / r:.2f}r x {(geo['canvas'][3] - geo['canvas'][1]) / r:.2f}r, "
              f"간격 {(t[0] - geo['cx'] - geo['R']) / r:.2f}r, 기관명 폭 {(t[2] - t[0]) / r:.2f}r")

    # 규정선 검증 이미지 (첫 번째 기관)
    name = args.names[0]
    title, glyphs, geo = build(font, name, args.type, args.parent)
    guide_svg = os.path.join(args.out, "구성규정_" + name + ".svg")
    W, _ = write_svg(guide_svg, title, geo, glyphs, guides=True)
    write_png(guide_svg, guide_svg[:-4] + ".png", W, args.px_per_pt)
    os.remove(guide_svg)
    write_preview(pngs, os.path.join(args.out, "미리보기.png"))


if __name__ == "__main__":
    main()
