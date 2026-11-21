import argparse
from functools import lru_cache
import json
import math
from pathlib import Path
import runpy
import subprocess
import sys

from PIL import Image, ImageDraw, ImageFont

EPISODIO = Path(__file__).resolve().parent
sys.path.insert(0, str(EPISODIO))
from arte import Avatar, board_art, control, crt_art, ease, icon, place

CANAL = EPISODIO.parents[2]
ABERTURA = runpy.run_path(str(CANAL / "apresentacao" / "montar.py"))
W, H, FPS = (ABERTURA[item] for item in ("W", "H", "FPS"))
AMBAR, CREME, ASA, SUAVE = (ABERTURA[item] for item in ("AMBER", "CREAM", "WING", "MUTED"))
CX = 540
GREEN = (44, 187, 93)

composicao = json.loads((EPISODIO / "cenas.json").read_text(encoding="utf-8"))
DURACAO = composicao["duracao"]
BLOCOS = composicao["blocos"]
ACOES = composicao["acoes"]
roteiro = (EPISODIO / "roteiro.txt").read_text(encoding="utf-8")
if " ".join(texto.replace("|", " ") for _, _, texto in BLOCOS) != " ".join(roteiro.split()):
    raise ValueError("As legendas divergem do roteiro.")
if BLOCOS[0][0] != 0 or BLOCOS[-1][0] >= DURACAO or any(
    a[0] >= b[0] for a, b in zip(BLOCOS, BLOCOS[1:])
):
    raise ValueError("Tempos de legenda inválidos.")
ENTRADAS = {}
for inicio, fase, _ in BLOCOS:
    ENTRADAS.setdefault(fase, inicio)


@lru_cache(maxsize=1)
def avatar():
    return Avatar(EPISODIO / "narracao.flac")


@lru_cache(maxsize=12)
def mono(size):
    return ImageFont.truetype("DejaVuSansMono.ttf", size)


def label(draw, text, x, y, size=35, color=SUAVE):
    draw.text((x,y),text,font=mono(size),fill=color,anchor="mt")


def titulo(draw, text, x, y, size, color=CREME, limit=920):
    face = ABERTURA["font"]
    size = min(size, math.floor(size*limit/face("title",size).getlength(text)))
    ABERTURA["text"](draw,text,(x,y),size,color,anchor="mt")


def panel(draw, box, color, border):
    draw.rounded_rectangle(box,28,fill=color,outline=border,width=4)


def progress(t, key, duration=.30):
    start = ACOES[key] if key in ACOES else ENTRADAS[key]
    return ease((t-start)/duration)


def animated_icon(image, name, x, y, width, v, direction=1):
    if v <= 0:
        return
    x += direction*118*(1-v)
    y += 39*(1-v)
    place(image,icon(name),(x,y),max(1,width*(.58+.42*v)),v)


def narrator(image, draw, phase, t):
    start = progress(t,"intro",.57)
    if phase == "intro":
        avatar().draw(image,t,CX-570*(1-start),735+209*(1-start),720,1.10,-16*(1-start))
    elif phase == "serie":
        v = progress(t,"serie",.34)
        avatar().draw(image,t,CX-108*v,728-45*v,735,1.12,-3*v)
        if v > 0:
            x,y=826,590+50*(1-v)
            w,h=84*v,63*v
            draw.rounded_rectangle((x-w,y-h,x+w,y+h),22,fill="#513668",outline="#eaa1ca",width=5)
            draw.polygon([(x-w+32,y+h-3),(x-w+12,y+h+29),(x-w+65,y+h-3)],fill="#513668")
            for dx in (-34,0,34):
                if v > .38:
                    draw.ellipse((x+dx-7,y-7,x+dx+7,y+7),fill="#ffddb1")
    elif phase in ("cta","cta_convite","despedida"):
        convite = phase == "cta_convite"
        v = progress(t,"cta_convite",.40) if convite else 0
        opacity = 1 - .96*ease((t-(DURACAO-.43))/.42) if phase == "despedida" else 1
        avatar().draw(image,t,CX-105*v,749,756,1.12,3*v,opacity=opacity)
        if convite:
            animated_icon(image,"comentario",830,773,180,v,1)
    else:
        avatar().draw(image,t,CX,704,690,1.0)


def criteria(draw, t):
    for index,(name,text) in enumerate((("criterio1","SEM CADASTRO"),("criterio2","CONTRA O COMPUTADOR"))):
        if t < ENTRADAS[name]:
            continue
        v = progress(t,name)
        x = (315,765)[index] + (-1 if not index else 1)*106*(1-v)
        y = 1205+38*(1-v)
        color,edge=(("#283255","#92b9f8"),("#273e43","#83d6a0"))[index]
        panel(draw,(round(x-205),round(y-49),round(x+205),round(y+49)),color,edge)
        titulo(draw,text,x,y-17,38,color=edge,limit=372)


