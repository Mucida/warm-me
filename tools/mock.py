"""Imagens fictícias da faixa do warm-me para o README. Uso: python3 -I tools/mock.py docs"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from PIL import Image, ImageDraw, ImageFont  # noqa: E402

import gen_sprites as g  # noqa: E402

FUNDO, FAIXA, CAIXA, BORDA = '#161616', '#242424', '#1e1e1e', '#3a3a3a'
TEXTO_DIM = '#8a8a8a'
FONTE = '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
FONTE_MONO = '/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf'


def fonte(caminho, tam):
    try:
        return ImageFont.truetype(caminho, tam)
    except OSError:
        return ImageFont.load_default()


def hexrgb(c):
    return tuple(int(c[i:i + 2], 16) for i in (1, 3, 5))


def desenhar_grade(img, grade, pal, x0, y0, escala, extra=()):
    d = ImageDraw.Draw(img)
    for y, linha in enumerate(grade):
        for x, ch in enumerate(linha):
            if ch != '.':
                d.rectangle([x0 + x * escala, y0 + y * escala, x0 + (x + 1) * escala - 1, y0 + (y + 1) * escala - 1],
                            fill=hexrgb(pal[ch]))
    for x, y, cor in extra:
        d.rectangle([x0 + x * escala, y0 + y * escala, x0 + (x + 1) * escala - 1, y0 + (y + 1) * escala - 1],
                    fill=hexrgb(cor))


FRAMES_FOGO = [g.fire_frame(*f) for f in g.FIRE_FRAMES]
GRADE_GELO = g.snow_grid()
# escala 2x das larguras do mod (44/34/26/18 px) em pixels inteiros por célula
ESCALAS_FOGO = {3: 5, 2: 4, 1: 3, 0: 2}
ESCALA_GELO = 4
L, A = 760, 250


def quadro(estado, passo, rotulo):
    """estado: 0..3 (quarto do fogo) ou 'frio'; passo: índice da animação."""
    img = Image.new('RGB', (L, A), FUNDO)
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([24, 20, L - 24, 160], radius=14, fill=FAIXA)
    d.rounded_rectangle([24, 176, L - 24, 226], radius=14, fill=CAIXA, outline=BORDA, width=2)
    d.text((48, 190), '+', fill=TEXTO_DIM, font=fonte(FONTE, 22))
    d.text((78, 192), 'Type / for commands', fill=TEXTO_DIM, font=fonte(FONTE, 17))

    cx, base = 82, 118  # centro do sprite e linha de base
    if estado == 'frio':
        esc = ESCALA_GELO
        lado = g.SW * esc
        x0, y0 = cx - lado // 2, base - lado
        brilho = [(sx, sy - 1 + k, g.ICE_PAL['P']) for i, (sx, sy) in enumerate(g.SNOW_SPARKLES)
                  if (passo + i) % 3 == 0 for k in range(3)]
        brilho += [(sx - 1 + k, sy, g.ICE_PAL['P']) for i, (sx, sy) in enumerate(g.SNOW_SPARKLES)
                   if (passo + i) % 3 == 0 for k in range(3)]
        desenhar_grade(img, GRADE_GELO, g.ICE_PAL, x0, y0, esc, brilho)
        cor = '#7cc4ff'
    else:
        esc = ESCALAS_FOGO[estado]
        grade = FRAMES_FOGO[passo % len(FRAMES_FOGO)]
        x0, y0 = cx - (g.FW * esc) // 2, base - g.FH * esc
        desenhar_grade(img, grade, g.FIRE_PAL, x0, y0, esc)
        cor = '#ff5a1f' if estado == 0 else '#ffb347'
    f = fonte(FONTE_MONO, 17)
    w = d.textlength(rotulo, font=f)
    d.text((cx - w / 2, base + 10), rotulo, fill=cor, font=f)
    return img


def legenda(img, texto):
    d = ImageDraw.Draw(img)
    d.text((140, 76), texto, fill='#c8c8c8', font=fonte(FONTE, 18))
    return img


ESTADOS = [
    (3, '59:21', 'Cache warm: big fire (more than 45 min left)'),
    (2, '38:10', 'Second quarter: the fire shrinks'),
    (1, '22:05', 'Third quarter: smaller still'),
    (0, '9:42', 'Last quarter: tiny fire, red timer'),
    ('frio', 'frio', 'Cache expired: the snowflake sparkles'),
]


def main(saida):
    os.makedirs(saida, exist_ok=True)
    # GIF: cada estado dança por ~2 s
    quadros = []
    for estado, rotulo, texto in ESTADOS:
        for passo in range(14):
            quadros.append(legenda(quadro(estado, passo, rotulo), texto))
    quadros[0].save(os.path.join(saida, 'demo.gif'), save_all=True, append_images=quadros[1:],
                    duration=150, loop=0, optimize=True)
    # PNG com os 5 estados empilhados
    pilha = Image.new('RGB', (L, A * len(ESTADOS)), FUNDO)
    for i, (estado, rotulo, texto) in enumerate(ESTADOS):
        pilha.paste(legenda(quadro(estado, 0, rotulo), texto), (0, A * i))
    pilha.save(os.path.join(saida, 'states.png'), optimize=True)


if __name__ == '__main__':
    main(sys.argv[1])
