# Anuário Brasileiro de Resíduos Municipais — distância até a destinação final

Código que constrói as variáveis `E3_DIST_ATERRO_KM` e `E3_TEMPO_ATERRO_MIN` do Anuário Brasileiro de Resíduos Municipais, edição 2026.

As duas medem o mesmo trajeto: da sede do município até a unidade que recebe seus resíduos sólidos urbanos, de carro, em condições normais de trânsito. Uma em quilômetros, outra em minutos.

André Augusto Santos - Mestrado em Finanças, FGV EAESP

---

## Bases necessárias

As bases são públicas e **não acompanham o repositório**: são pesadas e mudam de edição para edição, então cada pessoa baixa a sua na fonte original. Depois de baixar, informe onde elas estão no arquivo `config.py`.

| Base | O que é usado | Onde baixar |
|---|---|---|
| SINISA Resíduos 2023 | formulários Manejo e Infraestrutura | Ministério das Cidades, módulo Resíduos Sólidos, ano-base 2023 |
| IBGE — Localidades do Brasil 2022 | arquivo `BR_localidades_2022` | `geoftp.ibge.gov.br/organizacao_do_territorio/estrutura_territorial/localidades/Localidades_do_Brasil/2022/` |
| Coordenadas municipais de referência | tabela com código IBGE, latitude e longitude | `github.com/kelvins/municipios-brasileiros` |

Do SINISA são lidos quatro arquivos, com os nomes originais: `Manejo`,
`Infraestrutura_Destinacao_Final`,
`Infraestrutura_Unidades_de_Processamento_e_Tratamento` e
`Infraestrutura_Unidades_de_Transbordo`.

A terceira base **não entra no cálculo da distância**. Ela serve para conferir a qualidade dos dados. O campo de coordenada do formulário do SINISA já vem preenchido com o ponto do município, e quem não trocou pela posição real da instalação acabou registrando o centro da cidade no lugar do aterro. Comparar a coordenada declarada com essa tabela mostra quais registros ficaram assim: 2.514 das 6.171 unidades cadastradas coincidem com ela até a quarta casa decimal, contra 551 quando a comparação usa o arquivo do IBGE. A origem do trajeto é sempre o IBGE.

A lista dos 2.000 municípios do Anuário acompanha o repositório, em
`dados_referencia/municipios_anuario_2026.csv`.

---

## Como executar

Instale as bibliotecas, uma única vez:

```bash
pip install -r requirements.txt
```

Abra o `config.py` e ajuste os caminhos das bases. Crie um arquivo
`chave_google.txt` contendo apenas a chave da Google Routes API, sem mais nada.
O `.gitignore` impede que esse arquivo vá para o repositório.

Rode os quatro scripts na ordem:

```bash
python 01_montar_pares.py      # monta os pares origem-destino
python 02_calcular_rotas.py    # consulta a Routes API
python 03_gerar_auditoria.py   # separa o que precisa de conferência
python 04_consolidar.py        # produz a série final
```

Entre o terceiro e o quarto passo há trabalho humano: abrir o arquivo
`saida/03_auditoria.csv` e preencher as colunas em maiúsculas para os registros das prioridades 1 e 2.

O segundo passo salva o andamento a cada 25 municípios e ignora o que já
calculou. Se cair no meio, é só rodar de novo: ele continua de onde parou, sem repetir consulta.

---

## Como as variáveis são construídas

**Escolha da unidade de destino.** Cada município declara várias rotas de coleta. Adota-se a de maior massa anual (`GTR1008`), e a unidade dessa rota (`GTR1013`) passa a ser o ponto de chegada.

**De onde vem cada coordenada.** O destino vem dos formulários de Infraestrutura do SINISA: `GTR3203` e `GTR3204` na Disposição Final, `GTR3103` e `GTR3104` no Processamento e Tratamento, `GTR3002` e `GTR3003` no Transbordo. Esse campo é preenchido pelo município que abriga a instalação, e não pelo que gera o resíduo. A origem vem do arquivo do IBGE, lida do ponto desenhado no mapa e não dos campos `LAT_LOCALI` e `LONG_LOCAL`, que trazem no máximo quatro casas
decimais.

**Cálculo do trajeto.** Google Routes API, método `computeRoutes`, modo `DRIVE`, com `routingPreference` igual a `TRAFFIC_UNAWARE`. Esse parâmetro usa as velocidades típicas de cada via e ignora o trânsito do momento, de modo que o resultado não muda conforme a hora da consulta.

**Quem fica de fora.** Municípios sem rota declarada, com rota que não identifica a unidade, com unidade fora do cadastro, ou cuja coordenada declarada apenas repete o ponto do município que abriga a instalação.

**Conferência.** Os registros que apresentam algum sinal de problema são
conferidos um a um. Entre os que não apresentam sinal nenhum, 50 são sorteados, para estimar quanto erro ainda resta no grupo que não será conferido. O sorteio usa um número de partida fixo sobre a lista ordenada por código IBGE, então qualquer pessoa refaz e chega aos mesmos municípios.

---

## Resultado da execução de referência

| | |
|---|---|
| Municípios na matriz | 2.000 |
| Pares construídos | 1.067 |
| Sem dado no SINISA | 933 |
| Registros com valor | 1.052 |
| Conferidos individualmente | 309 |
| Coordenadas corrigidas na conferência | 43 |
| Erro estimado no grupo sorteado | 4,0% (entre 1,1% e 13,5%) |

---

## Limitações

**Cobertura.** As variáveis cobrem 52,6% da matriz, e o que falta não falta ao acaso: municípios que preenchem mal o SINISA tendem a ser os de gestão mais frágil, que é justamente o que as variáveis pretendem medir. 

**Qualidade do cadastro.** O SINISA é preenchido pelos próprios municípios, sem conferência do sistema, e apresenta três tipos de falha identificados neste trabalho: a coordenada que ficou com o valor padrão da cidade, a coordenada em lugar errado, e a declaração do endereço administrativo do responsável (a secretaria, a cooperativa, o galpão ou o horto municipal) no lugar da posição da unidade.

---

## Licença

MIT. Ver `LICENSE`.

