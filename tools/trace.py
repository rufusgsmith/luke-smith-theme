# Trace greyscale logo PNGs into small vector drawings (stdlib only). Each logo is cropped to its ink and
# sized for equal visual weight (see `sizes`), scaled to DETAIL times that size, and split into a few grey
# tones; each tone becomes a layer outlined by marching squares (darker layers on top, so tones nest).
# Usage: python3 -I tools/trace.py hooks/logos.ts   (run from the mod folder)
import sys, zlib, struct

# Top to bottom: name, file in assets/, and areas to blank out first as (x0, y0, x1, y1) in the
# file's pixels, None running to the edge; used to drop taglines and strap lines.
LOGOS = [
    ('Frameworks', 'frameworks.png', [(0, 840, None, None)]),  # the FRAMEWORKS wordmark
    ('TPM Co', 'tpm-co.png', [(0, 410, None, None)]),  # the rule and THE PROPERTY MAINTENANCE CO.
    ('Signtech Media', 'signtech-media.png', [(520, 446, None, None)]),  # Out of Home Advertising (right of the g)
    ('Signtech', 'signtech.png', []),
    ('Sarre & Company', 'sarre-and-company.png', [(0, 814, None, None)]),  # CHARTERED SURVEYORS
    ('Purpose', 'purpose.png', [(0, 580, None, None)]),  # Building better businesses.
    ('Assured Property Management', 'assured-property-management.png', []),
    ('Maillard & Co', 'maillard-and-co.png', []),
    ('Rowlands', 'rowlands.png', [(0, 274, None, None)]),  # Building careers since 1975
    ('AllSorted', 'allsorted.png', []),
]

COLUMN_W, COLUMN_H, GAP = 230, 920, 24  # the column's room in backdrop units (clear of the title bar), and the space between logos
INK_WEIGHT = .35  # how much a logo's ink density counts against its area (0: equal boxes, 1: equal ink)
WIDE = .4  # how fast width grows with a logo's aspect ratio (.5: equal area, lower reins in long wordmarks)
INK = .7  # every logo's darkest tone is drawn at this darkness (0 white, 1 black); lighter tones scale with it
DETAIL = 3.5  # trace at 3.5x the drawn size: finer than the screen, far smaller than the source

def darkness(src):  # 0 white .. 1 black, composited on white
    d = open(src, 'rb').read(); assert d[:8] == b'\x89PNG\r\n\x1a\n'
    i, idat = 8, b''
    while i < len(d):
        n, t = struct.unpack('>I4s', d[i:i+8]); c = d[i+8:i+8+n]; i += 12 + n
        if t == b'IHDR': w, h, bd, ct, _, _, il = struct.unpack('>IIBBBBB', c)
        elif t == b'IDAT': idat += c
    assert bd == 8 and ct in (2, 6) and il == 0, (bd, ct, il)
    bpp = 4 if ct == 6 else 3; raw = zlib.decompress(idat); stride = w * bpp
    out, prev, p = [], bytearray(stride), 0
    for y in range(h):
        f = raw[p]; line = bytearray(raw[p+1:p+1+stride]); p += 1 + stride
        for x in range(stride):
            a = line[x-bpp] if x >= bpp else 0; b = prev[x]; cc = prev[x-bpp] if x >= bpp else 0
            if f == 1: line[x] = (line[x] + a) & 255
            elif f == 2: line[x] = (line[x] + b) & 255
            elif f == 3: line[x] = (line[x] + (a + b) // 2) & 255
            elif f == 4:
                pa, pb, pc = abs(b - cc), abs(a - cc), abs(a + b - 2*cc)
                line[x] = (line[x] + (a if pa <= pb and pa <= pc else b if pb <= pc else cc)) & 255
        row = []
        for x in range(w):
            o = x * bpp; al = line[o+3] / 255 if bpp == 4 else 1
            row.append(al * (1 - (.2126 * line[o] + .7152 * line[o+1] + .0722 * line[o+2]) / 255))
        out.append(row); prev = line
    return out

def resample(g, x0, y0, x1, y1, tw, th):  # area average of the crop onto tw x th
    sx, sy = (x1 - x0) / tw, (y1 - y0) / th
    cols = [(x0 + int(i * sx), max(x0 + int(i * sx) + 1, x0 + int((i + 1) * sx))) for i in range(tw)]
    out = []
    for j in range(th):
        r0 = y0 + int(j * sy); r1 = max(r0 + 1, y0 + int((j + 1) * sy))
        rows = g[r0:r1]
        out.append([sum(sum(r[a:b]) for r in rows) / ((b - a) * len(rows)) for a, b in cols])
    return out

def tones(g):  # 1-D k-means on flat (non-edge) inked pixels; close tones merge
    flat = sorted(g[y][x] for y in range(1, len(g) - 1) for x in range(1, len(g[0]) - 1)
                  if g[y][x] > .08 and max(abs(g[y][x] - g[y+dy][x+dx]) for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))) < .04)
    if not flat: return [.8]
    cs = [flat[int(len(flat) * q)] for q in (.125, .375, .625, .875)]
    for _ in range(25):
        groups = [[] for _ in cs]
        for v in flat: groups[min(range(len(cs)), key=lambda k: abs(v - cs[k]))].append(v)
        cs = [sum(gr) / len(gr) for gr in groups if gr]
    merged = []
    for c in sorted(cs):
        if merged and c - merged[-1] < .12: merged[-1] = (merged[-1] + c) / 2
        else: merged.append(c)
    return merged

