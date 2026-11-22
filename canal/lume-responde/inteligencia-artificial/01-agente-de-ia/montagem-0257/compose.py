from pathlib import Path
import sys,subprocess as sp,math,json,csv,re
import numpy as np
from PIL import Image,ImageDraw
from tempfile import TemporaryDirectory
import argparse
import cama as c
import corpo as a

R=Path(__file__).resolve().parent
sys.path.insert(0,str(R.parent))
from arte import icon as original_icon
parser=argparse.ArgumentParser(description="Reproduz a montagem da tomada 02h57 do episódio 1.")
parser.add_argument("saida", type=Path, nargs="?", default=Path.cwd()/"Lume-Responde-01-remontado.mp4")
dest=parser.parse_args().saida.resolve()
if dest.exists():
 parser.error(f"O arquivo de saída já existe: {dest}")
work=TemporaryDirectory(prefix="lume-0257-")
D=Path(work.name)
F=c.FF
src=R/"Lume-Responde-01-balao-e-voz.mp4"
def run(args): sp.run([F,'-v','error','-y',*args],check=True)
def frame(q):
 raw=sp.check_output([F,'-v','error','-ss',f'{q/30:.8f}','-i',src,'-frames:v','1','-pix_fmt','rgb24','-f','rawvideo','-'])
 return Image.frombytes('RGB',(1080,1920),raw)
# Retain the scene behind the lens, and draw the actor and glass with true alpha.
plate=frame(1221); bg=a.ceu()
lens=original_icon('lupa')
def ease(x): x=np.clip(x,0,1); return x*x*(3-2*x)
def icon(img,sprite,x,y,w,alpha):
 sprite=sprite.resize((w,round(sprite.height*w/sprite.width)),Image.Resampling.LANCZOS)
 img.paste(sprite,(round(x-sprite.width/2),round(y-sprite.height/2)),sprite.getchannel('A').point(lambda p:round(p*alpha)))
def render(q):
 v=ease((q-1221)/34); t,x,y,w,angle,op=a.parametros(q)
 im=bg.copy()
 # The labels and lock retreat as the real magnifier takes over.
 k=ease((q-1221)/20)
 for box,dx,dy in [((94,535,610,1019),-175,-22),((615,904,978,1005),34,27)]:
  pic=plate.crop(box); b=np.asarray(bg.crop(box),float); delta=np.max(np.abs(np.asarray(pic,float)-b),2)
  mask=Image.fromarray(np.uint8(255*np.clip((delta-4)/14,0,1)*(1-k)))
  im.paste(pic,(round(box[0]+dx*k),round(box[1]+dy*k)),mask)
 tick=math.floor(t*15); s=a.rotacionar(a.sprite_512(a.estado_de_luz(q),round(2+2*math.sin(tick/15*math.tau*4)),a.boca_por_energia(a.MARKS['falas_15fps'][tick]),((t+.37)%3.62)<.13),w,angle,Image.Resampling.BICUBIC)
 lx=764.14-224.14*v; ly=688.25+15.75*v; size=293+1727*v**1.22
 radius=52.5*size/240+300*ease((q-1235)/15)
 layer=im.copy(); layer.paste(s,a.coordenadas(x,y,s),s.getchannel('A')); mask=Image.new('L',im.size); ImageDraw.Draw(mask).ellipse((lx-radius,ly-radius,lx+radius,ly+radius),fill=round(255*op));im=Image.composite(layer,im,mask)
 rim=lens.copy(); al=rim.getchannel('A'); ImageDraw.Draw(al).ellipse((46,42,150,146),fill=round(255*(1-ease((q-1222)/9))));rim.putalpha(al)
 if q<1250: icon(im,rim,lx+22*size/240,ly+26*size/240,round(size),1-ease((q-1234)/15))
 patch=im.crop((0,245,1080,1335)).convert('RGBA'); alpha=np.interp(np.arange(1090),[0,75,1000,1089],[0,255,255,0]); patch.putalpha(Image.fromarray(np.uint8(np.repeat(alpha[:,None],1080,axis=1)))); return patch
for q in range(1222,1255):render(q).save(D/f'p{q}.png',compress_level=1)
# Endpoints in the approved cut and in the supplied continuous reading.
old=np.array([0,80,112,199,439,574,670,714,749,1022,1096,1235,1322,1498,1733,1825,1948,2008,2052,2076,2231])
new=np.rint(np.array([0,2.97,3.85,6.05,13.70,17.35,20.56,21.95,23.89,32.36,34.92,39.98,42.99,48.59,55.85,58.27,61.27,62.86,66.36,67.16,72.33])*30).astype(int)
def remap(q):return np.interp(q,old,new)/30
sr=c.SR; N=round(new[-1]*sr/30); voice=c.samples(R/'Generated Audio November 22, 2026 - 2_57AM.wav',1)[:,0]
mus=c.samples(c.MUSIC,2,N/sr,'equalizer=f=2100:t=q:w=0.95:g=-1.5')[:N]
pos=np.arange(N)/sr; env=np.zeros(N//480+1); vv=np.pad(voice,(0,480-len(voice)%480)); lev=(np.mean(vv.reshape(-1,480)**2,axis=1)>0.000063); last=0
for i in range(len(env)):
 target=lev[max(0,i-13):i+10].any(); last+=(target-last)*(.1 if target>last else .026);env[i]=last
gain=np.interp(np.arange(N)/480,np.arange(len(env)),10**((-14.6-5.8*env)/20))*1.1649
mix=mus*(gain*np.sin(np.clip(pos/.65,0,1)*np.pi/2)**2*np.sin(np.clip((pos[-1]-pos)/1.15,0,1)*np.pi/2)**2)[:,None]
mix[:len(voice)]+=voice[:,None]*(.16/np.sqrt(np.mean(voice[abs(voice)>.035]**2)))
for row in csv.DictReader((R/'Lume-Responde-01-balao-e-voz-mapa.csv').open(encoding='utf-8-sig'),delimiter=';'):
 if row['camada']!='Efeito sonoro':continue
 p=R/row['asset_ou_fonte']; raw=c.samples(p,1); m=re.search(r'ganho (-?[0-9]+) dB \| pan (-?[\d.]+)',row['parametros_para_edicao'])
 db,pan=map(float,m.groups()) if m else (-11,-.12)
 start=round(remap(int(row['quadro_inicial_30fps']))*sr);theta=(1+pan)*math.pi/4
 mix[start:start+len(raw)]+=raw*10**(db/20)*np.array([math.cos(theta),math.sin(theta)])
mix*=min(1,.97/np.max(np.abs(mix)));c.write_wav(D/'mix.wav',mix)
expr='N'
for i in reversed(range(len(old)-1)):
 expr=f'if(lt(N,{old[i+1]}),{new[i]}+(N-{old[i]})*{new[i+1]-new[i]}/{old[i+1]-old[i]},{expr})'
fil=f"[1:v]setpts=PTS+1222/30/TB[p];[0:v][p]overlay=0:245:enable='between(n,1222,1254)':eof_action=pass,settb=1/90000,setpts='({expr})*3000',fps=30,trim=end_frame=2170[v]"
run(['-i',src,'-framerate','30','-start_number','1222','-i',D/'p%d.png','-i',D/'mix.wav','-filter_complex_threads','3','-filter_complex',fil,'-map','[v]','-map','2:a','-c:v','libx264','-preset','veryfast','-threads','6','-crf','15','-pix_fmt','yuv420p','-colorspace','bt709','-color_trc','bt709','-color_primaries','bt709','-c:a','aac','-b:a','256k','-movflags','+faststart',dest])


