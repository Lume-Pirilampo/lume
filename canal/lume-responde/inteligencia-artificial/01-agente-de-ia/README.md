# Lume responde 01 · O que é um agente de IA?

Terceiro corte para revisão, com narração Achernar em português brasileiro. A composição foi revisada a partir do [storyboard do episódio](https://chatgpt.com/library?file_id=libfile_8ac89307c67081918f970844fd6b5e8a&account_id=personal).

- [Vídeo vertical](Lume-Responde-01.mp4)
- [Roteiro](roteiro.txt), [marcas de cena e legenda](cenas.json) e [montagem editável](montar.py)
- [Narração](narracao.flac) e [animação do avatar e ilustrações](arte.py)
- [Capturas do Reversi 6×6 e símbolos](assets/). As capturas mostram o tabuleiro antes do lance de Lume em B2 e depois da resposta do computador em B3, no modo solo de [TryBoardGames](https://www.tryboardgames.com/reversi/6x6).

## Revisão

O avatar usa o desenho original do canal em camadas, com asas, inclinação, piscadas e poses de boca guiadas pela intensidade da voz. A pergunta ocupa um corte fixo em preto. As entradas de controle, tabuleiro, monitor e nome do jogo são marcas editáveis em `cenas.json`. As marcas foram ajustadas pela forma de onda e pelo espectrograma da fala. A montagem preserva as capturas do Reversi e acumula os quatro marcadores da demonstração.

As asas batem em torno de uma articulação fixa com sobreposição no tronco. Os critérios e os marcadores do jogo aparecem em destaque antes de ocupar suas posições menores. O cadeado reage à fala sobre acesso restrito. Os três exemplos têm rotação breve na chegada, e os símbolos do CTA aparecem ao longo da pergunta, do convite e da despedida.

A faixa reaproveita a tomada fornecida em Achernar e emenda «Talvez a sua pergunta seja o tema do nosso próximo vídeo» com «Até lá».

## Reexportar

Use Python, Pillow, NumPy, FFmpeg e a fonte KnockIt! Display Research v0.15 indicada na [receita do canal](../../../receita-videos-narrados.md). A partir da raiz do repositório:

```sh
LUME_FONT=/caminho/KnockIT_Display_Research_v0.15.ttf python3 canal/lume-responde/inteligencia-artificial/01-agente-de-ia/montar.py
```
