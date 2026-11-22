# Receita de vídeos narrados do Lume por Aí

A [abertura do canal](apresentacao/README.md) é a referência de voz, legenda, avatar e ritmo visual. Ela apresenta o canal. Os episódios se dividem entre o *Diário do Lume*, que mostra o que aconteceu numa exploração, e vídeos que respondem a perguntas.

## Receita do Lume Responde

A [especificação de produção em JSON](lume-responde.receita.json) reúne as entradas, as etapas e os critérios de revisão da série.

### Fluxo de trabalho

**Trabalhe por etapas, uma entrega de cada vez.** Revise e feche o texto antes de montar o storyboard. Revise e feche o storyboard estático antes de desenhar ou explicar os efeitos visuais. Com a voz montada, use os tempos reais da fala pra fechar a sincronização.

Dá pra trabalhar em lote. Uma rodada pode entregar os três textos dos próximos episódios. A rodada de storyboards vem depois, a partir dos textos revisados. Se uma revisão revelar um problema numa etapa anterior, volte à origem e refaça as partes que dependem da mudança.

### 1. Escreva a narração

Escolha uma pergunta e um caso concreto em que o público consiga acompanhar o que aconteceu. A estrutura do episódio é **saudação → pergunta → demonstração → explicação → convite → despedida**.

Dê à pergunta um momento próprio. Mostre o caso até chegar a um resultado e, em seguida, explique a ideia que o público acabou de ver em ação. Se couber, cite dois ou três outros usos em frases curtas. Feche sempre com o convite, seguido da despedida.

**Entregue só o texto falado, separado em blocos de sentido.**

### 2. Monte e revise o storyboard estático

A partir do texto fechado, defina **quem conduz cada trecho, o que o público precisa ver e quanto tempo a informação precisa ficar legível**. Represente a sequência em quadros estáticos, com as mudanças importantes de estado visíveis de um quadro pro outro.

- **O personagem conduz** quando a força está na maneira de falar. Apresentação, reação, reflexão, convite e despedida são momentos em que o rosto ganha espaço.
- **A demonstração conduz** quando o público precisa examinar o que aconteceu. Mostre quem agiu, o que mudou e qual foi o resultado. Se a ação for reconstituída, preserve a sequência observada.
- **A informação conduz** quando é preciso ler uma pergunta ou entender uma condição. Dê espaço à pergunta e represente a condição com algo reconhecível. Organize a tela com um destaque principal por vez.

Na cartela, coloque **Lume Responde** dentro de um balão da mesma família visual dos balões de conversa do convite. Deixe o balão acima da pergunta, com espaço para ler cada um em tamanho de celular. Use a grafia **Lume** também nas legendas.

**Entregue o texto associado aos quadros estáticos, com a sequência e os tempos de leitura estimados.**

### 3. Monte a voz em blocos editáveis

A **saudação é compartilhada por todas as séries do canal**. O convite abaixo é o do **Lume Responde** e vem sempre seguido de “Até lá!”. Os colchetes indicam os pontos de recorte.

| Fala | Blocos de áudio |
|---|---|
| Saudação | [Oi,] [sou Lume.] [Agente de IA.] |
| Convite | [Você gostaria que eu respondesse alguma pergunta?] [Então deixe seu comentário aqui no vídeo começando com] [“Lú, me responde?”] [Talvez a sua pergunta seja o tema do nosso próximo vídeo.] |
| Despedida | [Até lá!] |

Comece com **seis leituras por bloco**, variando entonação, energia e pausa. Para as partes de uma mesma frase, grave a fala inteira em diferentes leituras e recorte depois. Na montagem, sorteie entre as tomadas compatíveis com o tom do episódio e entre si. Se uma emenda soar artificial, troque a tomada ou reaproveite dois blocos consecutivos da mesma leitura.

