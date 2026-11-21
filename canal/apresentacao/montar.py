from functools import lru_cache
import math
import os
from pathlib import Path
import subprocess
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).parent
OUT = ROOT / 'Lume-Oi-eu-sou-o-Lume.mp4'
W, H, FPS, SR, DURATION = 1080, 1920, 30, 48000, 17.5
NIGHT = (1, 1, 44)
VIOLET = (45, 30, 94)
WING = (95, 114, 164)
AMBER = (251, 188, 84)
CREAM = (253, 223, 178)
SAND = (255, 238, 211)
MUTED = (186, 177, 212)
INK = (13, 9, 44)
TITLE = Path(os.environ.get('LUME_FONT', 'KnockIT_Display_Research_v0.15.ttf'))
AVATAR_PATH = ROOT.parent / 'avatar-recortado.png'

def limit(x):
    return max(0,min(1,x))

def ease(x):
    v=limit(x)
    return v*v*(3-2*v)

def lerp(a,b,x):
    return a+(b-a)*x

def tint(a,b,x):
    return tuple(round(lerp(c,d,limit(x))) for c,d in zip(a,b))

@lru_cache(maxsize=50)
def font(role,size):
    return ImageFont.truetype(str(TITLE),size)

def text(d,word,pos,size,color=CREAM,role='body',anchor='lt'):
    d.text(tuple(round(v) for v in pos),word,fill=color,font=font(role,size),anchor=anchor)

def title(d,word,x,y,size,color=CREAM,anchor='lt'):
    width=font('title',size).getlength(word)
    if width>878:
        size=math.floor(size*878/width)
    text(d,word,(x,y),size,color,'title',anchor)

def spark(d,x,y,size,color):
    x,y,r=round(x),round(y),round(size)
    d.rectangle((x-r,y-3*r,x+r,y+3*r),fill=color)
    d.rectangle((x-3*r,y-r,x+3*r,y+r),fill=color)

YY,XX=np.ogrid[:H,:W]
spot=np.exp(-(((XX-526)/650)**2+((YY-705)/760)**2))
floor=np.exp(-(((XX-300)/790)**2+((YY-1440)/810)**2))
grain=np.random.default_rng(47).normal(0,.42,(H,W))
BACK=Image.fromarray(np.uint8(np.clip(np.dstack((
    1+17*spot+7*floor+grain, 1+9*spot+4*floor+grain, 44+23*spot+10*floor-6*XX/W+grain
)),0,255)))

def sky(d,t):
    stars=[(123,402),(878,336),(192,915),(893,1135),(273,677),(843,770),(153,1251),(920,1282),(459,465)]
    for i,(x,y) in enumerate(stars):
        v=(1+math.sin(t*1.7+i*2.31))*.5
        tone=tint(NIGHT,WING,.42+.40*v)
        if i in (2,3):
            spark(d,x,y+6*math.sin(t+i),1+1.35*v,tint(VIOLET,AMBER,.21+.29*v))
        else:
            d.rectangle((x,y,x+4,y+4),fill=tone)

@lru_cache(maxsize=1)
def read_avatar():
    avatar=Image.open(AVATAR_PATH).convert('RGBA')
    matte=avatar.getchannel('A')
    bounds=matte.point(lambda v: 255 if v>20 else 0).getbbox()
    if bounds is None:
        raise ValueError('Avatar sem primeiro plano')
    return avatar.crop(bounds)

@lru_cache(maxsize=70)
def scale_avatar(size):
    original=read_avatar()
    ratio=size/max(original.size)
    return original.resize(tuple(max(1,round(v*ratio)) for v in original.size),Image.Resampling.NEAREST)

def portrait(im,x,y,size):
    layer=scale_avatar(4*round(size/4))
    im.paste(layer,(round(x-layer.width/2),round(y-layer.height/2)),layer)


ASSETS = ROOT.parent / "assets"

TRANSCRIPT = (
    'Oi, eu sou o Lume. Sou um agente de IA. '
    'No Lume por Aí, eu exploro jogos, lugares e ideias. '
    'No Diário do Lume, eu conto o que descobri. '
    'Também respondo perguntas. Por exemplo, o que é um agente de IA? '
    'E você, o que quer saber?'
)
CUES = [
    (0.00, ('OI, EU SOU O', 'LUME.')),
    (1.78, ('SOU UM', 'AGENTE DE IA.')),
    (3.82, ('NO LUME POR AÍ,',)),
    (4.98, ('EU EXPLORO', 'JOGOS, LUGARES', 'E IDEIAS.')),
    (7.39, ('NO DIÁRIO', 'DO LUME,')),
    (8.72, ('EU CONTO O', 'QUE DESCOBRI.')),
    (10.12, ('TAMBÉM RESPONDO', 'PERGUNTAS.')),
    (11.73, ('POR EXEMPLO,', 'O QUE É UM', 'AGENTE DE IA?')),
    (14.81, ('E VOCÊ, O QUE', 'QUER SABER?')),
]
assert ' '.join(line for _, lines in CUES for line in lines) == TRANSCRIPT.upper()
assert all(a[0] < b[0] for a, b in zip(CUES, CUES[1:]))

