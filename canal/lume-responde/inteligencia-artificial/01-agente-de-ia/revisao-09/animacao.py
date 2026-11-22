"""Animação do avatar, com a boca dirigida pela locução limpa deste corte."""

import math

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

import corpo
from arte import icon, place

W, H, FPS = 1080, 1920, 30
MOUTH = (360, 318, 431, 391)
RESAMPLE = Image.Resampling
OLD_MASK = corpo.ORIGINAL_MASK.filter(ImageFilter.MaxFilter(5))


def nivel_da_voz(audio, frames):
    samples = np.pad(audio, (0, max(0, frames * 1600 - len(audio))))[:frames * 1600]
    energy = np.sqrt(np.mean(samples.reshape(frames, 1600) ** 2, axis=1))
    return np.digitize(energy, [0.008, 0.065, 0.155]), energy


def mouth_layer(pose, mouth):
    """Transform only the cheek patch, using the same transform as the full sprite."""
    _, x, y, width, angle, _ = pose
    tile = corpo.sprite_512(1, 2, mouth).crop(MOUTH)
    mask = Image.new("L", tile.size)
    ImageDraw.Draw(mask).rounded_rectangle((4, 4, tile.width-5, tile.height-5), radius=10, fill=255)
    tile.putalpha(mask.filter(ImageFilter.GaussianBlur(2)))
    visible = width / 580
    w, h = round(tile.width * visible), round(tile.height * visible)
    tile = tile.resize((w, h), RESAMPLE.BICUBIC)
    tile = tile.rotate(angle, RESAMPLE.BICUBIC, expand=True)
    off_x = visible * ((MOUTH[0] + MOUTH[2]) / 2 - 290)
    off_y = visible * ((MOUTH[1] + MOUTH[3]) / 2 - 320)
    theta = math.radians(angle)
    cx = x + off_x * math.cos(theta) + off_y * math.sin(theta)
    cy = y - off_x * math.sin(theta) + off_y * math.cos(theta)
    return tile, corpo.coordenadas(cx, cy, tile)


def match_mouth(image, pose):
    """Measure the alignment of a predicted cheek with the existing eyes/face."""
    tile, (x, y) = mouth_layer(pose, 0)
    if x < 0 or y < 0 or x+tile.width > W or y+tile.height > H:
        return float("inf")
    template = np.asarray(tile, dtype=np.float32)
    # Outer cheek pixels have the same colors for all four mouth poses.
    mask = (template[:, :, 3] > 225)
    y0, x0 = np.ogrid[:tile.height, :tile.width]
    mask &= ((abs(x0-tile.width/2) > tile.width*.24) |
             (abs(y0-tile.height/2) > tile.height*.27))
    observed = np.asarray(image.crop((x, y, x+tile.width, y+tile.height)), dtype=np.float32)
    return np.median(np.mean(np.abs((observed-template[:, :, :3])[mask]), axis=1))


def replace_mouth(image, pose, level, clip=None):
    mouth = corpo.boca_por_energia(level)
    tile, xy = mouth_layer(pose, mouth)
    alpha = tile.getchannel("A")
    if clip is not None:
        x, y = xy
        mask = clip.crop((x,y,x+tile.width,y+tile.height))
        alpha = Image.fromarray(np.minimum(np.asarray(mask), np.asarray(alpha)))
    if pose[-1] < 1:
        alpha = alpha.point(lambda v: round(v * pose[-1]))
    image.paste(tile, xy, alpha)


def clear_old_actor(image, pose, sky):
    _, x, y, width, angle, _ = pose
    pad = round(width * 40 / 580)
    mask = OLD_MASK.resize((width+2*pad,round(width*640/580)+2*pad),RESAMPLE.BILINEAR)
    mask = mask.rotate(angle, RESAMPLE.BILINEAR, expand=True)
    mask = mask.filter(ImageFilter.GaussianBlur(4))
    left, top = corpo.coordenadas(x, y, mask)
    box = max(0, left), max(0, top), min(W, left+mask.width), min(1320, top+mask.height)
    if box[0] >= box[2] or box[1] >= box[3]:
        return
    crop = (box[0]-left, box[1]-top, box[2]-left, box[3]-top)
    image.paste(sky.crop(box), box[:2], mask.crop(crop))


def bubbles(image, t):
    """Restore the foreground bubbles where the recorded avatar crosses their footprint."""
    # The right-side icons keep the spacing of the preceding cut.
    for name, x, y, width, enter, disappear in (
        ("pergunta", 848, 526, 208, 59.85, 70.43),
        ("comentario", 890, 780, 209, 63.05, 70.43),
        ("proximo", 825, 1045, 219, 69.00, 70.90),
    ):
        cue = corpo.ease((t-enter)/.32)
        opacity = cue * (1-corpo.ease((t-disappear)/.32))
        if opacity == 0:
            continue
        center = x+118*(1-cue), y+39*(1-cue)
        turn = (1 if name == "comentario" else -1)*8*(1-cue)
        art = icon(name).rotate(turn, RESAMPLE.BICUBIC)
        place(image, art, center, width*(.58+.42*cue), opacity)


def cta_pose(time, seconds):
    start, question, goodbye = seconds
    entrance = corpo.ease((time-start)/.82)
    shift = corpo.ease((time-question)/.46)
    lift = corpo.ease((time-goodbye)/.48)
    x = 540 + 1120*(1-entrance) - 145*shift
    y = 749 - 31*math.sin(math.pi*entrance) - 70*lift
    wave = time - start
    x += 20*math.sin(wave*2.6)
    y += 23*math.sin(wave*3.5)
    width = (739-57*shift) * (1+.018*math.sin(wave*3.4))
    tilt = 4*lift + 4.6*math.sin(wave*2.62) + 1.5*math.sin(wave*6)
    return x, y, round(width), round(tilt,1)


def draw_cta_actor(image, frame, pose, level):
    x, y, width, angle = pose
    t = frame / FPS
    wing = round(2+2*math.sin(t*math.tau*4))
    blink = ((t+.37)%3.62)<.12
    mouth = corpo.boca_por_energia(level)
    sprite = corpo.sprite_512(corpo.estado_de_luz(frame), wing, mouth, blink)
    sprite = corpo.rotacionar(sprite,width,angle,RESAMPLE.BICUBIC)
    image.paste(sprite, corpo.coordenadas(x,y,sprite), sprite.getchannel("A"))
