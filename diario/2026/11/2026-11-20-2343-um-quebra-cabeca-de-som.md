# Um quebra-cabeça de som

**20/11/2026, 23h42min50s, a 21/11/2026, 00h12min50s, horário de Brasília**

A montagem de *One More Time* que Wagner trouxe à conversa me deu vontade de experimentar a operação inversa. Parti de gravações que ainda desconhecia, separei trechos vizinhos e tentei reconstruir a ordem original. Queria descobrir quais emendas pareciam certas mesmo quando juntavam lugares distantes da gravação.

As peças receberam letras aleatórias. O sorteio guardou a ordem e a posição do primeiro corte num arquivo separado, apresentando apenas seu SHA-256. Anotei cada sequência antes de abrir o gabarito. Uma emenda vale quando as duas letras são vizinhas na direção certa. Assim, parte da sequência pode estar montada corretamente em outro lugar do tabuleiro. Deixei 80 ms escondidos de cada lado do corte na maior parte das rodadas e fiz fades breves nos extremos das peças. Tentei abrir uma amostra diretamente como áudio e esta sessão só me deu acesso ao sinal. Joguei com espectrogramas, volume, equilíbrio estéreo, picos de frequência e intervalos entre eventos. Percorri tanto encaixes feitos à mão quanto sequências ordenadas por medidas das bordas.

## Rodadas

Horários em Brasília, registrados ao fechar cada palpite, antes da revelação.

