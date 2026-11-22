from bisect import bisect_right
from functools import lru_cache
from itertools import accumulate
import json
import math
from pathlib import Path
import subprocess

import numpy as np
from PIL import Image, ImageDraw

EPISODIO = Path(__file__).resolve().parent
CANAL = EPISODIO.parents[2]
NEAREST = Image.Resampling.NEAREST
LANCZOS = Image.Resampling.LANCZOS


def ease(x):
    x = max(0, min(1, x))
    return x * x * (3 - 2 * x)


def place(image, asset, center, width=None, opacity=1):
    if width is not None:
        w = max(1, round(width))
        if w != asset.width:
            asset = asset.resize((w, max(1, round(asset.height * w / asset.width))), LANCZOS)
    x, y = center
    alpha = asset.getchannel("A")
    if opacity < 1:
        alpha = alpha.point(lambda a: round(a * opacity))
    image.paste(asset, (round(x-asset.width/2), round(y-asset.height/2)), alpha)


AVATAR_ATLAS = CANAL / "assets" / "avatar-512"
AVATAR_BOX = (80, 27, 432, 485)
NEUTRAL_WING = 2


@lru_cache(maxsize=1)
def avatar_sheet():
    manifest = json.loads((AVATAR_ATLAS / "Lume-spritesheet-512.json").read_text(encoding="utf-8"))
    frames = manifest["frames"]
    with Image.open(AVATAR_ATLAS / manifest["meta"]["image"]) as atlas:
        atlas = atlas.convert("RGBA")
        sprites = []
        for item in frames:
            box = item["frame"]
            x, y = box["x"], box["y"]
            sprites.append(atlas.crop((x, y, x + box["w"], y + box["h"])))
    durations = [item["duration"] / 1000 for item in frames]
    return sprites, durations


def pulse_frame(t):
    sprites, durations = avatar_sheet()
    sequence = list(range(len(sprites))) + list(range(len(sprites) - 2, 0, -1))
    state_ends = list(accumulate(durations[index] for index in sequence))
    return sequence[bisect_right(state_ends, t % state_ends[-1])]


def signature_frame(t):
    sprites, durations = avatar_sheet()
    bright = len(sprites) - 1
    sequence = list(range(bright - 1, -1, -1)) + list(range(1, bright))
    state_ends = list(accumulate(durations[index] for index in sequence))
    index = bisect_right(state_ends, max(0, t))
    return sequence[index] if index < len(sequence) else bright


def signature_pulse_duration():
    _, durations = avatar_sheet()
    return durations[0] + 2 * sum(durations[1:-1])


@lru_cache(maxsize=18)
def avatar_layers(state):
    full = avatar_sheet()[0][state]
    matte = Image.new("L", full.size)
    ImageDraw.Draw(matte).polygon(
        [(44, 129), (172, 131), (190, 165), (191, 215), (197, 255),
         (220, 286), (199, 309), (170, 324), (103, 342), (52, 342)], fill=255
    )
    alpha = np.asarray(matte) > 0
    wings = np.array(full)
    body = wings.copy()
    wings[~alpha, 3] = 0
    body[alpha & (np.arange(full.width)[None, :] < 202), 3] = 0
    return Image.fromarray(body), Image.fromarray(wings)


