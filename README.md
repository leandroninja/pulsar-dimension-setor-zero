# PULSAR: DIMENSÃO SETOR ZERO

> *"Quando as dimensões colapsam, apenas a coragem permanece."*

Shoot 'em up retrô com visual CRT fósforo — continuação direta de **[PULSAR: SETOR ZERO](https://github.com/leandroninja/pulsar-setor-zero)**. Uma nova batalha, uma nova dimensão, um único piloto disposto a tudo.

![Tela inicial](screenshot.png)

---

## A Saga Continua

**PULSAR: DIMENSÃO SETOR ZERO** é a continuação direta de **PULSAR: SETOR ZERO**.

Se você ainda não jogou o primeiro, a história começa lá — e o fim dela é o que trouxe tudo isso.

---

## História

### O Fim do Começo — PULSAR: SETOR ZERO

**Ano 2247.** Após meses de uma guerra brutal pelos setores corrompidos da galáxia, o piloto **L.O.M** — último sobrevivente da tropa de elite da Resistência Galáctica — finalmente alcançou o coração da invasão: o **Setor Zero**.

Diante dele estava o **Soberano Zero**, o comandante supremo por trás da destruição de nove frotas inteiras da Aliança Interestelar. Uma entidade de poder incalculável, que havia corrompido setor por setor com uma precisão fria e implacável.

A batalha foi épica. A nave PULSAR, alimentada pela energia bruta de estrelas de nêutrons, resistiu ao impossível. Tiro a tiro, bomba a bomba, L.O.M foi destruindo os sistemas do Soberano — até que o fim parecia certo.

Então aconteceu.

Percebendo que a derrota era inevitável, o Soberano Zero não recuou. Não pediu trégua. Em vez disso, num ato de desespero calculado, **ativou um dispositivo dimensional proibido** — uma arma desenvolvida em segredo nos confins do espaço desconhecido, capaz de rasgar o próprio tecido da realidade.

O dispositivo distorceu o espaço-tempo ao redor do Setor Zero. A explosão final do Soberano criou um **buraco negro artificial** que colapsou em fração de segundo, engolindo tudo numa singularidade de escuridão absoluta.

A nave PULSAR, mesmo com toda a sua tecnologia, não teve como escapar.

**L.O.M foi sugado para os confins do universo.**

---

### Uma Nova Dimensão — PULSAR: DIMENSÃO SETOR ZERO

**Ano 2247 — Coordenadas: Desconhecidas. Dimensão: Desconhecida.**

A nave PULSAR emergiu do colapso dimensional em algum lugar que não existe em nenhum mapa. Uma região do cosmos onde as leis da física se dobram, onde os setores do espaço se sobrepõem em camadas distorcidas — uma **dimensão paralela**, corrompida por ecos do Setor Zero.

L.O.M está sozinho. Sem sinal de comunicação. Sem rota de retorno.

Mas o que ele encontra nessa dimensão desconhecida vai além de qualquer ameaça que já enfrentou.

**Esta dimensão é diferente.** Aqui, civilizações evoluíram por milênios em isolamento total, desenvolvendo tecnologias que a humanidade nunca imaginou — armas que manipulam a própria gravidade, escudos feitos de matéria escura condensada, projéteis que curvam trajetória no espaço-tempo. Os inimigos que patrulham esses setores nunca perderam uma batalha. Nunca precisaram.

Até agora.

O buraco negro não criou apenas um portal — ele **acordou algo**. Nas profundezas dessa dimensão estranha, as forças que a dominam identificaram a nave PULSAR como uma anomalia a ser eliminada. Frotas com tecnologia alienígena nunca antes vista começam a convergir ao redor do único intruso desta dimensão.

Para encontrar um caminho de volta, L.O.M precisa atravessar **10 setores dimensionais** — cada um guardado por comandantes com arsenais impossíveis e poder de fogo sem precedentes — até alcançar o epicentro do colapso: a **Dimensão Setor Zero**, onde ainda pulsa o resquício de energia do dispositivo do Soberano.

É a única chance de abrir um portal de volta para casa.

**Não há reforços. Não há manual. Não há tempo.**

Só existe o pulsar da nave, a determinação de um homem que já salvou a galáxia uma vez — e a certeza de que, desta vez, o universo inteiro depende dele.

---

## Funcionalidades

- **Visual CRT retrô** — fundo escuro, scanlines, efeito fósforo
- **Parallax de estrelas** — 3 camadas em velocidades distintas, sensação real de movimento
- **Nave PULSAR** com sprites 2D realistas em camadas de cor e brilho
- **10 setores dimensionais** com paletas de cor distintas e dificuldade crescente
- **10 tipos de inimigos** com tecnologia dimensional avançada e comportamentos únicos:
  - Padrão, Rápido, Pesado (3HP)
  - Zigue-zague, Bombardeiro, Varredor, Kamikaze
  - Torre (fogo rápido), Elite, Destruidor (mini-chefe 4HP)
- **Asteroides** com 12 vértices irregulares, sombra e crateras
- **Power-ups dropeados** por inimigos:
  - **Cristal (PWR)** — aumenta o nível do disparo até 5 (spread de 1 a 5 tiros)
  - **Bomba (BOMB)** — adiciona 1 bomba (máx. 5)
- **Bomba especial** — explosão visual com shockwave, linhas radiais e bursts secundários
- **10 guardiões dimensionais (chefes)** únicos, um por setor:

| Setor | Cor | Guardião |
|-------|-----|---------|
| 1 | Verde | Cruzador Asa-Delta |
| 2 | Ciano | Caranguejo de Guerra |
| 3 | Âmbar | Canhoneira Orbital |
| 4 | Violeta | Dreadnought Fortaleza |
| 5 | Vermelho | Fantasma Dimensional |
| 6 | Branco | Cristalino Pulsante |
| 7 | Rosa | Nave-Mãe |
| 8 | Laranja | Tempestade de Fogo |
| 9 | Dourado | Titã Encouraçado |
| 10 | Final | **Soberano Zero — Echo** |

- **10 vidas** por partida + **5 continues** com tela de seleção
- **Contagem regressiva de 10s** na tela de continue — sem resposta, volta ao menu
- **Highscore** salvo em highscore.json
- **Música e sons** 100% gerados por código — sem arquivos externos
  - 7 instrumentos (lead, pad, arp, bass, kick, snare, hi-hat), BPM 160, lá menor
  - 8 efeitos sonoros com síntese PCM elaborada

---

## Controles

| Tecla | Ação |
|-------|------|
| Setas / W A S D | Mover a nave |
| Espaço / Z | Atirar |
| B / X | Lançar bomba |
| Esc | Sair |

## Sistema de Continues

Ao perder todas as 10 vidas, aparece a tela de continue com **contagem regressiva de 10 segundos**:

| Tecla | Ação |
|-------|------|
| S / Enter | Continuar do setor atual (restaura 10 vidas) |
| N / R | Recomeçar do início |
| (sem input) | Volta ao menu após 10 segundos |

Após esgotar os **5 continues**, missão encerrada — **GAME OVER**.

---

## Requisitos

```bash
pip install pygame
```

## Como jogar

```bash
python jogo.py
```

---

## Jogue também

**[PULSAR: SETOR ZERO](https://github.com/leandroninja/pulsar-setor-zero)** — o primeiro capítulo da saga. Onde tudo começou, e onde o Soberano Zero encontrou seu fim... e o nosso começo.

---

## Desenvolvido por

**Leandro Oliveira Moraes** — https://github.com/leandroninja
