from functools import lru_cache
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


@lru_cache(maxsize=1)
def avatar_layers():
    full = Image.open(CANAL / "avatar-recortado.png").convert("RGBA")
    crop = full.crop(full.getchannel("A").point(lambda x: 255 if x > 20 else 0).getbbox())
    crop = crop.resize((580, 640), NEAREST)
    matte = Image.new("L", crop.size)
    ImageDraw.Draw(matte).polygon([(0,142),(174,143),(209,232),(209,342),
                                   (226,362),(218,382),(162,402),(119,431),(0,438)], fill=255)
    pixels = np.array(crop)
    wings = pixels.copy()
    main = pixels.copy()
    alpha = np.asarray(matte) > 0
    # Keep the inner strip on the body so both layers overlap at the joint.
    wings[~alpha, 3] = 0
    outer = alpha & (np.arange(crop.width)[None, :] < 191)
    main[outer, 3] = 0
    return Image.fromarray(main), Image.fromarray(wings)


def eyelid(draw, x, y, w, h, tone):
    draw.polygon([(x+10,y),(x+w-9,y),(x+w,y+13),(x+w,y+h-13),
                  (x+w-11,y+h),(x+10,y+h),(x,y+h-12),(x,y+11)], fill=tone)
    mid = y + round(h*.57)
    draw.line([(x+7,mid-3),(x+16,mid+3),(x+w-17,mid+3),(x+w-7,mid-3)],
              fill=(26,12,53,255), width=8)
    draw.line([(x+21,mid-7),(x+w-21,mid-7)], fill=(102,65,145,255), width=3)


@lru_cache(maxsize=110)
def avatar_pose(wing, mouth, blink):
    base, feather = avatar_layers()
    image = Image.new("RGBA", base.size)
    # Apply the inverse flap transform around the same point on every pose.
    hinge_x, hinge_y = 213, 354
    angle = math.radians((wing-2)*6)
    scale_x = .66 + wing*.075
    c, s = math.cos(angle), math.sin(angle)
    a, b, d, e = c/scale_x, s/scale_x, -s, c
    feather = feather.transform(base.size, Image.Transform.AFFINE, (
        a, b, hinge_x-a*hinge_x-b*hinge_y,
        d, e, hinge_y-d*hinge_x-e*hinge_y,
    ), NEAREST)
    image.alpha_composite(feather)
    image.alpha_composite(base)
    draw = ImageDraw.Draw(image)
    if blink:
        eyelid(draw, 279, 265, 89, 87, (62,39,103,255))
        eyelid(draw, 414, 240, 52, 82, (66,40,105,255))
    if mouth:
        draw.polygon([(370,335),(414,319),(423,325),(423,354),(407,370),(381,368),(370,355)],
                     fill=(62,39,102,255))
        h = (0,10,23,36)[mouth]
        top = 347-h//2
        if mouth == 1:
            draw.line([(377,344),(384,350),(404,350),(414,341)], fill=(23,11,48,255),width=7)
        else:
            left,right = (375,416) if mouth == 2 else (378,413)
            draw.polygon([(left+5,top),(right-6,top-3),(right,top+7),(right-3,top+h-4),
                          (right-10,top+h),(left+10,top+h),(left,top+h-9),(left,top+6)],
                         fill=(19,9,41,255))
            draw.rectangle((left+9,top+h-8,right-8,top+h-3),fill=(250,106,120,255))
            if mouth == 3:
                draw.rectangle((left+10,top+3,right-9,top+6),fill=(255,224,181,255))
    return image


class Avatar:
    def __init__(self, audio_path):
        self.rate = 16000
        pcm = subprocess.check_output([
            "ffmpeg", "-v", "error", "-i", str(audio_path), "-ac", "1",
            "-ar", str(self.rate), "-f", "s16le", "-"
        ])
        self.wave = np.frombuffer(pcm,dtype="<i2").astype(np.float32)/32768

    def speak(self, t):
        index = round(t*self.rate)
        r = round(.023*self.rate)
        chunk = self.wave[max(0,index-r):index+r+1]
        if not chunk.size:
            return 0
        energy = np.sqrt(np.mean(chunk*chunk))
        if energy < .010:
            return 0
        return 1 + int(energy > .036) + int(energy > .080)

    def draw(self, image, t, x, y, width, energy=1, tilt=0, opacity=1):
        tick = math.floor(t*15)/15
        wing = round(2+2*math.sin(tick*math.tau*4.0))
        blink = ((t+.37)%3.62) < .13 or 1.11 < t < 1.23 or 3.66 < t < 3.79
        sprite = avatar_pose(wing,self.speak(tick),blink)
        width = round(width*(1+.026*math.sin(t*3.4)))
        sprite = sprite.resize((width,round(width*640/580)),NEAREST)
        rotation = round(tilt+energy*(5.0*math.sin(t*2.62)+1.9*math.sin(t*6)),1)
        sprite = sprite.rotate(rotation,NEAREST,expand=True)
        place(image,sprite,(x+energy*24*math.sin(t*2.6),y+energy*31*math.sin(t*3.5)),opacity=opacity)


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