@lru_cache(maxsize=95)
def avatar_pose(state, wing, mouth, blink):
    if wing == NEUTRAL_WING:
        image = avatar_sheet()[0][state].copy()
    else:
        body, feather = avatar_layers(state)
        image = Image.new("RGBA", body.size)
        hinge_x, hinge_y = 207, 286
        angle = math.radians((wing - NEUTRAL_WING) * 5)
        scale_x = 1 + (wing - NEUTRAL_WING) * .075
        c, s = math.cos(angle), math.sin(angle)
        a, b, d, e = c / scale_x, s / scale_x, -s, c
        feather = feather.transform(body.size, Image.Transform.AFFINE, (
            a, b, hinge_x - a * hinge_x - b * hinge_y,
            d, e, hinge_y - d * hinge_x - e * hinge_y,
        ), NEAREST)
        image.alpha_composite(feather)
        image.alpha_composite(body)

    draw = ImageDraw.Draw(image)
    if blink:
        draw.polygon([(248, 226), (259, 213), (283, 209), (298, 219), (304, 241),
                      (297, 255), (277, 265), (254, 260), (246, 248)], fill="#744077")
        draw.line([(251, 243), (263, 247), (279, 244), (296, 234)], fill="#2d1538", width=6)
        draw.polygon([(333, 209), (339, 196), (354, 193), (366, 205), (371, 229),
                      (367, 243), (354, 250), (341, 244), (334, 231)], fill="#754279")
        draw.line([(338, 221), (346, 226), (355, 223), (365, 214)], fill="#301633", width=5)
    if mouth != 3:
        # The atlas pose is the open vowel. For the smaller poses, repaint only
        # the original mouth area using surrounding cheek colors.
        cover = Image.new("L", image.size)
        ImageDraw.Draw(cover).polygon(
            [(309, 253), (340, 252), (348, 261), (346, 277),
             (336, 292), (322, 293), (308, 284), (302, 270)], fill=255
        )
        colors = image.load()
        patch = Image.new("RGBA", (47, 42))
        for y in range(252, 294):
            left = colors[300, y]
            right = colors[350, y]
            for x in range(302, 349):
                u = (x - 300) / 50
                patch.putpixel((x - 302, y - 252),
                               tuple(round((1 - u) * a + u * b) for a, b in zip(left, right)))
        image.paste(patch, (302, 252), cover.crop((302, 252, 349, 294)))
        draw = ImageDraw.Draw(image)
        if mouth in (0, 4):
            draw.line([(313, 270), (322, 275), (332, 273), (339, 267)], fill="#321637", width=5)
        else:
            lower = 276 if mouth == 1 else 286
            draw.polygon([(313, 264), (336, 260), (342, 266), (339, lower - 4),
                          (329, lower), (318, lower - 2), (311, 271)], fill="#271429")
            if mouth == 2:
                draw.rectangle((320, 278, 332, 281), fill="#e98550")
    return image.crop(AVATAR_BOX)


class Avatar:
    def __init__(self, audio_path):
        self.rate = 16000
        pcm = subprocess.check_output([
            "ffmpeg", "-v", "error", "-i", str(audio_path), "-ac", "1",
            "-ar", str(self.rate), "-f", "s16le", "-"
        ])
        self.wave = np.frombuffer(pcm, dtype="<i2").astype(np.float32) / 32768

    def speak(self, t):
        index = round(t * self.rate)
        radius = round(.022 * self.rate)
        chunk = self.wave[max(0, index - radius):index + radius + 1]
        if not chunk.size:
            return 0
        energy = np.sqrt(np.mean(chunk * chunk))
        if energy < .011:
            return 0
        return 1 + int(energy > .054) + int(energy > .128)

    def draw(self, image, t, x, y, width, energy=1, tilt=0, opacity=1,
             state=None, smile=False, still=False):
        tick = math.floor(t * 15) / 15
        wing = NEUTRAL_WING if still else round(2 + 2 * math.sin(tick * math.tau * 4.0))
        blink = not still and ((t + .37) % 3.62) < .115
        state = pulse_frame(t) if state is None else state
        sprite = avatar_pose(state, wing, 4 if smile else self.speak(tick), blink)
        width = round(width * (1 + energy * .016 * math.sin(t * 3.4)))
        # The new artwork is taller. Preserve the old silhouette height and
        # register the eye midpoint in the same region of the portrait.
        height = round(width * 640 / 580)
        sprite = sprite.resize((round(height * sprite.width / sprite.height), height), NEAREST)
        rotation = tilt + energy * (4.2 * math.sin(t * 2.62) + 1.5 * math.sin(t * 6))
        if abs(rotation) > .1:
            sprite = sprite.rotate(rotation, NEAREST, expand=True)
        place(image, sprite, (x + energy * 19 * math.sin(t * 2.6),
                              y + energy * 25 * math.sin(t * 3.5)), opacity=opacity)

def rounded(draw, box, radius, fill, outline=None, width=1):
    draw.rounded_rectangle(box, radius, fill=fill, outline=outline, width=width)


