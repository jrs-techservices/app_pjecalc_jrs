# Valores aceitos pelo PJe-Calc — e o que o `.json` de lançamentos aceita

**Para:** desenvolvimento do SAP · **De:** time da automação do PJe-Calc · **Data:** 30/09/2026 (atualizado em 06/10/2026: referência campo a campo e bloco `arquivos`)

Extraído do **próprio PJe-Calc** desta máquina (versão em uso, `localhost:9257`), de um cálculo de rascunho
criado e excluído em 30/09/2026. É o que aparece nas listas e nos botões de cada tela. O catálogo completo, com os
5.569 municípios por UF, está em `servico/catalogo_pjecalc.json`.

## 1. O que o serviço faz com o `.json` (contrato `lancamentos-pjecalc/1`)

- **Campo que não reconhecemos:** ignorado, e listado em `lancamentos_resumo.ignorados` com o motivo. Não recusa.
- **Valor fora da lista num campo que reconhecemos:** o pedido é **recusado na porta** (`400 lancamentos_invalido`), com
  `erros: [{campo, valor, mensagem, aceitos}]`.
- **Contrato de outra versão:** recusado (`400 lancamentos_invalido`).
- **Sem planilha base:** o `.json` precisa trazer reclamante, reclamado, UF, município, admissão e ajuizamento; senão
  `400 lancamentos_incompleto` com `faltando`. Hoje o município/UF vêm da `vara` (`…DO RECIFE-PE`) quando não há
  `telas.dados-do-calculo.municipio`/`uf` — mandem os dois para não depender disso.
- **Com planilha base:** a planilha manda no que carrega; o `.json` preenche o que ela deixou vazio. Honorários, multas
  e custas são **blocos inteiros**: se a planilha já traz a família, ela prevalece inteira; se não, a do `.json` entra
  inteira. Tudo o que prevaleceu vai para o log da execução.

## 2. Códigos aceitos nos blocos `dadosDoCalculo`, `fgts`, `honorarios`, `multas`, `custas`

Cada campo aceita o **código** (coluna da esquerda) ou o **texto da tela** (da direita) — exceto `tipoDeDevedor` e
`tipoCobrancaReclamante`, que aceitam **só o código**.

### `fgts.destino`

| código | na tela |
|---|---|
| `RECOLHER` | Recolher |
| `PAGAR` | Pagar |

### `custas.tipoDeCustasDeConhecimentoDoReclamado`

| código | na tela |
|---|---|
| `NAO_SE_APLICA` | Não se Aplica |
| `CALCULADA_2_POR_CENTO` | Calculada 2% |
| `INFORMADA` | Informada |

### `honorarios[].tipoHonorario`

| código | na tela |
|---|---|
| `ADVOCATICIOS` | Honorários Advocatícios |
| `ASSISTENCIAIS` | Honorários Assistenciais |
| `CONTRATUAIS` | Honorários Contratuais |
| `PERICIAIS_CONTADOR` | Honorários Periciais - Contador |
| `PERICIAIS_DOCUMENTOSCOPIO` | Honorários Periciais - Documentoscópio |
| `PERICIAIS_ENGENHEIRO` | Honorários Periciais - Engenheiro |
| `PERICIAIS_INTERPRETE` | Honorários Periciais - Intérprete |
| `PERICIAIS_MEDICO` | Honorários Periciais - Médico |
| `PERICIAIS_OUTROS` | Honorários Periciais - Outros |
| `SUCUMBENCIAIS` | Honorários de Sucumbência |
| `LEILOEIRO` | Leiloeiro |

### `honorarios[].tipoDeDevedor`

| código | na tela |
|---|---|
| `RECLAMADO` | Reclamado |
| `RECLAMANTE` | Reclamante |

### `honorarios[].tipoCobrancaReclamante` · `multas[].tipoCobrancaReclamante`

| código | na tela |
|---|---|
| `COBRAR` | Cobrar |
| `DESCONTAR / DESCONTAR_CREDITO` | Descontar |

### `multas[].tipoCredorDevedor`

| código | na tela |
|---|---|
| `RECLAMANTE_RECLAMADO` | Reclamante e Reclamado |
| `RECLAMADO_RECLAMANTE` | Reclamado e Reclamante |
| `TERCEIRO_RECLAMANTE` | Terceiro e Reclamante |
| `TERCEIRO_RECLAMADO` | Terceiro e Reclamado |

### Casos atendidos a partir do retorno de 30/09

| caso | campos lidos | observação |
|---|---|---|
| honorário `CALCULADO` | `aliquota` (fração) · `baseParaApuracao` (código ou texto) · `tipoCobrancaReclamante` | só **Advocatícios, Assistenciais, Contratuais e Leiloeiro**; tipos periciais e sucumbência calculados são recusados. `outroIndiceDeCorrecao` preenchido é recusado (sai o índice trabalhista) |
| multa `CALCULADO` | `aliquotaMulta` (fração) · `tipoBaseMulta` (código ou texto) | juros em multa calculada: recusado |
| multa com terceiro | `tipoCredorDevedor` `TERCEIRO_E_RECLAMANTE` \| `TERCEIRO_E_RECLAMADO` · `nomeTerceiro` | `nomeTerceiro` obrigatório |
| custas `INFORMADA` | `valorConhecimentoDoReclamado` · `dataVencimentoConhecimentoDoReclamado` | |
| custas recolhidas | `dataVencimento` · `valor` | sem data, não é lançada (aviso) |

**Alíquotas desses blocos em fração** (`0.05` = 5%); valor fora de (0, 1] é recusado. Os códigos de base aceitos são o texto
da lista (§3) ou a mesma frase em código: `BRUTO`, `BRUTO_MENOS_CONTRIBUICAO_SOCIAL`, `PRINCIPAL_MENOS_CONTRIBUICAO_SOCIAL`…

### `telas.dados-do-calculo`: `uf` (e não `estado`)

Lemos **`uf`** (sigla) e **`municipio`**. `estado` ainda é aceito como sinônimo, mas pode sair: se vierem os dois
com valores diferentes, o pedido é recusado.

### `telas.dados-do-calculo`: parâmetros que antes ficavam no padrão do PJe-Calc

Quando um destes campos não vem, a tela fica como o PJe-Calc abre (o log mostra
`[não informado: mantido o padrão do PJe-Calc]`). Por isso, mandem sempre os campos abaixo:

| Campo no `.json` | Tipo | Exemplo |
|---|---|---|
| `prescricao_quinquenal` | `true`/`false` | `true` |
| `prescricao_fgts` | `true`/`false` | `false` |
| `regime` | texto da lista (§3) | `"Tempo Integral"` |
| `maior_remuneracao` · `ultima_remuneracao` | número | `2500.00` |
| `prazo_aviso_previo` | `Não apurar` · `Calculado` · `Informado` | `"Informado"` |
| `dias_aviso_previo` | inteiro, **obrigatório com `Informado`** (sem ele o PJe-Calc recusa o formulário: "Campo obrigatório: Quantidade") | `36` |
| `projetar_aviso_indenizado` | `true`/`false` | `true` |
| `limitar_avos` | `true`/`false` | `false` |
| `zerar_valor_negativo` | `true`/`false` | `false` |
| `feriados_estaduais` · `feriados_municipais` | `true`/`false` | `true` |
| `ponto_facultativo_carnaval` · `ponto_facultativo_corpus_christi` · `ponto_facultativo_sexta_feira_santa` | `true`/`false` | `false` |
| `comentarios` | texto (até 255) | `"Cálculo pericial"` |
| `aviso_previo_indenizado` | data (fim do aviso) | `"2023-06-13"` — só usada se faltar `dias_aviso_previo`: os dias saem de (esta data − demissão), entre 1 e 90, com aviso |

`prazo_aviso_previo: "Informado"` sem `dias_aviso_previo` (e sem data utilizável em `aviso_previo_indenizado`) é recusado na porta. `comentarios` com mais de 255 caracteres é cortado, com aviso.

Uma marcação que não venha como `true`/`false` (por exemplo `"sim"`), ou um prazo fora da lista, faz o pedido ser recusado
com `400 lancamentos_invalido`.

### `telas.contribuicao-social.cs_atividade_economica`

Esse campo é usado como atividade econômica (CNAE). Se vier junto com `dadosDoCalculo.atividadeEconomica` e o texto for
diferente, o pedido é recusado. Mandem a mesma atividade nos dois campos, ou só em um deles.