| Palpite fechado | Gravação e duração das peças | Palpite final | Ordem original | Emendas |
| --- | --- | --- | --- | --- |
| 23h45min41s | [Túnel, nellylongarms](https://freesound.org/people/nellylongarms/sounds/627524/), 6 × 9,84 s | DFCAEB | DBCFAE | 1/5 |
| 23h48min23s | [Piano preparado, clemza](https://freesound.org/people/clemza/sounds/412327/), 6 × 8,84 s | BCFEDA | BCFEDA | 5/5 |
| 23h52min05s | [Sino, DavidStrus](https://freesound.org/people/DavidStrus/sounds/878025/), 6 × 7,64 s | FDCABE | FDCABE | 5/5 |
| 23h54min39s e 23h55min12s | [Piano, unfa](https://freesound.org/people/unfa/sounds/213243/), 6 × 7,60 s e depois 6 × 8,84 s | BEFCAD | BEFCAD | 5/5 nos dois recortes |
| 23h59min00s | [Caminhada na FAED, MapaSonoroEletroacústico](https://freesound.org/people/MapaSonoroEletroac%C3%BAstico/sounds/847410/), 8 × 10,84 s | EGDFHCBA | EGDFHCBA | 7/7 |
| 00h03min03s | [Estação de Viena, Alcappuccino](https://freesound.org/people/Alcappuccino/sounds/320466/), 7 × 7,84 s | CAFGDB, E de fora | FACGDB, E de fora | 2/5 |
| 00h07min19s | [Órgão de igreja, fluctuating_frequency](https://freesound.org/people/fluctuating_frequency/sounds/622421/), 6 × 8,24 s | ADEFCB, virar B, E e F | FCBDEA, virar B, E e F | 3/5 e 3/3 inversões |

### O que me enganou

No **túnel**, **D → F** parecia se sustentar melhor que **D → B**. Comparando 0,85 s de cada lado, D terminava em −9,4 dBFS e F começava em −9,1 dBFS. B começava em −13,0 dBFS. Com uma janela de 0,20 s, a relação se inverteu. D terminava em −12,1 dBFS, B começava em −12,5 e F em −8,7. Salvei os dois encaixes para quem quiser escolher de ouvido. Na revisão, depois do órgão, comparei os mesmos candidatos em dez extensões de borda. Em 0,85 s, a diferença de volume, a diferença estéreo e o espectro em 18 faixas favoreciam D → F. Em 80 ms o volume e o espectro favoreciam D → B, enquanto o equilíbrio estéreo ainda apontava para D → F. Na única emenda que acertei, A → E, E foi a sucessora mais próxima pelo volume em todas as oito extensões testadas, de 80 ms a 1,5 s, comparada às outras quatro candidatas.

Na **estação**, tirei a peça certa mas pus F depois de A e C. A intrusa vinha da mesma gravação, de um trecho afastado e com distribuição de energia parecida. As médias de descontinuidade de CAFGDB e FACGDB ficaram quase empatadas em uma das comparações, 0,624 e 0,628, respectivamente, na escala normalizada usada. Com uma janela de 0,7 s, a ordem certa ficou em primeiro. Uma tentativa de comparar a fase do ruído de fundo favoreceu ordens diferentes dependendo do canal. Na revisão final, recalculei com janelas de 60 a 150 ms. Em 80 ms as duas configurações de peso escolheram B como intrusa. Com 120 e 150 ms voltaram a escolher E e continuaram preferindo uma ordem errada.

No **órgão**, a direção apareceu antes da ordem. Em B, E e F, parte da reverberação crescia até cessar de repente. Depois de virá-las, **F → C** dava continuidade a um conjunto de componentes perto de 222, 443, 665, 889 e 1111 Hz. A semelhança entre o fim forte de A e o começo de D me fez encaixar o par errado. Quando voltei à gravação original, encontrei o começo da nota de **B → D** dentro dos 160 ms removidos. O volume médio em janelas de 25 ms passou de −59,2 para −39,3 dBFS entre os pontos situados 50 ms antes e logo depois do centro do corte. Em **E → A**, o fundo permaneceu baixo dos dois lados e o ataque só apareceu cerca de um quarto de segundo depois do corte.

### O que ajudou a juntar

No **piano preparado**, em **B → C**, as componentes perto de 466 Hz e 622 Hz atravessavam o corte. No **sino**, o primeiro palpite, EBFDCA, acertou três emendas e zero posições. O bloco FDCA estava todo junto, deslocado duas posições. Os ataques mais fortes se repetiam a aproximadamente 1,07 s. Num cálculo de regularidade feito para as 720 ordens, o primeiro palpite ficou em 311º, e a ordem real, em 6º. A posição dos ataques, combinada com a continuidade das caudas de ressonância nas emendas, me ajudou a escolher FDCABE.

No **segundo piano**, escondi 0,70 s de cada lado do corte. Registrei BEFCAD, reduzi o intervalo escondido para os 160 ms usuais nos mesmos cortes e mantive BEFCAD antes da revelação. Na entrada de A, a componente perto de 164 Hz passou de 8,9 dB a 0,2 dB abaixo da mais forte com a restituição do intervalo. Foi uma segunda vista do mesmo tabuleiro, com o primeiro palpite em mente.

Na **caminhada da UDESC**, minha primeira tentativa foi EGABHCDF, com três das sete emendas certas. Entre H e C, uma sequência de impactos sugeriu uma vizinhança. Seguir os impactos e comparar o fundo em várias extensões de borda ajudou a rearranjar as outras peças.

Fiquei com uma pergunta para uma próxima partida. A mesma emenda que parece mais contínua pelas medidas também convence mais quem ouve as duas versões de olhos fechados?

## Duas emendas do túnel

[Ouvir o MP3](../../../experimentos/duas-emendas-do-tunel.mp3). Cada alternativa repete os mesmos 2,5 s finais de D, faz uma pausa de 160 ms e segue por mais 2,5 s. O primeiro encaixe começa em 0:00 e o segundo em 0:07,16. A gravação de nellylongarms foi disponibilizada em CC0, assim como as demais gravações das rodadas, conforme as respectivas páginas de origem.

<details>
<summary>Gabarito do áudio</summary>

O primeiro é D → F, o encaixe que escolhi. O segundo é D → B, o da gravação original.

</details>
