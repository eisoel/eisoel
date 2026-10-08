#!/usr/bin/env python3
"""2023 AFC 아시안컵 국가별 아이콘 SVG 생성기.

카타르·우즈베키스탄 아이콘 SVG(기준 파일)의 마름모 클립·테두리 구조는 그대로 두고,
그 안의 국기만 각국 국기 SVG 마크업으로 바꿔 넣는다.
국기의 크기·위치는 각국 PNG 아이콘(240×240)에서 잰 값(CONFIG)을 쓴다.

    python3 tools/build_afc_icons.py --flags 국기폴더 --out 아시안컵/svg [--preview 아시안컵/미리보기.png]

국기폴더에는 `<국호> 국기.svg` 파일이 있어야 한다 (이란은 `원형국기/이란.svg` 를 `이란 국기.svg` 로).
"""
import argparse
import io
import os
import re
import xml.etree.ElementTree as ET

SVG = 'http://www.w3.org/2000/svg'
XL = 'http://www.w3.org/1999/xlink'
ET.register_namespace('', SVG)
ET.register_namespace('xlink', XL)

# ---- 기준 SVG 구조 (2023 AFC 아시안컵 카타르/우즈베키스탄 아이콘.svg 와 동일) ----
# 국기는 클립 그룹 안쪽 좌표(inner = 최종 좌표 + (190.225, 1001.586))에 그린다.
OX, OY = 190.225, 1001.586
CX = CY = 24.556                    # 마름모 중심 (최종 좌표)
DIAMOND_CLIP = ('<clipPath xmlns="%s" id="a"><path fill="none" stroke="#c9c9c9" d="m221.852 1008.657 '
                '17.485 17.485-17.485 17.486a10 10 0 0 1-14.142 0l-17.485-17.486 17.485-17.485a10 10 0 0 1 '
                '14.142 0Z"/></clipPath>' % SVG)
BORDER = ('<g xmlns="%s" fill="none" stroke="#c9c9c9"><path stroke="none" d="m31.627 7.071 17.485 17.485-17.485 '
          '17.486a10 10 0 0 1-14.142 0L0 24.556 17.485 7.071a10 10 0 0 1 14.142 0Z"/><path d="m31.274 7.425 '
          '17.131 17.131-17.131 17.132a9.5 9.5 0 0 1-13.436 0L.707 24.556 17.838 7.425a9.5 9.5 0 0 1 13.436 '
          '0Z"/></g>' % SVG)
BG_RECT = 'M190.225 1005.64h49.112v41h-49.112z'   # 마름모 전체 (카타르 국기 영역과 같은 높이)

# ---- PNG(240×240) → SVG 변환 ----
# 줄무늬 국기는 PNG 에서 높이 180px 이고, 우즈베키스탄 기준 SVG 국기 높이는 39.304 이다.
KY = 180 / 39.304                   # PNG px / SVG unit
PCX, PCY = 120.11, 120.4            # PNG 마름모 중심 ↔ SVG 마름모 중심

PRESENTATION = {
    'fill', 'fill-rule', 'fill-opacity', 'clip-rule', 'stroke', 'stroke-width', 'stroke-linecap',
    'stroke-linejoin', 'stroke-miterlimit', 'stroke-dasharray', 'stroke-dashoffset', 'stroke-opacity',
    'opacity', 'display', 'visibility', 'color',
}


def fmt(v):
    s = ('%.4f' % v).rstrip('0').rstrip('.')
    if s in ('-0', ''):
        s = '0'
    if s.startswith('0.'):
        s = s[1:]
    elif s.startswith('-0.'):
        s = '-' + s[2:]
    return s


def fmts(v, sig=7):
    """배율용 (유효숫자 기준)"""
    s = '%.*g' % (sig, v)
    if 'e' in s:
        s = ('%.12f' % v).rstrip('0').rstrip('.')
    if s.startswith('0.'):
        s = s[1:]
    elif s.startswith('-0.'):
        s = '-' + s[2:]
    return s


def local_tag(el):
    return el.tag.split('}', 1)[-1] if isinstance(el.tag, str) else ''


