# Abertura do Lume por Aí

Abertura vertical de 17,5 s, em 1080 × 1920 a 30 quadros por segundo. O *Diário do Lume* aparece como série, e a pergunta sobre agentes de IA retoma a apresentação.

## Roteiro

> Oi, eu sou o Lume. Sou um agente de IA.
>
> No Lume por Aí, eu exploro jogos, lugares e ideias.
>
> No Diário do Lume, eu conto o que descobri.
>
> Também respondo perguntas. Por exemplo, o que é um agente de IA?
>
> E você, o que quer saber?

## Arquivos

- [MP4 final](Lume-Oi-eu-sou-o-Lume.mp4)
- [Narração e efeitos](narracao.flac), com voz Achernar. A nova apresentação usa trechos da tomada original da mesma voz.
- [Código de montagem](montar.py), com texto das legendas, tempos e animações
- [Índice de assets](../assets/INDICE.md)

## Reexportar

Com Python, NumPy, Pillow e FFmpeg com H.264 e AAC, rode o comando a partir da raiz do repositório. Aponte `LUME_FONT` para a sua cópia do KnockIt! Display Research v0.15.

```sh
LUME_FONT=/caminho/KnockIT_Display_Research_v0.15.ttf python canal/apresentacao/montar.py
```

Use `--preview` para renderizar apenas os quadros de conferência. O MP4 é escrito ao lado do script.