@lru_cache(maxsize=None)
def icon(name):
    im = Image.new("RGBA",(240,240))
    d = ImageDraw.Draw(im)
    r = d.rounded_rectangle
    e = d.ellipse
    l = d.line
    p = d.polygon
    if name == "lupa":
        l((151,153,209,213), fill="#1b293d",width=35)
        l((151,149,209,207), fill="#6bbcf4",width=24)
        l((158,148,208,197), fill="#c2e7ff",width=5)
        e((26,24,173,171),fill="#193953",outline="#101f38",width=12)
        e((34,30,162,158),fill="#413c7a",outline="#64c0ef",width=13)
        e((50,46,146,142),fill="#285272",outline="#bceaff",width=3)
        d.arc((59,53,136,127),192,284,fill="#f1faff",width=8)
        d.arc((57,56,141,135),16,79,fill="#5ab6cc",width=5)
        e((129,81,136,88),fill="#bceaff")
    elif name in ("cadeado", "cadeado_bloqueado"):
        d.arc((62,26,177,147),181,359,fill="#552638",width=30)
        d.arc((68,25,171,143),181,359,fill="#f29965",width=19)
        d.arc((68,26,171,142),199,299,fill="#ffe2a4",width=5)
        r((43,100,197,213),19,fill="#682649",outline="#2b172f",width=8)
        r((44,92,195,198),18,fill="#e97964",outline="#ffd795",width=5)
        r((57,107,182,183),14,fill="#fca470")
        e((105,119,136,151),fill="#542044")
        p([(113,140),(128,140),(134,166),(107,166)],fill="#542044")
        l((66,110,106,110),fill="#ffebbf",width=5)
        d.arc((132,134,171,172),298,33,fill="#e78966",width=5)
        if name == "cadeado_bloqueado":
            # Change the metal to red while keeping its relief and highlights.
            blocked = Image.new("RGBA", im.size)
            blocked.putdata([(
                min(255, round(red*1.13 + 16)), round(green*.49),
                min(255, round(blue*.81 + 45)), alpha,
            ) if alpha else (0,0,0,0) for red,green,blue,alpha in im.getdata()])
            return blocked
    elif name == "preco":
        p([(26,130),(132,28),(200,44),(207,112),(102,218)],fill="#56234e")
        p([(22,118),(127,21),(196,35),(202,102),(97,205)],fill="#ef62a7",outline="#ffd0e6",width=5)
        l((31,123,129,34),fill="#ffadcf",width=6)
        e((152,50,174,72),fill="#391947",outline="#ffdaf1",width=4)
        l((165,54,190,30,217,35),fill="#ffe48b",width=7,joint="curve")
        l((92,125,136,81),fill="#ffe8f5",width=9)
        e((86,90,106,110),outline="#fff4f8",width=6)
        e((118,121,138,141),outline="#fff4f8",width=6)
    elif name == "mapa":
        p([(25,75),(88,50),(151,75),(213,47),(215,181),(151,207),(88,180),(25,203)],
          fill="#155456",outline="#17344a",width=8)
        p([(30,78),(88,55),(88,174),(30,197)],fill="#91d899")
        p([(88,55),(150,78),(150,201),(88,174)],fill="#4a9b86")
        p([(150,78),(210,52),(210,176),(150,201)],fill="#b7e591")
        l((38,151,67,126,96,145,137,106,184,126,203,105),fill="#e8ffe0",width=10,joint="curve")
        e((111,30,170,89),fill="#fa6671",outline="#ffd0a5",width=5)
        p([(117,73),(165,73),(141,115)],fill="#fa6671")
        e((131,49,150,68),fill="#8a2545")
    elif name == "pastas":
        r((23,71,216,198),18,fill="#ae632e",outline="#462a3d",width=7)
        r((30,54,105,90),10,fill="#edac55")
        p([(50,75),(176,52),(189,149),(64,167)],fill="#fff0c6",outline="#805170",width=5)
        l((72,99,156,82),fill="#ae7aa1",width=5)
        l((77,114,161,97),fill="#ae7aa1",width=5)
        p([(26,118),(216,102),(197,199),(42,204)],fill="#fac15d",outline="#ffe295",width=5)
        l((44,130,187,118),fill="#ffe8ad",width=6)
        r((132,155,178,171),4,fill="#c77e36")
    elif name == "alvo":
        for bounds,color in [((21,23,217,219),"#763649"),((27,25,208,206),"#ef7365"),
                             ((49,47,186,184),"#ffe5bb"),((69,67,166,164),"#e96457"),
                             ((87,85,148,146),"#ffe9b8"),((103,101,134,132),"#ba4451")]:
            e(bounds,fill=color)
        l((117,117,196,38),fill="#324761",width=15)
        l((117,111,196,32),fill="#87d5ff",width=8)
        p([(173,43),(176,20),(205,12),(200,43),(183,58)],fill="#c1efff")
    elif name == "ferramentas":
        pts=[]
        for i in range(48):
            ang=i*math.tau/48
            rr=95 if i%6 in (1,2,3,4) else 76
            pts.append((120+rr*math.cos(ang),120+rr*math.sin(ang)))
        p([(x,y+12) for x,y in pts],fill="#143d59")
        p(pts,fill="#52beb9",outline="#c3ffeb",width=5)
        e((62,62,178,178),fill="#266982",outline="#76e7d1",width=9)
        e((88,88,152,152),fill="#162c48",outline="#b6faff",width=6)
        d.arc((43,43,198,198),194,281,fill="#effffe",width=6)
    elif name == "lista":
        r((48,40,201,213),14,fill="#255b50",outline="#163840",width=8)
        r((42,34,192,202),14,fill="#d9f2b5",outline="#86ce7f",width=6)
        r((82,17,151,59),13,fill="#386f61",outline="#abf3a3",width=5)
        for y in (87,124,160):
            l((61,y+3,70,y+11,84,y-5),fill="#258644",width=7)
            l((96,y+1,168,y+1),fill="#6a8268",width=6)
    elif name == "solo":
        r((30,73,211,169),36,fill="#7faafa",outline="#283366",width=9)
        r((34,66,204,155),34,fill="#a9c4ff",outline="#e6efff",width=4)
        r((59,100,113,117),4,fill="#483d77")
        r((76,83,95,136),4,fill="#483d77")
        for x,y,c in [(155,98,"#f07795"),(177,116,"#fbdb86"),(149,127,"#66bcab")]:
            e((x-10,y-10,x+10,y+10),fill=c,outline="#63568e",width=3)
    elif name == "conta":
        r((27,58,212,177),19,fill="#77396e",outline="#30234f",width=8)
        r((26,49,208,166),19,fill="#d696ce",outline="#f8d9ee",width=5)
        e((52,69,83,101),fill="#754b85")
        r((45,106,91,140),14,fill="#754b85")
        l((108,82,173,82),fill="#754b85",width=7)
        l((109,105,166,105),fill="#9d5787",width=6)
        e((156,126,223,192),fill="#513162",outline="#fff3f8",width=5)
        l((175,159,207,159),fill="#ffb0d5",width=9)
    elif name == "computador":
        r((89,172,154,212),12,fill="#264955",outline="#77c3bb",width=6)
        r((55,201,190,221),8,fill="#3f685f",outline="#96dabb",width=4)
        r((27,42,220,181),23,fill="#345f61",outline="#25344c",width=8)
        r((20,33,207,171),20,fill="#73b9af",outline="#baf3d5",width=5)
        r((37,50,189,147),12,fill="#18394d",outline="#358879",width=6)
        l((56,75,73,92,56,111),fill="#9ce9d0",width=8)
        l((87,113,131,113),fill="#e4e3a0",width=6)
        l((145,63,170,63),fill="#507b85",width=4)
        e((170,151,181,162),fill="#ebed82")
    elif name == "comentario":
        p([(67,144),(48,202),(109,168)],fill="#f28fb6",outline="#ffddda",width=6)
        r((24,46,203,169),30,fill="#9c4876",outline="#432545",width=8)
        r((23,35,196,157),28,fill="#f28fb6",outline="#ffddda",width=6)
        for x in (64,107,150):
            e((x-9,87,x+9,105),fill="#713b70")
        l((47,52,104,52),fill="#ffe4e4",width=5)
    elif name == "sem_cadastro":
        r((15,41,211,197),17,fill="#533663",outline="#292343",width=6)
        r((11,34,206,183),16,fill="#efd9f2",outline="#a875b2",width=5)
        r((16,39,201,70),11,fill="#aa7db4")
        for x in (33,48,63):
            e((x-4,50,x+4,58),fill="#f8e6f9")
        e((27,82,49,105),fill="#815d9c")
        r((23,105,53,125),7,fill="#815d9c")
        r((66,83,182,105),6,fill="#fff5fe",outline="#b292bc",width=3)
        r((66,113,182,134),6,fill="#fff5fe",outline="#b292bc",width=3)
        l((77,94,130,94),fill="#9f7caa",width=4)
        l((77,123,149,123),fill="#9f7caa",width=4)
        r((65,140,124,166),7,fill="#8e639e")
        e((85,58,229,202),outline="#fff5f5",width=22)
        e((85,58,229,202),outline="#e53649",width=15)
        l((110,80,207,180),fill="#fff5f5",width=19)
        l((110,80,207,180),fill="#e53649",width=13)
    elif name == "duelo":
        # Separate person and opponent; the cross sits in its own visual column.
        im = Image.new("RGBA",(408,232))
        d = ImageDraw.Draw(im)
        d.rounded_rectangle((5,36,155,194),21,fill="#423c74",outline="#ada9f3",width=5)
        d.ellipse((54,62,109,118),fill="#f1b6a3",outline="#ffe2c6",width=5)
        d.arc((47,56,116,124),189,344,fill="#9d6fc4",width=12)
        d.rounded_rectangle((34,125,128,173),20,fill="#8c83d2",outline="#bab5f2",width=4)
        d.line((182,96,222,137),fill="#fff1b4",width=10)
        d.line((222,96,182,137),fill="#fff1b4",width=10)
        place(im,icon("computador"),(319,112),184)
    elif name == "pergunta":
        p([(70,135),(42,195),(114,163)],fill="#8a75d3",outline="#d1d6ff",width=5)
        r((19,37,216,172),29,fill="#5c529f",outline="#282749",width=8)
        r((16,30,209,159),27,fill="#8e81d7",outline="#d9d6fc",width=5)
        d.arc((83,52,148,112),175,389,fill="#fff3e5",width=12)
        l((142,90,118,107,118,123),fill="#fff3e5",width=10)
        e((112,132,124,144),fill="#fff3e5")
    elif name == "proximo":
        r((17,55,210,183),16,fill="#234568",outline="#29334e",width=8)
        r((18,44,205,171),17,fill="#68bdc8",outline="#b9f0df",width=6)
        r((33,60,191,151),11,fill="#25475d")
        p([(70,76),(70,137),(113,106)],fill="#d0ffdc")
        l((125,105,170,105),fill="#f9d695",width=8)
        l((148,83,171,105,148,127),fill="#f9d695",width=8)
    elif name == "despedida":
        for x,y,radius,color in [(117,109,70,"#ffd296"),(193,56,29,"#c5aaff"),
                                 (184,170,34,"#fbaabd")]:
            p([(x,y-radius),(x+radius*.23,y-radius*.23),(x+radius,y),
               (x+radius*.23,y+radius*.23),(x,y+radius),
               (x-radius*.23,y+radius*.23),(x-radius,y),
               (x-radius*.23,y-radius*.23)],fill=color,outline="#fff1cb",width=4)
    else:
        raise ValueError(f"Ícone desconhecido: {name}")
    return im


