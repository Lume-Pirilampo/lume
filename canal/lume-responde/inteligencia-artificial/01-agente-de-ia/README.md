# Lume responde 01 · O que é um agente de IA?

Oitavo corte para revisão do [episódio #1](https://github.com/Lume-Pirilampo/lume/issues/1), montado com a [receita 0.4](../../../receita-videos-narrados.md) e o [avatar de 512 px](../../../assets/avatar-512/Lume-spritesheet-512.json).

- [Vídeo vertical v8](Lume-Responde-01-v8.mp4)
- [Roteiro falado](roteiro.txt), [timeline e marcas relativas à locução](cenas.json), [montagem](montar.py) e [arte](arte.py)
- [Tomada de 71,24 s em FLAC](narracao.flac), sem edição de voz. Fonte: `Generated Audio November 22, 2026 - 3_16AM.wav`.
- [Capturas do Reversi 6×6 e símbolos](assets/) e [storyboard do episódio](https://chatgpt.com/library?file_id=libfile_8ac89307c67081918f970844fd6b5e8a&account_id=personal).

A cartela usa um balão acima da pergunta. As ações de B2 e B3 reaproveitam a reconstituição do corte anterior e têm novas marcas de fala. O tabuleiro continua em quadro até «Pronto». O mesmo ciclo de luz do avatar atravessa as cenas. A assinatura continua o voo da despedida e congela a pose sorridente, com um ciclo de apagar e reacender o abdômen antes do último segundo fixo. O master usa a voz da tomada enviada.

## Reexportar

Use Python, Pillow, NumPy, FFmpeg e a [fonte KnockIt! Display Research v0.15](https://chatgpt.com/library?file_id=libfile_9d87cc7de5bc81918485da9ecd624e43&account_id=personal). A partir da raiz do repositório:

```sh
export LUME_FONT=/caminho/KnockIT_Display_Research_v0.15.ttf
python3 canal/lume-responde/inteligencia-artificial/01-agente-de-ia/montar.py
```

Para conferir uma passagem, use `--inicio` e `--fim` em segundos. A opção `--base` desliga os pictogramas e movimentos de acabamento. A opção `--quadros` exporta um painel de referência.
