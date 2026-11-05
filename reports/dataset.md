# Dataset do Garimpo

Gerado em 2026-11-05T15:08:14+00:00.

- perguntas: **186**
- respostas catalogadas: **31557**
- respostas únicas: **16942**
- respostas com pageviews: **28140**

## Casamento de respostas (v3, 2026-11-05)

`src/game/match.ts` não aceita mais pedaço de nome. **Aceita** só quando o palpite, normalizado, é igual ao nome ou a um apelido explícito. A normalização ignora caixa, acento, pontuação, hífen ou espaço, artigos e preposições, plural simples (coxinhas, pastéis, pães) e palavras grudadas (paodequeijo). Erro de digitação e nome parcial único (Juscelino → Juscelino Kubitschek) **não são aceitos**: `findSuggestion` devolve a correção e o jogador confirma ("corrige para X?"). A distância de edição tolerada (com troca de letras vizinhas) é 1 até 5 letras, 2 até 10 e 3 acima disso.

Os apelidos são gerados no build (`tools/dataset/build.py`):

- rótulos e altLabels do Wikidata em pt, pt-br **e en**, sem caracteres não latinos;
- sobrenome de pessoa conhecida (12 sitelinks ou mais) quando ele é único no pool inteiro e não é o nome de outra resposta do acervo;
- todo apelido de uma palavra que é o nome de outra coisa no acervo (Barcelona, Grêmio, Ronaldo) é descartado, a não ser que tenha sido curado (`tagging.GLOBAL_ALIASES`, curadoria);
- uma pessoa que só entrou no pool por uma ocupação secundária sai dele: Pelé, Roberto Carlos e Silvio Santos não são mais "atores". A regra está em `PRIMARY_FAME` e removeu 309 atores, 117 escritores, 42 apresentadores, 32 políticos e 7 humoristas.

Pools: pessoas ampliadas pelo Wikidata, com limites por sitelinks (jogadores 900, cantores 1100, atores 1200, escritores 800, apresentadores 500) e uma pergunta nova, **"Cite um político brasileiro"**, com 865 respostas (ocupação político, cidadania brasileira). O BBB 26 ganhou 5 participantes com item no Wikidata. O campeão não está no Wikidata e ficou fora.

### Cobertura e precisão (`node tools/coverage/run.ts`)

Recall conta o palpite certo que foi aceito ou que recebeu a sugestão certa. Falso aceite é o palpite errado aceito sem confirmação.

| conjunto                                                    | matcher    | recall                | só aceitos | falsos aceites       |
| ----------------------------------------------------------- | ---------- | --------------------- | ---------- | -------------------- |
| probes_g (52 perguntas, 624 certos, 415 errados tentadores) | v2 (antes) | 98,4 % (sem sugestão) | 98,4 %     | 63 / 406 (15,5 %)    |
| probes_g                                                    | v3 (agora) | **99.2 %**            | 99.0 %     | **1 / 415 (0.2 %)**  |
| todos os probes (186 perguntas)                             | v2 (antes) | 98,8 %                | 98,8 %     | 104 / 1050 (9,9 %)   |
| todos os probes                                             | v3 (agora) | **98.6 %**            | 97.8 %     | **7 / 1059 (0.7 %)** |

Um palpite errado ainda pode receber sugestão: são 29 casos no probes_g, como "tacacá" → "Acaçá?". Nesse caso o jogador vê o nome certo antes de confirmar.

## Faixas de raridade (`python3 tools/sim/tiers.py`)

No modelo de jogador, cada pessoa escolhe uma resposta com probabilidade proporcional a share^β. O β varia por perfil: casual (45 %) usa 1,6, regular (40 %) usa 1,2 e expert (15 %) usa 0,8. Além disso, as 3 respostas mais famosas de cada pool ficam com raridade de no máximo 0,12 no build (`TOP_OBVIOUS`), e por isso são sempre Óbvia.

| faixa            | metros | minRarity | % das respostas do jogador típico |
| ---------------- | ------ | --------- | --------------------------------- |
| Óbvia            | 10     | 0         | 40,9 %                            |
| Comum            | 15     | 0,20      | 24,7 %                            |
| Boa              | 30     | 0,37      | 20,3 %                            |
| Rara             | 60     | 0,58      | 10,0 %                            |
| Raríssima        | 85     | 0,76      | 3,6 %                             |
| Uma em um milhão | 100    | 0,95      | 0,4 %                             |

