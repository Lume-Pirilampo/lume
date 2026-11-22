# Lume Responde 01 · v9 de revisão

O [vídeo v9](../Lume-Responde-01-v9.mp4) usa a [imagem e a mixagem da v8](../Lume-Responde-01-v8.mp4). A fonte da fala é a [locução de 03h16](../montagem-0316/narracao.flac). O [mapa de legendas](legendas.json) separa as falas em blocos curtos de uma cor. O crescimento de letras tem uma prova de conceito separada para avaliação.

O compositor preserva os planos e as transições da base. Aplica a abertura da boca em quatro estados, calculados sobre janelas de áudio de um quadro. No convite, anima o avatar a 30 fps e desenha os balões à frente. A cartela usa a interrogação roxa. A opção `--interrogacao` também aceita `vermelho` e `amarelo`.

## Reexportar

Use Python, Pillow, NumPy, FFmpeg com libx264 e a [fonte KnockIt! Display Research v0.15](https://chatgpt.com/library?file_id=libfile_9d87cc7de5bc81918485da9ecd624e43&account_id=personal). A partir desta pasta:

```sh
python3 compose.py --font /caminho/KnockIT_Display_Research_v0.15.ttf ../Lume-Responde-01-v9.mp4
```