def request_scene(image, draw, t):
    if t < ACOES["jogo"]:
        narrator(image,draw,"pedido",t)
        return
    game = progress(t,"jogo",.28)
    board = progress(t,"tabuleiro",.34)
    crt = progress(t,"navegador",.42)
    if board < .996:
        x = -330+870*game
        place(image,control(),(x,780),752)
    if board > 0:
        if crt > 0:
            place(image,crt_art(),(CX,784),max(1,943*crt))
        # The monitor grows behind the board, whose endpoint sits inside the glass.
        x = 1425-885*board-39*crt
        y = 765-80*crt
        place(image,board_art(),(x,y),800-267*crt)
        if crt > .8:
            r = ease((crt-.8)/.2)
            draw.line((209,418,235,418+round(44*r)),fill="#9ececa",width=3)
    criteria(draw,t)


@lru_cache(maxsize=3)
def capture(state, width):
    with Image.open(EPISODIO/"assets"/f"reversi-{state}.jpg") as file:
        return file.convert("RGB").resize((width,width),Image.Resampling.LANCZOS)


def search_scene(image, draw, t):
    if t < ACOES["reversi"]:
        v = progress(t,"busca",.59)
        x = 252+470*v
        avatar().draw(image,t,455,720,487,.54,-8)
        animated_icon(image,"lupa",x,657,253,min(1,2*v),0)
        return
    v = progress(t,"reversi",.36)
    y = round(339+51*(1-v))
    x = CX+192*(1-v)
    titulo(draw,"REVERSI",x+6,y+8,156,"#162449",900)
    titulo(draw,"REVERSI",x,y,156,"#96f4c7",900)
    label(draw,"6 × 6",CX,527,60,"#d4ffd7")
    size = max(1,round(466*(.73+.27*v)))
    image.paste(capture("antes",size),(CX-size//2,632+round(63*(1-v))))
    label(draw,"TRYBOARDGAMES.COM",CX,1148,30,"#94c4ba")


def game_badge(image,draw,t,key,name,text,x,y,color):
    v = progress(t,key)
    if v <= 0:
        return
    animated_icon(image,name,x,y,116,v,-1 if x<CX else 1)
    if v > .5:
        titulo(draw,text,x,y+68,41,color,395)


def game_scene(image,draw,t):
    b2 = t >= ACOES["lance_b2"]
    b3 = t >= ACOES["lance_b3"]
    width,left,top=714,183,391
    panel(draw,(left-9,top-9,left+width+9,top+width+9),"#1a5b49","#6da48b")
    image.paste(capture("depois" if b3 else "antes",width),(left,top))
    game_badge(image,draw,t,"modo_solo","solo","MODO SOLO",263,232,"#bac8ff")
    game_badge(image,draw,t,"sem_conta","conta","SEM CONTA",817,232,"#f2b5d6")
    game_badge(image,draw,t,"lance_b2","lance","B2 - MINHA JOGADA",263,1230,"#ffdc9f")
    game_badge(image,draw,t,"lance_b3","computador","B3 - COMPUTADOR",817,1230,"#a7e7d7")
    if b2:
        act="lance_b3" if b3 else "lance_b2"
        v=progress(t,act,.22)
        x=left+width*((314-174)/532)
        yy=296 if b3 else 211
        y=top+width*((yy-72)/530)
        r=58-12*v
        draw.ellipse((x-r,y-r,x+r,y+r),outline="#7ee5a7" if b3 else "#ffcc72",width=8)


def checklist(image,draw,t):
    avatar().draw(image,t,CX,360,361,.58,3)
    rows=(("objetivo","alvo","OBJETIVO","#40324f", "#ffd1a6"),
          ("ferramentas","ferramentas","FERRAMENTAS","#263955","#abeaff"),
          ("confere","lista","CONFERÊNCIA","#253d45","#baf5d8"))
    for i,(phase,name,word,fill,edge) in enumerate(rows):
        v=progress(t,phase,.32)
        top=594+i*212
        dx=round(61*(1-v)) if t>=ENTRADAS[phase] else 0
        panel(draw,(98+dx,top,982+dx,top+172),fill if v>.1 else "#232641",edge if v>.1 else "#545a80")
        place(image,icon(name),(218+dx,top+86),133,.52+.48*v)
        titulo(draw,word,531+dx,top+48,70,CREME if v>.1 else "#a8acc5",479)
        x=870+dx
        draw.rounded_rectangle((x-47,top+39,x+47,top+133),19,
                               fill=GREEN if v>.23 else "#26314e",
                               outline="#91f7a1" if v>.23 else "#6d7a9b",width=5)
        if v>.25:
            draw.line((x-23,top+88,x-7,top+105),fill="#eaffdd",width=11)
            step=ease((v-.25)/.58)
            draw.line((x-7,top+105,round(x-7+35*step),round(top+105-43*step)),fill="#eaffdd",width=11)


def change_search(image,draw,t,phase):
    if phase == "alternativa":
        narrator(image,draw,phase,t)
        return
    a=progress(t,"cadastro")
    animated_icon(image,"cadeado",290,723,310,a,-1)
    if a>.5:
        titulo(draw,"CADASTRO",290,948,47,"#ffd1ac",390)
    if phase == "outra_busca":
        b=progress(t,"outra_busca",.43)
        x=442+153*b
        draw.line((441,720,x,720),fill="#a1bfeb",width=12)
        if b>.53:
            draw.line((x-26,697,x,720,x-26,743),fill="#cbeafa",width=10)
        animated_icon(image,"lupa",791,720,293,b,1)
        if b>.5:
            titulo(draw,"NOVA BUSCA",791,948,47,"#aee2fa",420)


def access(image,draw,t):
    v=progress(t,"acesso",.41)
    avatar().draw(image,t,CX-129*v,695,625,1.08,2)
    animated_icon(image,"cadeado",809,853,271,v,1)


def examples(image,draw,t):
    for i,(phase,name,text,color) in enumerate((
        ("precos","preco","PREÇOS","#ffb4d8"),
        ("viagem","mapa","VIAGEM","#c1f6a6"),
        ("arquivos","pastas","ARQUIVOS","#ffe0a4"),
    )):
        v=progress(t,phase,.32)
        if not v:
            continue
        x=(205,540,875)[i]
        animated_icon(image,name,x,750,278,v,(-1,0,1)[i])
        if v>.54:
            titulo(draw,text,x,966,52,color,285)


def caption(draw,text,y=1484,color=None,cap=108):
    lines=text.upper().replace("“",'"').replace("”",'"').split("|")
    font=ABERTURA["font"]
    maxw=max(font("title",cap).getlength(line) for line in lines)
    size=min(cap,math.floor(cap*936/maxw))
    heights=[font("title",size).getbbox(line,anchor="lt")[3] for line in lines]
    gap=round(size*.31)
    y-=(sum(heights)+gap*(len(lines)-1))/2
    for i,(line,h) in enumerate(zip(lines,heights)):
        cor=color or (AMBAR if i==len(lines)-1 else CREME)
        ABERTURA["text"](draw,line,(CX,y),size,cor,anchor="mt")
        y+=h+gap


def quadro(t):
    _,phase,text=next(b for b in reversed(BLOCOS) if b[0]<=t)
    if phase == "pergunta":
        image=Image.new("RGB",(W,H),"black")
        caption(ImageDraw.Draw(image),text,H/2,"#fff8e9",126)
        return image
    image=ABERTURA["BACK"].copy()
    draw=ImageDraw.Draw(image)
    ABERTURA["sky"](draw,t)
    if phase in ("solo","b2","b3"):
        game_scene(image,draw,t)
    elif phase in ("pedido","criterio1","criterio2"):
        request_scene(image,draw,t)
    elif phase in ("busca","resultado"):
        search_scene(image,draw,t)
    elif phase in ("explica","objetivo","ferramentas","confere"):
        checklist(image,draw,t)
    elif phase in ("alternativa","cadastro","outra_busca"):
        change_search(image,draw,t,phase)
    elif phase in ("pausa","acesso"):
        access(image,draw,t)
    elif phase in ("precos","viagem","arquivos"):
        examples(image,draw,t)
    else:
        narrator(image,draw,phase,t)
    caption(draw,text)
    return image


def galeria(destino):
    pontos=[.52,1.14,2.85,5.2,ACOES["jogo"]+.26,ACOES["tabuleiro"]+.30,
            ACOES["navegador"]+.44,ACOES["reversi"]+.43,23.93,31.54,39.1,44.1,54.0,61.7,66.22]
    im=Image.new("RGB",(1350,1440),ABERTURA["NIGHT"])
    for i,t in enumerate(pontos):
        im.paste(quadro(t).resize((270,480),Image.Resampling.LANCZOS),((i%5)*270,(i//5)*480))
    im.save(destino,quality=92)


def exportar(destino):
    command=["ffmpeg","-y","-v","error","-f","rawvideo","-pix_fmt","rgb24","-s",f"{W}x{H}",
             "-r",str(FPS),"-i","-","-i",str(EPISODIO/"narracao.flac"),"-c:v","libx264",
             "-preset","veryfast","-crf","20","-pix_fmt","yuv420p","-threads","6",
             "-c:a","aac","-ar","48000","-b:a","128k","-movflags","+faststart",
             "-color_primaries","bt709","-color_trc","bt709","-colorspace","bt709",
             "-metadata","title=Lume responde - O que é um agente de IA?",
             "-metadata","artist=Lume",str(destino)]
    with subprocess.Popen(command,stdin=subprocess.PIPE) as encoder:
        for i in range(round(DURACAO*FPS)):
            encoder.stdin.write(quadro(i/FPS).tobytes())
        encoder.stdin.close()
        if encoder.wait():
            raise SystemExit("FFmpeg falhou ao exportar o episódio.")


if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--quadros",action="store_true")
    parser.add_argument("--saida",type=Path)
    args=parser.parse_args()
    if args.quadros:
        galeria(args.saida or EPISODIO/"quadros.jpg")
    else:
        exportar(args.saida or EPISODIO/"Lume-Responde-01.mp4")