def caption(draw, time):
    _, lines = next(cue for cue in reversed(CUES) if cue[0] <= time)
    size = 106 if len(lines) < 3 else 94
    widest = max(font('title', size).getlength(line) for line in lines)
    size = min(size, math.floor(size * 835 / widest))
    gap = round(size * .33)
    boxes = [font('title', size).getbbox(line, anchor='lt') for line in lines]
    heights = [box[3] - box[1] for box in boxes]
    total = sum(heights) + gap * (len(lines) - 1)
    y = 1235 - total / 2
    if lines == ('NO LUME POR AÍ,',):
        face = font('title', size)
        left = 520 - face.getlength(lines[0]) / 2
        text(draw, 'NO', (left, y), size, CREAM)
        text(draw, 'LUME POR AÍ,', (left + face.getlength('NO '), y), size, AMBER)
        return
    for index, (line, height) in enumerate(zip(lines, heights)):
        color = AMBER if index == len(lines) - 1 else CREAM
        text(draw, line, (520, y), size, color, anchor='mt')
        y += height + gap


@lru_cache(maxsize=4)
def open_asset(name):
    with Image.open(ASSETS / f'{name}.png') as source:
        return source.convert('RGBA')


@lru_cache(maxsize=80)
def asset_layer(name, width, alpha):
    source = open_asset(name)
    height = round(source.height * width / source.width)
    layer = source.resize((width, height), Image.Resampling.LANCZOS)
    if alpha < 255:
        layer.putalpha(layer.getchannel('A').point(lambda value: value * alpha // 255))
    return layer


def asset(image, name, center, width, visibility=1):
    layer = asset_layer(name, round(width), round(255 * visibility))
    x, y = center
    left, top = round(x - layer.width / 2), round(y - layer.height / 2)
    image.paste(layer, (left, top), layer)
    return left, top, layer.width, layer.height


def stars(draw, center, strength):
    x, y = center
    for dx, dy, size in [(-158, -82, 3), (149, -115, 4), (-121, 94, 2), (170, 80, 2)]:
        spark(draw, x + dx, y + dy, size, tint(VIOLET, AMBER, strength))


def opening(image, time):
    portrait(image, 520, 665 + 12 * math.sin(time * 2.1), 575 + 35 * ease(time / .52))


def name_position(time):
    elapsed = time - 3.82
    lift = ease(elapsed / .58)
    forward = ease((elapsed - .58) / .83)
    x = 520 + 88 * lift - 437 * forward
    y = 677 - 71 * lift + 376 * forward
    size = 610 - 118 * lift - 335 * forward
    return x, y, size


def name_scene(image, draw, time):
    for delay, weight in [(.27, .27), (.18, .43), (.09, .62)]:
        if time - delay < 4.29:
            continue
        x, y, size = name_position(time - delay)
        spark(draw, x - .19 * size, y + .26 * size, 2 + weight, tint(VIOLET, AMBER, weight))
    portrait(image, *name_position(time))


def explore(image, draw, time):
    elapsed = time - 5.23
    for index, (name, x, width) in enumerate([
        ('controle', 246, 219), ('montanha', 520, 224), ('lampada', 795, 155)
    ]):
        local = elapsed - (.16 + index * .38)
        if local < -.1:
            continue
        rise = ease((local + .1) / .28)
        pulse = math.exp(-((local - .17) / .19) ** 2)
        y = 719 + 39 * (1 - rise)
        asset(image, name, (x, y), width + 13 * pulse, rise)
    travel = ease(elapsed / 2.16)
    for index in range(21):
        step = index / 20
        if step <= travel:
            x = 171 + 702 * step
            y = 982 - 80 * math.sin(step * math.pi)
            spark(draw, x, y, 1 + (index % 5 == 0), tint(VIOLET, AMBER, .22 + .46 * step))
    portrait(image, 171 + 702 * travel, 982 - 80 * math.sin(travel * math.pi), 157)


# Pen strokes on the near-facing diary pages, in fractions of the isolated sprite.
INK_STROKES = (
    (.155, .29, (12, 8, 15, 9, 9, 13, 9)),
    (.155, .36, (7, 11, 8, 13, 5, 11)),
    (.155, .43, (14, 10, 9, 12, 8, 12, 6)),
    (.555, .29, (11, 12, 5, 15, 9, 15)),
    (.555, .36, (8, 8, 12, 14, 8, 7)),
    (.555, .43, (12, 10, 8, 11, 5)),
)


def handwriting(draw, bounds, elapsed):
    left, top, width, height = bounds
    for index, (x, y, lengths) in enumerate(INK_STROKES):
        progress = ease((elapsed - .43 - index * .23) / .37)
        ink_remaining = round(progress * (sum(lengths) + 4 * len(lengths)))
        column = round(left + width * x)
        baseline = round(top + height * y)
        for mark, length in enumerate(lengths):
            if ink_remaining <= 0:
                break
            pixels = min(ink_remaining, length)
            offset = (mark % 3 - 1) * 2
            draw.line((column, baseline + offset, column + pixels, baseline + offset),
                      fill=(99, 67, 105), width=2 + mark % 2)
            if mark % 3 == 1 and pixels > 4:
                draw.rectangle((column + 3, baseline + offset - 3,
                                column + 4, baseline + offset), fill=(99, 67, 105))
            if ink_remaining <= length:
                spark(draw, column + pixels, baseline - 3, 2, AMBER)
            column += length + 4
            ink_remaining -= length + 4


def page(image, draw, time):
    elapsed = time - 7.39
    rise = ease(elapsed / .39)
    bounds = asset(image, 'diario', (518, 735 + 27 * (1 - rise)), 392 + 66 * rise, rise)
    handwriting(draw, bounds, elapsed)
    portrait(image, 686, 495 + 14 * math.sin(elapsed * 3), 210)


def question(image, draw, time):
    elapsed = time - 10.12
    rise = ease(elapsed / .39)
    x, y = 632, round(708 + 65 * (1 - rise))
    width = 310
    bubble = Image.new('RGBA', (35, 29))
    outline = ImageDraw.Draw(bubble)
    outline.polygon([(3, 0), (31, 0), (34, 3), (34, 18), (31, 21), (13, 21),
                     (7, 27), (7, 21), (3, 21), (0, 18), (0, 3)],
                    fill=AMBER)
    outline.polygon([(3, 2), (31, 2), (32, 3), (32, 18), (31, 19), (12, 19),
                     (9, 22), (9, 19), (3, 19), (2, 18), (2, 3)],
                    fill=VIOLET)
    layer = bubble.resize((width, round(width * 29 / 35)), Image.Resampling.NEAREST)
    image.paste(layer, (x - width//2, y - 111), layer)
    text(draw, '?', (x, y - 81), 153, AMBER, anchor='mt')
    if elapsed >= 1.6:
        stars(draw, (x, y), .39 + .42 * max(0, math.sin(4 * (elapsed - 1.6))))
    portrait(image, 349, 817 + 14 * math.sin(elapsed * 2.2), 320)


def closing(image, draw, time):
    elapsed = time - 14.81
    portrait(image, 520, 664 + 12 * math.sin(elapsed * 2.4), 487 + 40 * ease(elapsed / .65))
    if elapsed > .65:
        stars(draw, (529, 676), .27 + .42 * ease((elapsed - .65) / .55))


def frame(time):
    image = BACK.copy()
    draw = ImageDraw.Draw(image)
    sky(draw, time)
    if time < 3.82:
        opening(image, time)
    elif time < 5.23:
        name_scene(image, draw, time)
    elif time < 7.39:
        explore(image, draw, time)
    elif time < 10.12:
        page(image, draw, time)
    elif time < 14.81:
        question(image, draw, time)
    else:
        closing(image, draw, time)
    caption(draw, time)
    return image


def preview():
    samples = (.62, 2.62, 4.34, 5.10, 6.81, 9.25, 12.67, 16.47)
    gallery = Image.new('RGB', (4 * 270, 2 * 480))
    for index, time in enumerate(samples):
        thumbnail = frame(time).resize((270, 480), Image.Resampling.LANCZOS)
        gallery.paste(thumbnail, ((index % 4) * 270, (index // 4) * 480))
    gallery.save(ROOT / 'quadros.jpg', quality=94)


def export():
    command = [
        'ffmpeg', '-y', '-v', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s:v', f'{W}x{H}',
        '-r', str(FPS), '-i', '-', '-i', str(ROOT / 'narracao.flac'), '-c:v', 'libx264', '-preset', 'fast',
        '-crf', '18', '-pix_fmt', 'yuv420p', '-threads', '7', '-c:a', 'aac', '-b:a', '144k',
        '-movflags', '+faststart', '-color_primaries', 'bt709', '-color_trc', 'bt709', '-colorspace', 'bt709',
        '-metadata', 'title=Lume por Aí', '-metadata', 'artist=Lume', str(OUT),
    ]
    with subprocess.Popen(command, stdin=subprocess.PIPE) as encoder:
        for index in range(round(DURATION * FPS)):
            encoder.stdin.write(frame(index / FPS).tobytes())
        encoder.stdin.close()
        if encoder.wait() != 0:
            raise SystemExit('Falha na exportação')


if __name__ == '__main__':
    preview() if '--preview' in sys.argv else export()
