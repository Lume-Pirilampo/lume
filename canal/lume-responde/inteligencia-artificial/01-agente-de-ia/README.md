# Lume responde 01 · O que é um agente de IA?

Sétimo corte para revisão, com a narração limpa da Achernar em português brasileiro. A composição foi revisada a partir do [storyboard do episódio](https://chatgpt.com/library?file_id=libfile_8ac89307c67081918f970844fd6b5e8a&account_id=personal).

- [Vídeo vertical](Lume-Responde-01.mp4)
- [Roteiro](roteiro.txt), [marcas de cena e legenda](cenas.json) e [montagem editável](montar.py)
- [Narração](narracao.flac), [tomada da abertura em Achernar](assets/abertura-achernar.wav) e [animação do avatar e ilustrações](arte.py)
- [Capturas do Reversi 6×6 e símbolos](assets/). As capturas mostram o tabuleiro antes do lance de Lume em B2 e depois da resposta do computador em B3, no modo solo de [TryBoardGames](https://www.tryboardgames.com/reversi/6x6).

## Revisão

A introdução «Oi, sou Lumi. Agente de IA.» usa uma única tomada, gerada com a voz Achernar no Google AI Studio. O logotipo «Lumi Responde» aparece em lilás na cartela da pergunta. O tabuleiro abre o exemplo, e os dois símbolos de condições ficam mais tempo no centro antes de encolherem. O nome Reversi e o tamanho do tabuleiro entram na faixa inferior conforme a fala.

Os dois lances são reconstituídos a partir das capturas e do histórico da partida. O cursor marca o lance do Lumi, e a aura e o ícone de computador marcam a resposta. A transição intermediária mostra a peça que vira com cada lance. A montagem editável registra as marcas em `cenas.json`.

A montagem ajusta o silêncio inicial e o nível da nova tomada e sincroniza o movimento da boca ao áudio. A exportação reutiliza a narração codificada do quarto corte e os quadros do sexto corte a partir da cartela da pergunta. A faixa de edição usa a voz limpa decodificada do quarto corte a partir da emenda. A exportação está sem trilha.

## Reexportar

Use Python, Pillow, NumPy, FFmpeg e a fonte KnockIt! Display Research v0.15 indicada na [receita do canal](../../../receita-videos-narrados.md). A partir da raiz do repositório:

```sh
LUME_FONT=/caminho/KnockIT_Display_Research_v0.15.ttf python3 canal/lume-responde/inteligencia-artificial/01-agente-de-ia/montar.py
```
