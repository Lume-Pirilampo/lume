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
from arte import Avatar, board_art, crt_art, ease, icon, place

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


def animated_icon(image, name, x, y, width, v, direction=1, angle=0, opacity=1):
    if v <= 0 or opacity <= 0:
        return
    x += direction*118*(1-v)
    y += 39*(1-v)
    art = icon(name)
    if abs(angle) > .15:
        # Rotate on the square canvas so the visual centre stays in place.
        art = art.rotate(angle, Image.Resampling.BICUBIC)
    place(image,art,(x,y),max(1,width*(.58+.42*v)),v*opacity)


def feature_icon(image, name, age, target, large, compact, center_y, hold=.28):
    if age < 0:
        return 0
    show = ease(age/.13)
    settle = ease((age-hold)/.30)
    x, y = target
    start = (CX, center_y+26*(1-show))
    center = (start[0]+(x-start[0])*settle, start[1]+(y-start[1])*settle)
    width = large*(.76+.24*show)*(1-settle)+compact*settle
    place(image,icon(name),center,max(1,width),show)
    return settle


def narrator(image, draw, phase, t):
    start = progress(t,"intro",.57)
    if phase == "intro":
        avatar().draw(image,t,CX-570*(1-start),735+209*(1-start),720,1.10,-16*(1-start))
    elif phase in ("cta","cta_convite","despedida"):
        outro(image, t, phase)
    else:
        avatar().draw(image,t,CX,704,690,1.0)


def criteria(image, draw, t):
    for index,(phase,name,text,large) in enumerate((
        ("criterio1","sem_cadastro","SEM CADASTRO",560),
        ("criterio2","duelo","CONTRA O COMPUTADOR",690),
    )):
        age = t-ENTRADAS[phase]
        if age < 0:
            continue
        x = (315,765)[index]
        color,edge = (("#373245","#ffacb6"),("#273e43","#a9efc5"))[index]
        if age > .72:
            panel(draw,(x-202,1122,x+202,1350),color,edge)
        settle = feature_icon(image,name,age,(x,1215),large,200,800,hold=.54)
        if settle > .84:
            titulo(draw,text,x,1306,37,color=edge,limit=366)


def request_scene(image, draw, t):
    if t < ACOES["tabuleiro"]:
        narrator(image,draw,"pedido",t)
        return
    board = progress(t,"tabuleiro",.36)
    crt = progress(t,"navegador",.42)
    if crt > 0:
        place(image,crt_art(),(CX,784),max(1,943*crt))
    x = 1425-885*board-39*crt
    y = 765-80*crt
    place(image,board_art(),(x,y),800-267*crt)
    if crt > .8:
        r = ease((crt-.8)/.2)
        draw.line((209,418,235,418+round(44*r)),fill="#9ececa",width=3)
    criteria(image,draw,t)


@lru_cache(maxsize=3)
def capture(state, width):
    with Image.open(EPISODIO/"assets"/f"reversi-{state}.jpg") as file:
        return file.convert("RGB").resize((width,width),Image.Resampling.LANCZOS)


BOARD_WIDTH = 714
BOARD_LEFT = 183
BOARD_TOP = 391


def board_panel(image, draw, board):
    l, t, w = BOARD_LEFT, BOARD_TOP, BOARD_WIDTH
    panel(draw,(l-9,t-9,l+w+9,t+w+9),"#1a5b49","#6da48b")
    image.paste(board,(l,t))


def search_scene(image, t):
    v = progress(t,"busca",.59)
    avatar().draw(image,t,455,720,487,.54,-8)
    animated_icon(image,"lupa",252+470*v,657,253,min(1,2*v),0)


def result_scene(image, draw, t):
    board_panel(image,draw,capture("antes",BOARD_WIDTH))
    name = progress(t,"reversi",.33)
    number = progress(t,"reversi_dimensao",.28)
    x = CX - 760*(1-name) - 115*number
    titulo(draw,"REVERSI",x,1404,121,"#99f0c1",617)
    if t >= ACOES["reversi_dimensao"]:
        label(draw,"6×6",839+343*(1-number),1431,69,"#d1ffe0")


def game_badge(image, draw, t, key, name, text, x, y, color):
    age = t-ACOES[key]
    settled = feature_icon(image,name,age,(x,y),417,174,587)
    if settled > .82:
        titulo(draw,text,x,y+91,44,color,430)


