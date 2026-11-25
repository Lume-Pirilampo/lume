# Arquitetura da Engine do Canal — Post-Mortem do Ep. 1 e Regras Anti-Atalho

> **Leitura obrigatória para qualquer IA ou colaborador antes de alterar código de vídeo do canal.**
> Este documento registra os erros estruturais que aconteceram na construção do Episódio 1 (`01-agente-de-ia`) e define o padrão obrigatório da **engine compartilhada** para os próximos episódios.

---

## 1. O que deu errado no Episódio 1 (Post-Mortem)

O Episódio 1 cumpriu bem o papel de **laboratório visual e editorial** (olhar acompanhando a tela, legenda sincronizada por palavra, pulso contínuo do abdômen, alternância de condutor). Porém, do ponto de vista de engenharia, **a engine reutilizável do canal ainda não foi construída** — o que saiu foi uma implementação acoplada ao Ep. 1 com remendos em cascata:

1. **Cirurgia em cima de MP4 já renderizado (`v8 → v9 → v10`):**
   - `montagem-0257/compose.py` remapeou tempo com `setpts` em cima do MP4 anterior (repetindo/pulando quadros).
   - `revisao-09/compose.py` pintou um `sky_plate` por cima do MP4 da `v8` para apagar estrelas, balões e legendas já gravados e recoloriu corações por faixa RGB.
   - `revisao-10/compose.py` cobriu novamente a faixa de legenda do MP4 da `v9` e usou heurística de cor (`olhar.is_open`) nos pixels decodificados do vídeo para adivinhar se o olho estava aberto antes de colar a pupila.
   - **Consequência:** perda de qualidade por recompressão em cascata, números mágicos de quadro presos ao Ep. 1 (ex.: `q >= 2052`) e impossibilidade de rodar outro episódio pelo mesmo fluxo.
2. **Fábrica e episódio misturados (ausência de `canal/engine/`):**
   - `01-agente-de-ia/montar.py` importava constantes direto de `canal/apresentacao/montar.py` via `runpy.run_path`.
   - Cada revisão (`montagem-0257`, `revisao-09`, `revisao-10`) injetava pastas de revisões anteriores no `sys.path`.
   - **Consequência:** não existe um motor único que receba os dados de um episódio e monte o vídeo do zero.
3. **Receita com *overfitting* no piloto do Reversi:**
   - `receita-videos-narrados.md` e `lume-responde.receita.json` misturam regras gerais da série com parâmetros exclusivos do Ep. 1 (ex.: aumento específico de pictogramas, tempos pontuais de lampejos, selos A/B/C de teste de trilha).
4. **Gargalos manuais, links privados e peso no Git:**
   - Geração da voz Achernar dependente de interface web com login manual.
   - Fonte obrigatória (`KnockIt! Display Research v0.15`) referenciada por link privado do ChatGPT.
   - Múltiplos MP4s intermediários de revisão (`v8`, `v9`, `v10`) commitados direto no Git sem Git LFS.
5. **Faltas de produto para YouTube Shorts:**
   - Ausência de máscara explícita de *Safe Zones* (para evitar que botões/descrição do app cubram informações ou legendas).
   - Ausência de alvo formal de loudness na exportação (`-14 LUFS` integrado / `-1 dBTP` true peak).
   - Falta de modo rascunho rápido (*animatic*) para validar ritmo no celular antes de renderizar efeitos pesados.

---

## 2. O Modo Certo — Arquitetura da Engine (`canal/engine/`)

### Princípio central: separar Motor (fixo) de Episódio (ingredientes)
- **`canal/engine/` (código compartilhado do canal):** sabe *como* compor qualquer episódio da série do zero, sem conhecer nenhum detalhe específico do Reversi, da letra A ou de um gato.
- **`canal/lume-responde/<tema>/<episodio>/` (pacote do episódio):** contém **apenas dados e insumos** (`roteiro.txt`, áudio da narração, `cenas.json` / marcações de tempo, mídia da demonstração e `olhar-cenas.json`).

### Ordem fixa de composição em camadas (sempre da origem limpa)
Toda renderização — seja rascunho ou versão final — nasce **sempre das camadas originais**, nunca de um MP4 anterior, nesta ordem:
1. `fundo` (céu noturno, paleta oficial)
2. `vaga-lumes` (partículas ambientes)
3. `demonstracao` (gravação/animação da tela com recorte 9:16)
4. `avatar` (corpo + pulso contínuo do abdômen + boca + direção do olhar)
5. `hud` (balões, cartela *Lume Responde*, pictogramas)
6. `legendas` (onda tipográfica sincronizada por palavra)

### Requisitos obrigatórios da Engine e da Receita enxuta
- **Cache por cena sem perda:** se usar cache para acelerar revisões, guardar intermediários *lossless* indexados por hash das entradas — comprimir em H.264 **apenas na exportação final**.
- **Separação documental:** manter separados (a) manual editorial/visual da série, (b) schema formal do episódio e (c) estudo de caso histórico do piloto (Ep. 1).
- **Acabamento YouTube Shorts:**
  - Overlay opcional de *Safe Zones* (`--safe-zones`) no preview/rascunho para conferência visual.
  - Normalização de áudio na masterização para `-14 LUFS` / `-1 dBTP`.
  - Modo `--animatic` (ou `--preview`) rápido para aprovar ritmo e legibilidade no celular em segundos.
  - Validador único (`validar.py`) checando schema, correspondência exata entre roteiro e legenda, codec/fps/loudness e gerando prancha de inspeção (*contact sheet*).
  - Pacote de saída padronizado: MP4 final + `.srt` + frame limpo de capa.

---

## 3. Regras Anti-Atalho (Checklist para qualquer IA)

Antes de escrever ou aprovar qualquer alteração no código de vídeo, confira estas 5 travas:

1. **Proibido editar MP4 pronto:** nenhuma revisão pode abrir um vídeo já renderizado para apagar, cobrir ou recolorir elementos. Se algo mudou, ajuste os dados/camadas na origem e re-renderize limpo.
2. **Proibido código exclusivo de episódio dentro do motor:** se uma regra só vale para o Episódio 1 (ou usa número mágico de quadro/tempo de um vídeo específico), ela **não pode** existir na engine — deve virar parâmetro no JSON do episódio ou ficar fora.
3. **Toda melhoria entra na base compartilhada:** se você criou ou melhorou olhar, legenda, transição ou efeito, isso deve entrar em `canal/engine/` funcionando por parâmetros para todos os episódios.
4. **Teste de abstração obrigatório (Ep. 2 como detector):** qualquer mudança na engine só é considerada pronta quando consegue renderizar do zero tanto o **Ep. 1** quanto o **Ep. 2 (letra A)** sem `if` específico por episódio.
5. **Proibido commitar MP4s intermediários no repositório:** manter no Git apenas código, roteiros, configs e assets leves (usar Releases ou armazenamento externo para vídeos pesados).