def contours(g, iso):  # marching squares; closed loops in grid units
    gh, gw = len(g), len(g[0])
    def pt(e):
        kind, x, y = e
        a, b = (g[y][x], g[y][x+1]) if kind == 'h' else (g[y][x], g[y+1][x])
        t = (iso - a) / (b - a)
        return (x + t, y) if kind == 'h' else (x, y + t)
    adj = {}
    for y in range(gh - 1):
        r0, r1 = g[y], g[y+1]
        for x in range(gw - 1):
            tl, tr, br, bl = r0[x] >= iso, r0[x+1] >= iso, r1[x+1] >= iso, r1[x] >= iso
            if tl == tr == br == bl: continue
            T, R, B, L = ('h', x, y), ('v', x+1, y), ('h', x, y+1), ('v', x, y)
            cut = [e for e, on in ((T, tl != tr), (R, tr != br), (B, br != bl), (L, bl != tl)) if on]
            if len(cut) == 4:
                mid = (r0[x] + r0[x+1] + r1[x+1] + r1[x]) / 4 >= iso
                segs = [(T, R), (B, L)] if tl == mid else [(T, L), (R, B)]
            else:
                segs = [tuple(cut)]
            for a, b in segs: adj.setdefault(a, []).append(b); adj.setdefault(b, []).append(a)
    loops, done = [], set()
    for start in adj:
        if start in done: continue
        loop, prev, cur = [], None, start
        while cur not in done:
            done.add(cur); loop.append(pt(cur))
            nxt = [e for e in adj[cur] if e != prev and e not in done]
            prev, cur = cur, (nxt[0] if nxt else start)
        loops.append(loop)
    return loops

def simplify(p, eps):  # Douglas-Peucker on an open run
    if len(p) < 3: return p
    (ax, ay), (bx, by) = p[0], p[-1]; dx, dy = bx - ax, by - ay; n = (dx*dx + dy*dy) ** .5 or 1
    i, dm = max(((i, abs((q[0]-ax)*dy - (q[1]-ay)*dx) / n) for i, q in enumerate(p[1:-1], 1)), key=lambda t: t[1])
    return simplify(p[:i+1], eps)[:-1] + simplify(p[i:], eps) if dm > eps else [p[0], p[-1]]

K = [2.718 ** (-k * k / (2 * .6 ** 2)) for k in range(-2, 3)]; KS = sum(K)

