import argparse
from functools import lru_cache
import json
import math
import os
from pathlib import Path
import runpy
import subprocess

from PIL import Image, ImageDraw, ImageFont

EPISODIO = Path(__file__).resolve().parent
CANAL = EPISODIO.parents[2]
ABERTURA = runpy.run_path(str(CANAL / "apresentacao" / "montar.py"))
W, H, FPS = (ABERTURA[item] for item in ("W", "H", "FPS"))
AMBAR, CREME, VIOLETA, ASA, SUAVE = (
    ABERTURA[item] for item in ("AMBER", "CREAM", "VIOLET", "WING", "MUTED")
)
CX = 520

composicao = json.loads((EPISODIO / "cenas.json").read_text(encoding="utf-8"))
DURACAO = composicao["duracao"]
BLOCOS = composicao["blocos"]
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


@lru_cache(maxsize=12)
def mono(tamanho):
    return ImageFont.truetype("DejaVuSansMono.ttf", tamanho)


def etiqueta(draw, texto, x, y, tamanho=34, cor=SUAVE):
    draw.text((x, y), texto, font=mono(tamanho), fill=cor, anchor="mt")


def placa(draw, caixa, cor=VIOLETA, contorno=ASA):
    draw.rounded_rectangle(caixa, radius=24, fill=cor, outline=contorno, width=3)


@lru_cache(maxsize=2)
def tabuleiro(estado):
    with Image.open(EPISODIO / "assets" / f"reversi-{estado}.jpg") as imagem:
        return imagem.resize((788, 785), Image.Resampling.LANCZOS)


@lru_cache(maxsize=5)
def simbolo(nome):
    with Image.open(EPISODIO / "assets" / f"{nome}.png") as imagem:
        return imagem.convert("RGBA")


def progresso(t, fase, duracao=.28):
    return ABERTURA["ease"]((t - ENTRADAS[fase]) / duracao)


def icone(imagem, nome, x, y, v):
    if v <= 0:
        return
    layer = simbolo(nome)
    left = round(x - layer.width / 2)
    top = round(y - layer.height / 2 + 32 * (1 - v))
    if v >= 1:
        imagem.paste(layer, (left, top), layer)
        return
    alpha = layer.getchannel("A").point(lambda value: round(value * v))
    imagem.paste(layer, (left, top), alpha)


def cena_jogo(imagem, draw, fase, t):
    estado = "depois" if fase == "b3" else "antes"
    draw.rounded_rectangle((116, 332, 924, 1199), radius=14, fill=(17, 65, 46))
    etiqueta(draw, "Reversi 6×6  /  Modo solo", CX, 355, 33, CREME)
    imagem.paste(tabuleiro(estado), (126, 403))
    if fase == "solo":
        etiqueta(draw, "Sessão sem cadastro", CX, 1232, 36, AMBAR)
        return
    x = 126 + 788 * ((314 - 174) / 532)
    row = 296 if fase == "b3" else 211
    y = 403 + 785 * ((row - 72) / 530)
    v = progresso(t, fase)
    r = 79 - 20 * v
    draw.ellipse((x - r, y - r, x + r, y + r),
                 outline=ABERTURA["tint"](ASA, AMBAR, v), width=7)
    etiqueta(draw, "B3 · resposta do computador" if fase == "b3" else "B2 · minha jogada",
             CX, 1232, 36, AMBAR)


def cena_etapas(imagem, draw, t):
    ABERTURA["portrait"](imagem, CX, 610, 420)
    y = 986
    draw.line((235, y, 805, y), fill=ASA, width=4)
    for x, nome, fase in zip((235, CX, 805), ("Objetivo", "Ferramentas", "Conferência"),
                            ("objetivo", "ferramentas", "confere")):
        v = progresso(t, fase)
        cor = ABERTURA["tint"](ASA, AMBAR, v)
        draw.ellipse((x - 30, y - 30, x + 30, y + 30), fill=VIOLETA, outline=cor, width=5)
        if v > .3:
            draw.line((x - 12, y, x - 3, y + 9, x + 14, y - 10), fill=cor, width=5)
        etiqueta(draw, nome, x, y + 66, 31, ABERTURA["tint"](SUAVE, CREME, v))