### Referência campo a campo (tudo o que o serviço lê hoje)

Regras gerais: **datas** `AAAA-MM-DD` · **valores em reais** número (`2500.00`) · **alíquotas** fração entre 0 e 1 (`0.05` = 5%) ·
**marcações** `true`/`false` (booleano JSON; texto como `"sim"` é recusado) · **obrigatório** = sem ele o pedido é recusado
(`400 lancamentos_invalido`) · **ignorado** = campo ou valor sem uso, que só aparece em `lancamentos_resumo.ignorados`.

**Raiz e `dadosDoCalculo`**

| campo | tipo / formato | se faltar ou vier errado |
|---|---|---|
| `contrato` | `lancamentos-pjecalc/1` (aceita `/1.x`) | outro valor: recusa o `.json` inteiro |
| `processo.id` | número ou texto | opcional |
| `processo.numero` · `dadosDoCalculo.numeroProcesso` | CNJ `0000000-00.0000.0.00.0000` | fora do formato: recusado |
| `dadosDoCalculo.partes[].polo` | `ATIVO` (reclamante) · `PASSIVO` (reclamado) | outro valor: recusado |
| `dadosDoCalculo.partes[].nome` | texto, até 150 | opcional |
| `dadosDoCalculo.partes[].documento` | CPF ou CNPJ (com ou sem pontuação) | vazio/`null`: documento fica em branco no PJe-Calc |
| `dataAdmissao` · `dataDemissao` · `dataAjuizamento` · `dataInicioCalculo` · `dataTerminoCalculo` | data | data inválida: recusado |
| `atividadeEconomica` | texto da CNAE | opcional; mande a **descrição completa** do CNAE como no PJe-Calc: se mais de uma atividade combinar, a execução para e lista os candidatos |
| `vara` | `…VARA DO TRABALHO DO RECIFE-PE` | só serve para achar UF/município quando não vierem em `telas`; senão sai um aviso |
| `identificacao` · `classe` · `tipoRescisao` | — | ignorados (sem campo na tela) |
| `fgts.destino` | `RECOLHER` · `PAGAR` | fora da lista: recusado |
| `fgts.multaDoFgts` | `true`/`false` | opcional |

**`custas`**

| campo | tipo / formato | observação |
|---|---|---|
| `tipoDeCustasDeConhecimentoDoReclamado` | `NAO_SE_APLICA` · `CALCULADA_2_POR_CENTO` · `INFORMADA` | fora da lista: recusado |
| `dataVencimentoConhecimentoDoReclamado` · `valorConhecimentoDoReclamado` | data · número | **obrigatórios** se `INFORMADA`; ignorados nos outros tipos |
| `custasPagasDoReclamado[].valor` · `.dataVencimento` (também aceita `.vencimento`) | número · data | sem data, a custa **não é lançada** (aviso) |

**`honorarios[]`** (cada item)

| campo | tipo / formato | observação |
|---|---|---|
| `tipoValor` | `INFORMADO` (padrão) · `CALCULADO` | outro valor: recusado |
| `descricao` | texto **sem hífen** | obrigatória; `-` é o marcador interno de "bloco vazio" |
| `tipoHonorario` | códigos do §2 | obrigatório; `CALCULADO` só em `ADVOCATICIOS`, `ASSISTENCIAIS`, `CONTRATUAIS`, `LEILOEIRO` |
| `tipoDeDevedor` | `RECLAMADO` · `RECLAMANTE` | obrigatório |
| `tipoCobrancaReclamante` | `COBRAR` (padrão) · `DESCONTAR` · `DESCONTAR_CREDITO` | |
| `nomeCredor` | texto | opcional |
| `dataVencimento` · `valor` | data · número | **obrigatórios** se `INFORMADO` |
| `aliquota` · `baseParaApuracao` | fração · texto/código da lista do §3 | **obrigatórios** se `CALCULADO` |
| `outroIndiceDeCorrecao` (ou `tipoDeIndiceDeCorrecao` "OUTRO…") | — | em `CALCULADO` é recusado; sai o índice trabalhista |

**`multas[]`** (cada item; no máximo **9** por pedido)

| campo | tipo / formato | observação |
|---|---|---|
| `tipoValorDaMulta` | `INFORMADO` (padrão) · `CALCULADO` | outro valor: recusado |
| `descricao` | texto | obrigatória |
| `tipoCredorDevedor` | códigos do §2 (com `_` ou `_E_`) | obrigatório |
| `nomeTerceiro` | texto | **obrigatório** quando o credor/devedor é `TERCEIRO_…` |
| `tipoCobrancaReclamante` | `COBRAR` (padrão) · `DESCONTAR` · `DESCONTAR_CREDITO` | |
| `dataVencimentoMulta` · `valorMulta` | data · número | **obrigatórios** se `INFORMADO` |
| `aplicarJurosSobreMulta` · `dataJurosAPartirDe` | `true`/`false` · data | em `INFORMADO` com juros a data é obrigatória; em `CALCULADO` juros são recusados |
| `aliquotaMulta` · `tipoBaseMulta` | fração · texto/código da lista do §3 | **obrigatórios** se `CALCULADO` |

**`telas.*`** (nomes em minúsculas, como a tela do SAP)

| campo | tipo / formato | observação |
|---|---|---|
| `dados-do-calculo.reclamante_nome` · `reclamado_nome` | texto, até 150 | |
| `dados-do-calculo.reclamante_cpf` · `reclamado_cnpj` · `reclamado_cpf` | CPF/CNPJ | |
| `dados-do-calculo.numero_processo` | CNJ | |
| `dados-do-calculo.admissao` · `demissao` · `ajuizamento` · `data_inicial` · `data_final` | data | |
| `dados-do-calculo.ultima_remuneracao` · `maior_remuneracao` · `valor_da_causa` | número | |
| `dados-do-calculo.carga_horaria` | número (ou texto com número: `"220h"`) | sem número: recusado |
| `dados-do-calculo.sabado_dia_util` | `true`/`false` | |
| `dados-do-calculo.regime` (ou `regime_trabalho`) | lista do §3 | |
| `dados-do-calculo.autuado_em` | data `AAAA-MM-DD` | campo "Autuado em" (formulario:autuadoEm) |
| `dados-do-calculo.reclamante_pis` | texto com 11 dígitos (`"120.56551.23-5"`) | dígito verificador conferido; inválido: recusado. Marca a opção PIS e grava o número |
| `dados-do-calculo.uf` · `municipio` | sigla · nome na lista do PJe-Calc para a UF | município fora da lista: recusado |
| demais campos de `dados-do-calculo` | tabela da seção acima | |
| `fgts.fgts_destino` | texto com "Pagar" ou "Recolher" | outro texto: recusado |
| `fgts.fgts_calcular_multa` | `true`/`false` | |
| `custas-judiciais.custas_reclamado` | "Não se Aplica" · "Calculada 2%" | "Informada" aqui é recusado: use o bloco `custas` |
| `contribuicao-social.cs_atividade_economica` | texto da CNAE | igual a `atividadeEconomica` |
| `correcao-juros-multa.cj_correcao` | índice da lista do §3 (ou "texto (índice)") | fora da lista: recusado |
| `correcao-juros-multa.cj_juros_pre_judicial` | `true`/`false` | "Aplicar Juros na Fase Pré-Judicial"; sem o campo, fica o padrão da tela (marcado) |

**Não lido ainda** (vai para `ignorados`, o pedido segue): o bloco `verbas` ("próxima fase"), o `cartao-de-ponto` de `arquivos`; as telas
`salario-familia`, `seguro-desemprego`, `previdencia-privada`, `pensao-alimenticia`, `imposto-de-renda` e `cartao-de-ponto`
("tela ainda não automatizada"); qualquer outro campo ("campo não reconhecido" / "campo sem correspondente na automação").

### `telas.fgts`: a tela inteira (implementado em 14/10/2026)

