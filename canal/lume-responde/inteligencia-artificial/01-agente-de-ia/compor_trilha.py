"""Gera a trilha instrumental original do episódio em PCM estéreo."""

import argparse
import json
import math
import subprocess
import tempfile
import wave
from pathlib import Path

import numpy as np


PASTA = Path(__file__).resolve().parent
TAXA = 48_000
PULSO = 60 / 92
ACORDES = (
    (50, (57, 61, 64, 66)),  # Ré maior com sétima e nona
    (47, (57, 61, 62, 66)),  # Si menor com sétima e nona
    (43, (55, 57, 59, 66)),  # Sol maior com sétima e nona
    (45, (55, 57, 62, 64)),  # Lá com quarta suspensa
)
SEQUENCIA = (0, 0, 1, 2, 0, 1, 2, 3, 0, 0, 1, 2, 0, 1, 2, 3, 0, 1, 2, 3, 0, 1, 2, 3, 0)


def nota(trilha, inicio, altura, duracao, forca, panorama=0.0, timbre="tecla"):
    primeiro = round(inicio * TAXA)
    pontos = min(len(trilha) - primeiro, round(duracao * TAXA))
    if pontos <= 0:
        return
    tempo = np.arange(pontos) / TAXA
    fase = 2 * math.pi * 440 * 2 ** ((altura - 69) / 12) * tempo
    if timbre == "base":
        sinal = np.sin(fase) + 0.16 * np.sin(fase * 2)
        curva = np.minimum(tempo / .045, 1) * np.exp(-tempo / .72)
    elif timbre == "acorde":
        sinal = np.sin(fase) + .15 * np.sin(fase * 2 + .36 * np.sin(tempo * 9))
        curva = np.minimum(tempo / .32, 1) * np.exp(-tempo / 2.15)
    else:
        sinal = (np.sin(fase) + .24 * np.sin(fase * 2) * np.exp(-tempo / .18)
                 + .09 * np.sin(fase * 3.002) * np.exp(-tempo / .12))
        curva = np.minimum(tempo / .013, 1) * np.exp(-tempo / .29)
    cauda = np.minimum(1, (pontos - 1 - np.arange(pontos)) / (TAXA * .09))
    angulo = (panorama + 1) * math.pi / 4
    trilha[primeiro:primeiro + pontos] += (
        (forca * curva * cauda * sinal)[:, None] * [math.cos(angulo), math.sin(angulo)]
    )


def compor(duracao):
    trilha = np.zeros((round(TAXA * duracao), 2), dtype=np.float32)
    entrada = .31
    for compasso, acorde in enumerate(SEQUENCIA):
        inicio = entrada + compasso * PULSO * 4
        baixo, vozes = ACORDES[acorde]
        for altura, posicao in zip(vozes, (-.5, -.2, .22, .5)):
            nota(trilha, inicio, altura, 2.81, .038, posicao, "acorde")

        nota(trilha, inicio, baixo, 1.34, .113, timbre="base")
        if 2 <= compasso < 24:
            nota(trilha, inicio + 2.5 * PULSO, baixo + 7, .74, .047, .04, "base")

        motivo = ((0, 0), (1.5, 2), (2.5, 1), (3.5, 3))
        if compasso in (0, 1, 7, 8, 12, 15, 16, 20, 24):
            motivo = ((.5, 0), (2, 2))
        for batida, escala in motivo:
            hora = inicio + batida * PULSO
            altura = vozes[escala]
            nota(trilha, hora, altura, .83, .105, -.19)
            nota(trilha, hora + .202, altura, .6, .022, .55)

    tempo = np.arange(len(trilha)) / TAXA
    ganho = np.interp(tempo, [0, .3, .9, 63.6, duracao], [0, 0, 1, 1, 0])
    return trilha * ganho[:, None]


def gravar_trilha(destino, duracao):
    amostras = np.round(np.clip(compor(duracao), -1, 1) * 32767).astype("<i2")
    with wave.open(str(destino), "wb") as arquivo:
        arquivo.setparams((2, 2, TAXA, 0, "NONE", "not compressed"))
        arquivo.writeframes(amostras.tobytes())


def mixar(video, trilha, destino):
    filtros = (
        "[1:a]aformat=channel_layouts=stereo,volume=-1.8dB,asplit[voz][controle];"
        "[2:a]volume=-10.5dB[base];"
        "[base][controle]sidechaincompress=threshold=0.025:ratio=2.2:"
        "attack=32:release=340[trilha];"
        "[voz][trilha]amix=inputs=2:duration=first:normalize=0[audio]"
    )
    subprocess.run([
        "ffmpeg", "-v", "error", "-y", "-i", str(video),
        "-i", str(PASTA / "narracao.flac"), "-i", str(trilha),
        "-filter_complex", filtros, "-map", "0:v:0", "-map", "[audio]",
        "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart",
        str(destino),
    ], check=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("saida", type=Path)
    parser.add_argument("--video", type=Path, help="MP4 da montagem para mixar sem recodificar a imagem")
    args = parser.parse_args()
    duracao = json.loads((PASTA / "cenas.json").read_text())["duracao"]
    if args.video is None:
        gravar_trilha(args.saida, duracao)
    else:
        with tempfile.TemporaryDirectory() as temporario:
            trilha = Path(temporario) / "trilha.wav"
            gravar_trilha(trilha, duracao)
            mixar(args.video, trilha, args.saida)
