# Mapa `.json` de lançamentos → XML do `.PJC`

**Para:** quem confere o cálculo depois da execução (auditoria do Sistema de Cálculo) · **De:** automação PJe-Calc ·
**Base:** PJe-Calc 2.16.0, cálculo 602 (processo 17455, execução `4c838b4bfd17`) e cálculo 593 (17111), lidos em 13/10/2026.

O `.PJC` é um zip com um XML. A raiz é `Calculo`; cada tela do PJe-Calc é um bloco dele. Este documento diz, para cada campo
que a automação preenche a partir do `.json`, onde ele fica no XML e como comparar. A lista completa dos campos do `.json` e
dos valores aceitos está no [VALORES-ACEITOS-PJECALC.md](VALORES-ACEITOS-PJECALC.md).

## 1. Como ler o XML

- **Objetos reaproveitados:** cada objeto aparece completo na **primeira** vez e, nas seguintes, só como
  `<internalRef>id</internalRef>`. Antes de comparar, indexe todos os elementos por `tag + <id>` e resolva os `internalRef`.
  Ex.: as verbas principais aparecem dentro dos reflexos (`baseVerba/.../verbaDeCalculo/Calculada`), e o histórico
  salarial da base aparece como `historicoSalarial/HistoricoSalarial/internalRef`.
- **Datas:** milissegundos desde 1970, à **meia-noite de Brasília** (UTC−3). `1703300400000` = 23/12/2023.
  Compare só a data.
- **Números:** ponto decimal e precisão longa (`1.5000000000000000000000000`, `0E-25` = zero). Compare arredondando
  (2 casas para valores em R$, 4 para quantidades e divisores, 8 para multiplicadores).
- **Booleanos:** `true`/`false`. **Vazio:** `null`.
- **Texto:** o PJe-Calc grava em **MAIÚSCULAS** e em Latin-1 (`&#193;` = Á). A descrição da verba e o nome do reflexo são
  **cortados em 50 caracteres**. Compare em maiúsculas, sem espaços duplicados, até 50 caracteres.

## 2. Dados do Cálculo — `Calculo/…`

| `.json` | XML | tradução |
|---|---|---|
| `dadosDoCalculo.numeroProcesso` · `telas.….numero_processo` | `processo/Processo/identificador/IdentificadorDoProcesso/{numero, digito, ano, justica, regiao, vara}` | `0000618-49.2025.5.10.0006` → numero 618, digito 49, ano 2025, justica 5, regiao 10, vara 6 (sem zeros à esquerda) |
| `telas.….valor_da_causa` | `processo/Processo/valorDaCausa` | número |
| `partes[ATIVO].nome` · `reclamante_nome` | `processo/Processo/reclamante/Reclamante/nome` | maiúsculas |
| `partes[ATIVO].documento` · `reclamante_cpf` | `…/Reclamante/numeroDocumentoFiscal` (+ `tipoDocumentoFiscal` = `CPF`) | só dígitos |
| `partes[PASSIVO].nome` · `reclamado_nome` | `processo/Processo/reclamado/Reclamado/nome` | maiúsculas |
| `partes[PASSIVO].documento` · `reclamado_cnpj`/`reclamado_cpf` | `…/Reclamado/numeroDocumentoFiscal` (+ `tipoDocumentoFiscal` `CNPJ`/`CPF`) | só dígitos |
| `dataAdmissao` · `admissao` | `dataAdmissao` | epoch ms |
| `dataDemissao` · `demissao` | `dataDemissao` | epoch ms |
| `dataAjuizamento` · `ajuizamento` | `dataAjuizamento` | epoch ms |
| `dataInicioCalculo` · `data_inicial` | `dataInicioCalculo` | epoch ms |
| `dataTerminoCalculo` · `data_final` | `dataTerminoCalculo` | epoch ms |
| `ultima_remuneracao` / `maior_remuneracao` | `valorUltimaRemuneracao` / `valorMaiorRemuneracao` | número |
| `carga_horaria` | `valorCargaHorariaPadrao` | número (`220.0000`) |
| `sabado_dia_util` | `sabadoDiaUtil` | booleano |
| `prescricao_quinquenal` / `prescricao_fgts` | `prescricaoQuinquenal` / `prescricaoFgts` | booleano |
| `projetar_aviso_indenizado` | `projetaAvisoIndenizado` | booleano |
| `limitar_avos` | `limitarAvosAoPeriodoDoCalculo` | booleano |
| `zerar_valor_negativo` | `zeraValorNegativo` | booleano |
| `feriados_estaduais` / `feriados_municipais` | `consideraFeriadoEstadual` / `consideraFeriadoMunicipal` | booleano |
| `regime` | `regimeDoContrato` | `Tempo Integral` → `INTEGRAL` (visto); `Tempo Parcial` → `PARCIAL` e `Trabalho Intermitente` → `INTERMITENTE` (**a confirmar**) |
| `prazo_aviso_previo` | `apuracaoPrazoDoAvisoPrevio` | `Não apurar` → `NAO_APURAR` e `Informado` → `APURACAO_INFORMADA` (vistos); `Calculado` → `APURACAO_CALCULADA` (**a confirmar**) |
| `dias_aviso_previo` | `prazoAvisoInformado` | inteiro; `null` se o prazo não é `Informado` |
| `comentarios` | `comentarios` | maiúsculas; o `.json` pode ter mais de 255 caracteres e a automação corta |

