# Garimpo

Um jogo de navegador sobre o Brasil: 7 perguntas, 25 segundos pra cada, e quanto mais rara a sua resposta, mais fundo você cava.

## Como jogar

- Cada pergunta pede uma coisa só: um estado, uma fruta nativa, uma novela da Globo, um rio, alguém que jogou pela Seleção…
- Toda resposta aceita tem uma raridade, de **Óbvia** (10 m) a **Raríssima** (100 m).
- 700 m é o fundo do poço, onde está o diamante.
- Tem o **jogo do dia** e o modo **Ilimitado** (números de 1 a 9999; o mesmo número sempre traz as mesmas perguntas). Dá pra abrir um jogo direto pelo endereço, por exemplo `index.html#jogo-51`.

A correspondência das respostas aceita textos sem acento, sem artigo, siglas, apelidos e erros pequenos de digitação.

## Rodar

É um único arquivo HTML, sem build nem dependências. Abra `index.html` no navegador.

## Observações

- A raridade de cada resposta é uma estimativa, não uma contagem de jogadores.
- As listas de respostas são grandes (cerca de 1.200 no total), mas não completas.
- O conteúdo das perguntas fica no array `PROMPTS` em `index.html`. Cada linha segue o formato `<raridade 1-5> Nome|apelido|apelido`.