| campo | valores | regra na porta |
|---|---|---|
| `fgts_aliquota` | `"8%"` · `"2%"` (ou `8` · `2`) | `2%` é gravado em Ocorrências › Regerar › Confirmar |
| `fgts_multa_lc110` · `fgts_contribuicao_lc110` | `true`/`false` | |
| `fgts_tipo_valor_multa` | `"Calculado"` · `"Informado"` | só com `fgts_calcular_multa = true` |
| `fgts_percentual_multa` | `"40%"` · `"20%"` (ou `40` · `20`) | só com multa e valor Calculado |
| `fgts_incidencia_multa` | lista do §3 (`Sobre devido`, …, `Sobre devido - saldo e/ou saque`) | só com multa e valor Calculado |
| `fgts_valor_multa_informado` | número (reais) | obrigatório com `Informado`; proibido nos outros casos |
| `fgts_multa_467` · `fgts_excluir_aviso_multa` | `true`/`false` | só com multa; sem `fgts_excluir_aviso_multa` fica o padrão da tela (marcado) |

### `telas.contribuicao-social` e `contribuicaoSocial`: a tela inteira (implementado em 14/10/2026)

Na tela principal ficam os quatro checkboxes; o resto é a janela de **Ocorrências › Regerar**, gravada no Confirmar
(`tipoRegeracao` fica no padrão, *Manter*). Campo fora da condição em que a tela o mostra → `400`.

| campo | valores | condição |
|---|---|---|
| `cs_apurar_segurado` · `cs_apurar_salarios_pagos` | `true`/`false` | |
| `cs_cobrar_reclamante` · `cs_corrigir_desconto_reclamante` | `true`/`false` | não com `cs_apurar_segurado = false`; `cs_corrigir_desconto_reclamante = true` exige `cs_cobrar_reclamante` ≠ `false` (a tela só mostra "Com Correção Trabalhista" com "Cobrar" marcado) |
| `cs_aliquota_segurado` | `"Segurado Empregado"` · `"Empregado Doméstico"` · `"Fixa"` | |
| `cs_aliquota_segurado_fixa` | percentual (`11`; a tela guarda 2 decimais) | obrigatório com segurado `Fixa`, proibido sem |
| `cs_limitar_teto` | `true`/`false` | só com segurado `Fixa`; sem ele, padrão da tela (marcado) |
| `cs_aliquota_empregador` | `"Por Atividade Econômica"` · `"Por Período"` · `"Fixa"` | sem ele, vale o fluxo de antes (CNAE se houver) |
| `cs_atividade_economica` · `cs_apurar_empresa` · `cs_apurar_sat` · `cs_apurar_terceiros` | CNAE · `true`/`false` | só com `Por Atividade Econômica`, que exige a CNAE (aqui ou em `dadosDoCalculo.atividadeEconomica`) |
| `cs_cota_empresa` · `cs_sat` · `cs_terceiros` | percentual (`20`, `3`, `5.8`) | só com empregador `Fixa`; ausentes ficam no padrão da tela |
| `cs_incidencia_devidos_inicio` · `_fim` · `cs_incidencia_pagos_inicio` · `_fim` | data `AAAA-MM-DD` | fim ≥ início; sem elas, o período do cálculo |

Na raiz do `.json`:

```json
"contribuicaoSocial": {
  "simplesNacional":     [{ "inicio": "01/2024", "fim": "06/2024" }],
  "aliquotasPorPeriodo": [{ "inicio": "12/2023", "fim": "06/2024", "empresa": 20, "sat": 3, "terceiros": 5.8 }]
}
```

Competências `MM/AAAA`, fim ≥ início, sem sobreposição, dentro do contrato (admissão → demissão/data final). `simplesNacional`
vale com qualquer alíquota; `aliquotasPorPeriodo` só com `Por Período`, e é obrigatória nela (`empresa` e `sat` obrigatórios,
`terceiros` opcional). Período que o PJe-Calc recusar ao incluir vira pendência na execução. Com planilha que marca
agroindústria/desoneração/filantrópica (ou Simples), a planilha prevalece.

### `telas.imposto-de-renda`: a tela inteira (implementado em 16/10/2026)

| campo | caixa da tela | valores |
|---|---|---|
| `ir_apurar` | `apurarImpostoRenda` | `true`/`false` |
| `ir_sobre_juros` · `ir_cobrar_reclamado` | `incidirSobreJurosDeMora` · `cobrarDoReclamado` | `true`/`false` |
| `ir_tributacao_exclusiva` · `ir_tributacao_em_separado` · `ir_regime_caixa` | `considerarTributacaoExclusiva` · `considerarTributacaoEmSeparado` · `regimeDeCaixa` | `true`/`false` |
| `ir_deduzir_cs_reclamante` · `ir_deduzir_previdencia_privada` · `ir_deduzir_pensao_alimenticia` · `ir_deduzir_honorarios_reclamante` | `deduzirContribuicaoSocialDevidaPeloReclamante` · `deduzirPrevidenciaPrivada` · `deduzirPensaoAlimenticia` · `deduzirHonorariosDevidosPeloReclamante` | `true`/`false` |
| `ir_aposentado_65` | `aposentadoMaiorQue65Anos` | `true`/`false` |
| `ir_dependentes` | `possuiDependentes` + `quantidadeDependentes` | inteiro ≥ 0 (0 desmarca) |

Com `ir_apurar = false` a tela desabilita todas as outras: mandá-las junto → `400`. Campo ausente fica no padrão da tela
(Apurar e as quatro deduções marcadas; o resto desmarcado). Sem nenhuma chave `ir_*`, a tela não é tocada. As chaves do
formato antigo (`ir_regime`, `ir_exclusiva`, `ir_deducoes`, em texto) vão para `ignorados`.

### `parametrosDoCalculo`: exceções da carga horária e do sábado (Dados do Cálculo › Parâmetros)

```json
"parametrosDoCalculo": {
  "excecoesCargaHoraria": [{ "inicio": "2024-01-01", "fim": "2024-06-30", "valor": 180 }],
  "excecoesSabado":       [{ "inicio": "2024-03-01", "fim": "2024-05-31" }]
}
```

Datas `AAAA-MM-DD`, fim ≥ início, dentro do período do cálculo (início/fim do cálculo, ou admissão/demissão), sem
sobreposição dentro de cada lista; `valor` = carga horária mensal (> 0). Fora disso → `400`. Cada linha entra pelo
"Adicionar Base" da tela; linha que o PJe-Calc recusar vira pendência na execução.

### `advogados`: advogados de cada parte (Dados do Cálculo)

```json
"advogados": {
  "reclamante": [ { "nome": "JOÃO DA SILVA", "oab": "12345/PE", "tipoDocumento": "CPF", "documento": "529.982.247-25" } ],
  "reclamado":  [ { "nome": "MARIA SOUZA", "oab": "9876/SP" } ]
}
```

| campo | regra (recusado com `400` se quebrada) |
|---|---|
| `nome` | obrigatório, até 150 caracteres; vai em maiúsculas |
| `oab` | opcional, `NUMERO/UF`, **até 9 caracteres** (limite do campo); suplementar sem hífen: `12345A/PE` |
| `tipoDocumento` + `documento` | juntos ou nenhum; `CPF` · `CNPJ` · `CEI`; CPF/CNPJ com dígito verificador; CEI com 12 dígitos |
| repetição | o mesmo documento duas vezes na **mesma parte** é recusado (o PJe-Calc não inclui o segundo e não avisa) |
| quantidade | até 10 por parte, na ordem da tela |

Cada advogado é incluído com o botão "+" da tela e conferido na lista; se não entrar, vira pendência. Com planilha base
que traga `advogado_parte1`/`advogado_parte2`, a planilha prevalece naquela parte (aviso). O caminho da planilha também
passou a clicar no "+" (antes o advogado só era digitado e não ficava gravado).

### `arquivos`: faltas, férias e histórico salarial (`.csv`)

O `.json` aponta para os arquivos; o serviço os lê **na porta** e importa pelas telas do PJe-Calc, no mesmo lugar em que a
planilha base fazia. Cada valor é o **caminho do arquivo** (absoluto ou relativo à pasta do `.json`), de extensão `.csv`,
dentro das pastas permitidas. Arquivo inexistente ou com linha inválida: `400 lancamentos_invalido`, com `campo`
(`arquivos.faltas` …) e a linha com problema (no máximo 5 por arquivo).