## 3. Faltas, Férias e Histórico Salarial

| `.json` (`.csv` em `arquivos`) | XML | tradução |
|---|---|---|
| faltas: `INICIO` / `FIM` | `faltas/Set/Falta/dataInicioPeriodoFalta` / `dataTerminoPeriodoFalta` | `dd/mm/aaaa` ↔ epoch ms |
| faltas: `JUSTIFICADA` / `REINICIAR_PER_AQ` | `…/faltaJustificada` / `reiniciarFerias` | `S`/`N` ↔ `true`/`false` |
| faltas: `JUSTIFICATIVA` | `…/justificativaDaFalta` | texto |
| férias: `RELATIVAS` | `listaDeFerias/Set/Ferias/relativa` | `2023/2024` |
| férias: `PRAZO` · `SITUACAO` · `DOBRA` · `ABONO` · `QTD_DIAS_ABONO` | `…/prazo` · `situacao` · `dobraGeral` · `abono` · `quantidadeDiasAbono` | `situacao`: `G` → `GOZADAS`, `GP` → `GOZADAS_PARCIALMENTE`, `I` → `INDENIZADAS`, `P` → `PERDIDAS` (vistos na tela); `S`/`N` ↔ booleano |
| férias: `G1INI`…`G3FIM`, `G1DOBRA`… | `…/dataInicialDoPeriodoDeGozo1`…`dataFinalDoPeriodoDeGozo3`, `dobraDoPeriodoDeGozo1`… | epoch ms; booleano |
| histórico: título da 2ª coluna | `historicosSalariais/Set/HistoricoSalarial/nome` | maiúsculas |
| histórico: parcela variável | `…/tipoVariacaoParcela` = `VARIAVEL` | a automação sempre cria como variável |
| histórico: cada linha `MM/AAAA;valor;FGTS;FGTS_REC.;CS;CS_REC.` | `…/ocorrencias/…/OcorrenciaDoHistoricoSalarial/{dataOcorrencia, valor, incidenciaFGTS, recolhidoFGTS, incidenciaINSS, recolhidoINSS}` | `dataOcorrencia` = 1º dia do mês em epoch ms; `S`/`N` ↔ booleano. Competências fora do período do cálculo existem com valor `0.00` |

## 4. Verbas — `verbas/Set/…`

As verbas principais **não ficam numa lista própria**: `verbas/Set` traz os **reflexos** (`Reflexo`), e cada principal
(`Calculada`) aparece dentro da base de um reflexo ou por `internalRef`. Para achar todas as principais, junte todos os
`Calculada` com `<id>` do XML.

