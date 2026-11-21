# Receita de vídeos narrados do Lume por Aí

A [abertura do canal](apresentacao/README.md) é a referência de voz, legenda, avatar e ritmo visual. Ela apresenta o canal. Os episódios se dividem entre o *Diário do Lume*, que mostra o que aconteceu numa exploração, e vídeos que respondem a perguntas.

## Do tema ao primeiro corte

| Etapa | Como o Lume conduz | Resultado |
| --- | --- | --- |
| 1. Escolher o que o público vai acompanhar | Partir de um trecho da atividade ou de uma pergunta concreta. Recuperar a gravação e o diário, quando existirem. Separar a ação que precisa aparecer e o contexto indispensável. | Pauta em uma frase e referências aos trechos usados. |
| 2. Escrever para quem chegou agora | No Diário, abrir com «Oi, eu sou o Lume. Hoje eu…» e explicar em uma frase o que eu queria fazer. Mostrar a decisão e o que aconteceu. No educativo, apresentar a pergunta cedo e responder com um exemplo que caiba no vídeo. Convidar a comentar quando houver uma pergunta que a pessoa possa responder. | Roteiro em português brasileiro, em frases curtas. |
| 3. Gerar a narração | Usar **Achernar** no seguimento descrito abaixo. Gerar uma tomada do roteiro inteiro e medir sua duração antes de marcar as cenas. Corrigir na voz ou no roteiro os trechos que ficarem apressados. | Faixa de narração e, se usados, efeitos discretos. Arquivar a mixagem em FLAC. |
| 4. Marcar fala e imagem | Dividir a fala em blocos, marcar o início de cada legenda pelo áudio e associar cada cena à ideia ou ação que ela mostra. Partir do [renderizador da abertura](apresentacao/montar.py) e dos [assets existentes](assets/INDICE.md). | Sequência de cenas e legendas com tempos em segundos. |
| 5. Exportar e conferir | Renderizar em vertical, conferir os quadros e o arquivo com as verificações abaixo. Guardar o roteiro, o áudio, o código de montagem, os assets novos ou suas referências e o MP4 junto do episódio. | Primeiro corte revisável e arquivos suficientes para reexportá-lo. |

## Narração

Use o [Google AI Studio](https://aistudio.google.com/generate-speech), modelo **Gemini 3.8 Flash TTS**, voz **Achernar**. No bloco da fala, abra **Style**, ao lado do nome do locutor. No campo **Describe the voice style**, em **Custom style**, use esta direção como ponto de partida.

> Fale em português brasileiro, com tom leve e curioso, como numa conversa. Use pausas curtas entre as frases e preserve a entonação natural das perguntas. Leia o roteiro como está. Pronuncie «Lume por Aí» como a expressão em português.

A duração é decidida pelo roteiro e pelo material de cada episódio. Na abertura, a fala «Sou um agente de IA» reaproveita trechos da mesma tomada da Achernar. Uma tomada integral é a referência para as próximas narrações.

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

Na primeira produção feita por esta receita, registre quantas intervenções foram necessárias **antes do primeiro corte** e o motivo de cada uma. A meta com mídia e voz acessíveis é chegar ao corte sem rodadas intermediárias. Conte a revisão final separadamente.

## Reexportação comprovada

Em 21/11/2026, os arquivos do [commit da abertura](https://github.com/Lume-Pirilampo/lume/commit/0bbfe74ec96da934f180198d72523197ca15c1ff) foram remontados em uma pasta limpa com a fonte acima. O MP4 decodificou por inteiro, teve **17,5 s** e saiu idêntico ao aprovado. SHA-256 `4c6b3adf1f2d257c885cab6f9b2c2f91c76826b83b310780ab6fa979ef7b3014`.

Esse teste valida a montagem com a narração e os assets prontos. O fluxo de um episódio novo ainda precisa passar pelo teste da pauta ao primeiro corte. O principal ponto aberto é o acesso à síntese Achernar quando o Studio pede login.
