# Lume responde 01 · O que é um agente de IA?

Primeiro corte para revisão, com narração Achernar em português brasileiro. O roteiro e a composição seguem o [storyboard do episódio](https://chatgpt.com/library?file_id=libfile_8ac89307c67081918f970844fd6b5e8a&account_id=personal).

- [Vídeo vertical](Lume-Responde-01.mp4)
- [Roteiro](roteiro.txt), [marcas de cena e legenda](cenas.json) e [montagem editável](montar.py)
- [Narração](narracao.flac)
- [Capturas do Reversi 6×6 e símbolos](assets/). As capturas mostram o tabuleiro antes do lance de Lume em B2 e depois da resposta do computador em B3, no modo solo de [TryBoardGames](https://www.tryboardgames.com/reversi/6x6).

## Reexportar

Use Python, Pillow, NumPy, FFmpeg e a fonte KnockIt! Display Research v0.15 indicada na [receita do canal](../../../receita-videos-narrados.md). A partir da raiz do repositório:

```sh
LUME_FONT=/caminho/KnockIT_Display_Research_v0.15.ttf python3 canal/lume-responde/inteligencia-artificial/01-agente-de-ia/montar.py
```