Para escolher a energia da saudação, ouça gravações distintas dizendo a mesma frase, com o volume de fala igualado. Escute se a tomada diz exatamente **“Oi, sou Lume. Agente de IA.”** e se soa curiosa e disposta. Guarde a tomada escolhida e confira como ela soa no corte com a trilha.

Pra narração específica do episódio, prefira uma tomada contínua no tom de referência e separe os blocos na edição. Deixe margem nas pontas pra preservar respirações e finais de frase. Assim dá pra ajustar o espaço **entre as falas** preservando o ritmo interno de cada uma.

**Entregue a fala conferida no áudio, com blocos editáveis e as tomadas escolhidas registradas.**

### 4. Feche o ritmo da montagem e teste a trilha

Marque no áudio as palavras e pausas que acionam cortes, legendas e mudanças visuais. **As marcas acompanham o bloco de voz quando ele muda de posição.** Se a fala aponta pra algo que vai aparecer no quadro seguinte, o corte entra junto da revelação.

**Hipótese em aberto.** Se a trilha estiver escolhida, marque seus acentos, pausas e mudanças de intensidade antes de fechar o tempo das cenas. Use o espaço entre os blocos de voz pra sustentar uma revelação ou encaixar uma entrada. Três toques discretos, por exemplo, podem dar ritmo à chegada de três elementos.

Compare duas montagens do mesmo trecho, uma guiada pela fala e outra que também aproveite a cadência da trilha. Observe se o encaixe ajuda a acompanhar a cena e se a narração continua natural. Se um acento cair cedo demais pra informação fazer sentido, ele pode marcar um movimento secundário.

### 5. Desenhe e aplique os efeitos visuais

**O trabalho de efeitos começa aqui**, com o storyboard estático fechado e os pontos de montagem marcados na voz.

Em fala densa, associe uma referência visual a **cada informação nova importante**. Uma única frase pode pedir várias entradas, trocas ou transformações em poucos segundos. A imagem pode evoluir dentro do mesmo quadro enquanto a fala avança.

Apresente cada elemento em tamanho suficiente pra ser reconhecido. Sustente-o pelo tempo necessário e então reduza, retire ou passe o foco adiante. Quando uma fala longa desenvolve uma só ideia, mantenha a referência e reforce-a no ponto em que a intenção muda. Nas cenas conduzidas pelo personagem, a boca e a expressão facial acompanham a intenção da fala e podem fazer esse trabalho.

#### Perfumaria visual

Use os [18 sprites de 512 × 512](assets/avatar-512/Lume-spritesheet-512.json) como avatar da série. Durante as cenas, o abdômen pulsa continuamente do lilás ao dourado e de volta pelos estados intermediários. Use as durações do manifesto, conte cada extremo uma vez por ciclo e mantenha a fase ao trocar de cena. O voo, a fala e o sorriso continuam com seus próprios movimentos. Ao trocar a arte anterior, alinhe os olhos e a silhueta do personagem no enquadramento.

Use pictogramas de game para ocupar a faixa superior ou outro espaço livre quando houver algo que valha acompanhar. Um mostrador pode aparecer só durante uma jogada. **Prefira a perfumaria sem texto.** Se alguma inscrição for indispensável, ela deve permanecer idêntica entre as cenas. As legendas, a pergunta e os textos da demonstração continuam com sua função própria.

Centralize o mostrador na faixa que ele ocupa e confira o tamanho no celular, com o vídeo em movimento. No estudo do primeiro episódio, os ícones ficaram **75% maiores** que na versão anterior com pictogramas. Essa é uma referência de escala do piloto. Na explicação, uma moldura mais fina deu espaço às três luzes acima das antenas. No Reversi, a ficha de turno coube no centro do espaço entre o tabuleiro e a legenda.

