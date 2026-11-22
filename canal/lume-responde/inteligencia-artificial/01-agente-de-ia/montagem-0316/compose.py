"""Remonta o corte de referência do episódio 01 com a locução de 03h16."""

import argparse
import csv
import json
import math
import os
from pathlib import Path
import re
import subprocess
import sys
from tempfile import TemporaryDirectory

import numpy as np
from PIL import Image, ImageDraw, ImageFont


HERE = Path(__file__).resolve().parent
REFERENCE = HERE.parent / "montagem-0257"
sys.path.insert(0, str(REFERENCE))
import cama

TIMELINE = json.loads((HERE / "tempo.json").read_text(encoding="utf-8"))
FPS = TIMELINE["fps"]
SR = cama.SR
SOURCE = REFERENCE / TIMELINE["fonte_imagem"]
CORRECTED_SOURCE = REFERENCE / TIMELINE["fonte_retoque_lupa"]
SOURCE_FRAMES, TARGET_SECONDS = np.asarray(TIMELINE["marcas_fonte_para_tempo"]).T
TARGET_FRAMES = np.rint(TARGET_SECONDS * FPS).astype(int)
HOLD_FRAME = int(np.interp(TIMELINE["quadro_fim_movimento_da_fonte"], SOURCE_FRAMES, TARGET_FRAMES))
TOTAL_FRAMES = int(TARGET_FRAMES[-1])
VIDEO_OPTIONS = [
    "-c:v", "libx264", "-preset", "medium", "-bf", "0", "-threads", "6",
    "-pix_fmt", "yuv420p", "-colorspace", "bt709", "-color_trc", "bt709",
    "-color_primaries", "bt709", "-video_track_timescale", "90000",
]


def ffmpeg(args, **options):
    return subprocess.run([cama.FF, "-hide_banner", "-nostdin", "-v", "error", "-y", *args],
                          check=True, **options)


def target_time(frame):
    return np.interp(frame, SOURCE_FRAMES, TARGET_FRAMES) / FPS


def frame_at(path, frame):
    out = ffmpeg(["-ss", f"{frame / FPS:.9f}", "-i", str(path), "-frames:v", "1",
                  "-pix_fmt", "rgb24", "-f", "rawvideo", "-"], stdout=subprocess.PIPE)
    return Image.frombytes("RGB", (1080, 1920), out.stdout)


def write_lens_patches(work):
    """Preserva, no mesmo quadro de origem, o retoque de lupa da tomada anterior."""
    start, end = TIMELINE["quadros_de_retoque_lupa"]
    source_marks, corrected_times = np.asarray(TIMELINE["marcas_da_lupa_na_tomada_0257"]).T
    ref_frames = np.rint(np.interp(np.arange(start, end + 1), source_marks,
                                 np.rint(corrected_times * FPS))).astype(int)
    first, last = ref_frames[0], ref_frames[-1]
    crop = (0, 245, 1080, 1335)
    width, height = crop[2] - crop[0], crop[3] - crop[1]
    data = ffmpeg(["-ss", f"{first / FPS:.9f}", "-i", str(CORRECTED_SOURCE),
                   "-frames:v", str(last - first + 1),
                   "-vf", f"crop={width}:{height}:{crop[0]}:{crop[1]}",
                   "-pix_fmt", "rgb24", "-f", "rawvideo", "-"], stdout=subprocess.PIPE).stdout
    frames = np.frombuffer(data, dtype=np.uint8).reshape(-1, height, width, 3)
    if len(frames) != last - first + 1:
        raise ValueError("A transição da lupa está incompleta na referência.")
    for q, ref in enumerate(ref_frames, start):
        Image.fromarray(frames[ref - first]).save(work / f"lupa-{q}.png", compress_level=1)


def write_pronto(work, font_path):
    marks = TIMELINE["legenda_pronto"]
    # Reuse the same animated stage's unobstructed lower strip, below the turn marker.
    picture = frame_at(SOURCE, marks["quadro_fundo_da_fonte"]).crop((34, 1400, 1046, 1568))
    draw = ImageDraw.Draw(picture)
    font = ImageFont.truetype(str(font_path), 108)
    draw.text((506, 84), "PRONTO.", fill=(251, 188, 84), font=font, anchor="mm")
    picture.save(work / "pronto.png")