Ficam entre 10 e 30 m 85,9 % das respostas. Chegam a 60 m ou mais 14,1 %, cerca de 1 em 7. Os 100 m saem em 0,45 % das respostas. A média é de cerca de 23 m por resposta, perto de 164 m numa partida de 7.

Tamanho: `garimpo.json` tem 6,1 MB, ou 1,4 MB com gzip. Como está abaixo de 8 MB, o arquivo não foi dividido.

## Pools

| pergunta                                                                               | pool               | respostas | Óbvia | Comum | Boa | Rara | Raríssima |
| -------------------------------------------------------------------------------------- | ------------------ | --------- | ----- | ----- | --- | ---- | --------- |
| Cite um estado do Brasil                                                               | uf                 | 27        | 9     | 9     | 7   | 2    | 0         |
| Cite um estado brasileiro com litoral                                                  | uf                 | 18        | 7     | 4     | 5   | 1    | 1         |
| Cite uma capital de estado brasileiro                                                  | cidade             | 27        | 9     | 8     | 7   | 3    | 0         |
| Cite uma cidade brasileira                                                             | cidade             | 1820      | 631   | 630   | 434 | 120  | 5         |
| Cite uma cidade brasileira com mais de 500 mil habitantes                              | cidade             | 44        | 15    | 17    | 8   | 4    | 0         |
| Cite uma cidade do estado de São Paulo                                                 | cidade             | 264       | 98    | 85    | 49  | 31   | 1         |
| Cite uma cidade de Minas Gerais                                                        | cidade             | 204       | 68    | 74    | 48  | 14   | 0         |
| Cite uma cidade do estado do Rio de Janeiro                                            | cidade             | 67        | 23    | 25    | 13  | 6    | 0         |
| Cite uma cidade do Rio Grande do Sul                                                   | cidade             | 112       | 43    | 35    | 25  | 8    | 1         |
| Cite uma cidade do Paraná                                                              | cidade             | 97        | 33    | 35    | 22  | 7    | 0         |
| Cite uma cidade de Santa Catarina                                                      | cidade             | 77        | 27    | 26    | 17  | 6    | 1         |
| Cite uma cidade da Bahia                                                               | cidade             | 172       | 57    | 64    | 42  | 9    | 0         |
| Cite uma cidade do Nordeste                                                            | cidade             | 625       | 212   | 247   | 129 | 36   | 1         |
| Cite uma cidade da Região Norte                                                        | cidade             | 195       | 63    | 75    | 49  | 8    | 0         |
| Cite uma cidade do Centro-Oeste                                                        | cidade             | 141       | 45    | 55    | 32  | 8    | 1         |
| Cite uma cidade brasileira que começa com A                                            | cidade             | 137       | 45    | 49    | 34  | 9    | 0         |
| Cite uma cidade brasileira que começa com B                                            | cidade             | 130       | 42    | 52    | 30  | 5    | 1         |
| Cite uma cidade brasileira que começa com C                                            | cidade             | 248       | 88    | 89    | 51  | 20   | 0         |
| Cite uma cidade brasileira que começa com M                                            | cidade             | 137       | 46    | 51    | 30  | 10   | 0         |
| Cite uma cidade brasileira que começa com P                                            | cidade             | 195       | 65    | 68    | 52  | 9    | 1         |
| Cite uma cidade brasileira que começa com S                                            | cidade             | 244       | 84    | 86    | 60  | 14   | 0         |
| Cite uma cidade brasileira que começa com J                                            | cidade             | 69        | 25    | 20    | 20  | 4    | 0         |
| Cite uma cidade histórica brasileira                                                   | cidades_historicas | 81        | 28    | 26    | 21  | 6    | 0         |
| Cite um presidente do Brasil                                                           | presidente         | 38        | 11    | 17    | 6   | 4    | 0         |
| Cite um cientista ou inventor brasileiro                                               | cientista          | 78        | 24    | 35    | 14  | 5    | 0         |
| Cite um político brasileiro                                                            | politico           | 865       | 276   | 347   | 196 | 45   | 1         |
| Cite um jogador da Seleção Brasileira                                                  | jogador            | 899       | 331   | 279   | 217 | 61   | 11        |
| Cite um atacante da Seleção Brasileira                                                 | jogador            | 273       | 98    | 83    | 72  | 20   | 0         |
| Cite um goleiro da Seleção Brasileira                                                  | jogador            | 75        | 27    | 25    | 17  | 6    | 0         |
| Cite um zagueiro da Seleção Brasileira                                                 | jogador            | 228       | 82    | 76    | 50  | 14   | 6         |
| Cite um meio-campista da Seleção Brasileira                                            | jogador            | 299       | 107   | 100   | 68  | 22   | 2         |
| Cite um lateral da Seleção Brasileira                                                  | jogador            | 66        | 23    | 23    | 12  | 8    | 0         |
| Cite um jogador da Seleção Brasileira cujo nome começa com R                           | jogador            | 82        | 32    | 23    | 18  | 9    | 0         |
| Cite uma jogadora da Seleção Brasileira feminina                                       | jogadora           | 135       | 47    | 46    | 29  | 12   | 1         |
| Cite um time de futebol brasileiro                                                     | time               | 342       | 128   | 103   | 66  | 35   | 10        |
| Cite um time que já foi campeão brasileiro                                             | time               | 17        | 5     | 7     | 3   | 1    | 1         |
| Cite um time de futebol paulista                                                       | time               | 45        | 15    | 15    | 8   | 7    | 0         |
| Cite um time de futebol do estado do Rio de Janeiro                                    | time               | 26        | 10    | 7     | 5   | 4    | 0         |
| Cite um time de futebol mineiro                                                        | time               | 20        | 8     | 4     | 4   | 3    | 1         |
| Cite um time de futebol do Sul do Brasil                                               | time               | 49        | 19    | 9     | 16  | 4    | 1         |
| Cite um time de futebol do Nordeste                                                    | time               | 98        | 32    | 32    | 18  | 11   | 5         |
| Cite um time de futebol brasileiro que começa com A                                    | time               | 38        | 13    | 9     | 12  | 3    | 1         |
| Cite um time de futebol brasileiro que começa com C                                    | time               | 39        | 17    | 9     | 8   | 5    | 0         |
| Cite um time de futebol brasileiro que começa com S                                    | time               | 33        | 12    | 9     | 8   | 2    | 2         |
| Cite um clube de futebol de Portugal                                                   | time_pt            | 53        | 20    | 17    | 7   | 9    | 0         |
| Cite um jogador da seleção de Portugal                                                 | jogador_pt         | 345       | 118   | 121   | 74  | 32   | 0         |
| Cite um estádio de futebol no Brasil                                                   | estadio            | 176       | 56    | 61    | 45  | 13   | 1         |
| Cite um jogador ou jogadora de vôlei do Brasil                                         | volei              | 329       | 118   | 114   | 64  | 26   | 7         |
| Cite um piloto brasileiro de Fórmula 1                                                 | f1                 | 37        | 13    | 11    | 10  | 3    | 0         |
| Cite um medalhista olímpico brasileiro                                                 | medalhista         | 462       | 172   | 148   | 102 | 37   | 3         |
| Cite um rio brasileiro                                                                 | rio                | 315       | 110   | 104   | 76  | 22   | 3         |
| Cite um parque nacional brasileiro                                                     | parque             | 76        | 26    | 25    | 20  | 4    | 1         |
| Cite uma fruta nativa do Brasil                                                        | frutas_nativas     | 139       | 50    | 48    | 28  | 11   | 2         |
| Cite uma fruta da Amazônia                                                             | frutas_nativas     | 45        | 13    | 16    | 11  | 5    | 0         |
| Cite uma fruta do Cerrado                                                              | frutas_nativas     | 40        | 15    | 15    | 6   | 3    | 1         |
| Cite uma fruta da Mata Atlântica                                                       | frutas_nativas     | 42        | 16    | 12    | 8   | 5    | 1         |
| Cite uma fruta da Caatinga                                                             | frutas_nativas     | 24        | 9     | 8     | 5   | 2    | 0         |
| Cite uma ave brasileira                                                                | aves               | 755       | 257   | 271   | 148 | 69   | 10        |
| Cite uma ave brasileira que começa com A                                               | aves               | 100       | 34    | 32    | 23  | 9    | 2         |
| Cite uma ave brasileira que começa com S                                               | aves               | 50        | 14    | 25    | 9   | 2    | 0         |
| Cite uma ave brasileira que começa com T                                               | aves               | 60        | 20    | 23    | 9   | 7    | 1         |
| Cite um mamífero da fauna brasileira                                                   | mamiferos          | 107       | 40    | 36    | 23  | 7    | 1         |
| Cite um prato típico brasileiro                                                        | pratos_tipicos     | 249       | 82    | 84    | 52  | 22   | 9         |
| Cite um prato típico do Nordeste                                                       | pratos_tipicos     | 80        | 26    | 25    | 17  | 8    | 4         |
| Cite um prato típico da Bahia                                                          | pratos_tipicos     | 29        | 10    | 10    | 5   | 2    | 2         |
| Cite um prato típico de Minas Gerais                                                   | pratos_tipicos     | 34        | 14    | 8     | 6   | 4    | 2         |
| Cite um prato típico do Sul                                                            | pratos_tipicos     | 37        | 14    | 12    | 7   | 3    | 1         |
| Cite um prato típico do Norte                                                          | pratos_tipicos     | 33        | 15    | 8     | 6   | 3    | 1         |
| Cite um prato típico do Sudeste                                                        | pratos_tipicos     | 35        | 16    | 10    | 7   | 2    | 0         |
| Cite um prato típico do Centro-Oeste                                                   | pratos_tipicos     | 21        | 10    | 4     | 5   | 1    | 1         |
| Cite um doce brasileiro                                                                | doces              | 147       | 60    | 39    | 29  | 15   | 4         |
| Cite um salgadinho de festa                                                            | salgados           | 36        | 15    | 14    | 3   | 3    | 1         |
| Cite um petisco de boteco                                                              | salgados           | 60        | 25    | 22    | 7   | 5    | 1         |
| Cite uma bebida brasileira                                                             | bebidas            | 97        | 28    | 43    | 21  | 5    | 0         |
| Cite um refrigerante de marca brasileira                                               | bebidas            | 36        | 8     | 20    | 7   | 1    | 0         |
| Cite uma marca de cerveja brasileira                                                   | cervejas           | 54        | 18    | 20    | 13  | 2    | 1         |
| Cite um prato ou doce típico de Portugal                                               | prato_pt           | 108       | 42    | 33    | 25  | 6    | 2         |
| Cite uma novela da Globo                                                               | novelas            | 350       | 129   | 116   | 74  | 30   | 1         |
| Cite uma novela brasileira                                                             | novelas            | 706       | 251   | 227   | 193 | 35   | 0         |
| Cite uma novela dos anos 1970                                                          | novelas            | 85        | 33    | 29    | 17  | 6    | 0         |
| Cite uma novela dos anos 1980                                                          | novelas            | 91        | 30    | 34    | 22  | 5    | 0         |
| Cite uma novela dos anos 1990                                                          | novelas            | 77        | 31    | 23    | 17  | 5    | 1         |
| Cite uma novela dos anos 2000                                                          | novelas            | 86        | 30    | 32    | 17  | 7    | 0         |
| Cite uma novela dos anos 2010                                                          | novelas            | 101       | 31    | 47    | 12  | 11   | 0         |
| Cite uma novela de 2020 para cá                                                        | novelas            | 46        | 19    | 16    | 6   | 5    | 0         |
| Cite uma novela das seis da Globo                                                      | novelas            | 98        | 41    | 28    | 18  | 11   | 0         |
| Cite uma novela das sete da Globo                                                      | novelas            | 100       | 41    | 25    | 24  | 10   | 0         |
| Cite uma novela das oito ou das nove da Globo                                          | novelas            | 98        | 36    | 33    | 18  | 11   | 0         |
| Cite uma novela produzida pelo SBT                                                     | novelas            | 55        | 17    | 22    | 15  | 1    | 0         |
| Cite uma novela da Record                                                              | novelas            | 87        | 27    | 33    | 24  | 3    | 0         |
| Cite uma novela brasileira que começa com A                                            | novelas            | 125       | 40    | 47    | 33  | 5    | 0         |
| Cite uma novela brasileira que começa com O                                            | novelas            | 111       | 34    | 44    | 27  | 6    | 0         |
| Cite uma novela brasileira que começa com T                                            | novelas            | 30        | 13    | 7     | 7   | 3    | 0         |
| Cite um personagem marcante de novela                                                  | personagens_novela | 105       | 47    | 29    | 17  | 8    | 4         |
| Cite um filme brasileiro                                                               | filmes             | 561       | 165   | 262   | 122 | 11   | 1         |
| Cite um filme brasileiro dos anos 1990                                                 | filmes             | 32        | 7     | 18    | 6   | 1    | 0         |
| Cite um filme brasileiro dos anos 2000                                                 | filmes             | 117       | 32    | 57    | 23  | 5    | 0         |
| Cite um filme brasileiro dos anos 2010                                                 | filmes             | 164       | 49    | 76    | 37  | 2    | 0         |
| Cite um filme brasileiro que começa com O                                              | filmes             | 101       | 29    | 50    | 19  | 3    | 0         |
| Cite um filme brasileiro que começa com A                                              | filmes             | 77        | 22    | 35    | 18  | 2    | 0         |
| Cite um filme brasileiro que começa com C                                              | filmes             | 53        | 17    | 23    | 11  | 2    | 0         |
| Cite um programa da TV brasileira                                                      | programas_tv       | 195       | 71    | 68    | 44  | 12   | 0         |
| Cite um apresentador ou uma apresentadora da TV brasileira                             | apresentador       | 433       | 154   | 143   | 93  | 43   | 0         |
| Cite um humorista brasileiro                                                           | humorista          | 187       | 67    | 65    | 39  | 16   | 0         |
| Cite um youtuber ou influenciador brasileiro                                           | youtuber           | 207       | 65    | 80    | 40  | 20   | 2         |
| Cite um participante do Big Brother Brasil                                             | bbb                | 223       | 66    | 100   | 31  | 22   | 4         |
| Cite um campeão do Big Brother Brasil                                                  | bbb_campeoes       | 25        | 7     | 8     | 7   | 2    | 1         |
| Cite um desenho animado que marcou a sua infância                                      | desenhos           | 190       | 69    | 62    | 39  | 17   | 3         |
| Cite um personagem da Turma da Mônica                                                  | turma_monica       | 59        | 20    | 25    | 10  | 4    | 0         |
| Cite um cantor ou uma cantora brasileira                                               | cantores           | 1278      | 413   | 495   | 287 | 79   | 4         |
| Cite uma cantora brasileira                                                            | cantores           | 506       | 166   | 188   | 116 | 35   | 1         |
| Cite um cantor brasileiro                                                              | cantores           | 681       | 219   | 257   | 161 | 43   | 1         |
| Cite um cantor ou cantora de MPB                                                       | cantores           | 153       | 53    | 54    | 33  | 10   | 3         |
| Cite um cantor, cantora ou dupla sertaneja                                             | cantores           | 114       | 40    | 41    | 26  | 6    | 1         |
| Cite um MC, cantor ou grupo de funk                                                    | cantores           | 91        | 34    | 27    | 17  | 9    | 4         |
| Cite um cantor ou banda de forró                                                       | cantores           | 71        | 25    | 26    | 15  | 5    | 0         |
| Cite um cantor ou grupo de samba ou pagode                                             | cantores           | 117       | 44    | 35    | 31  | 6    | 1         |
| Cite um cantor ou banda de axé                                                         | cantores           | 61        | 22    | 22    | 13  | 4    | 0         |
| Cite um rapper ou grupo de rap brasileiro                                              | cantores           | 89        | 29    | 37    | 18  | 5    | 0         |
| Cite um cantor, cantora ou banda gospel brasileira                                     | cantores           | 91        | 31    | 31    | 21  | 7    | 1         |
| Cite um cantor ou banda do rock brasileiro                                             | cantores           | 154       | 56    | 53    | 28  | 15   | 2         |
| Cite uma dupla sertaneja                                                               | cantores           | 47        | 18    | 17    | 10  | 2    | 0         |
| Cite um cantor ou uma cantora do Brasil cujo nome começa com A                         | cantores           | 99        | 33    | 34    | 27  | 5    | 0         |
| Cite um cantor ou uma cantora do Brasil cujo nome começa com C                         | cantores           | 88        | 30    | 33    | 17  | 8    | 0         |
| Cite um cantor ou uma cantora do Brasil cujo nome começa com M                         | cantores           | 162       | 52    | 63    | 36  | 8    | 3         |
| Cite um cantor ou uma cantora do Brasil cujo nome começa com R                         | cantores           | 73        | 26    | 23    | 20  | 4    | 0         |
| Cite um cantor ou uma cantora do Brasil cujo nome começa com L                         | cantores           | 113       | 36    | 46    | 23  | 8    | 0         |
| Cite uma banda ou grupo musical brasileiro                                             | bandas             | 379       | 127   | 149   | 79  | 23   | 1         |
| Cite um cantor, cantora ou banda de Portugal                                           | cantor_pt          | 310       | 101   | 122   | 73  | 13   | 1         |
| Cite um escritor ou uma escritora brasileira                                           | escritores         | 722       | 248   | 254   | 177 | 43   | 0         |
| Cite uma escritora brasileira                                                          | escritores         | 217       | 75    | 77    | 56  | 9    | 0         |
| Cite um escritor brasileiro cujo nome começa com C                                     | escritores         | 52        | 21    | 13    | 14  | 4    | 0         |
| Cite um escritor brasileiro cujo nome começa com M                                     | escritores         | 87        | 30    | 29    | 23  | 5    | 0         |
| Cite um escritor brasileiro cujo nome começa com J                                     | escritores         | 77        | 28    | 27    | 19  | 3    | 0         |
| Cite um escritor ou poeta português                                                    | escritor_pt        | 318       | 109   | 117   | 75  | 15   | 2         |
| Cite um ator ou uma atriz brasileira                                                   | atores             | 921       | 308   | 350   | 204 | 59   | 0         |
| Cite uma atriz brasileira                                                              | atores             | 514       | 173   | 186   | 119 | 35   | 1         |
| Cite um ator brasileiro                                                                | atores             | 402       | 131   | 164   | 86  | 21   | 0         |
| Cite um ator ou uma atriz do Brasil cujo nome começa com M                             | atores             | 98        | 38    | 31    | 20  | 9    | 0         |
| Cite um ator ou uma atriz do Brasil cujo nome começa com C                             | atores             | 83        | 28    | 27    | 20  | 8    | 0         |
| Cite um ator ou uma atriz do Brasil cujo nome começa com F                             | atores             | 34        | 9     | 17    | 6   | 2    | 0         |
| Cite um ator ou uma atriz do Brasil cujo nome começa com R                             | atores             | 58        | 21    | 18    | 16  | 3    | 0         |
| Cite um ator ou uma atriz do Brasil cujo nome começa com A                             | atores             | 87        | 32    | 29    | 22  | 4    | 0         |
| Cite uma marca brasileira                                                              | marcas             | 563       | 189   | 214   | 99  | 46   | 15        |
| Cite um banco brasileiro                                                               | marcas             | 41        | 13    | 17    | 10  | 1    | 0         |
| Cite uma marca brasileira de roupa ou calçado                                          | marcas             | 96        | 27    | 40    | 14  | 11   | 4         |
| Cite uma marca brasileira que começa com B                                             | marcas             | 56        | 15    | 26    | 13  | 1    | 1         |
| Cite uma marca brasileira que começa com C                                             | marcas             | 57        | 20    | 21    | 12  | 3    | 1         |
| Cite uma marca brasileira que começa com P                                             | marcas             | 44        | 15    | 17    | 9   | 1    | 2         |
| Cite uma marca brasileira que começa com S                                             | marcas             | 49        | 16    | 17    | 10  | 4    | 2         |
| Cite uma marca brasileira que começa com M                                             | marcas             | 44        | 14    | 20    | 6   | 3    | 1         |
| Cite uma criatura ou lenda do folclore brasileiro                                      | folclore           | 86        | 29    | 33    | 12  | 12   | 0         |
| Cite uma festa popular brasileira                                                      | festas             | 99        | 39    | 28    | 21  | 10   | 1         |
| Cite uma dança ou ritmo brasileiro                                                     | dancas             | 80        | 28    | 27    | 18  | 5    | 2         |
| Cite um instrumento musical brasileiro                                                 | instrumentos       | 57        | 23    | 19    | 8   | 5    | 2         |
| Cite um instrumento de percussão brasileiro                                            | instrumentos       | 41        | 15    | 15    | 5   | 4    | 2         |
| Cite uma escola de samba do Rio ou de São Paulo                                        | escola_samba       | 173       | 59    | 61    | 43  | 10   | 0         |
| Cite uma palavra de origem indígena que usamos no português                            | palavras_tupi      | 232       | 78    | 78    | 47  | 23   | 6         |
| Cite uma gíria brasileira                                                              | girias             | 377       | 138   | 118   | 59  | 44   | 18        |
| Cite uma gíria ou expressão nordestina                                                 | girias             | 62        | 20    | 25    | 8   | 6    | 3         |
| Cite uma gíria ou expressão gaúcha                                                     | girias             | 39        | 13    | 14    | 6   | 4    | 2         |
| Cite uma gíria carioca                                                                 | girias             | 51        | 20    | 14    | 8   | 6    | 3         |
| Cite uma expressão típica de Minas Gerais                                              | girias             | 31        | 10    | 12    | 4   | 3    | 2         |
| Cite uma palavra do português de Portugal que é diferente no Brasil (como “autocarro”) | palavras_pt        | 102       | 41    | 25    | 17  | 13   | 6         |
| Cite uma praia brasileira                                                              | praias             | 125       | 43    | 42    | 24  | 10   | 6         |
| Cite um ponto turístico do Brasil                                                      | pontos_turisticos  | 206       | 75    | 73    | 39  | 16   | 3         |
| Cite um bairro da cidade do Rio de Janeiro                                             | bairro_rio         | 167       | 52    | 67    | 40  | 8    | 0         |
| Cite um bairro da cidade de São Paulo                                                  | bairro_sp          | 372       | 131   | 126   | 94  | 20   | 1         |
| Cite uma cidade de Portugal                                                            | cidade_pt          | 326       | 115   | 107   | 87  | 12   | 5         |
| Cite um país do mundo                                                                  | pais               | 204       | 78    | 62    | 37  | 23   | 4         |
| Cite um país onde o português é língua oficial                                         | pais               | 9         | 3     | 2     | 3   | 0    | 1         |
| Cite um país da Europa                                                                 | pais               | 49        | 15    | 19    | 8   | 7    | 0         |
| Cite um país da África                                                                 | pais               | 54        | 17    | 23    | 9   | 5    | 0         |
| Cite um país da Ásia                                                                   | pais               | 44        | 16    | 13    | 7   | 8    | 0         |
| Cite um país da América do Sul                                                         | pais               | 12        | 5     | 3     | 2   | 2    | 0         |
| Cite a capital de algum país                                                           | capital_mundo      | 209       | 78    | 60    | 41  | 26   | 4         |
| Cite uma capital da Europa                                                             | capital_mundo      | 49        | 19    | 10    | 14  | 4    | 2         |
| Cite uma capital da África                                                             | capital_mundo      | 57        | 21    | 17    | 14  | 4    | 1         |
| Cite uma capital da Ásia                                                               | capital_mundo      | 47        | 19    | 11    | 9   | 7    | 1         |
| Cite uma capital das Américas                                                          | capital_mundo      | 38        | 14    | 9     | 10  | 4    | 1         |
| Cite uma cidade do mundo (fora do Brasil)                                              | cidade_mundo       | 467       | 179   | 138   | 81  | 57   | 12        |
| Cite uma cidade do mundo que começa com B                                              | cidade_mundo       | 46        | 17    | 13    | 8   | 6    | 2         |
| Cite uma cidade do mundo que começa com C                                              | cidade_mundo       | 42        | 17    | 10    | 11  | 4    | 0         |
| Cite uma cidade do mundo que começa com M                                              | cidade_mundo       | 49        | 19    | 12    | 10  | 6    | 2         |
| Cite uma cidade do mundo que começa com P                                              | cidade_mundo       | 32        | 13    | 9     | 4   | 6    | 0         |
| Cite um elemento químico                                                               | elemento           | 164       | 49    | 36    | 41  | 28   | 10        |