@lru_cache(maxsize=1)
def board_art():
    im=Image.new("RGBA",(570,570))
    d=ImageDraw.Draw(im)
    rounded(d,(16,28,556,560),30,"#3a1d38")
    rounded(d,(8,8,550,547),31,"#9c6139","#e0a96d",7)
    rounded(d,(27,27,532,531),21,"#432b39","#603a37",9)
    for i in range(6):
        for j in range(6):
            x,y=38+80*i,38+80*j
            d.rectangle((x,y,x+78,y+78),fill=("#26664f","#2e7657")[(i+j)%2],
                        outline="#183d3d",width=2)
    for i,j,white in [(2,2,True),(3,3,True),(2,3,False),(3,2,False)]:
        x,y=78+80*i,78+80*j
        d.ellipse((x-31,y-27,x+31,y+32),fill="#133a38")
        d.ellipse((x-30,y-32,x+30,y+26),fill="#eecfa0" if white else "#34304c",
                  outline="#fff4ce" if white else "#635c7c",width=4)
        d.arc((x-24,y-26,x+24,y+18),188,281,fill="#fff7df" if white else "#9589a4",width=3)
    d.line((37,17,516,17),fill="#f6c483",width=3)
    d.line((24,67,24,493),fill="#c27e4d",width=3)
    return im


