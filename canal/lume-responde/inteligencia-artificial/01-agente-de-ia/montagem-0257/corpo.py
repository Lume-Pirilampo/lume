"""Place the 512-pixel Lume on the motion and occlusions of the approved cut."""
from bisect import bisect_right
from functools import lru_cache
from pathlib import Path
import json
import math

import numpy as np
from PIL import Image, ImageDraw


WORK = Path(__file__).resolve().parent
ROOT = WORK
BUNDLE = WORK.parents[3] / "assets/avatar-512"
MANIFEST = json.loads((BUNDLE / "Lume-spritesheet-512.json").read_text(encoding="utf8"))
FRAMES = MANIFEST["frames"]
CYCLE = tuple(range(1, 19)) + tuple(range(17, 1, -1))
ENDS = np.cumsum([FRAMES[number - 1]["duration"] for number in CYCLE])
RESAMPLE = Image.Resampling


def estado_de_luz(q):
    """Use the episode clock and play each endpoint once in the ping-pong cycle."""
    moment = (1000 * q) % (30 * int(ENDS[-1]))
    return CYCLE[bisect_right(ENDS, moment / 30)]


def boca_por_energia(nivel):
    """Rest, syllable onset, stressed syllable, then the natural wide-open pose."""
    return (1,2,3,0)[nivel]


@lru_cache(maxsize=18)
def partes(estado):
    original = Image.open(BUNDLE / FRAMES[estado-1]["filename"]).convert("RGBA")
    mask = Image.new("L", original.size)
    ImageDraw.Draw(mask).polygon([(67,138),(153,137),(205,190),(198,216),
                                  (198,238),(207,260),(227,284),(207,294),
                                  (191,304),(168,318),(151,331),(136,340),
                                  (78,339)],fill=255)
    shape = np.asarray(mask) > 0
    a = np.asarray(original).copy()
    wings = a.copy()
    wings[~shape,3] = 0
    a[shape,3] = 0
    return Image.fromarray(a),Image.fromarray(wings)


@lru_cache(maxsize=1)
def bochecha_e_boca():
    # The face is identical across the eighteen abdomen states. Inpaint its
    # open mouth once, preserving both neighbouring eyes and cheek shading.
    base,_=partes(1)
    box=(300,246,352,300)
    local=base.crop(box)
    border=[(305,264),(308,259),(313,254),(318,251),(333,251),(341,254),
            (346,260),(346,276),(341,287),(335,292),(330,294),(320,294),
            (315,289),(309,283),(305,276)]
    matte=Image.new("L",local.size)
    ImageDraw.Draw(matte).polygon([(x-box[0],y-box[1]) for x,y in border],fill=255)
    mask=np.asarray(matte)>0
    pixels=np.array(local,dtype=float)
    pixels[mask,:3]=pixels[25,3,:3]
    for _ in range(400):
        average=(np.roll(pixels,1,0)+np.roll(pixels,-1,0)+
                 np.roll(pixels,1,1)+np.roll(pixels,-1,1))*.25
        pixels[mask,:3]=average[mask,:3]
    cheek=Image.composite(Image.fromarray(np.uint8(np.rint(pixels))),local,matte)
    mouth=local.copy()
    mouth.putalpha(matte)
    return cheek,mouth.crop(matte.getbbox())