| `.json` (`verbas[]`) | XML (`Calculada`) | tradução |
|---|---|---|
| `descricao` | `descricao` (e `nome`) | maiúsculas, Latin-1, até 50 caracteres |
| `expresso` | — | **não conferível**: o `.PJC` não guarda o item do Lançamento Expresso (só o `assuntoCnj`) |
| `parcela` | `tipoVariacaoParcela` | `FIXA`/`VARIAVEL` |
| `valor` | o tipo do elemento: `Calculada` (visto) ou, para `INFORMADO`, outro elemento (**a confirmar**: as amostras só têm calculadas) | `CALCULADO`/`INFORMADO` |
| `caracteristica` | `caracteristica` | mesmo código |
| `ocorrenciaPagamento` | `ocorrenciaDePagamento` | mesmo código |
| `incidencias.{inss, irpf, fgts, previdenciaPrivada, pensaoAlimenticia}` | `incidenciaINSS`, `incidenciaIRPF`, `incidenciaFGTS`, `incidenciaPrevidenciaPrivada`, `incidenciaPensaoAlimenticia` | booleano. Com `comporPrincipal = NAO`, o PJe-Calc não aplica INSS/FGTS/Previdência (a automação registra pendência `automacao`) |
| `jurosSumula439` | `jurosDoAjuizamento` | `true` → `OCORRENCIAS_VENCIDAS_E_VINCENDAS`; `false` → `OCORRENCIAS_VENCIDAS` |
| `geraReflexo` / `gerarPrincipal` | `gerarReflexo` / `gerarPrincipal` | mesmo código |
| `comporPrincipal` | `comporPrincipal` | `true` ↔ `SIM` (visto); `false` ↔ `NAO` (**a confirmar**) |
| `zerarValorNegativo` | `zeraValorNegativo` | booleano |
| `dobrarValor` | `formula/FormulaCalculada/dobra` | booleano |
| `excluirFaltaJustificada` · `excluirFaltaNaoJustificada` · `excluirFeriasGozadas` | mesmos nomes | booleano |
| `periodo.inicio` / `periodo.termino` | `periodoInicial` / `periodoFinal` | epoch ms |
| `proporcionalidade` | `aplicarProporcionalidade` | booleano |
| `valorDevido` (INFORMADO) | valor informado da verba (**a confirmar** a tag) | número |
| `baseTabelada` | `formula/FormulaCalculada/baseTabelada/BaseTabelada/tipo` | mesmo código |
| `bases[HISTORICO]` | `historicosDaVerbaDoValorDevido/List/HistoricoSalarialDaVerba` com `tipoVinculoHistorico = BASE`, `aplicarProporcionalidade`, `historicoSalarial → nome` | resolva o `internalRef` do histórico para comparar o nome |
| `bases[VERBA]` | `formula/FormulaCalculada/baseVerba/BaseVerba/itens/List/ItemBaseVerba/{integralizar, verbaDeCalculo → descricao}` | `proporcionalizar` do `.json` ↔ `integralizar` `SIM`/`NAO` |
| `divisor.tipo` / `divisor.valor` | `formula/FormulaCalculada/divisor/Divisor/tipo` / `outroValor` | mesmo código; número |
| `multiplicador` | `formula/FormulaCalculada/multiplicador/Multiplicador/outroValor` | número |
| `quantidade.tipo` / `.valor` / `.proporcionalidade` | `formula/FormulaCalculada/quantidade/Quantidade/tipo` / `valorInformado` / `aplicarProporcionalidade` | mesmo código (`AVOS`/`APURADA` saem da característica) |
| `quantidade.calendario` | `…/Quantidade/tipoImportadaCalendarioEnum` | código do calendário (**a confirmar** os nomes) |
| `valorPago.tipo` / `.valor` / `.quantidade` / `.proporcionalidade` | `formula/FormulaCalculada/valorPago/ValorPago/tipo` / `valorInformado` / `quantidade` / `aplicarProporcionalidade` | mesmo código; números |
| `valorPago.base` | `…/ValorPago/baseTabelada` | mesmo código |
| `valorPago.bases[]` | `historicosDaVerbaDoValorPago/List/HistoricoSalarialDaVerba` | como `bases[HISTORICO]` |
| `comentario` | `comentarios` | maiúsculas |

### Reflexos

| `.json` | XML (`verbas/Set/Reflexo`) | tradução |
|---|---|---|
| `reflexos.{X} = true` | `Reflexo` cuja base (`formula/FormulaReflexo/baseVerba/…/verbaDeCalculo`) é a principal e `ativo = true` | `false`/ausente ↔ o reflexo existe com `ativo = false` (o PJe-Calc gera sozinho) |
| qual reflexo é qual | `nome` = `<TIPO> SOBRE <descrição da principal>` (cortado em 50+) e `descricao` = `<TIPO>`: `13º SALÁRIO`, `AVISO PRÉVIO`, `FÉRIAS + 1/3`, `MULTA DO ARTIGO 477 DA CLT`, `REPOUSO SEMANAL REMUNERADO E FERIADO` | casar pelo prefixo de `nome` ou por `descricao` |
| `reflexosManuais[]` | `Reflexo` com `descricao` = a descrição do item manual e `assuntoCnj/AssuntoCnj/externalRef` = `assuntoCnj` | demais campos como na tabela da verba (em `formula/FormulaReflexo/…`) |
| `comportamento` · `periodoMedia` · `tratamentoFracaoMes` | `comportamentoDoReflexo` · `periodoMediaReflexo` · `tratamentoDaFracaoDeMesDoReflexo` | mesmo código; `periodoMediaReflexo` vem preenchido mesmo sem média (padrão do PJe-Calc) — só compare com média |