| chave | layout do `.csv` (separador `;`, texto UTF-8 ou Windows-1252) | o que a automação faz |
|---|---|---|
| `faltas` | `INICIO;FIM;JUSTIFICADA;REINICIAR_PER_AQ;JUSTIFICATIVA` — datas `dd/mm/aaaa`, `S`/`N` | importa em **Faltas** |
| `ferias` | `RELATIVAS;PRAZO;SITUACAO;DOBRA;ABONO;QTD_DIAS_ABONO;G1INI;G1FIM;G1DOBRA;G2INI;G2FIM;G2DOBRA;G3INI;G3FIM;G3DOBRA` — datas `dd/mm/aaaa`; `SITUACAO` só `G` · `GP` · `I` · `P` (`NG` é gravado como Gozadas: recusado); período aquisitivo (aniversário da admissão no 1º ano até a véspera do seguinte) dentro do contrato — as proporcionais o PJe-Calc calcula sozinho | importa em **Férias** |
| `historico-salarial` | `MES_ANO;<NOME DO HISTÓRICO>;FGTS;FGTS_REC.;CONTRIBUICAO_SOCIAL;CONTRIBUICAO_SOCIAL_REC.` — competência `MM/AAAA`, valor com vírgula (`1234,56`), marcas `S`/`N` | cria o histórico salarial (**parcela variável**, nome = título da 2ª coluna, até 120 caracteres) e importa as competências; o PJe-Calc marca as incidências FGTS e Contribuição Social conforme os `S`/`N` do arquivo |
| `base-inss` | `MES_ANO;PARCELA;VALOR` — competência `MM/AAAA`, `PARCELA` = `SALARIO` ou `13`, valor com vírgula decimal | grava a coluna **Salários Pagos (Histórico)** de Contribuição Social › Ocorrências, **casando por competência**: a 1ª linha do mês recebe o `SALARIO`, a 2ª (dezembro, ou o mês da demissão/data final no último ano) recebe o `13`. **Vence** a soma dos históricos com `CONTRIBUICAO_SOCIAL = S`. Na porta: competência dentro do contrato, uma linha por competência e parcela, `13` só em dezembro ou no mês da demissão/data final. Linha do arquivo sem linha na tela, ou o contrário: pendência `automacao` (fica o valor do PJe-Calc) |
| `cartao-de-ponto` | — | recebido, mas **ainda não importado** (vai para `ignorados`) |

- **Histórico: o que o PJe-Calc 2.16.0 aceita na importação** (testado na tela em 07/10/2026; a porta espelha isto):
  - competência **`MM/AAAA`** (`02/2018`). `fev/18` é **recusado pelo próprio PJe-Calc**: *"Valor inválido para data. A data
    deve estar no formato [MM/yyyy]. Erro na linha 2 do arquivo."* O exemplo oficial (`ExemploHistoricoSalarial.csv`) traz
    `"10/2012"` — o `out/12` aparece quando o arquivo é aberto no Excel, que exibe a data nesse formato;
  - valor `1500`, `162,5`, `1.500,00` e `150,00` são aceitos (viram `1.500,00`, `162,50`…);
  - cabeçalho: o PJe-Calc ignora os títulos. **Para a automação**, o título da **2ª coluna é o nome do histórico** (é o que ela
    digita no campo *Nome* e o que `bases[].referencia` casa); o título da 1ª coluna é livre (`DATA` ou `MES_ANO`).
    `VALOR` como título da 2ª coluna é recusado (é o genérico do exemplo, não um nome de parcela).
- **Contribuição Social (salários pagos):** o PJe-Calc preenche a coluna *Salários Pagos (Histórico)* da Contribuição Social com a soma dos históricos marcados com **`CONTRIBUICAO_SOCIAL = S`** (testado na tela em 13/10/2026: com `S` no `SALARIO BASE`, 1.500,00 · 1.550,00 · 1.677,42…; com `N` em todos, usa a última remuneração). Marque `S` nas parcelas que compõem o salário de contribuição; `CONTRIBUICAO_SOCIAL_REC. = S` quando a contribuição daquele mês já foi recolhida. O mesmo vale para `FGTS`/`FGTS_REC.` na base do FGTS. Sem nenhum `S`: aviso no resumo e pendência `automacao` na execução.
- Mais de um histórico: mande uma lista de caminhos em `historico-salarial`; os nomes (2ª coluna do cabeçalho) não podem se repetir.
- Colunas das marcas podem faltar; competências fora do período do cálculo são aceitas pelo PJe-Calc.
- **Com planilha base** no pedido, a planilha prevalece: faltas, férias e histórico do `.json` são ignorados (aviso no log).
- Valor `null` ou vazio em uma chave: ignorado.
- Sem planilha base e com histórico em `.csv`, a base do INSS dos salários pagos ainda **não** é lançada (aviso no log).

### Planilha em branco

Planilha do SAP (com a aba `PJe Histórico`) **sem nenhum histórico nomeado** é recusada na porta:
`400 planilha_em_branco`. Planilha salva sem calcular as macros ou fora do layout: `400 planilha_invalida`.

### Resultado da execução: `concluido` só com `.PJC` e PDF, e o bloco `pendencias`