def expressao(base, boca, pisca_olhos, sorriso):
    if boca==0 and not pisca_olhos and sorriso==0:
        return base
    im=base.copy()
    if boca or sorriso:
        cheek,mouth=bochecha_e_boca()
        im.paste(cheek,(300,246))
        pen=ImageDraw.Draw(im)
        if boca==1 or sorriso:
            lift=round(4*sorriso)
            pontos=[(311-lift//2,270-lift),(314,273-lift//2),(319,276),
                    (326,277),(332,275),(338,270-lift)]
            pen.line([(x,y+1) for x,y in pontos],fill=(131,66,130),width=3)
            pen.line(pontos,fill=(44,15,52),width=3)
        else:
            h=21 if boca==2 else 33
            resized=mouth.resize((mouth.width,h),RESAMPLE.LANCZOS)
            im.alpha_composite(resized,(305,272-h//2))
    if pisca_olhos:
        draw=ImageDraw.Draw(im)
        for region,color,stroke in [
            ([(236,230),(242,211),(256,200),(274,196),(293,201),(304,214),
              (309,232),(305,246),(293,259),(257,263),(245,256),(235,246)],
             (102,51,111),[(239,236),(247,241),(255,244),(269,246),(284,244),(300,236)]),
            ([(330,216),(332,199),(340,191),(354,189),(368,198),(376,217),
              (377,237),(370,247),(349,253),(336,246),(329,231)],
             (108,53,114),[(332,223),(339,228),(350,230),(361,227),(373,219)])]:
            draw.polygon(region,fill=color)
            draw.line(stroke,fill=(50,19,56),width=4)
    return im


@lru_cache(maxsize=80)
def _asas(asa):
    _,wings=partes(18)
    dx,dy=212,285
    angle=math.radians((asa-2)*4)
    sx=.85+.075*asa
    c,s=math.cos(angle),math.sin(angle)
    a,b,d,e=c/sx,s/sx,-s,c
    coeff=(a,b,dx-a*dx-b*dy,d,e,dy-d*dx-e*dy)
    return wings.transform(wings.size,Image.Transform.AFFINE,coeff,RESAMPLE.BICUBIC)


@lru_cache(maxsize=96)
def sprite_512(estado, asa=2, boca=0, pisca_olhos=False, sorriso=0.0):
    base,_=partes(estado)
    layer=_asas(asa).copy()
    layer.alpha_composite(expressao(base,boca,pisca_olhos,sorriso))
    # Eyes (approx. 273,228 and 351,220) register to the eye line on the
    # episode's 580x640 articulated rig. Keep the new aspect ratio intact.
    canonical=Image.new("RGBA",(580,640))
    art=layer.crop((51,14,455,486))
    art=art.resize((round(art.width*1.36),round(art.height*1.36)),RESAMPLE.LANCZOS)
    canonical.alpha_composite(art,(round(51*1.36-47),round(14*1.36-18)))
    return canonical


MARKS = json.loads((WORK / "marcas-origem.json").read_text(encoding="utf8"))
MAP = np.asarray(json.loads((ROOT / "Lume-montagem-trilha/mapa-de-montagem.json").read_text(
    encoding="utf8"))["marcas_imagem_v7_para_montagem"])
ORIGINAL_MASK = Image.open(WORK / "silhueta-margem.png").convert("L")


def ease(x):
    x=min(1.,max(0.,x))
    return x*x*(3-2*x)


def source_time(q):
    return round(np.interp(q,MAP[:,1],MAP[:,0]))/30.


def progress(t,key,duration):
    start=MARKS["acoes"].get(key,MARKS["fases"].get(key))
    return ease((t-start)/duration)


def parametros(q):
    """Recover the shot's pose, including the independent paths introduced in v05."""
    t=source_time(q)
    x,y,w,energy,tilt,op=540,704,690,1.,0.,1.
    if q<128:
        t=q/30
        p=progress(t,"intro",.57)
        x,y,w,energy,tilt=540-570*(1-p),735+209*(1-p),720,1.10,-16*(1-p)
    elif 199<=q<265:
        if t>=MARKS["acoes"]["tabuleiro"]: return None
    elif 439<=q<502:
        leave=ease((q-481)/20)
        if q>=473:
            t=float(np.interp(q,MAP[:,1],MAP[:,0]))/30
        x,y,w,energy,tilt,op=455-516*leave,720+55*leave,487-75*leave,.54,-8-9*leave,1-leave
    elif 750<=q<1007:
        x,y,w,energy,tilt=540,360,361,.58,3
        op=ease((q-752)/18)
    elif 1007<=q<1040:
        t=float(np.interp(q,MAP[:,1],MAP[:,0]))/30
        p=ease((q-1011)/27)
        y,w,energy,tilt=360+344*p,361+329*p,.58+.42*p,3*(1-p)
    elif 1040<=q<1085:
        pass
    elif 1085<=q<1108:
        p=ease((q-1085)/22)
        x,y,w,tilt=540+960*p,704-205*p-64*math.sin(p*math.pi),690*(1-.21*p),-8*math.sin(p*math.pi)
    elif 1222<=q<1255:
        v=ease((q-1221)/34)
        x,y=764.14+(540-764.14)*v,688.25+(704-688.25)*v
        energy=.145+.855*v
        w=690*energy
        op=ease((q-1221)/7)
        if q>=1251:
            p=ease((q-1251)/4)
            x=x*(1-p)+540*p
            y=y*(1-p)+695*p
            energy+=p*(1.08-energy)
            w+=p*(625-w)
            tilt=2*p
    elif 1255<=q<1506:
        p=progress(t,"acesso",.41)
        x,y,w,energy,tilt=540-129*p,695,625,1.08,2
        if q>=1484:
            p=ease((q-1484)/22)
            x-=818*p
            y-=100*math.sin(p*math.pi/2)
    elif 1722<=q<2052:
        pin=ease((q-1721)/29)
        if q<1752:
            frame=max(1733,min(1751,q+round(12*(1-pin))))
            t=source_time(frame)
        shift=progress(t,"pergunta_final",.43)
        lift=progress(t,"despedida",.48) if t>=MARKS["fases"]["despedida"] else 0
        x,y,w,energy,tilt=540-145*shift,749-70*lift,739-57*shift,1.12,4*lift
        if q<1752:
            x+=round(1120*(1-pin));y-=round(31*math.sin(math.pi*pin))
    else:
        return None
    if op<=0: return None
    width=round(w*(1+.026*math.sin(t*3.4)))
    angle=round(tilt+energy*(5*math.sin(t*2.62)+1.9*math.sin(t*6)),1)
    return (t,x+energy*24*math.sin(t*2.6),y+energy*31*math.sin(t*3.5),width,angle,op)


@lru_cache(maxsize=1)
def ceu():
    yy,xx=np.ogrid[:1920,:1080]
    spot=np.exp(-(((xx-526)/650)**2+((yy-705)/760)**2))
    floor=np.exp(-(((xx-300)/790)**2+((yy-1440)/810)**2))
    colors=(1+17*spot+7*floor-1.55,1+9*spot+4*floor-.48,
            44+23*spot+10*floor-6*xx/1080-.75)
    return Image.fromarray(np.uint8(np.clip(np.round(np.dstack(colors)),0,255)))


def rotacionar(asset,width,angle,method):
    im=asset.resize((width,round(width*640/580)),method)
    if angle:
        im=im.rotate(angle,method if method==RESAMPLE.NEAREST else RESAMPLE.BICUBIC,expand=True)
    return im


def coordenadas(x,y,im):
    return round(x-im.width/2),round(y-im.height/2)


def janela(q,source,box):
    """Areas in front of the character: never paint over a lens, board, card or subtitle."""
    left,top,right,bottom=box
    xs=np.arange(left,right)[None,:];ys=np.arange(top,bottom)[:,None]
    if 112<=q<128:
        distance=np.abs(np.floor((xs-535)/14+.5))+np.abs(np.floor((ys-945)/14+.5))
        maximum=(abs(math.floor((1919-945)/14+.5))+
                 abs(math.floor((1079-535)/14+.5)))
        radius=round((maximum+15)*ease((q-111)/16))
        return Image.fromarray(np.uint8((distance>radius)*255))
    if 750<=q<777:
        rgba=np.asarray(source)
        # The moving green board is in front of the dissolving actor. Taking
        # its edges from the actual shot also covers the disks and the label.
        region=rgba[307:1160:4,60:1010:4].astype(np.int16)
        r,g,b=region[:,:,0],region[:,:,1],region[:,:,2]
        isl=(g-r>24)&(g-b>12)&(g>64)
        y,x=np.nonzero(isl)
        mask=Image.new("L",(right-left,bottom-top),255)
        draw=ImageDraw.Draw(mask)
        if len(y):
            rect=(60+4*x.min()-6-left,307+4*y.min()-8-top,
                  60+4*x.max()+8-left,307+4*y.max()+7-top)
            draw.rounded_rectangle(tuple(map(int,rect)),radius=7,fill=0)
        if q<761:
            draw.rectangle((-left,110-top,366-left,360-top),fill=0)
            draw.rectangle((695-left,110-top,1080-left,360-top),fill=0)
        return mask
    if 1222<=q<1249:
        v=ease((q-1221)/34)
        size=293+(2020-293)*v**1.22
        cx=764.14+(540-764.14)*v
        cy=688.25+(704-688.25)*v
        radius=52.2*size/240 + 300*ease((q-1235)/15)
        return Image.fromarray(np.uint8(((xs-cx)**2+(ys-cy)**2<radius**2)*255))
    if 439<=q<501:
        t=source_time(q)
        if q<473:
            p=progress(t,"busca",.59); scale=max(0,min(1,2*p))
            icx=252+470*p;icy=657+39*(1-scale)
            w=round(253*(.58+.42*scale))
            gx=icx-22*w/240;gy=icy-26*w/240
            rc=76*w/240
        else:
            gr=ease((q-483)/23);t2=ease((q-482)/22)
            gx=699-159*t2;gy=630+118*t2-18*math.sin(math.pi*t2)
            rc=(51+315*gr)*(1.45-.45*gr)
            w=round(253*rc/77)
        if q>475:
            return Image.fromarray(np.uint8(((xs-gx)**2+(ys-gy)**2>(rc+3)**2)*255))
        if scale_or(q,t)>0:
            # Exact ornamental silhouette of the magnifying glass, including
            # the diagonal handle. It crosses the speaker's eyes in this shot.
            lens=Image.open(WORK/"mascara-lupa.png").resize((w,w),RESAMPLE.LANCZOS)
            cx=gx+22*w/240;cy=gy+26*w/240
            mask=Image.new("L",(right-left,bottom-top),255)
            mask.paste(0,(round(cx-w/2)-left,round(cy-w/2)-top,round(cx-w/2)-left+w,round(cy-w/2)-top+w),lens)
            return mask
    return None


def scale_or(q,t):
    return 1 if q>=473 else progress(t,"busca",.59)


def aplicar(frame_rgb_pil,q):
    p=parametros(q)
    if p is None:
        return frame_rgb_pil
    t,x,y,width,angle,op=p
    tick=math.floor(t*15)
    wing=round(2+2*math.sin(tick/15*math.tau*4))
    blink=((t+.37)%3.62)<.13 or 1.11<t<1.23 or 3.66<t<3.79
    mouth=boca_por_energia(0 if 80<=q<128 else MARKS["falas_15fps"][tick])
    # The original actor has detached gold specks at the extreme corners.
    # Rotate a padded footprint so their filter bleed is erased at every angle.
    pad_width=round(width*40/580)
    old=ORIGINAL_MASK.resize((width+2*pad_width,round(width*640/580)+2*pad_width),RESAMPLE.BILINEAR)
    if angle:
        old=old.rotate(angle,RESAMPLE.BILINEAR,expand=True)
    new=rotacionar(sprite_512(estado_de_luz(q),wing,mouth,blink),width,angle,RESAMPLE.BICUBIC)
    l,u=coordenadas(x,y,old)
    nl,nu=coordenadas(x,y,new)
    if 1011<=q<=1037:
        # The slide was feathered over the previous shot near the upper edge
        # of the motion field. That old antenna can therefore sit outside the
        # moving speaker's silhouette until the lower plate takes over.
        fragment=(410,112,676,213)
        frame_rgb_pil.paste(ceu().crop(fragment),fragment[:2])
    r=min(1080,l+old.width);b=min(1345,u+old.height)
    left,top=max(0,l),max(0,u)
    if left>=r or top>=b: return frame_rgb_pil
    box=(left,top,r,b)
    crop=(left-l,top-u,r-l,b-u)
    old=old.crop(crop)
    if 1251<=q<=1254:
        # The v05 handoff crossfades two actors of different scales. Both
        # silhouettes lie within this otherwise empty patch of the stage.
        old=Image.new("L",old.size,255)
    src=frame_rgb_pil.crop(box)
    # Rebuild only the moving footprint. The surrounding recorded stage,
    # badges, captions, all sound and all transition timings come from v05.
    area=Image.composite(ceu().crop(box),src,old)
    if op<1:
        a=new.getchannel("A").point(lambda v:round(v*op))
    else:
        a=new.getchannel("A")
    area.paste(new,(nl-left,nu-top),a)
    mask=janela(q,frame_rgb_pil,box)
    if mask is not None: area=Image.composite(area,src,mask)
    frame_rgb_pil.paste(area,box[:2])
    return frame_rgb_pil
