# Lume Responde 01 · v8 remontada com a tomada de 03h16

A base visual da [montagem de 02h57](../montagem-0257/) traz o avatar de 512 px, a cartela em caixa alta, os pictogramas e as transições entre cenas. A passagem pela lupa conserva o retoque do corte de 02h57. O [mapa de tempo](tempo.json) ajusta as marcas dessa base à [locução de 03h16](narracao.flac).

O tabuleiro permanece visível durante «Pronto.», com a legenda em KnockIt!, e então encolhe até o cartão Objetivo. A montagem usa a trilha C e as 29 entradas dos 12 efeitos do [mapa de referência](../montagem-0257/Lume-Responde-01-balao-e-voz-mapa.csv), com os mesmos arquivos, ganhos e panoramas da mixagem de 02h57. As marcas dos efeitos acompanham as ações da imagem. A assinatura termina com um segundo na pose acesa.

## Reexportar

A partir desta pasta, com Python, Pillow, NumPy, FFmpeg com libx264 e a [fonte KnockIt! Display Research v0.15](https://chatgpt.com/library?file_id=libfile_9d87cc7de5bc81918485da9ecd624e43&account_id=personal):

```sh
python3 compose.py --font /caminho/KnockIT_Display_Research_v0.15.ttf ../Lume-Responde-01-v8.mp4
```

O WAV original de 03h16 está reempacotado em FLAC sem perdas. A fala é nivelada na mixagem. O ajuste de tempo pode repetir ou pular quadros da base renderizada. O [corte para revisão](../Lume-Responde-01-v8.mp4) tem 1080 × 1920 a 30 fps, com áudio estéreo a 48 kHz.