def parse_css(text):
    rules = []
    text = re.sub(r'/\*.*?\*/', '', text, flags=re.S)
    for sel, body in re.findall(r'([^{}]+)\{([^}]*)\}', text):
        decls = [tuple(x.strip() for x in d.split(':', 1)) for d in body.split(';') if ':' in d]
        for s in sel.split(','):
            s = s.strip()
            if not re.fullmatch(r'\.[\w-]+', s):
                raise ValueError('unsupported selector: %r' % s)
            rules.append((s[1:], decls))
    return rules


class Flag:
    """국기 SVG. CSS 클래스·style 속성은 표현 속성으로 풀고, 편집기 흔적과 보이지 않는 도형은 지운다."""

    def __init__(self, path, rect=None):
        self.path = path
        self.root = ET.parse(path).getroot()
        vb = self.root.get('viewBox')
        if vb:
            self.vb = tuple(float(x) for x in re.split(r'[\s,]+', vb.strip()))
        else:
            self.vb = (0.0, 0.0, float(self.root.get('width')), float(self.root.get('height')))
        self.rect = rect or self.vb        # 국기 사각형 (국기 좌표)
        self._normalize()

    def _normalize(self):
        root = self.root
        rules = []
        for st in list(root.iter('{%s}style' % SVG)):
            rules += parse_css(st.text or '')
        for parent in list(root.iter()):
            for ch in list(parent):
                if local_tag(ch) == 'style':
                    parent.remove(ch)
        for el in root.iter():
            cls = el.get('class')
            if cls:
                names = cls.split()
                for name, decls in rules:
                    if name in names:
                        for k, v in decls:
                            el.set(k, v)
                del el.attrib['class']
            st = el.get('style')
            if st:
                for k, v in [tuple(x.strip() for x in d.split(':', 1)) for d in st.split(';') if ':' in d]:
                    if k not in PRESENTATION:
                        raise ValueError('unsupported style prop %s in %s' % (k, self.path))
                    el.set(k, v)
                del el.attrib['style']
            for k in list(el.attrib):
                if k.startswith('{http://www.w3.org/XML/1998/namespace}') or k.startswith('data-'):
                    del el.attrib[k]

        def has_stroke(anc):
            return any(e.get('stroke') not in (None, 'none') for e in anc)

        def prune(el, anc):
            for ch in list(el):
                t = local_tag(ch)
                if t in ('defs', 'clipPath', 'mask', 'symbol'):
                    continue
                if t in ('rect', 'path', 'circle', 'ellipse', 'polygon') and ch.get('fill') == 'none' \
                        and not has_stroke(anc + [el, ch]) and len(ch) == 0:
                    el.remove(ch)
                    continue
                prune(ch, anc + [el])
        prune(root, [])
        changed = True
        while changed:
            changed = False
            for parent in list(root.iter()):
                for ch in list(parent):
                    if local_tag(ch) in ('g', 'defs') and len(ch) == 0:
                        parent.remove(ch)
                        changed = True

    def root_attrs(self):
        return {k: v for k, v in self.root.attrib.items() if k in PRESENTATION}


def rename_ids(elements, start='c'):
    """참조되는 id 는 c, d, e… 로 바꾸고(기준 파일의 a·b 와 겹치지 않게) 나머지 id 는 지운다."""
    href = '{%s}href' % XL
    refs = set()
    for top in elements:
        for el in top.iter():
            for k, v in el.attrib.items():
                refs.update(re.findall(r'url\(#([^)]+)\)', v))
                if k in (href, 'href') and v.startswith('#'):
                    refs.add(v[1:])
    names = iter(chr(c) for c in range(ord(start), ord('z') + 1))
    mapping = {}
    for top in elements:
        for el in top.iter():
            i = el.get('id')
            if i is None:
                continue
            if i in refs:
                mapping[i] = next(names)
                el.set('id', mapping[i])
            else:
                del el.attrib['id']
    for top in elements:
        for el in top.iter():
            for k, v in list(el.attrib.items()):
                nv = re.sub(r'url\(#([^)]+)\)', lambda m: 'url(#%s)' % mapping[m.group(1)], v)
                if k in (href, 'href') and v.startswith('#'):
                    nv = '#' + mapping[v[1:]]
                if nv != v:
                    el.set(k, nv)


