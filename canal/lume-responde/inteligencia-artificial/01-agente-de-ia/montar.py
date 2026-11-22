import argparse
from functools import lru_cache
import json
import math
from pathlib import Path
import runpy
import subprocess
import sys
import tempfile

from PIL import Image, ImageColor, ImageDraw, ImageFont

EPISODIO = Path(__file__).resolve().parent
sys.path.insert(0, str(EPISODIO))
from arte import Avatar, board_art, crt_art, ease, icon, place, signature_frame, signature_pulse_duration

CANAL = EPISODIO.parents[2]
ABERTURA = runpy.run_path(str(CANAL / "apresentacao" / "montar.py"))
W, H, FPS = (ABERTURA[item] for item in ("W", "H", "FPS"))
AMBAR, CREME, SUAVE = (ABERTURA[item] for item in ("AMBER", "CREAM", "MUTED"))
CX = 540

composicao = json.loads((EPISODIO / "cenas.json").read_text(encoding="utf-8"))
FIM_DA_VOZ = composicao["fim_da_voz"]
POUSO = math.ceil((FIM_DA_VOZ + .48) * FPS) / FPS
QUADRO_FINAL = math.ceil((POUSO + signature_pulse_duration()) * FPS) / FPS
DURACAO = QUADRO_FINAL + 1
BLOCOS = composicao["blocos"]
ACOES = {}
for event, (block, offset) in composicao["acoes_relativas"].items():
    start = BLOCOS[block][0]
    limit = BLOCOS[block + 1][0] if block + 1 < len(BLOCOS) else FIM_DA_VOZ
    if not 0 <= offset < limit - start:
        raise ValueError(f"Marca fora de seu bloco: {event}")
    ACOES[event] = start + offset
EFEITOS = True
roteiro = (EPISODIO / "roteiro.txt").read_text(encoding="utf-8")
if " ".join(texto.replace("|", " ") for _, _, texto in BLOCOS) != " ".join(roteiro.split()):
    raise ValueError("As legendas divergem do roteiro.")
