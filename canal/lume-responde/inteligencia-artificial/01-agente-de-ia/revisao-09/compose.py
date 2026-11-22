"""Revisa a montagem do Lume Responde 01 sem recomprimir o áudio da v8."""

import argparse
from bisect import bisect_right
from functools import lru_cache
import json
import math
import os
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

HERE = Path(__file__).resolve().parent
EPISODE = HERE.parent
V8 = EPISODE / "montagem-0316"
sys.path[:0] = [str(EPISODE), str(EPISODE / "montagem-0257")]

import animacao as actor
import cama
import corpo

W, H, FPS = actor.W, actor.H, actor.FPS
SIZE = W, H
BYTES = W * H * 3
FF = [cama.FF, "-hide_banner", "-nostdin", "-v", "error", "-y"]
COLOR = "#ffd582"
CUES = json.loads((HERE / "legendas.json").read_text(encoding="utf-8"))
CUE_FRAMES = [round(start * FPS) for start, _ in CUES]
DESPEDIDA = json.loads((HERE / "despedida.json").read_text(encoding="utf-8"))
STARS = [(123,402),(878,336),(192,915),(893,1135),(273,677),
         (843,770),(153,1251),(920,1282),(459,465)]
FIREFLIES = [
    (109,380,8.4,1.3,28,36),(925,294,9.2,6.7,63,29),(190,841,7.3,4.1,38,41),
    (891,1124,8.8,2.0,39,57),(285,577,9.6,8.4,51,43),(963,725,7.8,3.7,48,36),
    (86,1239,8.2,6.9,28,61),(883,1633,9.4,5.3,74,37),(511,402,9.9,4.8,39,71),
    (680,1045,8.6,1.1,63,47),(335,1680,7.9,3.1,44,55),
]


def render_frame(source, at):
    raw = subprocess.check_output(FF+["-ss", f"{at:.8f}", "-i", str(source), "-frames:v", "1",
        "-pix_fmt", "rgb24", "-f", "rawvideo", "-"])
    return Image.frombytes("RGB", SIZE, raw)


def feather(size, axis, points):
    n = size[axis]
    levels = np.interp(np.arange(n), *np.asarray(points).T)
    alpha = np.broadcast_to(levels[:,None] if axis == 1 else levels[None,:], size[::-1])
    return Image.fromarray(alpha.astype("u1"))


@lru_cache(maxsize=64)
def font(path, size):
    return ImageFont.truetype(str(path), size)


@lru_cache(maxsize=80)
def caption(path, text):
    if not text:
        return None
    phrase = text.upper().replace("“", '"').replace("”", '"')
    cap = 106
    width = font(path, cap).getlength(phrase)
    face = font(path, min(cap, math.floor(956*cap/width)))
    layer = Image.new("RGBA", (W, 142))
    draw = ImageDraw.Draw(layer)
    draw.text((W/2, 71), phrase, font=face, fill=COLOR, anchor="mm")
    return layer


@lru_cache(maxsize=3)
def title_card(path, question_color):
    plate = Image.new("RGB", (W, H), "black")
    draw = ImageDraw.Draw(plate)
    lines = ("O QUE É UM", "AGENTE DE IA")
    face = font(path, 126)
    for y, line in zip((887, 1030), lines):
        draw.text((W/2, y), line, font=face, fill="#fff8e9", anchor="mm")
    draw.text((W/2, 1485), "?", font=font(path, 600), fill=question_color, anchor="mm")
    return plate.crop((0, 773, W, 1815))


def red_hearts(image):
    box = (347, 65, 733, 215)
    data = np.asarray(image.crop(box), dtype=np.float32)
    r,g,b = np.moveaxis(data, 2, 0)
    coverage = np.clip((r-b-22)/68,0,1) * np.clip((g-b-7)/40,0,1)
    target = np.stack((r, g*.22+18, b*.60+18), axis=2)
    image.paste(Image.fromarray(np.uint8(np.round(data + coverage[:,:,None]*(target-data)))), box[:2])


def remove_stars(image, sky):
    for i,(x,y) in enumerate(STARS):
        dy = 13 if i in (2,3) else 6
        box = (x-7,y-dy,x+9,y+dy+4)
        part = np.asarray(image.crop(box), dtype=np.int16)
        back = np.asarray(sky.crop(box), dtype=np.int16)
        delta = np.max(np.abs(part-back), axis=2)
        near_background = delta<16
        if np.count_nonzero(near_background) < .70 * delta.size:
            continue
        # Surrounding compressed pixels are preserved. Only the baked pinprick
        # and its immediate fringe are replaced with the clean sky.
        select = ((delta>9) | (part[:,:,0]>28)) & (part[:,:,0]<150)
        if np.count_nonzero(select) < .27 * delta.size:
            patch = Image.fromarray(np.uint8(np.where(select[:,:,None],back,part)))
            image.paste(patch,box[:2])


