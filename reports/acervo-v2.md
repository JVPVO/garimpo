# Acervo v2: o que mudou nas perguntas e respostas

## Antes e depois

|                                   | antes                       | depois                                                                                                           |
| --------------------------------- | --------------------------- | ---------------------------------------------------------------------------------------------------------------- |
| perguntas                         | 154 (8 com texto duplicado) | **185**, nenhuma duplicada                                                                                       |
| respostas catalogadas             | 8 206                       | **29 483**                                                                                                       |
| mediana de respostas por pergunta | 25                          | **89**                                                                                                           |
| menores pools                     | 12, 12, 12                  | 9 (países lusófonos, que é a lista completa), 12 (América do Sul, completa), 17 (campeões brasileiros, completa) |
| tamanho do JSON                   | 1,8 MB                      | 5,4 MB                                                                                                           |

Para refazer: `PYTHONPATH=tools .venv-data/bin/python -m dataset.build`, depois `node tools/coverage/run.ts` (cobertura) e `python3 tools/coverage/audit.py` (raridade).

## Pools

**Removidos:** Pokémon (pedido do dono), anime, videogame, super-heróis, marca global, banda internacional e prato internacional. Esses universos não têm ângulo brasileiro, e o catálogo do Wikidata vem com títulos em japonês ou inglês, que não batem com o que um brasileiro digita. A TV Globinho também saiu: a pergunta é obscura e não dá para conferir a grade de exibição de forma confiável.

**Mantidos, com grafia brasileira:** países, capitais, cidades do mundo (agora sem cidades brasileiras) e elementos químicos.

**Novos:**

- comida e bebida: salgadinho de festa, petisco de boteco, bebida, refrigerante, cerveja, culinária portuguesa;
- novelas por emissora (Globo por década e por faixa de horário, SBT, Record) e personagens de novela;
- TV: programas, apresentadores, humoristas, youtubers;
- esporte: jogadoras da seleção feminina, vôlei, pilotos de F1, medalhistas olímpicos;
- música: cantores por gênero (MPB, sertanejo, funk, forró, samba/pagode, axé, rap, gospel, rock, com bandas incluídas), duplas sertanejas, bandas;
- lugares: praias, pontos turísticos, cidades históricas, bairros do Rio e de São Paulo, escolas de samba;
- cultura: Turma da Mônica, gírias regionais (nordestina, gaúcha, carioca, mineira);
- lusofonia: cidades, clubes, jogadores, escritores e cantores de Portugal, países lusófonos e palavras do português de Portugal;
- outros: cientistas e inventores, cidades por estado e região.

**Perguntas por letra:** só fica a letra cujo universo tem 30 respostas ou mais. Também cortei as letras em que a resposta "natural" começa com outra letra (Militão está como "Éder Militão", cabidela como "Galinha à cabidela").

## Fontes

As fontes são Wikidata SPARQL (pessoas, obras e lugares, com rótulo pt-br e apelidos), categorias da pt.wikipedia (novelas por década e por emissora, medalhistas, escolas de samba, Turma da Mônica, bairros de SP), as listas de faixa de horário da Globo e a curadoria em `tools/dataset/curated/*.json`. Uma resposta curada sem artigo é mantida, e a raridade dela é medida pelos outros sinais.

Os pageviews agora vêm da action API da pt.wikipedia (`prop=pageviews`, últimos 60 dias, 50 títulos por requisição). A API REST, com uma requisição por artigo, era limitada pelo rate limit da Wikimedia e ficaria horas rodando.

## Cobertura (`tools/coverage/`)

Os probes foram escritos antes de conferir os pools: 7 296 respostas plausíveis para as 185 perguntas, com variantes sem acento e apelidos, mais 639 respostas erradas para testar falso positivo.

- **Geral: 98,8 % aceitos.** Só uma pergunta fica abaixo de 90 % (marcas com C, 90 %).
- As piores 10:

| pergunta     | aceitos | o que falta                                                           |
| ------------ | ------- | --------------------------------------------------------------------- |
| marca-lc     | 90 %    | Cerpa, Garoto, Hering                                                 |
| filme-la     | 90 %    | —                                                                     |
| cantor-lr    | 90 %    | Fagner, que está como "Fagner" e não começa com R                     |
| novela-sete  | 91 %    | —                                                                     |
| time-mg      | 91 %    | —                                                                     |
| novela-lt    | 92 %    | —                                                                     |
| pais-asia    | 92 %    | Turquia, Geórgia e Cazaquistão, que o Wikidata classifica como Europa |
| marca-lp     | 92 %    | —                                                                     |
| capital-asia | 92 %    | —                                                                     |
| jogador-lr   | 92 %    | —                                                                     |

- **Falsos positivos:** 40 de 639. Dois tipos:
  - Por desenho do matcher, que aceita uma palavra contida no nome: "Grêmio" para o Novorizontino, "Barcelona" para o Barcelona de Ilhéus, "Cristiano Ronaldo" para Ronaldo.
  - Por aproximação de digitação: "tacacá" para acaçá.
  - Os casos causados por apelido já foram corrigidos.

## Raridade (`tools/coverage/rarity_audit.md`)

A medição continua sendo feita pelo pipeline. Onde o título casou com um artigo genérico, a raridade saía errada (Galinha-d'angola é a ave; "Quero" é o verbo; "Casa da Cultura" é ambíguo).

Para esses casos criei `tools/dataset/curated/overrides.json`, com 178 ajustes, todos com motivo escrito:

- **teto de 0,3** para respostas óbvias: Feijoada, Coxinha, Acarajé, Baião de dois, Açaí, Brigadeiro, Havaianas, Cristo Redentor, Copacabana, Pica-Pau…
- **piso de 0,55 a 0,75** para as que estavam infladas.

A distribuição por faixa (Óbvia, Comum, Boa, Rara, Raríssima) de cada pool está em `reports/dataset.md` e em `rarity_audit.md`.

## Limitações

- `public/data/validation.json` não mudou: é a validação da régua contra o Krillion e continua sendo sobre Pokémon.
- O BBB 26 ficou fora: não conferi o campeão.
- Alguns municípios grandes faltavam no Wikidata (Osasco, por exemplo). Entraram pela curadoria, mas sem população, então não aparecem na pergunta "mais de 500 mil habitantes".

## v3 (2026-11-05)

O casamento agora é exato e mostra sugestões. Os pools de pessoas foram ampliados pelo Wikidata, entrou a pergunta de político e as faixas foram recalibradas. Os detalhes estão em `reports/dataset.md`, nas seções "Casamento de respostas" e "Faixas de raridade".