if BLOCOS[0][0] != 0 or BLOCOS[-1][0] >= FIM_DA_VOZ or any(
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
    return ease((t-start)/duration) if EFEITOS else int(t >= start)


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
    show = ease(age/.13) if EFEITOS else 1
    settle = ease((age-hold)/.30) if EFEITOS else int(age >= hold)
    x, y = target
    start = (CX, center_y+26*(1-show))
    center = (start[0]+(x-start[0])*settle, start[1]+(y-start[1])*settle)
    width = large*(.76+.24*show)*(1-settle)+compact*settle
    place(image,icon(name),center,max(1,width),show)
    return settle


def narrator(image, phase, t):
    start = progress(t, "intro", .68)
    if phase == "intro":
        avatar().draw(image,t,CX-580*(1-start),766+170*(1-start),747,1.04*EFEITOS,-14*(1-start))
    else:
        avatar().draw(image,t,CX,743,690,1.0*EFEITOS)


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
        settle = feature_icon(image,name,age,(x,1215),large,200,800,hold=.63)
        if settle > .84:
            titulo(draw,text,x,1306,37,color=edge,limit=366)


def request_scene(image, draw, t):
    board = progress(t,"tabuleiro",.44)
    if board < 1:
        avatar().draw(image,t,CX-470*board,748-97*board,680-134*board,
                      .83*EFEITOS,-12*board,1-board)
    if t < ACOES["tabuleiro"]:
        return
    crt = progress(t,"navegador",.42)
    if crt > 0:
        place(image,crt_art(),(CX,784),max(1,943*(.90+.10*crt)),crt)
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
    age = t - ENTRADAS["busca"]
    v = progress(t, "busca", .50)
    leave = progress(t, "revelacao", .42)
    avatar().draw(image, t, 454, 739, 620 - 140 * leave, .63 * EFEITOS,
                  -7, (1 - leave))
    animated_icon(image, "lupa", 793 - 59 * math.sin(age * 2) * EFEITOS,
                  790 + 20 * math.sin(age * 3) * EFEITOS, 272, v, 1,
                  opacity=1 - leave)


def result_scene(image, draw, t):
    reveal = progress(t, "revelacao", .32)
    if reveal < 1:
        search_scene(image, t)
        left = BOARD_LEFT + round(328 * (1 - reveal))
        panel(draw, (left - 9, BOARD_TOP - 9, left + BOARD_WIDTH + 9,
                     BOARD_TOP + BOARD_WIDTH + 9), "#1a5b49", "#6da48b")
        image.paste(capture("antes", BOARD_WIDTH), (left, BOARD_TOP))
    else:
        board_panel(image, draw, capture("antes", BOARD_WIDTH))
    name = progress(t, "reversi", .29)
    number = progress(t, "reversi_dimensao", .22)
    if t >= ACOES["reversi"]:
        x = CX - 730 * (1 - name) - 119 * number
        titulo(draw, "Reversi", x, 1425, 118, "#a4eac1", 590)
    if t >= ACOES["reversi_dimensao"]:
        label(draw, "6×6", 807 + 354 * (1 - number), 1445, 77, CREME)


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
    if phase != "b2" or human >= .49 or not EFEITOS:
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
    pulse=ease(age/.34) if EFEITOS else 0
    fade=1-.65*ease((age-.32)/.57)
    draw=ImageDraw.Draw(image,"RGBA")
    r=46+19*pulse
    draw.ellipse((x-r-7,y-r-7,x+r+7,y+r+7),outline=(119,249,219,round(60*fade)),width=14)
    draw.ellipse((x-r,y-r,x+r,y+r),outline=(144,255,223,round(245*fade)),width=7)
    animated_icon(image,"computador",BOARD_LEFT+BOARD_WIDTH-95,BOARD_TOP+91,163,ease(age/.24),0)


def game_scene(image, draw, t, phase):
    human = t - ACOES["lance_b2"]
    cpu = t - ACOES["lance_b3"]
    if not EFEITOS:
        human = 1 if human >= 0 else -1
        cpu = 1 if cpu >= 0 else -1
    board_panel(image, draw, played_board(human, cpu))
    age = t - ACOES["modo_solo"]
    if age >= 0:
        # The board keeps its exact position all the way through both moves.
        game_badge(image, draw, t, "modo_solo", "solo", "MODO SOLO", 263, 218, "#bac8ff")
        game_badge(image, draw, t, "sem_conta", "sem_cadastro", "SEM CONTA", 817, 218, "#f2b5d6")
    mouse_click(image, t, phase)
    computer_response(image, t)
    if EFEITOS and phase in ("b2", "b3"):
        turn = progress(t, "lance_b3", .22)
        pictogram_hud(image, (("lume", 1 - turn), ("computador", turn)), 1238,
                     spacing=102, slot=85)


def checklist(image, draw, t):
    avatar().draw(image, t, CX, 810, 724, .76 * EFEITOS)
    rows = (
        ("objetivo", "alvo", "#ffd49e"),
        ("ferramentas", "ferramentas", "#aadaf5"),
        ("confere", "lista", "#a6e8c7"),
    )
    if EFEITOS:
        pictogram_hud(image, tuple((key, progress(t, f"{phase}_visual", .22))
                      for phase, key, _ in rows), 212, spacing=128, slot=110)
    for i, (phase, name, color) in enumerate(rows):
        v = progress(t, f"{phase}_visual", .24)
        if v <= 0:
            continue
        x = (281, 540, 799)[i]
        scale = 148 + 20 * math.sin(math.pi * v) * EFEITOS
        place(image, icon(name), (x, 1277), scale, v)
        draw.rounded_rectangle((x - 36, 1365, x + 36, 1372), 3, fill=color)


def change_search(image, draw, t, phase):
    first = progress(t, "cadastro", .48)
    if first < 1:
        avatar().draw(image, t, CX - 46 * first, 753, 685, .82 * EFEITOS,
                      opacity=1 - first)
    if first <= 0:
        return
    start = (249, 1002)
    fork = (474, 854)
    closed = (787, 661)
    alternate = (789, 1037)
    path_line = [start, fork, closed]
    alternate_line = [fork, alternate]
    for points in (path_line, alternate_line):
        for width, color in ((20, "#24203c"), (9, "#635783")):
            draw.line(points, fill=color, width=width, joint="curve")
    age = t - ENTRADAS["outra_busca"]
    if age < 0:
        x, y = lerp_point(fork, closed, first)
    elif age < .42 and EFEITOS:
        x, y = lerp_point(closed, fork, ease(age / .42))
    else:
        x, y = lerp_point(fork, alternate, ease((age - .42) / .42) if EFEITOS else 1)
    animated_icon(image, "sem_cadastro", closed[0], closed[1] - 136, 208, first, 0)
    if age >= 0:
        v = progress(t, "outra_busca", .30)
        animated_icon(image, "lupa", alternate[0], alternate[1] + 120, 223, v, 0)
    draw.ellipse((x - 19, y - 19, x + 19, y + 19), fill="#ffbf76", outline="#ffe9b8", width=4)


def access(image, draw, t):
    v = progress(t, "acesso", .38)
    avatar().draw(image, t, CX - 122 * v, 752, 697 - 46 * v, .77 * EFEITOS, 0)
    if v <= 0:
        return
    age = t - ACOES["acesso_bloqueado"]
    release = max(0, 1 - age / .36) if age >= 0 and EFEITOS else 0
    shake = 12 * release * math.sin(age * math.tau * 6)
    place(image, pictogram("chave", 244), (819 + shake, 832), opacity=v)


def examples(image, draw, t):
    phases = ("precos", "viagem", "arquivos")
    names = ("preco", "mapa", "pastas")
    if EFEITOS:
        pictogram_hud(image, tuple((name, progress(t, f"{phase}_visual", .24))
                      for phase, name in zip(phases, names)), 306, spacing=122, slot=108)
    for i, (phase, name) in enumerate(zip(phases, names)):
        v = progress(t, f"{phase}_visual", .33)
        if v <= 0:
            continue
        x = (223, 540, 857)[i]
        angle = (-1 if i != 1 else 1) * 12 * (1 - v)
        animated_icon(image, name, x, 837, 305, v, i - 1, angle)


def outro(image, draw, t):
    start = progress(t, "pergunta_final", .42)
    farewell = progress(t, "despedida", .35)
    landing = ease((t - ENTRADAS["despedida"]) / (POUSO - ENTRADAS["despedida"]))
    x = CX - 154 * start * (1 - landing)
    y = 748 + 83 * landing - 68 * math.sin(math.pi * landing) * EFEITOS
    width = 720 - 38 * start * (1 - landing) - 82 * landing
    if t >= POUSO:
        avatar().draw(image, t, CX, 831, 638, 0, state=signature_frame(t - POUSO),
                      smile=True, still=True)
    else:
        avatar().draw(image,t,x,y,width,(1 - landing) * EFEITOS,
                      -5 * math.sin(math.pi * landing), smile=t >= FIM_DA_VOZ)
    if farewell < 1:
        opacity = 1 - farewell
        if t >= ACOES["pergunta_final"]:
            bubble(draw, (717, 495, 940, 649), "#7862a4", "#c5adea", opacity=opacity)
            if opacity > .44:
                titulo(draw, "?", 828, 524, 78, "#fef0d9", 160)
        if t >= ACOES["comentario_final"]:
            animated_icon(image, "comentario", 846, 807, 286,
                          progress(t, "comentario_final", .27), 1, opacity=opacity)
    if t >= FIM_DA_VOZ:
        v = ease((t - FIM_DA_VOZ) / (POUSO - FIM_DA_VOZ))
        if v > 0:
            title_color = ABERTURA["tint"]((16, 11, 54), CREME, v)
            titulo(draw, "Lume por Aí", CX, 1248, 130, title_color, 864)


def lerp_point(a, b, t):
    return tuple(j + (k - j) * t for j, k in zip(a, b))


def bubble(draw, box, fill, edge, opacity=1):
    if opacity <= 0:
        return
    x, y, right, bottom = box
    bg = (15, 10, 51)
    fill = ABERTURA["tint"](bg, ImageColor.getrgb(fill), opacity)
    edge = ABERTURA["tint"](bg, ImageColor.getrgb(edge), opacity)
    draw.polygon([(x + 42, bottom - 26), (x + 31, bottom + 28),
                  (x + 114, bottom - 14)], fill=fill, outline=edge, width=5)
    draw.rounded_rectangle(box, 35, fill=fill, outline=edge, width=5)
    draw.polygon([(x + 45, bottom - 7), (x + 36, bottom + 20),
                  (x + 90, bottom - 7)], fill=fill)


@lru_cache(maxsize=32)
def pictogram(name, width):
    art = icon(name) if name not in ("coracao", "envelope", "ficha", "chave", "lume") else None
    if name == "chave":
        art = Image.new("RGBA", (160, 160))
        d = ImageDraw.Draw(art)
        for line, stroke in (("#37243f", 17), ("#edbd77", 9)):
            d.ellipse((19, 48, 79, 108), outline=line, width=stroke)
            d.line((77, 78, 137, 78, 137, 111), fill=line, width=stroke, joint="curve")
            d.line((112, 80, 112, 102), fill=line, width=stroke)
    elif name in ("coracao", "envelope", "ficha", "lume"):
        art = Image.new("RGBA", (160, 160))
        d = ImageDraw.Draw(art)
        if name == "coracao":
            d.polygon([(29,31),(62,31),(80,49),(98,31),(131,31),(145,45),(145,77),
                       (80,137),(15,77),(15,45)], fill="#ebaa67", outline="#f9d08a", width=7)
            d.rectangle((33,49,52,58), fill="#ffedb0")
        elif name == "envelope":
            d.rounded_rectangle((15,38,145,124),10,fill="#8b75ac",outline="#efddf4",width=7)
            d.line((19,45,80,88,141,45),fill="#ffdfac",width=8,joint="curve")
        elif name == "ficha":
            d.ellipse((30,31,130,131),fill="#c39a68",outline="#ffe4b0",width=8)
            d.arc((40,41,120,115),190,295,fill="#fff1cb",width=7)
        elif name == "lume":
            d.ellipse((12,26,76,91),fill="#8798c7")
            d.ellipse((28,53,122,142),fill="#f4b45b",outline="#ffe3a2",width=5)
            d.ellipse((61,20,143,107),fill="#8f62a7",outline="#d7a6d8",width=5)
            d.ellipse((94,50,111,74),fill="#fff4dd")
            d.ellipse((126,45,137,66),fill="#fff4dd")
    return art.resize((width, width), Image.Resampling.LANCZOS)


def pictogram_hud(image, icons, y, spacing=111, slot=90):
    draw = ImageDraw.Draw(image)
    for i, (key, intensity) in enumerate(icons):
        x = CX + spacing * (i - (len(icons) - 1) / 2)
        r = slot // 2
        edge = ABERTURA["tint"]((74, 61, 106), (239, 171, 103), intensity)
        draw.rounded_rectangle((x - r, y - r, x + r, y + r), 16,
                               fill="#201439", outline=edge, width=3)
        if intensity > 0:
            place(image, pictogram(key, int(slot * .83)), (x, y), opacity=intensity)


def margins(draw, t):
    for n, (x, y, stagger) in enumerate(((119, 1129, .84), (951, 436, 5.27))):
        phase = (t - stagger) % 13.5
        if phase < 1.37:
            u = phase / 1.37
        elif 2.21 <= phase < 3.23:
            u = (phase - 2.21) / 1.02
        else:
            continue
        v = math.sin(math.pi * u) ** .8
        if v < .018:
            continue
        xx = x + round(13 * math.sin(t * .96 + n))
        yy = y + round(7 * math.sin(t * 1.09 + n))
        for r, intensity in ((36, .05), (24, .08), (15, .14), (7, .48), (3, .99)):
            draw.ellipse((xx-r,yy-r,xx+r,yy+r),
                         fill=ABERTURA["tint"]((17, 13, 58), (255, 205, 110), v * intensity))


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
    _, phase, text = next(b for b in reversed(BLOCOS) if b[0] <= t)
    if phase == "pergunta":
        image = Image.new("RGB", (W, H), "#080613")
        draw = ImageDraw.Draw(image)
        bubble(draw, (258, 657, 822, 770), "#5d4a80", "#b9a4d9")
        titulo(draw, "Lume Responde", CX, 687, 74, "#fff0d9", 500)
        caption(draw, text, 976, "#fff8e9", 134)
        return image
    image = ABERTURA["BACK"].copy()
    draw = ImageDraw.Draw(image)
    if EFEITOS and t < FIM_DA_VOZ:
        margins(draw, t)
    if phase in ("solo", "b2", "b3", "pronto"):
        game_scene(image, draw, t, phase)
    elif phase in ("pedido", "criterio1", "criterio2"):
        request_scene(image, draw, t)
        if EFEITOS:
            pictogram_hud(image, (("envelope",1),), 267, slot=101)
    elif phase == "busca":
        search_scene(image, t)
        if EFEITOS:
            pictogram_hud(image, (("lupa",1),), 267, slot=101)
    elif phase == "resultado":
        result_scene(image, draw, t)
        if EFEITOS:
            pictogram_hud(image, (("ficha",1),), 267, slot=101)
        if t >= ACOES["reversi"]:
            return image
    elif phase in ("explica", "objetivo", "ferramentas", "confere"):
        checklist(image, draw, t)
    elif phase in ("alternativa", "cadastro", "outra_busca"):
        change_search(image, draw, t, phase)
    elif phase in ("pausa", "acesso"):
        access(image, draw, t)
    elif phase in ("precos", "viagem", "arquivos"):
        examples(image, draw, t)
    elif phase in ("cta", "cta_convite", "despedida"):
        outro(image, draw, t)
    else:
        narrator(image, phase, t)
        if EFEITOS:
            v = progress(t, "intro", .60)
            pictogram_hud(image, tuple(("coracao", ease(v * 2 - i * .33))
                          for i in range(3)), 264, spacing=109, slot=91)
    if t < FIM_DA_VOZ:
        if phase == "cta_convite" and t >= ACOES["lu_me_responde"]:
            caption(draw, text, color=AMBAR)
        else:
            caption(draw, text)
    return image


def galeria(destino):
    pontos=[.61,ENTRADAS["pergunta"]+.18,ACOES["tabuleiro"]+.33,ACOES["navegador"]+.43,
            ENTRADAS["criterio1"]+.46,ENTRADAS["criterio2"]+.44,ACOES["reversi"]+.27,
            ACOES["reversi_dimensao"]+.35,ACOES["lance_b2"]-.13,ACOES["lance_b2"]+.22,
            ACOES["lance_b3"]+.19,ACOES["lance_b3"]+.49,ENTRADAS["confere"]+.6,
            ACOES["acesso_bloqueado"]+.36,ENTRADAS["despedida"]+.26, POUSO+.15, POUSO+signature_pulse_duration()/2, QUADRO_FINAL+.20]
    im=Image.new("RGB",(1350,1920),ABERTURA["NIGHT"])
    for i,t in enumerate(pontos):
        im.paste(quadro(t).resize((270,480),Image.Resampling.LANCZOS),((i%5)*270,(i//5)*480))
    im.save(destino,quality=92)


VIDEO_OPTIONS = [
    "-c:v", "libx264", "-preset", "medium", "-bf", "0", "-pix_fmt", "yuv420p", "-threads", "5",
    "-color_primaries", "bt709", "-color_trc", "bt709", "-colorspace", "bt709",
    "-video_track_timescale", "90000",
]


def render_frames(destino, first, last):
    command = ["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
               "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
               "-an", *VIDEO_OPTIONS, "-crf", "25", str(destino)]
    with subprocess.Popen(command, stdin=subprocess.PIPE) as encoder:
        for i in range(first, last):
            encoder.stdin.write(quadro(i / FPS).tobytes())
        encoder.stdin.close()
        if encoder.wait():
            raise SystemExit("FFmpeg falhou ao exportar o episódio.")


def exportar(destino, inicio=0, fim=None, sem_audio=False):
    first = round(inicio * FPS)
    last = round((DURACAO if fim is None else fim) * FPS)
    still = round(QUADRO_FINAL * FPS)
    if not 0 <= first < last <= round(DURACAO * FPS):
        raise ValueError("Selecione um intervalo válido do episódio.")
    with tempfile.TemporaryDirectory() as working:
        temp = Path(working)
        clips = []
        if first < still:
            count = min(last, still) - first
            render_frames(temp / "montagem.mp4", first, first + count)
            clips.append(("montagem.mp4", count / FPS))
        if last > still:
            count = last - max(first, still)
            quadro(QUADRO_FINAL).save(temp / "assinatura.png")
            # Fixed quantizer and independent frames keep the decoded hold identical.
            subprocess.run([
                "ffmpeg", "-y", "-v", "error", "-loop", "1", "-framerate", str(FPS),
                "-i", str(temp / "assinatura.png"), "-frames:v", str(count),
                "-an", *VIDEO_OPTIONS, "-qp", "23", "-g", "1", str(temp / "assinatura.mp4")
            ], check=True)
            clips.append(("assinatura.mp4", count / FPS))
        lista = temp / "lista.txt"
        lista.write_text("".join(f"file '{name}'\nduration {duration:.9f}\n"
                                 for name, duration in clips), encoding="utf-8")
        command = ["ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0",
                   "-i", str(lista)]
        if not sem_audio:
            command += ["-ss", str(first / FPS), "-i", str(EPISODIO / "narracao.flac"),
                        "-map", "0:v", "-map", "1:a", "-af", "apad",
                        "-c:a", "aac", "-ar", "48000", "-b:a", "144k"]
        command += ["-t", str((last - first) / FPS), "-c:v", "copy",
                    "-movflags", "+faststart",
                    "-metadata", "title=Lume Responde - O que é um agente de IA?",
                    "-metadata", "artist=Lume", str(destino)]
        subprocess.run(command, check=True)


if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--quadros",action="store_true")
    parser.add_argument("--saida",type=Path)
    parser.add_argument("--base", action="store_true", help="Desliga a animação de acabamento")
    parser.add_argument("--inicio", type=float, default=0)
    parser.add_argument("--fim", type=float)
    parser.add_argument("--sem-audio", action="store_true")
    args=parser.parse_args()
    EFEITOS = not args.base
    if args.quadros:
        galeria(args.saida or EPISODIO/"quadros.jpg")
    else:
        exportar(args.saida or EPISODIO/"Lume-Responde-01-v8.mp4", args.inicio, args.fim, args.sem_audio)