def cena_pedido(imagem, draw, t):
    ABERTURA["asset"](imagem, "controle", (CX, 626 + 24 * (1 - progresso(t, "pedido", .36))), 470)
    etiqueta(draw, "Jogo de tabuleiro no navegador", CX, 863, 34, CREME)
    for i, (texto, fase) in enumerate((("Sem cadastro", "criterio1"), ("Contra o computador", "criterio2"))):
        if t < ENTRADAS[fase]:
            continue
        v = progresso(t, fase)
        y = round(943 + i * 100 + 25 * (1 - v))
        placa(draw, (220, y, 820, y + 78), contorno=ABERTURA["tint"](ASA, AMBAR, v))
        etiqueta(draw, texto, CX, y + 19, 34, CREME)


def cena_busca(imagem, draw, t):
    v = progresso(t, "busca", .56)
    icone(imagem, "lupa", 383 + 137 * v, 620, min(1, 1.8 * v))
    if t >= ENTRADAS["resultado"]:
        y = round(821 + 30 * (1 - progresso(t, "resultado")))
        placa(draw, (158, y, 882, y + 210))
        etiqueta(draw, "tryboardgames.com", CX, y + 43, 34)
        etiqueta(draw, "Reversi 6×6", CX, y + 108, 56, CREME)


def cena_alternativa(imagem, draw, fase, t):
    if fase == "alternativa":
        ABERTURA["portrait"](imagem, CX, 655, 490)
        return
    v = progresso(t, "cadastro")
    icone(imagem, "cadeado", 302, 754, v)
    if v > .6:
        etiqueta(draw, "Cadastro", 302, 900, 39, CREME)
    if fase == "outra_busca":
        v = progresso(t, "outra_busca", .40)
        x = round(415 + 204 * v)
        draw.line((415, 754, x, 754), fill=ASA, width=8)
        if v > .84:
            draw.line((x - 29, 734, x, 754, x - 29, 774), fill=AMBAR, width=8)
        icone(imagem, "lupa", 743, 754, v)
        if v > .6:
            etiqueta(draw, "Nova busca", 743, 900, 39, CREME)


def cena_acesso(imagem, t):
    ABERTURA["portrait"](imagem, CX, 604, 450)
    icone(imagem, "cadeado", CX, 982, progresso(t, "acesso"))


def cena_exemplos(imagem, draw, t):
    for x, nome, rotulo, fase in (
        (240, "preco", "Preços", "precos"),
        (520, "mapa", "Viagem", "viagem"),
        (800, "pastas", "Arquivos", "arquivos"),
    ):
        v = progresso(t, fase)
        icone(imagem, nome, x, 745, v)
        if v > .58:
            etiqueta(draw, rotulo, x, 908, 37, CREME)


def balão(draw, y):
    draw.rounded_rectangle((370, y, 670, y + 142), radius=29, fill=VIOLETA, outline=ASA, width=6)
    draw.polygon(((482, y + 139), (514, y + 178), (542, y + 139)), fill=VIOLETA)
    etiqueta(draw, "?", CX, y + 22, 82, AMBAR)


def cena_avatar(imagem, draw, fase, t):
    v = progresso(t, "intro", .44)
    y = 711 - 66 * (1 - v) + 9 * math.sin(t * 2.15)
    ABERTURA["portrait"](imagem, CX, y, 600)
    if fase in ("serie", "pergunta"):
        balão(draw, round(965 + 24 * (1 - progresso(t, "serie"))))
    if fase == "despedida":
        v = ABERTURA["ease"]((t - max(ENTRADAS[fase], DURACAO - .59)) / .58)
        if v > 0:
            imagem.paste(ABERTURA["BACK"], (0, 0), Image.new("L", (W, H), round(229 * v)))