@lru_cache(maxsize=32)
def firefly_tile(strength):
    side = 42
    y,x = np.mgrid[:side,:side] - side//2
    halo = np.exp(-(x*x+y*y)/(2*6.3**2)) * .33
    body = np.exp(-(x*x/(2*1.65**2)+y*y/(2*2.2**2))) * .80
    alpha = np.clip((halo+body) * strength/31,0,1) * 255
    return alpha.astype("u1")


def flies(image, sky, time):
    fade = 1-corpo.ease((time-73.6)/1.42)
    if fade == 0:
        return
    for i,(x,y,period,phase,dx,dy) in enumerate(FIREFLIES):
        cycle = ((time-phase) % period)
        length = 1.13 + .065*(i%4)
        if cycle >= length:
            continue
        amount = round(31 * fade * math.sin(math.pi*cycle/length)**1.55)
        if not amount:
            continue
        angle = time*math.tau/period+i
        cx = round(x+dx*math.sin(angle*.89))
        cy = round(y+dy*math.cos(angle*.73))
        box = (cx-21,cy-21,cx+21,cy+21)
        observed = np.asarray(image.crop(box), dtype=np.int16)
        back = np.asarray(sky.crop(box), dtype=np.int16)
        # Depth test against the backdrop avoids putting the halo over cards,
        # the avatar, transitions, subtitles or the existing margin fireflies.
        visibility = np.clip((26-np.max(np.abs(observed-back),axis=2))/16,0,1)
        alpha = Image.fromarray(np.uint8(firefly_tile(amount)*visibility))
        image.paste((255,191,108), box, alpha)


def clear_baked_bubbles(image, sky, time):
    regions = [
        ((742,421,1080,666),59.85),
        ((768,677,1080,902),63.05),
        ((713,946,1080,1164),69.00),
    ]
    for box, start in regions:
        if time < start:
            continue
        plate = sky.crop(box)
        pixels = np.asarray(image.crop(box), dtype=np.int16)
        backdrop = np.asarray(plate, dtype=np.int16)
        change = np.max(np.abs(pixels-backdrop),axis=2)
        alpha = Image.fromarray(np.uint8(np.clip((change-8)/14,0,1)*255))
        image.paste(plate,box[:2],alpha.filter(ImageFilter.MaxFilter(5)))


def sky_plate(source):
    # In the examples shot the centre and right are clear. Fill the small
    # footprint occupied by the price tag with clean samples from other shots.
    clean = np.asarray(render_frame(source,52.70),dtype=np.int16)
    model = np.asarray(corpo.ceu(),dtype=np.int16) - [2,3,3]
    error = np.max(np.abs(clean-model),axis=2)
    for time in (59.70,74.50,39.75,17.45):
        candidate = np.asarray(render_frame(source,time),dtype=np.int16)
        difference = np.max(np.abs(candidate-model),axis=2)
        allowed = (error>12) & (difference<error)
        clean[allowed] = candidate[allowed]
        error[allowed] = difference[allowed]
    fallback = error>14
    clean[fallback] = model[fallback]
    return Image.fromarray(np.uint8(np.clip(clean,0,255)))

def revised_frame(image, num, q, level, asset, question_color):
    font_path, sky, clear_caption, caption_mask, intro_mask = asset
    time = num/FPS
    if 112 <= q < 199:
        card = title_card(font_path, question_color)
        if q >= 128:
            image.paste(card,(0,773))
            return image
        visibility = corpo.janela(q, image, (0,1340,W,1630))
        active = Image.fromarray(np.minimum(np.asarray(intro_mask),np.asarray(visibility)))
        region = image.crop((0,1340,W,1630))
        region.paste(clear_caption,(0,0),active)
        image.paste(region,(0,1340))

        # The question and the giant mark appear only inside the black part
        # of the opening diamond, leaving the baked illuminated edges intact.
        yy,xx = np.ogrid[773:1815,:W]
        distance = np.abs(np.floor((xx-535)/14+.5)) + np.abs(np.floor((yy-945)/14+.5))
        radius = round(124*corpo.ease((q-111)/16))
        reveal = Image.fromarray(np.uint8((distance<radius-6)*255))
        ramp = corpo.ease((q-115)/9)
        card = Image.blend(Image.new("RGB",card.size),card,ramp)
        image.paste(card,(0,773),reveal)
        return image

    # Preserve the visual name and final held signature below the avatar.
    if time < 71.25:
        image.paste(clear_caption, (0,1340), caption_mask)
    remove_stars(image, sky)
    if time < 3.42:
        red_hearts(image)

    pose = corpo.parametros(q)
    if 1722 <= q < 2052:
        if pose is not None:
            actor.clear_old_actor(image, pose, sky)
        clear_baked_bubbles(image, sky, time)
        p = np.asarray(actor.cta_pose(time, (58.87,59.85,70.43)))
        # Match the original landing at entry and the existing signature at exit.
        if pose is not None and (time < 59.19 or time > 70.03):
            k = corpo.ease((time-58.91)/.28) * (1-corpo.ease((time-70.03)/.40))
            p = np.asarray(pose[1:5])*(1-k)+p*k
        x,y,width,angle = p
        actor.draw_cta_actor(image,num,(x,y,round(width),angle),level)
        actor.bubbles(image,time)
    elif str(q) in DESPEDIDA and num < round(71.24*FPS):
        x,y,width,angle = DESPEDIDA[str(q)]
        actor.replace_mouth(image,(time,x,y,round(width),angle,1),level)
    elif pose is not None and actor.match_mouth(image,pose) < 25:
        actor.replace_mouth(image,pose,level)
    flies(image,sky,time)

    index = bisect_right(CUE_FRAMES,num)-1
    if index >= 0:
        layer = caption(font_path,CUES[index][1])
        if layer is not None:
            image.paste(layer,(0,1413),layer.getchannel("A"))
    return image