@lru_cache(maxsize=1)
def crt_art():
    im=Image.new("RGBA",(930,865))
    d=ImageDraw.Draw(im)
    rounded(d,(170,730,789,826),34,"#413655")
    rounded(d,(219,741,693,798),22,"#776276","#a89a9a",4)
    rounded(d,(51,56,902,777),53,"#3c304a")
    rounded(d,(18,21,881,755),53,"#a38780","#352844",9)
    rounded(d,(16,18,866,733),49,"#d7b999","#f8dac0",8)
    rounded(d,(44,52,825,689),43,"#c69273","#7a555c",8)
    rounded(d,(53,63,802,678),43,"#302a4c","#754b62",10)
    rounded(d,(70,78,786,659),33,"#182d42","#0f172d",8)
    rounded(d,(91,92,765,641),31,"#264354","#506f74",4)
    d.line((100,106,731,106),fill="#689899",width=5)
    for y in range(139,622,24):
        d.line((114,y,739,y),fill="#2d4a56",width=2)
    d.line((92,710,742,710),fill="#f6d3ad",width=4)
    for x in range(729,798,15):
        rounded(d,(x,691,x+7,710),3,"#8e6a71")
    d.ellipse((806,694,829,717),fill="#62c77e",outline="#3a6959",width=4)
    d.ellipse((811,697,818,703),fill="#e0ffa6")
    d.line((878,102,890,688),fill="#765964",width=7)
    return im