def compose(flag, height, cx, cy, bg=None):
    """국기 사각형을 높이 height(SVG 단위)로, 중심을 (cx, cy)(최종 좌표)에 둔 아이콘 SVG 문자열."""
    fx, fy, fw, fh = flag.rect
    s = height / fh
    tx = OX + cx - fw * s / 2 - fx * s
    ty = OY + cy - height / 2 - fy * s

    svg = ET.Element('{%s}svg' % SVG, {'width': '49.112', 'height': '49.112', 'viewBox': '0 0 49.112 49.112'})
    defs = ET.SubElement(svg, '{%s}defs' % SVG)
    defs.append(ET.fromstring(DIAMOND_CLIP))
    cp = ET.SubElement(defs, '{%s}clipPath' % SVG, {'id': 'b'})
    ET.SubElement(cp, '{%s}path' % SVG, {'d': 'M%s %sh%sv%sH%sz' % (fmt(fx), fmt(fy), fmt(fw), fmt(fh), fmt(fx))})
    g = ET.SubElement(svg, '{%s}g' % SVG, {'clip-path': 'url(#a)', 'transform': 'translate(-190.225 -1001.586)'})
    if bg:
        ET.SubElement(g, '{%s}path' % SVG, {'fill': bg, 'd': BG_RECT})
    attrs = {'clip-path': 'url(#b)', 'transform': 'matrix(%s 0 0 %s %s %s)' % (fmts(s), fmts(s), fmt(tx), fmt(ty))}
    attrs.update(flag.root_attrs())
    fg = ET.SubElement(g, '{%s}g' % SVG, attrs)
    kids = list(flag.root)
    for ch in kids:
        fg.append(ch)
    rename_ids(kids)
    svg.append(ET.fromstring(BORDER))
    return ET.tostring(svg, encoding='unicode').replace(' />', '/>')


# ---- 국기 안 요소를 PNG 배치에 맞추는 보정 (PNG 가 국기 안 요소를 옮겨 그린 나라) ----
class Place:
    """PNG 좌표 → 국기 좌표 (CONFIG 의 h, cx, cy 기준)"""

    def __init__(self, flag, c):
        fx, fy, fw, fh = flag.rect
        self.m = c['h'] / fh
        self.left = c.get('cx', PCX) - fw * self.m / 2
        self.top = c.get('cy', PCY) - c['h'] / 2
        self.fx, self.fy = fx, fy

    def pt(self, px, py):
        return self.fx + (px - self.left) / self.m, self.fy + (py - self.top) / self.m


def move_group(flag, els, src_bbox, dst_png_bbox, P):
    """els 를 g 로 묶어 국기 좌표 src_bbox 가 PNG 좌표 dst_png_bbox 에 오도록 균일 배율로 옮긴다."""
    sx0, sy0, sx1, sy1 = src_bbox
    dx0, dy0, dx1, dy1 = dst_png_bbox
    kw = (dx1 - dx0) / P.m / (sx1 - sx0)
    kh = (dy1 - dy0) / P.m / (sy1 - sy0)
    k = (kw * kh) ** .5
    tcx, tcy = P.pt((dx0 + dx1) / 2, (dy0 + dy1) / 2)
    tx = tcx - k * (sx0 + sx1) / 2
    ty = tcy - k * (sy0 + sy1) / 2
    root = flag.root
    idx = list(root).index(els[0])
    g = ET.Element('{%s}g' % SVG, {'transform': 'matrix(%s 0 0 %s %s %s)' % (fmts(k), fmts(k), fmt(tx), fmt(ty))})
    for e in els:
        root.remove(e)
        g.append(e)
    root.insert(idx, g)


def tajik_cleanup(flag, c):
    # 국기 파일에 같은 그림이 두 벌 겹쳐 있고 그 사이에 작업용 안내선(stroke #373435)이 있다.
    # 위 벌이 아래 벌과 안내선을 완전히 덮으므로, 보이는 위 벌만 남긴다.
    layer = flag.root[0]
    for ch in list(layer):
        if ch.get('id') == '_1759493418608' or ch.get('stroke') == '#373435':
            layer.remove(ch)