def mix_audio(work):
    count = TOTAL_FRAMES * SR // FPS
    voice = cama.samples(HERE / "narracao.flac", 1)[:, 0]
    if len(voice) > count:
        raise ValueError("A locução termina depois do vídeo.")
    if not np.any(np.abs(voice) > .035):
        raise ValueError("A locução está vazia.")
    narration_gain = .16 / np.sqrt(np.mean(voice[np.abs(voice) > .035] ** 2))
    music = cama.samples(cama.MUSIC, 2, count / SR, "equalizer=f=2100:t=q:w=0.95:g=-1.5")
    music = np.pad(music[:count], ((0, max(0, count - len(music))), (0, 0)))
    tick = 480
    levels = np.pad(voice, (0, -len(voice) % tick)).reshape(-1, tick)
    speaking = np.mean(levels ** 2, axis=1) > .000063
    envelope = np.zeros(count // tick + 1)
    gain = 0.
    for i in range(len(envelope)):
        target = speaking[max(0, i - 13):i + 10].any()
        gain += (target - gain) * (.1 if target > gain else .026)
        envelope[i] = gain
    music_gain = np.interp(np.arange(count) / tick, np.arange(len(envelope)),
                           1.1649 * 10 ** ((-14.6 - 5.8 * envelope) / 20))
    time = np.arange(count) / SR
    fade_in = np.sin(np.clip(time / .65, 0, 1) * np.pi / 2) ** 2
    fade_out = np.sin(np.clip((time[-1] - time) / 1.15, 0, 1) * np.pi / 2) ** 2
    music *= (music_gain * fade_in * fade_out)[:, None]
    mix = music.copy()
    mix[:len(voice)] += voice[:, None] * narration_gain
    events = []
    filename = REFERENCE / "Lume-Responde-01-balao-e-voz-mapa.csv"
    with filename.open(encoding="utf-8-sig") as handle:
        for row in csv.DictReader(handle, delimiter=";"):
            if row["camada"] != "Efeito sonoro":
                continue
            path = REFERENCE / row["asset_ou_fonte"]
            sample = cama.samples(path, 1)
            options = re.search(r"ganho (-?[0-9]+) dB \| pan (-?[\d.]+)",
                                row["parametros_para_edicao"])
            db, pan = map(float, options.groups()) if options else (-11, -.12)
            t = float(target_time(int(row["quadro_inicial_30fps"])))
            start = round(t * SR)
            end = start + len(sample)
            if end > len(mix):
                raise ValueError(f"Efeito fora da montagem: {path.name}")
            angle = (1 + pan) * math.pi / 4
            mix[start:end] += sample * 10 ** (db / 20) * [math.cos(angle), math.sin(angle)]
            events.append((path.name, t, db, pan))
    if len(events) != 29 or len({row[0] for row in events}) != 12:
        raise ValueError("O mapa precisa preservar as 29 entradas de efeitos do corte de referência.")
    mix *= min(1, .97 / np.max(np.abs(mix)))
    cama.write_wav(work / "mix.wav", mix)
    print(f"{len(events)} entradas de efeitos, trilha C e {len(voice) / SR:.2f} s de locução.", flush=True)


def map_expression():
    expr = "N"
    for start, end, before, after in reversed(list(zip(
            SOURCE_FRAMES[:-1], SOURCE_FRAMES[1:], TARGET_FRAMES[:-1], TARGET_FRAMES[1:]))):
        expr = (f"if(lt(N,{int(end)}),{before}+(N-{int(start)})"
                f"*{after - before}/{int(end - start)},{expr})")
    return expr


def render_video(work, font_path, preview):
    write_lens_patches(work)
    write_pronto(work, font_path)
    p0, p1 = TIMELINE["quadros_de_retoque_lupa"]
    pronto = TIMELINE["legenda_pronto"]
    lower, upper = round(pronto["inicio_s"] * FPS), round(pronto["fim_s"] * FPS)
    if preview:
        width, height = 540, 960
        variant = f",scale={width}:{height}"
    else:
        width, height = 1080, 1920
        variant = ""
    # Retiming happens after preserving the lens patch, before the new subtitle.
    chain = (
        f"[1:v]setpts=PTS+{p0}/{FPS}/TB[ret];"
        f"[0:v][ret]overlay=0:245:enable='between(n,{p0},{p1})':eof_action=pass,"
        f"settb=1/90000,setpts='({map_expression()})*3000',fps={FPS},"
        f"trim=end_frame={HOLD_FRAME}[base];"
        f"[base][2:v]overlay=34:1400:enable='gte(n,{lower})*lt(n,{upper})'{variant}[v]"
    )
    end_frame = frame_at(SOURCE, TIMELINE["quadro_fixo_da_fonte"])
    if preview:
        end_frame = end_frame.resize((width, height), Image.Resampling.LANCZOS)
    end_frame.save(work / "assinatura.png")
    rate = ["-crf", "23", "-maxrate", "1120k", "-bufsize", "2240k"]
    ffmpeg(["-i", str(SOURCE), "-framerate", str(FPS), "-start_number", str(p0),
            "-i", str(work / "lupa-%d.png"), "-i", str(work / "pronto.png"),
            "-filter_complex_threads", "4", "-filter_complex", chain, "-map", "[v]", "-an",
            *VIDEO_OPTIONS, *rate, str(work / "movimento.mp4")])
    ffmpeg(["-loop", "1", "-framerate", str(FPS), "-i", str(work / "assinatura.png"),
            "-frames:v", str(TOTAL_FRAMES - HOLD_FRAME), "-an", *VIDEO_OPTIONS,
            "-qp", "23", "-g", "1", str(work / "fecho.mp4")])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("saida", type=Path)
    parser.add_argument("--font", type=Path, default=os.environ.get("LUME_FONT"))
    parser.add_argument("--preview", action="store_true", help="Exporta em 540 × 960 para revisão.")
    args = parser.parse_args()
    if args.font is None or not args.font.is_file():
        parser.error("Forneça a fonte KnockIt! Display Research v0.15 com --font ou LUME_FONT.")
    if np.any(np.diff(TARGET_FRAMES) <= 0) or TOTAL_FRAMES - HOLD_FRAME != FPS:
        raise ValueError("A montagem precisa de marcas crescentes e de um segundo de quadro final.")
    with TemporaryDirectory(prefix="lume-v8-") as directory:
        work = Path(directory)
        mix_audio(work)
        render_video(work, args.font, args.preview)
        listing = work / "lista.txt"
        listing.write_text(f"file movimento.mp4\nduration {HOLD_FRAME / FPS:.9f}\n"
                           f"file fecho.mp4\nduration 1.0\n", encoding="utf-8")
        ffmpeg(["-f", "concat", "-safe", "0", "-i", str(listing),
                "-i", str(work / "mix.wav"), "-map", "0:v", "-map", "1:a",
                "-c:v", "copy", "-c:a", "aac", "-b:a", "160k", "-ar", str(SR),
                "-movflags", "+faststart", "-metadata", "artist=Lume",
                "-metadata", "title=Lume Responde - O que é um agente de IA?",
                str(args.saida)])


if __name__ == "__main__":
    main()