def outline(loop):
    n = len(loop)
    if n < 4 or abs(sum(loop[i-1][0] * loop[i][1] - loop[i][0] * loop[i-1][1] for i in range(n))) / 2 < 3: return ''  # specks
    loop = [tuple(sum(K[k] * loop[(i + k - 2) % n][a] for k in range(5)) / KS for a in (0, 1)) for i in range(n)]
    i0 = max(range(n), key=lambda i: (loop[i][0] - loop[0][0])**2 + (loop[i][1] - loop[0][1])**2)
    pts = simplify(loop[:i0+1], .3)[:-1] + simplify(loop[i0:] + [loop[0]], .3)[:-1]
    # Padded grid point (x, y) is the centre of pixel x - 1, i.e. x - .5 in the drawing.
    return 'M' + 'L'.join(f'{round(x - .5)} {round(y - .5)}' for x, y in pts) + 'Z'

def sizes(logos):
    # Roughly equal area looks equal in size across wide and compact logos, though long one-line
    # wordmarks still read big, so width grows with aspect ** WIDE (.5 would be equal area). Dense,
    # bold logos get a little less and light, airy ones a little more. The area is the largest that
    # keeps every logo within the column's width and the whole stack within its height.
    inks = sorted(ink for _, ink in logos); mid = inks[len(inks) // 2]
    def at(area): return [((area / (ink / mid) ** INK_WEIGHT) ** .5 * a ** WIDE, (area / (ink / mid) ** INK_WEIGHT) ** .5 * a ** (WIDE - 1)) for a, ink in logos]
    lo, hi = 1, 1e6
    for _ in range(60):
        area = (lo + hi) / 2; s = at(area)
        fits = max(w for w, _ in s) <= COLUMN_W and sum(h for _, h in s) + GAP * (len(s) - 1) <= COLUMN_H
        lo, hi = (area, hi) if fits else (lo, area)
    return at(lo)

crops = []
for name, file, blanks in LOGOS:
    g = darkness(f'assets/{file}'); h, w = len(g), len(g[0])
    for bx0, by0, bx1, by1 in blanks:
        for y in range(by0, by1 or h): g[y][bx0:bx1 or w] = [0.0] * ((bx1 or w) - bx0)
    ys = [y for y in range(h) if sum(v > .1 for v in g[y]) > 1]; xs = [x for x in range(w) if sum(g[y][x] > .1 for y in ys) > 1]
    x0, x1, y0, y1 = max(xs[0] - 2, 0), min(xs[-1] + 3, w), max(ys[0] - 2, 0), min(ys[-1] + 3, h)
    ink = sum(sum(r[x0:x1]) for r in g[y0:y1]) / ((x1 - x0) * (y1 - y0))
    crops.append((name, g, x0, y0, x1, y1, ink))

entries = []
for (name, g, x0, y0, x1, y1, ink), (dw, dh) in zip(crops, sizes([((c[4] - c[2]) / (c[5] - c[3]), c[6]) for c in crops])):
    tw, th = round(dw * DETAIL), round(dh * DETAIL)
    small = resample(g, x0, y0, x1, y1, tw, th)
    padded = [[0.0] * (tw + 2)] + [[0.0] + r + [0.0] for r in small] + [[0.0] * (tw + 2)]
    cs = tones(small); layers = ''
    for k, c in enumerate(cs):
        iso = c / 2 if k == 0 else (cs[k-1] + c) / 2
        d = ''.join(outline(loop) for loop in contours(padded, iso))
        grey = round(255 * (1 - INK * c / cs[-1]))
        if d: layers += f'<path fill="#{grey:02x}{grey:02x}{grey:02x}" d="{d}"/>'
    svg = f'<svg xmlns="http://www.w3.org/2000/svg" width="{dw:.1f}" height="{dh:.1f}" viewBox="0 0 {tw} {th}" fill-rule="evenodd">{layers}</svg>'
    entries.append(f"  {{ name: '{name}', width: {dw:.1f}, height: {dh:.1f}, svg: '{svg}' }},")
    print(f'{name}: {dw:.0f}x{dh:.0f}, tones {[round(c, 2) for c in cs]}, chars {len(svg)}')
open(sys.argv[1], 'w').write(f'// Generated by tools/trace.py from assets/*.png, top to bottom.\nexport const COLUMN_WIDTH = {COLUMN_W}\nexport const GAP = {GAP}\nexport const LOGOS = [\n' + '\n'.join(entries) + '\n]\n')
print('total chars', sum(len(e) for e in entries))
