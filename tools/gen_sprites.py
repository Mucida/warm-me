"""Gera os sprites pixel-art do warm-me (fogo e floco de gelo) como SVG animado (SMIL)
e uma prévia PNG. Uso: python3 -I tools/gen_sprites.py hooks/sprites.ts previa.png"""
import math
import sys
from PIL import Image

# ---------- fogo ----------
FW, FH = 18, 22
FIRE_PAL = {
    'K': '#1a0a06', 'D': '#8e1b0e', 'R': '#d2321a', 'O': '#f2661f',
    'L': '#ff9a2e', 'Y': '#ffcf40', 'W': '#fff1b0', 'S': '#ff5a1f', 's': '#c0200f',
}

# (inclinação do topo, lado da língua lateral, faíscas) por quadro
FIRE_FRAMES = [
    (-2.2, +1, [(3, 2, 'S'), (14, 6, 'S'), (2, 9, 's'), (15, 11, 'S')]),
    (-0.8, -1, [(5, 1, 'S'), (13, 3, 's'), (1, 10, 'S'), (16, 8, 'S')]),
    (+1.2, +1, [(7, 0, 'S'), (14, 2, 'S'), (2, 6, 's'), (16, 12, 'S')]),
    (+2.2, -1, [(11, 1, 's'), (3, 4, 'S'), (16, 7, 'S'), (1, 13, 'S')]),
    (+0.6, +1, [(9, 0, 'S'), (2, 3, 'S'), (15, 5, 's'), (16, 10, 'S')]),
    (-1.5, -1, [(4, 0, 's'), (12, 1, 'S'), (1, 7, 'S'), (15, 12, 'S')]),
]

BASE_Y = 19  # linha de baixo da chama


def fire_frame(lean, side, sparks):
    g = [['.'] * FW for _ in range(FH)]
    inside = [[False] * FW for _ in range(FH)]
    top = 4
    for y in range(top, BASE_Y + 1):
        t = (BASE_Y - y) / (BASE_Y - top)          # 0 embaixo, 1 no topo
        if t < 0.22:
            w = 6.9 * math.sqrt(max(0.0, 1 - ((0.22 - t) / 0.30) ** 2))
        else:
            w = 6.9 * (1 - t) ** 0.85 + 0.6
        c = 8.5 + 1.4 * lean * t ** 2
        for x in range(FW):
            if abs(x + 0.5 - c) <= w:
                inside[y][x] = True
        # língua lateral: um pico secundário que dança
        if 0.35 < t < 0.75:
            tc = 8.5 + side * 4.2
            tw = 1.6 * (1 - abs(t - 0.5) / 0.25)
            for x in range(FW):
                if abs(x + 0.5 - tc) <= max(0.0, tw) and abs(x + 0.5 - c) <= w + 2.5:
                    inside[y][x] = True
    cx, cy = 8.5, BASE_Y - 1.5
    for y in range(FH):
        for x in range(FW):
            if not inside[y][x]:
                continue
            edge = any(
                not (0 <= y + dy < FH and 0 <= x + dx < FW and inside[y + dy][x + dx])
                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))
            )
            if edge:
                g[y][x] = 'K' if y >= BASE_Y - 4 else 'D'
                continue
            d = math.hypot((x + 0.5 - cx) / 5.2, (y + 0.5 - cy) / 9.5)
            g[y][x] = 'W' if d < 0.28 else 'Y' if d < 0.45 else 'L' if d < 0.62 else 'O' if d < 0.82 else 'R'
    # base escura, mais estreita que a chama
    for x in range(4, FW - 4):
        g[BASE_Y + 1][x] = 'K'
    for x, y, col in sparks:
        if g[y][x] == '.':
            g[y][x] = col
    return g


# ---------- floco de gelo ----------
SW = SH = 21
ICE_PAL = {'N': '#0b2550', 'B': '#2f6fc4', 'M': '#6fb0f0', 'L': '#bfe4ff', 'W': '#f2fbff', 'P': '#7cc4ff'}


