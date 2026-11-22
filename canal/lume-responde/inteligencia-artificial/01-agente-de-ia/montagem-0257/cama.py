import subprocess
from pathlib import Path
import numpy as np

FF = "ffmpeg"
SR = 48000
MUSIC = Path(__file__).resolve().parent / "no-copyright-music-2026-corporate-632312.mp3"

def samples(path, channels=2, seconds=None, audio_filter=None):
    args = [FF,"-hide_banner","-nostdin","-v","error","-i",str(path),"-map","0:a:0"]
    if seconds is not None:
        args += ["-t",str(seconds)]
    if audio_filter:
        args += ["-af",audio_filter]
    args += ["-ac",str(channels),"-ar",str(SR),"-f","f32le","-"]
    return np.frombuffer(subprocess.check_output(args), "<f4").reshape(-1,channels)


def write_wav(path, pcm):
    data=np.ascontiguousarray(pcm,dtype="<f4")
    subprocess.run([FF,"-hide_banner","-nostdin","-v","error","-y","-f","f32le",
        "-ac",str(data.shape[1]),"-ar",str(SR),"-i","-","-c:a","pcm_s24le",str(path)],
        input=data.tobytes(),check=True)