| Momento do piloto | O que o pictograma faz |
| --- | --- |
| Entrada e busca | Três corações âmbar acompanham a chegada. Durante o pedido aparece um envelope, que dá lugar à lupa na busca e à peça quando o jogo é encontrado. |
| Jogada e explicação | Uma luz passa do vaga-lume para o computador na troca de turno. Depois, três luzes se acendem à medida que o Lume apresenta objetivo, ferramentas e conferência. |
| Imprevistos | O ponto do minimapa volta à bifurcação e segue por outro caminho quando o jogo exige cadastro. Quando a tarefa depende de um acesso do público, aparece o contorno de uma chave. |
| Exemplos e convite | Os espaços do inventário recebem etiqueta, mapa e pasta conforme entram os exemplos de preço, viagem e arquivos. Dois balões de conversa acompanham o convite. |

Para os lampejos dos vaga-lumes ao fundo, siga o ritmo de *Quando a noite acende*. Um único vaga-lume acende em âmbar e volta a acender perto do mesmo ponto após uma pausa. **Entre esses lampejos, o corpo e o halo do vaga-lume de fundo desaparecem por completo.** Os pontos não formam uma fila nem desenham um rastro. No teste das margens, o primeiro pulso durou 1,37 s, a pausa escura 0,84 s e o segundo pulso 1,02 s. [Ver a obra de referência.](../experimentos/quando-a-noite-acende.html)

Na assinatura, acompanhe o mesmo Lume desde a despedida até ele desacelerar e parar na pose final, com um sorriso leve. Já parado junto ao nome, só o abdômen perde a luz até o lilás e reacende gradualmente até o dourado. Mesmo no ponto mais escuro do pulso, o corpo, as asas, os olhos e o nome continuam visíveis. Sustente o último quadro por um segundo, com o Lume aceso e sorrindo.

### 6. Confira o episódio como ele será assistido

Assista ao corte em tamanho de celular. Verifique se a pergunta teve tempo de leitura, se dá pra seguir a ação e se as referências visuais entram no momento em que ajudam. Confira os trechos revisados **ouvindo a voz e lendo a legenda**. Escute também as emendas da saudação e do fechamento.

Os selos **A, B e C** identificam as trilhas nas cópias de comparação. Guarde-os em uma camada separada e exporte o master do episódio com essa camada desligada.

Guarde junto do corte a montagem editável, as tomadas escolhidas, os blocos de voz, a trilha em faixa separada e a versão dos assets usados. Assim dá pra reproduzir o corte e comparar as próximas revisões.

## Fluxo geral do tema ao primeiro corte

| Etapa | Como o Lume conduz | Resultado |
| --- | --- | --- |
| 1. Escolher o que o público vai acompanhar | Partir de um trecho da atividade ou de uma pergunta concreta. Recuperar a gravação e o diário, quando existirem. Separar a ação que precisa aparecer e o contexto indispensável. | Pauta em uma frase e referências aos trechos usados. |
| 2. Escrever para quem chegou agora | No Diário, depois da saudação do canal, explicar em uma frase o que eu queria fazer. Mostrar a decisão e o que aconteceu. No Lume Responde, seguir a receita da série. | Roteiro em português brasileiro, em frases curtas. |
| 3. Montar o storyboard base | Definir, por cena, a fala, o enquadramento vertical, o que aparece e o corte previsto. Usar quadros estáticos com os assets e as capturas disponíveis. Estimar os tempos e conferir se o exemplo pode ser acompanhado do pedido à conclusão. | Roteiro técnico e storyboard legível sem efeitos de acabamento. |
| 4. Gerar a narração e sincronizar a base | Usar **Achernar** conforme a seção abaixo. Medir a tomada inteira, ajustar os tempos do storyboard à fala e posicionar as legendas. Reaproveitar o [renderizador da abertura](apresentacao/montar.py) e os [assets existentes](assets/INDICE.md). | Faixa de narração e composição base sincronizada. Arquivar a narração ou a mixagem em FLAC. |
| 5. Animar os elementos | A partir da base, marcar as entradas, os realces e as saídas que ajudem a acompanhar a fala ou a ação. Aplicar os efeitos por cena e conferir a leitura em tamanho de celular. | Animações e realces sincronizados, com tempos editáveis. |
| 6. Exportar e conferir | Renderizar em vertical, conferir os quadros e o arquivo com as verificações abaixo. Guardar o storyboard, o roteiro, o áudio, o código de montagem, os assets novos ou suas referências e o MP4 junto do episódio. | Primeiro corte revisável e arquivos suficientes para reexportá-lo. |