def square(col, row):
    return (round(BOARD_WIDTH*(140+(ord(col)-ord("b"))*84.3)/532),
            round(BOARD_WIDTH*(139+(row-2)*84.1)/530))


@lru_cache(maxsize=3)
def piece(state, col, row):
    x, y = square(col,row)
    radius = 49
    sprite = capture(state,BOARD_WIDTH).crop((x-radius,y-radius,x+radius,y+radius)).convert("RGBA")
    matte = Image.new("L",sprite.size)
    ImageDraw.Draw(matte).ellipse((1,1,2*radius-2,2*radius-2),fill=255)
    sprite.putalpha(matte)
    return sprite


def clear_circle(board, x, y, radius):
    # Sample an open corner of the same square to retain its colour.
    shade = board.getpixel((x+radius,y+radius))
    ImageDraw.Draw(board).ellipse((x-radius,y-radius,x+radius,y+radius),fill=shade)


def stamp(board, sprite, center, scale=1, horizontal=1):
    if scale <= 0:
        return
    w = max(1,round(sprite.width*scale*horizontal))
    h = max(1,round(sprite.height*scale))
    place(board,sprite.resize((w,h),Image.Resampling.LANCZOS),center)


def played_board(human, cpu):
    before = capture("antes",BOARD_WIDTH)
    if human < 0:
        return before
    if cpu >= .37:
        return capture("depois",BOARD_WIDTH)
    board = before.copy()
    # The intermediate move follows the recorded B2/C3/B3 sequence.
    for col,row in (("b",2),("d",2),("b",4)):
        clear_circle(board,*square(col,row),16)
    clear_circle(board,*square("c",2),10)
    human_disk = piece("depois","b",2)
    computer_disk = piece("depois","b",3)
    dark_disk = piece("antes","c",3)
    stamp(board,human_disk,square("b",2),ease(human/.17))
    cx,cy = square("c",3)
    clear_circle(board,cx,cy,50)
    flip = ease(cpu/.26) if cpu >= 0 else ease(human/.24)
    flipped = human_disk if (flip < .5)==(cpu >= 0) else dark_disk
    stamp(board,flipped,(cx,cy),horizontal=max(.065,abs(math.cos(math.pi*flip))))
    if cpu >= 0:
        stamp(board,computer_disk,square("b",3),ease(cpu/.20))
    return board


def mouse_click(image,t,phase):
    human = t-ACOES["lance_b2"]
    if phase != "b2" or human >= .49:
        return
    x,y = square("b",2)
    x += BOARD_LEFT
    y += BOARD_TOP
    v = ease((human+.41)/.41)
    dx = 73*(1-v)
    dy = 119*(1-v)
    mx,my=x+dx,y+dy
    draw=ImageDraw.Draw(image,"RGBA")
    pointer=[(mx,my),(mx+13,my+65),(mx+24,my+48),(mx+39,my+71),
             (mx+51,my+64),(mx+34,my+41),(mx+57,my+36)]
    if 0 <= human < .31:
        u=human/.31
        r=16+55*u
        draw.ellipse((x-r,y-r,x+r,y+r),outline=(255,218,145,round(215*(1-u))),width=8)
    draw.polygon(pointer,fill="#fffaee",outline="#25304d",width=5)


def computer_response(image,t):
    age=t-ACOES["lance_b3"]
    if age < 0:
        return
    x,y=square("b",3)
    x+=BOARD_LEFT
    y+=BOARD_TOP
    pulse=ease(age/.34)
    fade=1-.65*ease((age-.32)/.57)
    draw=ImageDraw.Draw(image,"RGBA")
    r=46+19*pulse
    draw.ellipse((x-r-7,y-r-7,x+r+7,y+r+7),outline=(119,249,219,round(60*fade)),width=14)
    draw.ellipse((x-r,y-r,x+r,y+r),outline=(144,255,223,round(245*fade)),width=7)
    animated_icon(image,"computador",BOARD_LEFT+BOARD_WIDTH-95,BOARD_TOP+91,163,ease(age/.24),0)