def snow_grid():
    cx = cy = 10.0
    inside = [[False] * SW for _ in range(SH)]
    segs = []
    for k in range(6):
        a = math.radians(90 + 60 * k)
        ex, ey = cx + 7.6 * math.cos(a), cy - 7.6 * math.sin(a)
        segs.append(((cx, cy), (ex, ey), 1.8))
        # galhinhos em V no meio do braço
        mx, my = cx + 4.6 * math.cos(a), cy - 4.6 * math.sin(a)
        for s in (-1, 1):
            b = a + s * math.radians(50)
            segs.append(((mx, my), (mx + 2.4 * math.cos(b), my - 2.4 * math.sin(b)), 0.95))

    def dist(px, py, a, b):
        (x1, y1), (x2, y2) = a, b
        vx, vy = x2 - x1, y2 - y1
        t = max(0.0, min(1.0, ((px - x1) * vx + (py - y1) * vy) / (vx * vx + vy * vy)))
        return math.hypot(px - x1 - t * vx, py - y1 - t * vy)

    for y in range(SH):
        for x in range(SW):
            px, py = x + 0.5, y + 0.5
            if math.hypot(px - cx - 0.5, py - cy - 0.5) < 3.2 or any(
                dist(px, py, a, b) < r for a, b, r in segs
            ):
                inside[y][x] = True
    g = [['.'] * SW for _ in range(SH)]
    for y in range(SH):
        for x in range(SW):
            if not inside[y][x]:
                continue
            edge = any(
                not (0 <= y + dy < SH and 0 <= x + dx < SW and inside[y + dy][x + dx])
                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))
            )
            if edge:
                g[y][x] = 'N'
                continue
            # miolo dos braços claro (o brilho), bordas escurecendo para baixo à direita
            axis = min(dist(x + 0.5, y + 0.5, a, b) for a, b, r in segs[::3])
            shade = axis / 1.8 + ((x - 10) + (y - 10)) / 40
            g[y][x] = 'W' if shade < 0.3 else 'L' if shade < 0.6 else 'M' if shade < 0.9 else 'B'
    return g


SNOW_SPARKLES = [(2, 2), (18, 3), (1, 17), (18, 17), (10, 0)]


def rects(grid, pal, skip=()):
    out = []
    for y, row in enumerate(grid):
        x = 0
        while x < len(row):
            ch = row[x]
            if ch == '.' or ch in skip:
                x += 1
                continue
            x2 = x
            while x2 + 1 < len(row) and row[x2 + 1] == ch:
                x2 += 1
            out.append(f'<rect x="{x}" y="{y}" width="{x2 - x + 1}" height="1" fill="{pal[ch]}"/>')
            x = x2 + 1
    return ''.join(out)


def fire_svg():
    n = len(FIRE_FRAMES)
    dur = 0.9
    parts = []
    for i, f in enumerate(FIRE_FRAMES):
        vals = ';'.join('1' if j == i else '0' for j in range(n))
        parts.append(
            f'<g opacity="{1 if i == 0 else 0}">{rects(fire_frame(*f), FIRE_PAL)}'
            f'<animate attributeName="opacity" values="{vals}" dur="{dur}s" calcMode="discrete" repeatCount="indefinite"/></g>'
        )
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {FW} {FH}" shape-rendering="crispEdges">'
            + ''.join(parts) + '</svg>')


def sparkle(x, y, begin):
    p = ICE_PAL['P']
    return (f'<g opacity="0"><rect x="{x}" y="{y - 1}" width="1" height="3" fill="{p}"/>'
            f'<rect x="{x - 1}" y="{y}" width="3" height="1" fill="{p}"/>'
            f'<animate attributeName="opacity" values="0;1;0" dur="1.6s" begin="{begin}s" repeatCount="indefinite"/></g>')


def snow_svg():
    g = snow_grid()
    glow = rects(g, ICE_PAL, skip=('N', 'B', 'M'))
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="-1 -1 {SW + 2} {SH + 2}" shape-rendering="crispEdges">'
            f'{rects(g, ICE_PAL)}'
            # brilho: o miolo claro pulsa
            f'<g>{glow}'
            f'<animate attributeName="opacity" values="1;0.45;1" dur="2.2s" repeatCount="indefinite"/></g>'
            + ''.join(sparkle(x, y, i * 0.37) for i, (x, y) in enumerate(SNOW_SPARKLES))
            + '</svg>')


def preview(path):
    scale = 8
    frames = [fire_frame(*f) for f in FIRE_FRAMES]
    sg = snow_grid()
    W = (FW * len(frames) + SW + len(frames) + 2) * scale
    img = Image.new('RGB', (W, max(FH, SH) * scale), '#2b2b2b')
    ox = 0
    for grid, pal in [(f, FIRE_PAL) for f in frames] + [(sg, ICE_PAL)]:
        for y, row in enumerate(grid):
            for x, ch in enumerate(row):
                if ch != '.':
                    c = pal[ch]
                    rgb = tuple(int(c[i:i + 2], 16) for i in (1, 3, 5))
                    for yy in range(scale):
                        for xx in range(scale):
                            img.putpixel(((ox + x) * scale + xx, y * scale + yy), rgb)
        ox += len(grid[0]) + 1
    img.save(path)


if __name__ == '__main__':
    out_ts, out_png = sys.argv[1], sys.argv[2]
    with open(out_ts, 'w') as fh:
        fh.write('// Gerado por gen_sprites.py: pixel art animada com SMIL (Svg como imagem, sem isInteractive).\n')
        fh.write(f'export const FOGO = `{fire_svg()}`\n')
        fh.write(f'export const GELO = `{snow_svg()}`\n')
    preview(out_png)