def build_assets(source, font_path):
    reference = render_frame(source, 74.5)
    sky = sky_plate(source)
    # The closing frame carries the same clean lower plate as the other shots.
    band = (0,1340,W,1630)
    clear_caption = reference.crop(band)
    caption_mask = feather(clear_caption.size, 1, [(0,0),(23,255),(260,255),(289,0)])
    intro = np.asarray(render_frame(source,.90).crop(band))
    mask = Image.fromarray(np.uint8((intro[:,:,0]>50)*255)).filter(ImageFilter.MaxFilter(17))
    return font_path,sky,clear_caption,caption_mask,mask


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("saida", type=Path)
    parser.add_argument("--base", type=Path, default=EPISODE/"Lume-Responde-01-v8.mp4")
    parser.add_argument("--font", type=Path, default=os.environ.get("LUME_FONT"))
    parser.add_argument("--interrogacao", choices=["roxo","vermelho","amarelo"], default="roxo")
    parser.add_argument("--trecho", nargs=2, type=float, metavar=("INICIO","FIM"))
    args = parser.parse_args()
    if args.font is None or not args.font.is_file():
        parser.error("Forneça a fonte KnockIt! Display Research v0.15 com --font ou LUME_FONT.")
    marks = json.loads((V8/"tempo.json").read_text(encoding="utf-8"))
    q,s = np.asarray(marks["marcas_fonte_para_tempo"]).T
    target = np.rint(s*FPS).astype(int)
    total = target[-1]
    pts = np.rint(np.interp(np.arange(int(q[-1])),q,target)).astype(int)
    at_source = np.searchsorted(pts,np.arange(total),side="right")-1
    hold = round(np.interp(marks["quadro_fim_movimento_da_fonte"],q,target))
    levels,_ = actor.nivel_da_voz(cama.samples(V8/"narracao.flac",1)[:,0],total)
    first,stop = (round(sec*FPS) for sec in args.trecho) if args.trecho else (0,total)
    if not 0 <= first < stop <= total:
        parser.error("O trecho está fora da duração do episódio.")
    tone = {"roxo":"#a88aef","vermelho":"#ff4b59","amarelo":"#ffcb63"}[args.interrogacao]
    assets = build_assets(args.base,args.font)
    with TemporaryDirectory(prefix="lume-v9-") as folder:
        raw_video = Path(folder)/"revisado.mp4"
        seek = ["-ss",f"{first/FPS:.9f}"]
        with subprocess.Popen(FF+seek+["-threads","3","-i",str(args.base),"-an","-frames:v",str(stop-first),
                "-f","rawvideo","-pix_fmt","rgb24","-"],stdout=subprocess.PIPE) as source, \
             subprocess.Popen(FF+["-f","rawvideo","-pix_fmt","rgb24","-s","1080x1920","-r",str(FPS),"-i","-",
                "-an","-c:v","libx264","-threads","5","-preset","fast","-crf","18","-pix_fmt","yuv420p",
                "-colorspace","bt709","-color_trc","bt709","-color_primaries","bt709","-movflags","+faststart",
                str(raw_video)],stdin=subprocess.PIPE) as render:
            final = None
            for num in range(first,stop):
                image = Image.frombytes("RGB",SIZE,source.stdout.read(BYTES))
                if num < hold or final is None:
                    image = revised_frame(image,num,at_source[num],levels[num],assets,tone)
                    final = image.tobytes()
                render.stdin.write(final)
                if num%300 == 0:
                    print(f"{num}/{stop} quadros",flush=True)
            render.stdin.close()
            if source.wait() or render.wait():
                raise RuntimeError("A exportação dos quadros não terminou.")
        audio = ["-ss",f"{first/FPS:.9f}"] if first else []
        limit = ["-t",f"{(stop-first)/FPS:.9f}"] if args.trecho else []
        subprocess.run(FF+["-i",str(raw_video),*audio,"-i",str(args.base),"-map","0:v","-map","1:a",
            "-c","copy",*limit,"-movflags","+faststart",str(args.saida)],check=True)


if __name__ == "__main__":
    main()