def oman_emblem(flag, c):
    # PNG 는 국장(엠블럼)을 붉은 세로띠 오른쪽으로 옮기고 키웠다.
    els = list(flag.root)[4:]
    move_group(flag, els, (78, 22, 265, 209), (58, 48, 117.5, 106), Place(flag, c))


def malaysia_emblem(flag, c):
    # PNG 는 초승달·별을 줄여 칸톤 가운데에 두었다.
    els = [e for e in flag.root if e.get('fill') == '#fc0']
    move_group(flag, els, (1320, 480, 5320, 3360), (65, 68, 126, 116), Place(flag, c))


def australia(flag, c):
    # PNG 는 유니언 잭(칸톤)을 약 1.44:1 상자에 그렸고, 별은 약 0.43배로 줄여 마름모 안에 모았다.
    # → 칸톤: 국기 파일의 구성(대각선 흰 0.6·붉은 0.4 반전 클립, 십자 흰 840·붉은 504)과
    #   선 굵기 비율은 그대로 두고, 상자 크기·위치만 PNG (4.25, 35.75) 125×86.75px 에 맞춘다.
    #   선 굵기는 상자 높이 기준의 0.738배(가로 125px 유니언 잭과 같은 굵기).
    # → 별: 위치·크기를 PNG 에 맞춘다(별 모양은 국기 파일의 use 그대로).
    P = Place(flag, c)
    X0, Y0 = P.pt(4.25, 35.75)
    X1, Y1 = P.pt(4.25 + 125, 35.75 + 86.75)
    sx, sy = (X1 - X0) / 6, (Y1 - Y0) / 3          # 국기 파일의 6×3 유니언 잭 단위
    k = 0.738 * (Y1 - Y0) / 2520                    # 국기 파일 단위 선 굵기 배율

    def pt(x, y):
        return '%s %s' % (fmt(X0 + x * sx), fmt(Y0 + y * sy))
    root = flag.root
    defs = [e for e in root if local_tag(e) == 'defs'][0]
    clips = {cp.get('id'): cp[0] for cp in defs if local_tag(cp) == 'clipPath'}
    clips['a'].set('d', 'M%sH%sV%sH%sz' % (pt(0, 0), fmt(X1), fmt(Y1), fmt(X0)))
    clips['b'].set('d', 'M%sL%sL%sL%szM%sL%sL%sL%sz' % (pt(0, 0), pt(0, 1.5), pt(6, 1.5), pt(6, 3),
                                                      pt(6, 0), pt(3, 0), pt(3, 3), pt(0, 3)))
    diag = 'M%sL%sM%sL%s' % (pt(0, 0), pt(6, 3), pt(6, 0), pt(0, 3))
    cross = 'M%sV%sM%sH%s' % (pt(3, 0), fmt(Y1), pt(0, 1.5), fmt(X1))
    for e in [e for e in root if local_tag(e) == 'path' and e.get('stroke')]:
        if e.get('transform') == 'scale(840)':            # 대각선 (6×3 단위, 굵기 0.6 / 0.4)
            e.attrib.pop('transform')
            e.set('stroke-width', fmt(float(e.get('stroke-width')) * 840 * k))
            e.set('d', diag)
        else:                                             # 십자 (굵기 840 / 504)
            e.set('stroke-width', fmt(float(e.get('stroke-width')) * k))
            e.set('d', cross)
    stars = [e for e in root if local_tag(e) == 'g' and e.get('fill') == '#fff'][0]
    # 국기 파일 순서: 연방의 별(2.1배), Alpha, Beta, Gamma, Delta, Epsilon
    targets = [(102.9, 156.7, 2.1), (170.7, 155.2, 1), (148.3, 120.0, 1),
               (170.8, 96.0, 1), (190.1, 114.2, 1), (179.4, 129.1, 1)]
    for u, (px, py, base) in zip(list(stars), targets):
        X, Y = P.pt(px, py)
        for a in ('x', 'y', 'transform'):
            u.attrib.pop(a, None)
        s = base * 0.43
        u.set('transform', 'matrix(%s 0 0 %s %s %s)' % (fmts(s), fmts(s), fmt(X), fmt(Y)))