## 5. FGTS · Contribuição Social · Correção · Custas · Honorários

| `.json` | XML | tradução |
|---|---|---|
| `fgts.destino` · `telas.fgts.fgts_destino` | `fgts/Fgts/destinoDoFgts` | `RECOLHER` → `DEPOSITAR` (visto); `PAGAR` → **a confirmar** |
| `fgts.multaDoFgts` · `fgts_calcular_multa` | `fgts/Fgts/multa` | booleano |
| CNAE (`atividadeEconomica` · `cs_atividade_economica`) | `inss/Inss/atividadeEconomica/AtividadeEconomica/externalRef` (+ `tipoAliquotaEmpregador = POR_ATIVIDADE_ECONOMICA`) | id da atividade na tabela do PJe-Calc 2.16.0 (ex.: `505` = "Fornecimento de alimentos preparados preponderantemente para empresas"); traduza pela tabela de atividades e compare a descrição. `null` = nenhuma atividade gravada (ex.: CNAE não encontrada) |
| `cj_correcao` | `parametrosDeAtualizacao/ParametrosDeAtualizacao/indiceTrabalhista` | `IPCA-E` → `IPCAE` (visto); demais **a confirmar** (o texto da tela sem pontuação, em maiúsculas) |
| `custas.tipoDeCustasDeConhecimentoDoReclamado` | `custasJudiciais/CustasJudiciais/tipoDeCustasDeConhecimentoDoReclamado` | mesmo código |
| `custas.dataVencimentoConhecimentoDoReclamado` / `valorConhecimentoDoReclamado` | `…/dataVencimentoConhecimentoDoReclamado` / `valorConhecimentoDoReclamado` | epoch ms; número (com `CALCULADA_2_POR_CENTO` o valor é calculado pelo PJe-Calc) |
| `custas.custasPagasDoReclamado[]` | `custasJudiciais/CustasJudiciais/…` (lista de custas recolhidas) | **a confirmar**: os dois cálculos lidos não têm custa recolhida lançada |
| `honorarios[].descricao` · `tipoHonorario` · `tipoDeDevedor` · `nomeCredor` | `honorarios/Set/Honorario/descricao` · `tipoHonorario` · `tipoDeDevedor` · `nomeCredor` | maiúsculas; no honorário **INFORMADO a descrição é cortada em 50 caracteres** (compare os 50 primeiros); no CALCULADO ela fica inteira (58 e 79 caracteres nos cálculos 602/603); mesmo código (`RECLAMADO`, `RECLAMANTE`) |
| `honorarios[].tipoValor` · `valor` · `dataVencimento` | `…/tipoValor` · `valor` · `dataVencimento` | número; epoch ms. Em `CALCULADO`, `valor` é o resultado |
| `honorarios[].aliquota` | `…/aliquota` | **o `.json` usa fração (`0.15`), o XML usa percentual (`15.00`)** |
| `honorarios[].baseParaApuracao` | `…/baseParaApuracao` | mesmo código (`BRUTO`, …) |
| `honorarios[].tipoCobrancaReclamante` | `…/tipoCobrancaReclamante` | `COBRAR` → `COBRAR`; `DESCONTAR` → `DESCONTAR_CREDITO` (vistos). **Só vale com devedor `RECLAMANTE`**: com devedor reclamado o campo não aparece e o PJe-Calc grava `DESCONTAR_CREDITO` — não é divergência |
| `multas[]` | `multas/Set/…` | **a confirmar**: os dois cálculos lidos não têm multa lançada |

## 6. O que não dá para conferir no `.PJC`

| campo do `.json` | por quê |
|---|---|
| `verbas[].expresso` | o `.PJC` não guarda o item do Lançamento Expresso |
| `uf` / `municipio` | `municipio/Municipio/externalRef` é o código interno do PJe-Calc (ex.: `9701`), não o nome |
| pontos facultativos | `pontosFacultativos/Set/ItemPontoFacultativo/pontoFacultativo/Feriado/externalRef` é um identificador interno |
| advogados das partes | o `.json` não os envia |
| `assuntoCnj` das verbas principais | o PJe-Calc o define pelo item do Expresso (ex.: `2086`), não pelo pedido |
| valores calculados (total de honorários, custas 2%, ocorrências mês a mês das verbas) | são resultado da liquidação, não do pedido |

Os itens marcados **a confirmar** ainda não apareceram nos cálculos lidos; quando aparecerem, este documento é atualizado.