- **`concluido`** exige o `.PJC` **e** o relatório em PDF. Sem o PDF a execução fica `falhou` ("o relatório em PDF não foi gerado").
- **Liquidação recusada** pelo PJe-Calc → `falhou`, com a mensagem dele (ex.: *"É necessário resolver as pendências do tipo
  Erro antes de realizar a liquidação"*). Antes saía `concluido` sem relatório.
- **Verba ou reflexo manual recusado ao salvar** → `falhou`, com o nome da verba e a mensagem do PJe-Calc (a captura de tela
  mostra o formulário com o erro). Antes a verba era descartada e a execução seguia.
- **`pendencias`** no `GET /calculos/{id}`: `[{ tela, mensagem, origem: "pjecalc" | "automacao" }]` — tudo o que o PJe-Calc não
  confirmou ao salvar uma tela e o que a automação contornou (ex.: incidência que o PJe-Calc esconde numa verba que não compõe
  o principal). Vem em qualquer situação final (`concluido` ou `falhou`); lista vazia = nada a apontar.
- **`lancamentos_resumo.ignorados`** é um objeto `{ campo: motivo }` (formato oficial).

### Descrição das verbas (o que o PJe-Calc guarda)

- Só caracteres **Latin-1**: travessão `—`/`–`, aspas `“ ”`/`‘ ’` e reticências `…` são trocados por `-`, `"`, `'` e `...`
  (aviso no resumo); o que não tiver equivalente é retirado. Sem isso o PJe-Calc grava `¿`.
- **Até 50 caracteres**: o PJe-Calc corta o resto. Verba com reflexo marcado ou usada como base de outra (endereçada) acima de
  50 é **recusada** — cortada, a automação não a acharia; nas demais, aviso com o texto que vai ficar.
- `valorPago.tipo: CALCULADO` exige `valorPago.base` (o PJe-Calc recusa salvar a verba sem ela).

### O resumo volta na resposta

O `202` do `POST /calculos` já traz `execucao.lancamentos_resumo` com `usados`, `ignorados` (campo → motivo) e
`avisos`, e o `GET /calculos/{id}` traz o mesmo resumo, refeito na hora da execução.

### Ainda não lido de `telas`

nenhuma: FGTS, Contribuição Social e Imposto de Renda são lidos por inteiro (seções acima).

## 3. Listas de cada tela, como o PJe-Calc as mostra

### Dados do Cálculo

| campo (id na tela) | valores |
|---|---|
| `estado` (lista) | `27 UFs` |
| `tipoDaBaseTabelada` (lista) | `Trabalho Intermitente` · `Tempo Integral` · `Tempo Parcial` |
| `apuracaoPrazoDoAvisoPrevio` (lista) | `Não apurar` · `Calculado` · `Informado` |
| `pontoFacultativo` (lista) | `SEXTA-FEIRA SANTA` · `CORPUS CHRISTI` · `CARNAVAL` |
| `documentoFiscalReclamante` (opção) | `CPF` · `CNPJ` · `CEI` |
| `reclamanteTipoDocumentoPrevidenciario` (opção) | `PIS` · `PASEP` · `NIT` |
| `tipoDocumentoAdvogadoReclamante` (opção) | `CPF` · `CNPJ` · `CEI` |
| `tipoDocumentoFiscalReclamado` (opção) | `CPF` · `CNPJ` · `CEI` |
| `tipoDocumentoAdvogadoReclamado` (opção) | `CPF` · `CNPJ` · `CEI` |

### FGTS

| campo (id na tela) | valores |
|---|---|
| `incidenciaDoFgts` (lista) | `Sobre devido` · `Sobre saldo e/ou saque` · `Sobre diferença` · `Sobre devido + saldo e/ou saque` · `Sobre devido - saldo e/ou saque` |
| `tipoDeVerba` (opção) | `Pagar` · `Recolher` |
| `comporPrincipal` (opção) | `Sim` · `Não` |
| `tipoDoValorDaMulta` (opção) | `Calculado` · `Informado` |
| `multaDoFgts` (opção) | `20%` · `40%` |
| `aliquota` (opção) | `2%` · `8%` |

### Contribuição Social

| campo (id na tela) | valores |
|---|---|
| `aliquotaEmpregado` (opção) | `Segurado Empregado` · `Empregado Doméstico` · `Fixa` |
| `aliquotaEmpregador` (opção) | `Por Atividade Econômica` · `Por Período` · `Fixa` |

### Multas e Indenizações

| campo (id na tela) | valores |
|---|---|
| `credorDevedor` (lista) | `Reclamante e Reclamado` · `Reclamado e Reclamante` · `Terceiro e Reclamante` · `Terceiro e Reclamado` |
| `tipoBaseMulta` (lista) | `Principal` · `Principal (-) Contribuição Social` · `Principal (-) Contribuição Social (-) Previdência Privada` · `Valor Corrigido da Causa` |
| `valor` (opção) | `Informado` · `Calculado` |

### Honorários

| campo (id na tela) | valores |
|---|---|
| `tpHonorario` (lista) | `Honorários Advocatícios` · `Honorários Assistenciais` · `Honorários Contratuais` · `Honorários Periciais - Contador` · `Honorários Periciais - Documentoscópio` · `Honorários Periciais - Engenheiro` · `Honorários Periciais - Intérprete` · `Honorários Periciais - Médico` · `Honorários Periciais - Outros` · `Honorários de Sucumbência` · `Leiloeiro` |
| `baseParaApuracao` (lista) | `Bruto` · `Bruto (-) Contribuição Social` · `Bruto (-) Contribuição Social (-) Previdência Privada` |
| `tipoDeDevedor` (opção) | `Reclamante` · `Reclamado` |
| `tipoValor` (opção) | `Informado` · `Calculado` |
| `tipoDocumentoFiscalCredor` (opção) | `CPF` · `CNPJ` · `CEI` |

### Custas Judiciais

| campo (id na tela) | valores |
|---|---|
| `baseParaCustasCalculadas` (lista) | `Bruto Devido ao Reclamante` · `Bruto Devido ao Reclamante + Outros Débitos do Reclamado` |
| `tipoDeAuto` (lista) | `Remição` · `Adjudicação` · `Arrematação` |
| `tipoDeCustasDeConhecimentoDoReclamante` (opção) | `Não se Aplica` · `Calculada 2%` · `Informada` |
| `tipoDeCustasDeConhecimentoDoReclamado` (opção) | `Não se Aplica` · `Calculada 2%` · `Informada` |
| `tipoDeCustasDeLiquidacao` (opção) | `Não se Aplica` · `Calculada 0,5%` · `Informada` |

### Correção, Juros e Multa

| campo (id na tela) | valores |
|---|---|
| `indiceTrabalhista` (lista) | `Tabela Única de Atualização e Conversão de Débitos Trabalhistas` · `Devedor Fazenda Pública` · `Repetição de Indébito Tributário` · `Tabela JT Mensal` · `Tabela JT Diária` · `TR` · `IGP-M` · `INPC` · `IPC` · `IPCA` · `IPCA-E` · `IPCA-E/TR` · `SELIC (Receita Federal)` · `SELIC Simples` · `SELIC Composta` · `Sem Correção` |
| `juros` (lista) | `Juros Padrão` · `Juros Caderneta de Poupança` · `Juros Fazenda Pública` · `Juros Simples 0,5% a.m.` · `Juros Simples 1,0% a.m.` · `Juros Simples 0,0333333% a.d.` · `Juros Simples 2,0% a.a. (0,1666666% a.m.)` · `SELIC (Receita Federal)` · `SELIC Simples` · `SELIC Composta` · `TRD Juros Simples` · `TRD Juros Compostos` · `Taxa Legal` · `Sem Juros` |
| `outroJuros` (lista) | `Juros Padrão` · `Juros Caderneta de Poupança` · `Juros Fazenda Pública` · `Juros Simples 0,5% a.m.` · `Juros Simples 1,0% a.m.` · `Juros Simples 0,0333333% a.d.` · `Juros Simples 2,0% a.a. (0,1666666% a.m.)` · `SELIC (Receita Federal)` · `SELIC Simples` · `SELIC Composta` · `TRD Juros Simples` · `TRD Juros Compostos` · `Taxa Legal` · `Sem Juros` |
| `baseDeJurosDasVerbas` (lista) | `Verbas` · `Verba (-) Contribuição Social` · `Verba (-) Contribuição Social (-) Previdência Privada` |
| `outroIndiceDeCorrecaoDePrevidenciaPrivada` (lista) | `Tabela Única de Atualização e Conversão de Débitos Trabalhistas` · `Devedor Fazenda Pública` · `Repetição de Indébito Tributário` · `Tabela JT Mensal` · `Tabela JT Diária` · `TR` · `IGP-M` · `INPC` · `IPC` · `IPCA` · `IPCA-E` · `IPCA-E/TR` · `SELIC (Receita Federal)` · `SELIC Simples` · `SELIC Composta` · `Sem Correção` |
| `outroIndiceDeCorrecaoDasCustas` (lista) | `Tabela Única de Atualização e Conversão de Débitos Trabalhistas` · `Devedor Fazenda Pública` · `Repetição de Indébito Tributário` · `Tabela JT Mensal` · `Tabela JT Diária` · `TR` · `IGP-M` · `INPC` · `IPC` · `IPCA` · `IPCA-E` · `IPCA-E/TR` · `SELIC (Receita Federal)` · `SELIC Simples` · `SELIC Composta` · `Sem Correção` |
| `indiceDeCorrecaoDoFGTS` (opção) | `Utilizar índice trabalhista` · `Utilizar índice JAM` · `Utilizar índice JAM e índice trabalhista` |
| `indiceDeCorrecaoDePrevidenciaPrivada` (opção) | `Utilizar índice trabalhista` · `Utilizar outro índice` |
| `indiceDeCorrecaoDasCustas` (opção) | `Utilizar índice trabalhista` · `Utilizar outro índice` |
| `tipoDeMultaDosSalariosDevidosDoINSS` (opção) | `Urbana` · `Rural` |
| `pagamentoDaMultaDosSalariosDevidosDoINSS` (opção) | `Integral` · `Reduzido` |
| `radioFormaAplicacaoSalarioPago` (opção) | `Mês-a-mês` · `A partir de` |
| `tipoDeMultaDosSalariosPagosDoINSS` (opção) | `Urbana` · `Rural` |
| `pagamentoDaMultaDosSalariosPagosDoINSS` (opção) | `Integral` · `Reduzido` |

### Verbas (parâmetros da verba)

| campo (id na tela) | valores |
|---|---|
| `tipoDaBaseTabelada` (lista) | `Maior Remuneração` · `Histórico Salarial` · `Piso Salarial` · `Salário Mínimo` · `Vale Transporte` |
| `baseVerbaDeCalculo` (lista) |  |
| `integralizarBase` (lista) | `Sim` · `Não` |
| `tipoVariacaoDaParcela` (opção) | `Fixa` · `Variável` |
| `valor` (opção) | `Calculado` · `Informado` |
| `caracteristicaVerba` (opção) | `Comum` · `13º Salário` · `Aviso Prévio` · `Férias` |
| `ocorrenciaPagto` (opção) | `Desligamento` · `Dezembro` · `Mensal` · `Período Aquisitivo` |
| `ocorrenciaAjuizamento` (opção) | `Sim` · `Não` |
| `tipoDeVerba` (opção) | `Principal` · `Reflexa` |
| `geraReflexo` (opção) | `Devido` · `Diferença` |
| `gerarPrincipal` (opção) | `Devido` · `Diferença` |
| `comporPrincipal` (opção) | `Sim` · `Não` |
| `tipoDeDivisor` (opção) | `Informado` · `Carga Horária` · `Dias Úteis` · `Importada do Cartão de Ponto` |
| `tipoDaQuantidade` (opção) | `Informada` · `Importada do Calendário` · `Importada do Cartão de Ponto` |
| `tipoDoValorPago` (opção) | `Informado` · `Calculado` |

### Férias

| campo (id na tela) | valores |
|---|---|
| `situacao` (lista) | `Gozadas` · `Gozadas Parcialmente` · `Indenizadas` · `Perdidas` |

### Salário-família

| campo (id na tela) | valores |
|---|---|
| `historicoSalarial` (lista) |  |
| `verba` (lista) |  |
| `integralizar` (lista) | `Sim` · `Não` |
| `comporPrincipal` (opção) | `Sim` · `Não` |
| `tipoSalarioPago` (opção) | `Nenhum` · `Maior Remuneração` · `Histórico Salarial` |

## 4. Ordem entre as telas

A automação segue: Dados do Cálculo → Faltas → Férias → Histórico Salarial → Verbas → FGTS → Contribuição Social →
Multas → Honorários → Custas → Correção → Liquidação. Dependências conhecidas: Histórico antes das Verbas (base HS);
Faltas e Férias antes das Verbas que as excluem; Cartão de Ponto (quando existir) antes das Verbas com quantidade
importada do cartão.

## 5. Verbas — como a automação lança hoje (para desenhar o bloco `verbas` do `.json`)

O bloco `verbas` do `.json` **ainda não é lido** (vai para `ignorados`). Hoje as verbas só entram pela **planilha de verbas**
(abas `TBVERBABD`, `TBREFLEXA`, `DEVIDOBD_EXP`, `PAGOBD_EXP`). O que segue descreve esse caminho — é o contrato que o
bloco `verbas` vai reproduzir.

### Como uma verba é criada na tela

1. **Verbas > Lançamento Expresso**: escolhe a verba numa **lista fechada** do PJe-Calc (`SNMVERBAEXPRESSOPJECALC`, por
   igualdade exata de texto) e salva. Sem igualdade exata, a execução para.
2. Abre os parâmetros da verba criada e **sobrescreve a descrição** (`SNMDESCRICAOVERBA`) — **texto livre**, até onde o
   PJe-Calc aceita; a automação tira os espaços das pontas.
3. Preenche os parâmetros (tabela abaixo), salva e, se algum `SFLREFLEXO…` = `S`, expande os reflexos da verba **pela
   descrição** e marca/cria os reflexos.

Ou seja: **a "verba-modelo" é lista fechada; o nome que aparece no cálculo é livre.** A descrição precisa ser única dentro
do cálculo, porque reflexos e bases a localizam pelo texto.

**Lista do Lançamento Expresso** (PJe-Calc 2.16.0 desta máquina, lida na tela em 07/10/2026 — 54 itens; em 30/09
havia `REPOUSO SEMANAL REMUNERADO` simples, hoje são `REPOUSO SEMANAL REMUNERADO (COMISSIONISTA)` e `REPOUSO SEMANAL
REMUNERADO EM DOBRO`: a lista muda quando o PJe-Calc atualiza as tabelas):
13º SALÁRIO · ABONO PECUNIÁRIO · ACORDO (MERA LIBERALIDADE) · ACORDO (MULTA) · ACORDO (VERBAS INDENIZATÓRIAS) · ACORDO (VERBAS REMUNERATÓRIAS) · ADICIONAL DE HORAS EXTRAS 50% · ADICIONAL DE INSALUBRIDADE 10% · ADICIONAL DE INSALUBRIDADE 20% · ADICIONAL DE INSALUBRIDADE 40% · ADICIONAL DE PERICULOSIDADE 30% · ADICIONAL DE PRODUTIVIDADE 30% · ADICIONAL DE RISCO 40% · ADICIONAL DE SOBREAVISO · ADICIONAL DE TRANSFERÊNCIA 25% · ADICIONAL NOTURNO 20% · AJUDA DE CUSTO · AVISO PRÉVIO · CESTA BÁSICA · COMISSÃO · DEVOLUÇÃO DE DESCONTOS INDEVIDOS · DIFERENÇA SALARIAL · DIÁRIAS - INTEGRAÇÃO AO SALÁRIO · DIÁRIAS - PAGAMENTO · FERIADO EM DOBRO · FÉRIAS + 1/3 · GORJETA · GRATIFICAÇÃO DE FUNÇÃO · GRATIFICAÇÃO POR TEMPO DE SERVIÇO · HORAS EXTRAS 100% · HORAS EXTRAS 50% · HORAS IN ITINERE · INDENIZAÇÃO ADICIONAL · INDENIZAÇÃO PIS - ABONO SALARIAL · INDENIZAÇÃO POR DANO ESTÉTICO · INDENIZAÇÃO POR DANO MATERIAL · INDENIZAÇÃO POR DANO MORAL · INTERVALO INTERJORNADAS · INTERVALO INTRAJORNADA · MULTA CONVENCIONAL · MULTA DO ARTIGO 477 DA CLT · PARTICIPAÇÃO NOS LUCROS OU RESULTADOS - PLR · PRÊMIO PRODUÇÃO · REPOUSO SEMANAL REMUNERADO (COMISSIONISTA) · REPOUSO SEMANAL REMUNERADO EM DOBRO · RESTITUIÇÃO / INDENIZAÇÃO DE DESPESA · SALDO DE EMPREITADA · SALDO DE SALÁRIO · SALÁRIO MATERNIDADE · SALÁRIO RETIDO · TÍQUETE-ALIMENTAÇÃO · VALE TRANSPORTE · VALOR PAGO - NÃO TRIBUTÁVEL · VALOR PAGO - TRIBUTÁVEL

### Parâmetros que a automação consome (`TBVERBABD`) e os códigos de cada um

| coluna | códigos aceitos hoje (planilha) | na tela | XML do `.PJC` |
|---|---|---|---|
| `SNMVERBAEXPRESSOPJECALC` | texto da lista acima | Lançamento Expresso | — |
| `SNMDESCRICAOVERBA` | texto livre | Descrição | — |
| `STPPARCELA` | `F` · `V` | Fixa · Variável | — |
| `STPVALOR` | `C` · `I` | Calculado · Informado | — |
| `SFLINCIDENCIAINSS` · `…IRPF` · `…FGTS` · `…PREVPRIVADA` · `…PENSAO` | `S` · `N` | incidências | — |
| `STPCARACTERISTICAVERBA` | `C` · `DT` · `AP` · `F` | Comum · 13º Salário · Aviso Prévio · Férias | — |
| `STPOCORRENCIAPAGAMENTO` | `DL` · `DZ` · `M` · `PA` | Desligamento · Dezembro · Mensal · Período Aquisitivo | `DESLIGAMENTO` · `DEZEMBRO` · `MENSAL` · `PERIODO_AQUISITIVO` |
| `STPJUROSSUMULA` | `S` · outro = Não | Súmula 439 (ajuizamento) | — |
| `STPTIPOVERBA` | `P` · `R` | Principal · Reflexa | — |
| `STPGERARVERBAREFLEXA` · `STPGERARVERBAPRINCIPAL` | `DV` · `DF` | Devido · Diferença | — |
| `SFLCOMPORPRINCIPAL` · `SFLPADRAOZERARVALORNEGATIVO` · `SFLDOBRARVALOR` | `S` · `N` | marcações | — |
| `SFLEXCLUIRFALTAJUSTIFICADA` · `…FALTANAOJUSTIFICADA` · `…FERIASGOZADAS` | `S` · `N` | exclusões | — |
| `DDTINICIO` · `DDTTERMINO` | data | período da verba | — |
| `RVLVALORDEVIDO` · `SFLPROPORCIONALIDADE` | número · `S`/`N` | só se `STPVALOR` = `I` | — |
| `STPBASEDEVIDO` | `HS` · `MR` · `PS` · `SM` · `VT` | Histórico Salarial · Maior Remuneração · Piso · Salário Mínimo · Vale Transporte | `HISTORICO_SALARIAL` · `MAIOR_REMUNERACAO` · … · `SALARIO_MINIMO` · `VALE_TRANSPORTE` |
| `STPDIVISOR` · `RVLOUTRODIVISOR` | `IN` · `CH` · `DU` · `ICP` · número | Informado · Carga Horária · Dias Úteis · Importada do Cartão | `OUTRO_VALOR` · `CARGA_HORARIA` · `DIAS_UTEIS` · `IMPORTADA_DO_CARTAO` |
| `RVLMULTIPLICADOR` | número | multiplicador | — |
| `STPQUANTIDADE` · `STPCALENDARIO` · `RVLOUTROVALORQTD` · `SFLQTDPROPORCIONALIDADE` | `IN` · `AV` · `ICL` · `ICP` · calendário `RF`/`R`/`F`/`DU` · número · `S`/`N` | Informada · Avos · Importada do Calendário · Importada do Cartão | `INFORMADA` · `AVOS` · `IMPORTADA_DO_CALENDARIO` · `IMPORTADA_DO_CARTAO` |
| `STPVALORPAGO` · `STPBASEPAGO` · `RVLINOUTROVALOR` · `SFLVPGPROPORCIONALIDADE` | `I` · `C` · base como `STPBASEDEVIDO` · número · `S`/`N` | Valor pago | `INFORMADO` · `CALCULADO` |
| `RVLQUANTIDADE` · `SDSCOMENTARIO` | número · texto | | — |

Linhas sem código conhecido não marcam nada (a opção fica no padrão da tela). `APURADA` (quantidade) e `PISO_SALARIAL`
existem no XML mas não têm código na planilha.

### Reflexos e bases

- **Reflexos que o PJe-Calc gera sozinho** a partir da principal: a automação lê **14 marcações** da linha da principal —
  `SFLREFLEXO13TERCEIRO`, `…AVISO`, `…FERIAS`, `…ART477CLT`, `…ART467CLT`, `…REPOUSO`, `SFLSEPARARFERIAS`, `SFLREFLEXOHEXTRAS50`,
  `…HEXTRAS100`, `…GANUAL`, `…GSEMESTRAL`, `…LPREMIO`, `…APIP`, `…PLR` (`S`/`N`). Para cada `S`, marca o reflexo na lista da
  principal; se o PJe-Calc não o oferecer, **cria o reflexo manualmente** com a linha de `TBREFLEXA` cuja
  `SNMVERBAREFLEXA` é o nome da marcação (e, em alguns, `SNMVERBAEXPRESSOPJECALC` da principal).
- **Reflexo manual** (`TBREFLEXA`): é amarrado à **principal** (selecionada pela descrição) e usa os mesmos parâmetros da
  tabela acima, mais `STPCOMPORTAMENTOREFLEXO`, `STPPERIODOMEDIAREFLEXO`, `STPTRATAMENTOFRACAOMESREFLEXO`.
- **Bases da verba** (`DEVIDOBD_EXP` e `PAGOBD_EXP`): ligadas à principal por `FKVERBA` = `IIDVERBAJRS`, com `TIPO` = `HS` (um
  **histórico salarial pelo nome** — o mesmo nome do título da 2ª coluna do `.csv` de histórico) ou `VB` (outra **verba pela
  descrição**), e `PROP/INT` (`S`/`N`, proporcionalizar/integralizar).

### Respostas das medições do SAP (06/10)

- **`AVOS` e `APURADA` não são opção de tela**: o PJe-Calc grava sozinho conforme a característica (13º/Férias → `AVOS`;
  Aviso Prévio → `APURADA`). O que precisa chegar certo é a característica.
- **13º, Férias e Aviso**: a automação assume que o PJe-Calc sempre os oferece na lista de reflexos da principal (não há
  criação manual para eles). Os rótulos que ela procura são `13º SALÁRIO SOBRE <DESCRIÇÃO>`, `AVISO PRÉVIO SOBRE …`,
  `FÉRIAS + 1/3 SOBRE …` — a descrição em **maiúsculas**.
- **Os 11 `…ATIVAR`** da `TBVERBA` (v1.12): a automação **não lê nenhum**. Ficam fora do contrato.
- **`SNMVERBAEXPRESSOPJECALC` de `TBREFLEXA`**: só é usado para escolher a linha no `SFLSEPARARFERIAS` e no
  `SFLREFLEXOHEXTRAS50` (comparado ao Expresso da principal) e no `SFLREFLEXOART477CLT` (comparado à **descrição** da
  principal — **corrigido em 06/10/2026**: agora compara primeiro com o Expresso da principal, como nos outros dois, e usa
  a descrição só se não houver linha com o Expresso). Nos demais reflexos manuais (`REPOUSO`, `ART467CLT`, `GANUAL`, `GSEMESTRAL`, `LPREMIO`, `APIP`, …) a coluna
  **não é lida** — vale a primeira linha com aquele `SNMVERBAREFLEXA`. Os números (`180`, `246`…) nessa coluna não são
  lidos pela automação e não temos de/para deles.

### Contrato do bloco `verbas` (aprovado em 06/10/2026; implementado em 07/10/2026)

**Quando o bloco é lido** — só no formato deste contrato: a porta lê `verbas` quando os itens trazem `id` **e** `expresso`.
Sem esses dois (o formato anterior do emissor: `tipo`, `ocorrencia`, `modo`, `base`, `divisor`…), o bloco é **ignorado como
antes** e listado em `ignorados` — assim nenhum pedido bom vira 400 por causa da ordem dos deploys. Num bloco no formato
novo, item sem `id`/`expresso` é recusado. **`verbas: []`** = decisão de não lançar verbas (aceito, aviso no resumo);
**ausente** = silêncio.

Vocabulário único: **o código do XML do `.PJC`**. Valor fora da lista → `400 lancamentos_invalido` com `aceitos`.

`verbas[]` — uma verba principal por item:

| campo | tipo / valores | regra |
|---|---|---|
| `id` | texto ou número | obrigatório, único no pedido; é o que `bases[].referencia` e `reflexosManuais[].principal` usam |
| `expresso` | um dos 54 itens da lista acima | obrigatório |
| `descricao` | texto | obrigatório; a porta **normaliza** (tira espaços das pontas e põe em MAIÚSCULAS) e devolve o valor normalizado no resumo. **Unicidade só para verba endereçada** (alvo de `bases[]` do tipo `VERBA`, com algum `reflexos[X] = true` ou principal de `reflexosManuais`): a descrição dela não pode ser igual à de **nenhuma** outra verba do pedido (a tela a localiza pelo texto). Verba que ninguém endereça pode repetir a descrição — ex.: `CONTRIBUIÇÃO SOCIAL SALARIOS DEVIDOS` em `COMUM`/`MENSAL` e em `DECIMO_TERCEIRO_SALARIO`/`DEZEMBRO`, como em 6% dos cálculos de hoje |
| `parcela` | `FIXA` · `VARIAVEL` | |
| `valor` | `CALCULADO` · `INFORMADO` | obrigatório |
| `caracteristica` | `COMUM` · `DECIMO_TERCEIRO_SALARIO` · `AVISO_PREVIO` · `FERIAS` | |
| `ocorrenciaPagamento` | `MENSAL` · `DEZEMBRO` · `DESLIGAMENTO` · `PERIODO_AQUISITIVO` | |
| `incidencias` | `{ inss, irpf, fgts, previdenciaPrivada, pensaoAlimenticia }` booleanos | |
| `jurosSumula439` · `comporPrincipal` · `zerarValorNegativo` · `dobrarValor` | booleanos | |
| `excluirFaltaJustificada` · `excluirFaltaNaoJustificada` · `excluirFeriasGozadas` | booleanos | |
| `geraReflexo` · `gerarPrincipal` | `DEVIDO` · `DIFERENCA` | |
| `periodo` | `{ inicio, termino }` em `AAAA-MM-DD` | |
| `valorDevido` · `proporcionalidade` | número · booleano | só com `valor` = `INFORMADO` (aí `valorDevido` é obrigatório) |
| `baseTabelada` | `HISTORICO_SALARIAL` · `MAIOR_REMUNERACAO` · `PISO_SALARIAL` · `SALARIO_MINIMO` · `VALE_TRANSPORTE` | só com `CALCULADO` |
| `bases[]` | `{ tipo: HISTORICO \| VERBA, referencia, proporcionalizar }` | `HISTORICO`: `referencia` = nome de um histórico do **mesmo pedido** (título da 2ª coluna do `.csv`) — **se não existir, o pedido é recusado** (o PJe-Calc zeraria a verba em silêncio). `VERBA`: `referencia` = `id` de outra verba do pedido |
| `divisor` | `{ tipo: OUTRO_VALOR \| CARGA_HORARIA \| DIAS_UTEIS \| IMPORTADA_DO_CARTAO, valor }` | **obrigatório com `CALCULADO`** (a tela exige); `valor` obrigatório com `OUTRO_VALOR` |
| `multiplicador` | número | **obrigatório com `CALCULADO`** (a tela exige); só o campo numérico, sem tipo |
| `quantidade` | `{ tipo: INFORMADA \| IMPORTADA_DO_CALENDARIO \| IMPORTADA_DO_CARTAO \| AVOS \| APURADA, valor, calendario, proporcionalidade }` — `valor` é o `RVLOUTROVALORQTD` da planilha | `AVOS` só com 13º/Férias e `APURADA` só com Aviso Prévio (não clicam nada); `calendario`: `REPOUSOS_E_FERIADOS` · `REPOUSOS` · `FERIADOS` · `DIAS_UTEIS` |
| `valorPago` | `{ tipo: INFORMADO \| CALCULADO, base, valor, quantidade, proporcionalidade, bases }` (`bases[].proporcionalizar` ausente = `false`) | `base` com os valores de `baseTabelada`; `quantidade` é o `RVLQUANTIDADE` da planilha |
| `comentario` | texto | |
| `reflexos` | `{ decimoTerceiro, ferias, aviso, repouso, art477, art467, separarFerias, horasExtras50, horasExtras100, gratificacaoAnual, gratificacaoSemestral, licencaPremio, apip, plr }` booleanos | `true` = marcar (ativar) o reflexo na principal; se o PJe-Calc não o oferecer, vale `reflexosManuais`. `false` ou ausente = **não mexer**: os reflexos que o PJe-Calc gera sozinho continuam lá, **desativados** (como nos `.PJC` de hoje); reflexo manual não é criado |

**Invariante entre `baseTabelada` e `bases[]`** (recusado na porta se quebrado):
- `baseTabelada = HISTORICO_SALARIAL` **se e somente se** houver ao menos um item `bases[]` com `tipo: HISTORICO`.
  **`baseTabelada` ausente com base `HISTORICO` é derivada** como `HISTORICO_SALARIAL` (aviso no resumo);
- com `MAIOR_REMUNERACAO`, `PISO_SALARIAL`, `SALARIO_MINIMO`, `VALE_TRANSPORTE` ou sem `baseTabelada`, não há base `HISTORICO`;
- `bases[]` com `tipo: VERBA` convive com qualquer um deles — **base mista** (histórico + outras verbas) é lançada inteira:
  todos os históricos e todas as verbas de `bases[]`. Com base `VERBA`, `baseTabelada` é obrigatória (a tela só
  inclui as verbas da base depois de escolher a base tabelada).
- `bases[].referencia` do tipo `VERBA`: `id` de **outra** verba do pedido. Auto-referência (A → A) e ciclo (A → B → A) são
  recusados; a ordem de criação é calculada (a verba usada como base nasce antes).
- `valorPago` com `base: HISTORICO_SALARIAL` exige `valorPago.bases[] { referencia (nome do histórico), proporcionalizar }`.
- Nome de histórico (em `bases[]` e `valorPago.bases[]`) é conferido contra os históricos que o cálculo vai ter: os da
  planilha base, ou os `.csv` do bloco `arquivos`.

`reflexosManuais[]` — reflexo criado à mão quando o PJe-Calc não oferece: `{ principal (id da verba), reflexo (a chave de
`reflexos`), descricao, … }` com os mesmos parâmetros da verba, mais `comportamento`, `periodoMedia`, `tratamentoFracaoMes`
(valores abaixo, levantados na tela em 06/10/2026), e `assuntoCnj` (código do assunto CNJ, que a tela exige no
"Novo"; ausente → `2581`, o de todos os reflexos manuais da planilha da casa, com aviso). `bases`/`baseTabelada` num
reflexo manual são ignorados: a base dele é sempre a principal. **As mesmas regras da verba valem para o reflexo manual**: `valor` é obrigatório e, com `CALCULADO`, `divisor` e `multiplicador` também (a tela exige). **`descricao` do reflexo manual sem o "SOBRE …"**: o PJe-Calc completa sozinho com " SOBRE <descrição da principal>" (ex.: `GRATIFICAÇÃO ANUAL` vira `GRATIFICAÇÃO ANUAL SOBRE HORAS EXTRAS SOBREJORNADA`), como na planilha da casa.

**Reflexo que exige manual é conferido na porta.** `decimoTerceiro`, `ferias` e `aviso` o PJe-Calc sempre oferece; **todos os
outros** (`repouso`, `art477`, `art467`, `separarFerias`, `horasExtras50`, `horasExtras100`, `gratificacaoAnual`,
`gratificacaoSemestral`, `licencaPremio`, `apip`, `plr`) marcados `true` **exigem** um item em `reflexosManuais` com aquela
`principal` e aquele `reflexo` — senão `400`, com o nome do reflexo. Se o PJe-Calc oferecer o reflexo na lista da principal,
ele é usado e o manual não é criado. `separarFerias` exige também `reflexos.ferias = true`. Item manual de um reflexo que a
principal não marca vira aviso (não é criado).

**Parâmetros do reflexo manual** (PJe-Calc 2.16.0, conferido na tela em 06/10/2026). As opções dependem da
**`ocorrenciaPagamento`** do reflexo — não da característica (a característica só muda a ocorrência sugerida: 13º →
Dezembro, Aviso → Desligamento, Férias → Período Aquisitivo):

| `ocorrenciaPagamento` | `comportamento` | `periodoMedia` (só com média) |
|---|---|---|
| `MENSAL` | `VALOR_MENSAL` | — |
| `DEZEMBRO` | `VALOR_MENSAL` · `MEDIA_PELO_VALOR` · `MEDIA_PELO_VALOR_CORRIGIDO` · `MEDIA_PELA_QUANTIDADE` | `ANO_CIVIL` |
| `DESLIGAMENTO` | idem | `ULTIMOS_DOZE_MESES_DO_CONTRATO` · `DOZE_MESES_ANTERIORES_AO_VENCIMENTO_DA_PARCELA` |
| `PERIODO_AQUISITIVO` | idem | `PERIODO_AQUISITIVO` · `DOZE_MESES_ANTERIORES_AO_VENCIMENTO_DA_PARCELA` |

- `tratamentoFracaoMes`: `MANTER` · `INTEGRALIZAR`; com média, também `DESPREZAR` · `DESPREZAR_MENOR_QUE_15_DIAS`.
- **`periodoMedia` com `VALOR_MENSAL` é ignorado, nunca recusado** — o `.PJC` grava `PERIODO_AQUISITIVO` como padrão mesmo
  quando a tela não mostra o campo (658 dos 1.378 reflexos medidos pelo SAP).
- Recusado: média com `MENSAL`; `periodoMedia` fora da lista da ocorrência quando há média.
- Ex.: a multa do 477 (`COMUM` · `DESLIGAMENTO` · `MEDIA_PELA_QUANTIDADE` · `ULTIMOS_DOZE_MESES_DO_CONTRATO`) é aceita.
- **`ocorrenciaPagamento` ausente**: a porta a **deriva da característica**, como a tela sugere ao trocar a característica —
  `COMUM` → `MENSAL`, `DECIMO_TERCEIRO_SALARIO` → `DEZEMBRO`, `AVISO_PREVIO` → `DESLIGAMENTO`, `FERIAS` → `PERIODO_AQUISITIVO` —
  e **diz no resumo** (`avisos`) que derivou. `COMUM` sem ocorrência e com média é recusado (`MENSAL` não tem média):
  mande a ocorrência.

Na planilha (`TBREFLEXA`) os mesmos valores vêm como `VM`/`MA`/`MC`/`MQ`, `AC`/`DM`/`DV`/`PA` e `M`/`I`/`D`/`DMQ`.

Com planilha de verbas no pedido, a planilha prevalece e o bloco `verbas` é ignorado — **listado em `lancamentos_resumo.ignorados` da resposta** (`verbas`: "a planilha de verbas do pedido prevalece"), além do log. **Verba-modelo** `---------- AUTOMAÇÃO` (Expresso `AJUDA DE CUSTO`, R$ 0,01, não compõe o principal): o PJe-Calc não
liquida cálculo sem verba, então ela é criada para a 1ª liquidação. **Quando o pedido traz verbas** (bloco `verbas` ou
planilha de verbas), ela é **excluída depois que as verbas entram, antes da liquidação final** — o `.PJC` e o PDF saem sem
ela. Pedido sem verbas: ela continua (sem ela a liquidação falha). Cálculos gerados antes de 07/10/2026 ainda a têm.