def game_scene(image, draw, t, phase):
    human=t-ACOES["lance_b2"]
    cpu=t-ACOES["lance_b3"]
    board_panel(image,draw,played_board(human,cpu))
    game_badge(image,draw,t,"modo_solo","solo","MODO SOLO",263,206,"#bac8ff")
    game_badge(image,draw,t,"sem_conta","sem_cadastro","SEM CONTA",817,206,"#f2b5d6")
    mouse_click(image,t,phase)
    computer_response(image,t)


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


def access(image, draw, t):
    v = progress(t,"acesso",.41)
    avatar().draw(image,t,CX-129*v,695,625,1.08,2)
    age = t-ACOES["acesso_bloqueado"]
    if age < 0:
        animated_icon(image,"cadeado",809,853,271,v,1)
        return
    release = max(0, 1-age/.62)
    shake = 27*release*math.sin(age*math.tau*9)
    bounce = 67*release*abs(math.sin(age*math.tau*1.8))
    turn = 8*release*math.sin(age*math.tau*7)
    name = "cadeado_bloqueado" if age >= .09 else "cadeado"
    animated_icon(image,name,809+shake,853-bounce,271+18*release,1,0,turn)
    if .07 < age < .38:
        color = "#f67d9a" if age < .25 else "#a65b82"
        draw.line((671,759,651,723),fill=color,width=9)
        draw.line((943,753,971,724),fill=color,width=9)


def examples(image, draw, t):
    for i,(phase,name,text,color) in enumerate((
        ("precos","preco","PREÇOS","#ffb4d8"),
        ("viagem","mapa","VIAGEM","#c1f6a6"),
        ("arquivos","pastas","ARQUIVOS","#ffe0a4"),
    )):
        age = t-ENTRADAS[phase]
        if age <= 0:
            continue
        v = ease(age/.32)
        x = (205,540,875)[i]
        sign = (-1,1,-1)[i]
        landed = max(0,age-.32)
        angle = sign*(16*(1-v)+3*v - 6*math.exp(-landed*4)*math.sin(landed*12))
        animated_icon(image,name,x,750,278,v,(-1,0,1)[i],angle)
        if v>.54:
            titulo(draw,text,x,966,52,color,285)


def outro(image, t, phase):
    shift = progress(t,"pergunta_final",.43)
    despedida = phase == "despedida"
    lift = progress(t,"despedida",.48) if despedida else 0
    fade = ease((t-(DURACAO-.34))/.33) if despedida else 0
    avatar().draw(image,t,CX-145*shift,749-70*lift,739-57*shift,1.12,4*lift,1-.94*fade)
    for key,name,x,y,size,direction in (
        ("pergunta_final","pergunta",848,526,208,1),
        ("comentario_final","comentario",890,780,209,1),
        ("proximo_video","proximo",825,1045,219,1),
    ):
        v = progress(t,key,.32)
        angle = (1 if key=="comentario_final" else -1)*8*(1-v)
        opacity = 1-lift if key!="proximo_video" else 1-.6*lift
        animated_icon(image,name,x,y, size,v,direction,angle,opacity)
    if despedida:
        animated_icon(image,"despedida",842,700-153*lift,272,lift,1,-9*(1-lift),1-.58*fade)


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
        draw = ImageDraw.Draw(image)
        titulo(draw,"LUMI RESPONDE",CX,682,64,"#afa6ee",790)
        caption(draw,text,H/2,"#fff8e9",126)
        return image
    image=ABERTURA["BACK"].copy()
    draw=ImageDraw.Draw(image)
    ABERTURA["sky"](draw,t)
    if phase in ("solo","b2","b3"):
        game_scene(image,draw,t,phase)
    elif phase in ("pedido","criterio1","criterio2"):
        request_scene(image,draw,t)
    elif phase == "busca":
        search_scene(image,t)
    elif phase == "resultado":
        result_scene(image,draw,t)
        return image
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
    pontos=[.61,ENTRADAS["pergunta"]+.18,ACOES["tabuleiro"]+.33,ACOES["navegador"]+.43,
            ENTRADAS["criterio1"]+.46,ENTRADAS["criterio2"]+.44,ACOES["reversi"]+.27,
            ACOES["reversi_dimensao"]+.35,ACOES["lance_b2"]-.13,ACOES["lance_b2"]+.22,
            ACOES["lance_b3"]+.19,ACOES["lance_b3"]+.49,ENTRADAS["confere"]+.6,
            ACOES["acesso_bloqueado"]+.36,ENTRADAS["despedida"]+.50]
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

