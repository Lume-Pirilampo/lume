"""Mantém o corte v9, direciona o olhar e anima as legendas pela voz."""
import argparse
from bisect import bisect_right
import json
import os
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory

import numpy as np
from PIL import Image

HERE=Path(__file__).resolve().parent
EP=HERE.parent
sys.path[:0]=[str(EP),str(EP/"montagem-0257"),str(EP/"revisao-09")]

import animacao
import corpo
import legenda
import olhar

FPS=30
SIZE=(1080,1920)
RAW=SIZE[0]*SIZE[1]*3
FF=["ffmpeg","-hide_banner","-nostdin","-v","error","-y"]
CUES=json.loads((HERE/"legendas.json").read_text(encoding="utf-8"))
CUE_FRAMES=[round(a*FPS) for a,_,_ in CUES]
SCENES=json.loads((HERE/"olhar-cenas.json").read_text(encoding="utf-8"))
ENDING=json.loads((HERE/"assinatura.json").read_text(encoding="utf-8"))


def eyes_at(t):
    for cue in SCENES:
        if cue["entrada"] <= t < cue["retorno"]:
            enter = corpo.ease((t-cue["entrada"])/(cue["chegada"]-cue["entrada"]))
            leave = corpo.ease((cue["retorno"]-t)/(cue["retorno"]-cue["saida"]))
            return round(enter*leave*cue["x"]),round(enter*leave*cue["y"])
    return 0,0


def pose_at(q,t):
    if q>=2052:
        x,y,w,a=ENDING[str(min(q,2200))]
        return t,x,y,round(w),a,1.0
    old=corpo.parametros(q)
    if 1722<=q<2052:
        p=np.asarray(animacao.cta_pose(t,(58.87,59.85,70.43)))
        if old is not None and (t<59.19 or t>70.03):
            v=corpo.ease((t-58.91)/.28)*(1-corpo.ease((t-70.03)/.40))
            p=np.asarray(old[1:5])*(1-v)+p*v
        x,y,w,a=p
        return t,x,y,round(w),a,1.0
    return old


def frame_at(source,time):
    data=subprocess.check_output(FF+["-ss",str(time),"-i",str(source),"-frames:v","1",
        "-f","rawvideo","-pix_fmt","rgb24","-"])
    return Image.frombytes("RGB",SIZE,data)


def backdrop(source):
    plate=frame_at(source,74.5).crop((0,1340,SIZE[0],1630))
    gradient=np.interp(np.arange(290),[0,23,260,289],[0,255,255,0])
    matte=np.broadcast_to(gradient[:,None],(290,SIZE[0]))
    return plate,Image.fromarray(matte.astype("u1"))


def render(image,num,q,plate,matte,font):
    t=num/FPS
    pose=pose_at(q,t)
    if pose is not None and -35<pose[1]<1130:
        if q>=1722 or animacao.match_mouth(image,pose)<24:
            dx,dy=eyes_at(t)
            is_blink=not olhar.is_open(image,pose)
            # The closed expression is built from the adjusted eye contours.
            olhar.draw(image,pose,dx,dy,q,is_blink)
    k=bisect_right(CUE_FRAMES,num)-1
    if k>=0:
        _,phrase,marks=CUES[k]
        if phrase:
            image.paste(plate,(0,1340),matte)
            legenda.desenhar(image,font,phrase.upper().replace("“",'"').replace("”",'"'),marks,t)
    return image


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("saida",type=Path)
    parser.add_argument("--base",type=Path,default=EP/"Lume-Responde-01-v9.mp4")
    parser.add_argument("--font",type=Path,default=os.environ.get("LUME_FONT"))
    parser.add_argument("--trecho",nargs=2,type=float,metavar=("INICIO","FIM"))
    args=parser.parse_args()
    if args.font is None or not args.font.is_file():
        parser.error("Informe a fonte KnockIt! Display Research v0.15 com --font ou LUME_FONT.")
    marks=json.loads((EP/"montagem-0316"/"tempo.json").read_text(encoding="utf-8"))
    raw,times=np.asarray(marks["marcas_fonte_para_tempo"]).T
    target=np.rint(times*FPS).astype(int)
    total=int(target[-1])
    origin=np.rint(np.interp(np.arange(int(raw[-1])),raw,target)).astype(int)
    frames=np.searchsorted(origin,np.arange(total),side="right")-1
    first,stop=(round(t*FPS) for t in args.trecho) if args.trecho else (0,total)
    if not 0<=first<stop<=total:
        parser.error("O trecho está fora da duração do episódio.")
    plate,matte=backdrop(args.base)
    with TemporaryDirectory(prefix="lume-v10-") as folder:
        video=Path(folder)/"v.mp4"
        seek=["-ss",f"{first/FPS:.9f}"] if first else []
        with subprocess.Popen(FF+seek+["-threads","3","-i",str(args.base),"-an","-frames:v",str(stop-first),
              "-f","rawvideo","-pix_fmt","rgb24","-"],stdout=subprocess.PIPE) as source, \
             subprocess.Popen(FF+["-f","rawvideo","-pix_fmt","rgb24","-s","1080x1920","-r",str(FPS),
              "-i","-","-an","-c:v","libx264","-threads","5","-preset","fast","-crf","18",
              "-pix_fmt","yuv420p","-colorspace","bt709","-color_trc","bt709","-color_primaries","bt709",
              "-movflags","+faststart",str(video)],stdin=subprocess.PIPE) as encoder:
            for num in range(first,stop):
                image=Image.frombytes("RGB",SIZE,source.stdout.read(RAW))
                render(image,num,int(frames[num]),plate,matte,args.font)
                encoder.stdin.write(image.tobytes())
                if num%300==0:
                    print(f"{num}/{stop} quadros",flush=True)
            encoder.stdin.close()
            if source.wait() or encoder.wait():
                raise RuntimeError("Exportação de quadros incompleta.")
        limit=["-t",f"{(stop-first)/FPS:.9f}"] if args.trecho else []
        subprocess.run(FF+["-i",str(video),*seek,"-i",str(args.base),"-map","0:v","-map","1:a",
            "-c","copy",*limit,"-movflags","+faststart",str(args.saida)],check=True)


if __name__=="__main__":
    main()