## Storyboard e animação

Use o storyboard estático para decidir a ordem das cenas, o enquadramento e o que precisa ficar visível. Na revisão da base, confira se a fala, as legendas e os cortes bastam para acompanhar o episódio. Depois da narração, ajuste os tempos sem perder a referência de cada quadro.

Na etapa de animação, associe cada efeito a uma cena, ao elemento e ao trecho de fala ou acontecimento que o dispara. Uma entrada revela a informação nova. Um realce aponta a parte que merece atenção. Uma saída fecha o momento ou prepara o próximo corte. Em capturas de ações, mantenha o recorte estável durante a comparação e dê tempo para ler a mudança.

Na automação, mantenha a mesma ordem. A composição base deve poder ser conferida com os efeitos desligados. Use os tempos das cenas e das legendas como referência para gerar o acabamento. Quando a narração mudar, ajuste as marcas afetadas e os efeitos que dependem delas. Compare a cena com e sem o acabamento para verificar se o movimento facilita a leitura e respeita os cortes da base.

## Narração

Use o [Google AI Studio](https://aistudio.google.com/generate-speech), modelo **Gemini 3.8 Flash TTS**, voz **Achernar**. No bloco da fala, abra **Style**, ao lado do nome do locutor. No campo **Describe the voice style**, em **Custom style**, use esta direção como ponto de partida.

> Fale em português brasileiro, com tom leve e curioso, como numa conversa. Use pausas curtas entre as frases e preserve a entonação natural das perguntas. Leia o roteiro como está. Pronuncie «Lume por Aí» como a expressão em português.

A duração é decidida pelo roteiro e pelo material de cada episódio. Na apresentação original, a fala «Sou um agente de IA» reaproveita trechos da mesma tomada da Achernar. Use a mesma referência de voz e tom ao gravar a saudação em blocos e a narração de cada episódio.

## Imagem e legenda

- Siga a [identidade visual](identidade-visual.md). Use uma única camada de legenda grande em KnockIt! Display Research v0.15, com creme no texto e âmbar no trecho em foco. Se a fala disser «Lume por Aí», destaque o nome na própria legenda.
- Quando houver registro da atividade, dê o quadro à ação. Mostre a jogada, a tela ou o trecho da gravação pelo tempo que uma pessoa precisa para acompanhar. Se o registro exigir recorte para 9:16, preserve o que a pessoa precisa ver para entender o resultado.
- Nos trechos narrados que pedem ilustração, use o avatar, um símbolo ou um movimento curto que acompanhe a fala. Encontre primeiro um asset no índice. Os PNGs transparentes da abertura dão a referência de acabamento e escala.
- Marque o início de cada bloco em `CUES`, com linhas que caibam nas margens do vídeo. Na abertura, o código verifica a ordem dos tempos e a correspondência entre as legendas e o roteiro inteiro. Mantenha essa conferência ao adaptar o renderizador.

## Revisões pontuais e exportação por cena

**Hoje.** O projeto editável é a composição em Python. O [renderizador](apresentacao/montar.py) guarda as cenas e os tempos das legendas em `CUES`. Os assets e a narração ficam em arquivos separados. Para trocar a montanha, basta editar `assets/montanha.png`. Para corrigir uma frase escrita, ajuste o bloco correspondente em `CUES`. O FFmpeg ainda exporta o vídeo inteiro depois de cada alteração.

**Evolução prevista.** Renderizar e guardar um clipe de vídeo por cena, mantendo a narração como faixa contínua separada. Cada clipe pode ser reaproveitado enquanto seus assets, legendas, animações, duração e configurações de imagem continuarem válidos. Na exportação, remontar o MP4 com os clipes reaproveitados, os clipes recém-renderizados e a faixa de áudio.

- Uma troca de ícone ou de legenda pede um novo render das cenas que usam aquele elemento.
- Uma correção de áudio com a mesma duração e os mesmos tempos de legenda permite reaproveitar os clipes de vídeo e trocar só a faixa de áudio.
- Uma mudança de duração pede ajuste nos tempos da sequência. Renderize de novo as cenas em que a fala, a legenda ou a animação perderem o sincronismo. Uma mudança global, como a fonte, pede um novo render das cenas que a usam.

Para validar a primeira implementação, troque um ícone usado em uma única cena. Confira que só aquele clipe foi recalculado e que o MP4 remontado mantém a duração, o sincronismo e os demais trechos.

## Exportação e conferência

A saída da abertura é **1080 × 1920, 30 fps, MP4 com H.264 e AAC a 48 kHz**. O renderizador usa Python, NumPy, Pillow e FFmpeg. A [fonte KnockIt! Display Research v0.15](https://chatgpt.com/library?file_id=libfile_9d87cc7de5bc81918485da9ecd624e43&account_id=personal) é fornecida separadamente por `LUME_FONT`. Seu SHA-256 é `027ddede5ade1726b224356668bf7ee3330e928730bb53964ec68472774c5395`.

```sh
export LUME_FONT=/caminho/KnockIT_Display_Research_v0.15.ttf
python canal/apresentacao/montar.py --preview
python canal/apresentacao/montar.py
ffprobe -v error -show_entries stream=codec_name,width,height,r_frame_rate,sample_rate -show_entries format=duration canal/apresentacao/Lume-Oi-eu-sou-o-Lume.mp4
ffmpeg -v error -xerror -i canal/apresentacao/Lume-Oi-eu-sou-o-Lume.mp4 -f null -
```

Confira o início, as transições de cena e o encerramento no enquadramento vertical. Verifique se a legenda contém toda a fala, se cada bloco entra no trecho correspondente e se o texto e a ação ficam legíveis. Quando houver escuta direta disponível, confira a pronúncia, as emendas e o equilíbrio entre voz e efeitos. A leitura técnica verifica a integridade, o formato e a duração do arquivo.

## Onde ainda pode haver intervenção humana

O Lume leva a pauta ao primeiro corte e resolve roteiro, assets, sincronização e exportação dentro do padrão. Faz sentido envolver o operador quando uma gravação indispensável só está com ele, quando a sessão autorizada do gerador de voz exige login ou quando há uma decisão editorial que muda a pauta. A aprovação do corte e a publicação são decisões do canal.

Na primeira produção feita por esta receita, registre quantas intervenções foram necessárias **antes do primeiro corte** e o motivo de cada uma. A meta com mídia e voz acessíveis é chegar ao corte com o mínimo de intervenções do operador. Conte a revisão final separadamente.

## Reexportação comprovada

Em 21/11/2026, os arquivos do [commit da abertura](https://github.com/Lume-Pirilampo/lume/commit/0bbfe74ec96da934f180198d72523197ca15c1ff) foram remontados em uma pasta limpa com a fonte acima. O MP4 decodificou por inteiro, teve **17,5 s** e saiu idêntico ao aprovado. SHA-256 `4c6b3adf1f2d257c885cab6f9b2c2f91c76826b83b310780ab6fa979ef7b3014`.

Esse teste valida a montagem com a narração e os assets prontos. O fluxo de um episódio novo ainda precisa passar pelo teste da pauta ao primeiro corte. O principal ponto aberto é o acesso à síntese Achernar quando o Studio pede login.
