"""Anima as pupilas na abertura de cada olho, independentemente do brilho."""
from functools import lru_cache
import json
import math

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

import corpo


BUNDLE = corpo.BUNDLE
PUPIL = json.loads((BUNDLE/"pupilas.json").read_text(encoding="utf-8"))
ART = Image.open(BUNDLE / "sprites/lume-acendimento-18.png").convert("RGBA")
NATIVE_SIZE = (512, 512)
VISIBLE = (51,14,455,486)
ORIGIN = (22,1)
CANONICAL_CLIP = (255,226,479,371)
APERTURE = {
    "esquerda": [(266,205),(286,205),(295,210),(299,217),(302,227),(301,241),
                 (296,251),(289,256),(283,259),(261,259),(251,254),(246,246),
                 (245,235),(250,222),(257,211)],
    "direita": [(345,195),(356,195),(365,201),(368,208),(371,220),(371,236),
                (368,245),(362,249),(350,249),(342,244),(338,238),(335,226),
                (335,212),(337,205),(342,199)],
}
PATCH = [
    [(239,208),(256,194),(275,193),(295,197),(310,219),(311,241),
     (300,268),(277,277),(248,276),(235,256),(231,233)],
    [(329,205),(342,189),(360,188),(373,199),(380,220),
     (379,245),(368,255),(348,256),(334,242),(328,224)],
]


def raster(polygons, feather=None):
    im = Image.new("L",NATIVE_SIZE)
    pen = ImageDraw.Draw(im)
    for shape in polygons:
        pen.polygon(shape,fill=255)
    if feather:
        im = im.filter(ImageFilter.GaussianBlur(feather))
    return im


def eye_layers():
    color = np.asarray(ART)
    sclera = color.copy()
    layers = {}
    for eye, rows in PUPIL.items():
        matte = np.zeros(color.shape[:2],dtype=np.uint8)
        clip = np.asarray(raster([APERTURE[eye]]))
        for y,left,right in rows:
            matte[y,left:right+1] = 255
        iris = color.copy()
        iris[:,:,3] = matte
        if eye=="direita":
            # The camera pose already hides a small section behind the nose.
            # Keep its color available when the eye looks away from it.
            for y,left,_ in rows:
                iris[y,left-2:left] = iris[y,left]
                iris[y,left-2:left,3] = 255
        for y,left,right in rows:
            row = color[y]
            lo,hi = (243,304) if eye=="esquerda" else (334,372)
            swatch = row[lo:hi]
            cream = swatch[(swatch[:,0]>229)&(swatch[:,1]>192)&
                           (swatch[:,2]>148)&(swatch[:,2]<224)]
            if not len(cream):
                cream = np.array([[251,237,199,255]],dtype=np.uint8)
            shade = np.median(cream,axis=0).astype(np.uint8)
            sclera[y,left:right+1] = shade
        layers[eye] = Image.fromarray(iris),clip
    return Image.fromarray(sclera),layers


CLEAN,LAYERS = eye_layers()
COVER = raster(PATCH,feather=1.3)


@lru_cache(maxsize=60)
def native(dx,dy,blink):
    if blink:
        return corpo.expressao(ART,0,True,0)
    if dx==0 and dy==0:
        return ART
    out = CLEAN.copy()
    for eye,(iris,clip) in LAYERS.items():
        x = dx if eye=="esquerda" else round(dx*.65)
        y = dy if eye=="esquerda" else round(dy*.80)
        moved = Image.new("RGBA",NATIVE_SIZE)
        moved.paste(iris,(x,y))
        alpha = np.minimum(np.asarray(moved.getchannel("A")),clip)
        out.paste(moved,(0,0),Image.fromarray(alpha))
    return out


def canonical(image):
    canvas = Image.new(image.mode,(580,640))
    art = image.crop(VISIBLE)
    art = art.resize((round(art.width*1.36),round(art.height*1.36)),Image.Resampling.LANCZOS)
    canvas.paste(art,ORIGIN)
    return canvas.crop(CANONICAL_CLIP)


COVER_CANONICAL = canonical(COVER)


@lru_cache(maxsize=64)
def patch(dx,dy,blink):
    tile = canonical(native(dx,dy,blink))
    tile.putalpha(COVER_CANONICAL)
    return tile


def frame_tile(pose,dx,dy,blink):
    _,x,y,width,angle,_ = pose
    part = patch(dx,dy,blink)
    scale = width/580
    tile = part.resize((round(part.width*scale),round(part.height*scale)),Image.Resampling.BICUBIC)
    tile = tile.rotate(angle,Image.Resampling.BICUBIC,expand=True)
    left,top,right,bottom = CANONICAL_CLIP
    shift_x = scale*((left+right)/2-290)
    shift_y = scale*((top+bottom)/2-320)
    theta = math.radians(angle)
    a,b = math.cos(theta),math.sin(theta)
    xy=corpo.coordenadas(x+shift_x*a+shift_y*b,y-shift_x*b+shift_y*a,tile)
    return tile,xy


def is_open(image,pose):
    tile,(x,y)=frame_tile(pose,0,0,False)
    crop=np.asarray(image.crop((x,y,x+tile.width,y+tile.height)),dtype=np.int16)
    rgb=np.asarray(tile,dtype=np.int16)
    a=(rgb[:,:,3]>120)&(rgb[:,:,0]>155)&(rgb[:,:,1]>113)&(rgb[:,:,0]-rgb[:,:,2]>13)
    seen=(crop[:,:,0]>144)&(crop[:,:,1]>98)&(crop[:,:,0]-crop[:,:,2]>8)
    return np.count_nonzero(a&seen)>.20*np.count_nonzero(a)


def draw(image,pose,dx,dy,q,blink):
    tile,(x,y)=frame_tile(pose,dx,dy,blink)
    alpha=tile.getchannel("A")
    if not (1722<=q<2052):
        clip=corpo.janela(q,image,(x,y,x+tile.width,y+tile.height))
        if clip is not None:
            alpha=Image.fromarray(np.minimum(np.asarray(clip),np.asarray(alpha)))
    if pose[-1]<1:
        alpha=alpha.point(lambda value:round(value*pose[-1]))
    image.paste(tile,(x,y),alpha)