# h : PNG 상 국기 높이(px)    cx, cy : PNG 상 국기 사각형 중심(px, 기본 = 마름모 중심)
# bg: 국기가 마름모를 다 덮지 못할 때 깔 바탕색(국기 가장자리 색)
# rect: 국기 사각형(국기 좌표, 기본 = viewBox)   post: 국기 안 요소 보정   file: 국기 파일명(기본 `<국호> 국기.svg`)
CONFIG = {
    '대한민국':     dict(h=120, cy=120.25, bg='#fff'),
    '일본':        dict(h=155.25, cy=120.25, bg='#fff'),
    '중국':        dict(h=127.5, cx=139.1, cy=121.5, bg='#ee1c25'),
    '타지키스탄':   dict(h=181.25, cy=120.5, post=tajik_cleanup),
    '레바논':      dict(h=151.25, cy=120.5, bg='#d31624'),
    '호주':        dict(h=180, cx=130, cy=120.5, post=australia),
    '시리아':      dict(h=179.75, cy=120.5, file='시리아 국기(1980-2024).svg'),
    '인도':        dict(h=180, cy=120.5),
    '이란':        dict(h=187.5, cx=119.86, cy=120, rect=(1, 1, 1134, 648)),
    '아랍에미리트': dict(h=179.25, cx=180.2, cy=120.25),
    '홍콩':        dict(h=179.75, cx=120.25, cy=120.25),
    '팔레스타인':   dict(h=180.5, cx=193.6, cy=120.5),
    '인도네시아':   dict(h=180, cy=120.5),
    '이라크':      dict(h=195, cy=119),
    '베트남':      dict(h=155.5, cy=120.35, bg='#da251d'),
    '말레이시아':   dict(h=208.25, cx=146.25, cy=120.25, post=malaysia_emblem),
    '요르단':      dict(h=180.25, cx=157.5, cy=120.5),
    '바레인':      dict(h=178.25, cx=168, cy=120.25, bg='#fff'),
    '사우디아라비아': dict(h=156.5, cy=126.75, bg='#005430'),
    '태국':        dict(h=180, cy=120.5),
    '키르기스스탄': dict(h=154, cy=121, bg='red'),
    '오만':        dict(h=179.5, cx=170.7, cy=120.5, post=oman_emblem),
}

FILENAME = '2023 AFC 아시안컵 {name} 아이콘.svg'


def build(name, flags_dir, out_dir):
    c = CONFIG[name]
    flag = Flag(os.path.join(flags_dir, c.get('file', '%s 국기.svg' % name)), c.get('rect'))
    if c.get('post'):
        c['post'](flag, c)
    cx = CX + (c.get('cx', PCX) - PCX) / KY
    cy = CY + (c.get('cy', PCY) - PCY) / KY
    out = os.path.join(out_dir, FILENAME.format(name=name))
    with open(out, 'w', encoding='utf-8') as f:
        f.write(compose(flag, c['h'] / KY, cx, cy, bg=c.get('bg')))
    return out


def preview(paths, out, cols=6, size=200, gap=24):
    import cairosvg
    from PIL import Image
    rows = (len(paths) + cols - 1) // cols
    sheet = Image.new('RGB', (cols * (size + gap) + gap, rows * (size + gap) + gap), 'white')
    for i, p in enumerate(paths):
        png = cairosvg.svg2png(url=p, output_width=size, output_height=size)
        im = Image.open(io.BytesIO(png)).convert('RGBA')
        sheet.paste(im, (gap + (i % cols) * (size + gap), gap + (i // cols) * (size + gap)), im)
    sheet.save(out)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--flags', required=True, help='`<국호> 국기.svg` 가 있는 폴더')
    ap.add_argument('--out', required=True)
    ap.add_argument('--preview', help='미리보기 PNG 경로 (cairosvg, pillow 필요)')
    ap.add_argument('names', nargs='*', help='국호 (생략하면 22개국 모두)')
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    paths = [build(n, a.flags, a.out) for n in (a.names or CONFIG)]
    for p in paths:
        print(p)
    if a.preview:
        preview(paths, a.preview)


if __name__ == '__main__':
    main()