def legenda(draw, texto):
    linhas = texto.upper().replace("“", '"').replace("”", '"').split("|")
    face = ABERTURA["font"]
    tamanho = 90
    largura = max(face("title", tamanho).getlength(linha) for linha in linhas)
    tamanho = min(tamanho, math.floor(tamanho * 820 / largura))
    alturas = [face("title", tamanho).getbbox(linha, anchor="lt")[3] for linha in linhas]
    espaco = round(tamanho * .27)
    y = 1445 - (sum(alturas) + (len(linhas) - 1) * espaco) / 2
    for i, linha in enumerate(linhas):
        ABERTURA["text"](draw, linha, (CX, y), tamanho, AMBAR if i == len(linhas) - 1 else CREME, anchor="mt")
        y += alturas[i] + espaco


def quadro(t):
    _, fase, texto = next(bloco for bloco in reversed(BLOCOS) if bloco[0] <= t)
    imagem = ABERTURA["BACK"].copy()
    draw = ImageDraw.Draw(imagem)
    ABERTURA["sky"](draw, t)
    if fase in ("solo", "b2", "b3"):
        cena_jogo(imagem, draw, fase, t)
    elif fase in ("pedido", "criterio1", "criterio2"):
        cena_pedido(imagem, draw, t)
    elif fase in ("busca", "resultado"):
        cena_busca(imagem, draw, t)
    elif fase in ("explica", "objetivo", "ferramentas", "confere"):
        cena_etapas(imagem, draw, t)
    elif fase in ("alternativa", "cadastro", "outra_busca"):
        cena_alternativa(imagem, draw, fase, t)
    elif fase in ("pausa", "acesso"):
        cena_acesso(imagem, t)
    elif fase in ("precos", "viagem", "arquivos"):
        cena_exemplos(imagem, draw, t)
    else:
        cena_avatar(imagem, draw, fase, t)
    legenda(draw, texto)
    return imagem


def galeria(destino):
    fases = ("intro", "pergunta", "criterio2", "resultado", "solo", "b2", "b3", "confere",
             "outra_busca", "acesso", "arquivos", "cta_convite", "despedida")
    imagem = Image.new("RGB", (1350, 1440), ABERTURA["NIGHT"])
    for i, fase in enumerate(fases):
        t = ENTRADAS[fase] + .51
        pequeno = quadro(t).resize((270, 480), Image.Resampling.LANCZOS)
        imagem.paste(pequeno, ((i % 5) * 270, (i // 5) * 480))
    imagem.save(destino, quality=92)


def exportar(destino):
    comando = [
        "ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
        "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-i", str(EPISODIO / "narracao.flac"),
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "22", "-pix_fmt", "yuv420p",
        "-threads", "6", "-c:a", "aac", "-ar", "48000", "-b:a", "112k",
        "-movflags", "+faststart", "-color_primaries", "bt709", "-color_trc", "bt709",
        "-colorspace", "bt709", "-metadata", "title=Lume responde - O que é um agente de IA?",
        "-metadata", "artist=Lume", str(destino),
    ]
    with subprocess.Popen(comando, stdin=subprocess.PIPE) as encoder:
        for index in range(round(DURACAO * FPS)):
            encoder.stdin.write(quadro(index / FPS).tobytes())
        encoder.stdin.close()
        if encoder.wait():
            raise SystemExit("FFmpeg falhou ao exportar o episódio.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--quadros", action="store_true")
    parser.add_argument("--saida", type=Path)
    args = parser.parse_args()
    if args.quadros:
        galeria(args.saida or EPISODIO / "quadros.jpg")
    else:
        exportar(args.saida or EPISODIO / "Lume-Responde-01.mp4")

