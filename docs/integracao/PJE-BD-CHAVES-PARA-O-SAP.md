# A aba `PJE-BD` que a automação lê — lista completa de chaves

**Para:** desenvolvimento do SAP · **De:** time da automação do PJe-Calc · **Data:** 26/09/2026
**Referência real:** `17329 - Planilha Base v3.41.xlsb` (a planilha que calculou o processo 17329 pela API).

---

## 1. A regra que resolve quase tudo

**Espelhem a `PJE-BD` da v3.41: mesmas chaves, mesma grafia, mesma ordem de linhas e mesmos tipos.**

- Cabeçalho na **linha 2**, colunas exatamente `IDENTIFICADOR` e `INFORMACAO`.
- **A ordem das linhas importa.** Parte das chaves é procurada por "contém" e vale a primeira que casar, e os blocos repetidos (multas, honorários, custas, juros) só são enviados quando a leitura chega na **última chave do bloco** (a "chave de disparo", marcada ⚑ abaixo). Copiar a ordem da v3.41 evita os dois problemas.
- **Grafia:** algumas chaves da v3.41 têm grafia estranha e precisam ser mantidas assim: `ponto_facultutativo_*`, `honorarios_contratuais_alíquota_{n}` (com í), `multas_indenizacoes_base_pje-calc_{n}` (com hífen), `custas_recolhidas_rcdo{n}_*` (sem `_` antes do número).
- **Marcadores de "vazio"** usados na v3.41 e aceitos: `<nao_preenchido>` (também com acento), `-`, `<em branco>`, `<oculto>` ou célula vazia.

### 1.1 Tipos

| O dado é | Gravem como | Exemplo |
|---|---|---|
| data | **número serial do Excel, inteiro** (célula numérica, sem formato de data) | `44179` = 14/12/2020 |
| sim/não de checkbox | **texto** `True` / `False` | `True` |
| opção de lista do PJe-Calc | **texto idêntico ao que aparece na tela** | `Tempo Integral`, `Calculada 2%` |
| valor em reais, carga horária, dias | **número** | `1875.5`, `220`, `36` |
| percentual | **fração decimal** | `0.1` = 10% |
| CPF / CNPJ | número ou texto **só com dígitos** | `13079701410` |

> **Chave ausente ou com marcador de vazio não altera nada:** o campo fica como o PJe-Calc trouxe (antes, em várias telas,
> o `else` desmarcava). Para desmarcar, mande `False`.
>
> **Na tela Dados do Cálculo** a automação passou a aceitar também data de verdade, texto `dd/mm/aaaa`,
> booleano de verdade e número em texto (`"180"`, `"1.875,50"`). **Nas outras telas (FGTS, Contribuição
> Social, Multas, Honorários, Custas, Correção) ainda não** — ali os tipos da tabela acima são obrigatórios.

---

## 2. Dados do Cálculo

Procura por "contém", salvo onde diz *exata*. Chave ausente = o campo fica no padrão do PJe-Calc.

| chave | tipo | valores e observações | v3.41 |
|---|---|---|---|
| `id_processo` | inteiro | usado no log e no retorno | `17329` |
| `numero_processo` | texto CNJ | `NNNNNNN-DD.AAAA.J.TR.OOOO` | `0000511-74.2025.5.06.0019` |
| `valor_da_causa` | número | | `302947.1` |
| `nome_parte1` | texto | reclamante | |
| `doc_parte1` | dígitos | **sempre lançado como CPF**; deve vir **antes** de `tipo_doc_parte1` | `13079701410` |
| `advogado_parte1` | texto | | `<nao_preenchido>` |
| `nome_parte2` | texto | reclamada | |
| `doc_parte2` | dígitos | **sempre lançado como CNPJ** (completa com zeros até 14) | `8845676000198` |
| `advogado_parte2` | texto | | `<nao_preenchido>` |
| `uf` | texto | sigla, igual à lista do PJe-Calc. É a primeira chave que contém "uf" — nenhuma chave antes dela pode conter "uf" | `PE` |
| `municipio` | texto | nome; a automação tira acentos e põe em maiúsculas | `RECIFE` |
| `data_admissao` | data | | `44179` |
| `data_rescisao` | data | vazio = contrato em curso | `45054` |
| `data_ajuizamento` | data | | `45785` |
| `inicio_calculo` | data | | `44179` |
| `termino_calculo` | data | | `45054` |
| `aplicar_prescricao_verbas` | True/False | prescrição quinquenal | `False` |
| `aplicar_prescricao_FGTS` | True/False | **agora lida pela própria chave** (antes repetia a de verbas) | `False` |
| `regime_trabalho` | texto da lista | | `Tempo Integral` |
| `maior_remuneracao` | número ou vazio | **vazio é aceito** e o campo fica em branco, como o PJe-Calc permite | `<nao_preenchido>` |
| `ultima_remuneracao` | número ou vazio | idem | `<nao_preenchido>` |
| `prazo_de_aviso_previo` | texto da lista | se contiver `Informado`, lê a chave seguinte | `Informado` |
| `quantidade_dias_aviso_previo` | inteiro | | `36` |
| `projetar_aviso_previo_indenizado` | True/False | *exata* | `True` |
| `limitar_avos_ao_periodo_do_calculo` | True/False | *exata* | `False` |
| `zerar_valor_negativo_padrao` | True/False | *exata* | `False` |
| `considerar_feriados_estaduais` | True/False | *exata* | `True` |
| `considerar_feriados_municipais` | True/False | *exata* | `True` |
| `carga_horaria` | número | *exata*; **é o divisor padrão** — `180` passa a entrar como 180,00 | `220` |
| `sabado_como_dia_util` | True/False | *exata* | `True` |
| `ponto_facultutativo_sextafeirasanta` | True/False | **lida só se a planilha não tiver a aba `PJE-DIV`**; `False` remove o ponto facultativo | `True` |
| `ponto_facultutativo_corpuschristi` | True/False | idem | `False` |
| `ponto_facultutativo_carnaval` | True/False | idem | `True` |
| `comentarios_parametros` | texto ou vazio | *exata*; máx. 255 caracteres | `<nao_preenchido>` |

---

## 3. FGTS *(exata)*

| chave | tipo | valores | v3.41 |
|---|---|---|---|
| `destino_fgts` | texto | `Pagar`; **qualquer outro valor vira "Recolher"** | `Pagar` |
| `compor_principal` | texto | `Sim` / `Não` (com til) | vazio |
| `multa_fgts` | texto | `Sim` marca a multa; outro valor desmarca | `Sim` |

---

## 4. Contribuição Social *(exata)*

| chave | tipo | valores | v3.41 |
|---|---|---|---|
| `cont_social_apurar_segurado` | True/False | | `True` |
| `cont_social_cobrar_reclamante` | True/False | | `True` |
| `cont_social_com_correcao_trabalhista` | True/False | | `False` |
| `cont_social_salario_pagos` | True/False | | `False` |
| `cont_social_aliquota_segurado` | texto | `Segurado Empregado` · `Empregado Doméstico` · `Fixa` | `Segurado Empregado` |
| `processo_de_agroindustria` | True/False | deve vir **antes** de `entidade_filantropica` | `False` |
| `empresa_com_desoneracao` | True/False | idem; `True` lê os períodos da aba `PJE-DIV` (§8) | `False` |
| `entidade_filantropica` ⚑ | True/False | **ao chegar aqui** aplica a alíquota do empregador (agro → desoneração → filantrópica → CNAE) e o Simples. **Sem esta chave, nada disso é aplicado** | `False` |
| `cont_social_aliquota_empregador` | texto | **descrição completa** do CNAE, como no PJe-Calc (`Atividades de fisioterapia - Pessoa Jurídica`). Sem igualdade exata, só aceitamos o "contém" com **um** candidato; com mais de um, a execução falha e lista os candidatos | `Atividades de fisioterapia` |
| `cont_social_apurar_empresa` | True/False | | `True` |
| `cont_social_apurar_sat` | True/False | | `True` |
| `cont_social_apurar_terceiros` | True/False | | `False` |
| `empresa_enquadrada_simples` | True/False | `True` lê os períodos da aba `PJE-DIV` (§8) | `False` |

---

## 5. Multas e Indenizações — bloco repetido `n = 1, 2, …`

`multas_indenizacoes_qtd` (inteiro): `0` desliga a tela inteira.

Por bloco, nesta ordem, terminando no ⚑:

| chave | tipo | valores |
|---|---|---|
| `multas_indenizacoes_descricao_{n}` | texto | |
| `multas_indenizacoes_credor_{n}` | texto da lista | **`-` pula o bloco** (atenção: qualquer hífen no texto também pula). `Terceiro e Reclamante` / `Terceiro e Reclamado` usam o terceiro |
| `multas_indenizacoes_form_pagto_{n}` | texto | `DESCONTAR` · `COBRAR` |
| `multas_indenizacoes_terceiro_{n}` | texto | nome |
| `multas_indenizacoes_tipo_{n}` | texto | `CALCULADO` · `INFORMADO` |
| `multas_indenizacoes_vcto_{n}` | data | |
| `multas_indenizacoes_valor_{n}` | número | |
| `multas_indenizacoes_base_pje-calc_{n}` | texto da lista | base, quando calculado |
| `multas_indenizacoes_aliquota_{n}` | fração | `0.4` = 40% |
| `multas_indenizacoes_aplicar_juros_{n}` | texto | `SIM` aplica juros |
| `multas_indenizacoes_a_partir_de_{n}` ⚑ | data | **se faltar, este bloco e todos os seguintes são ignorados** |

---

## 6. Honorários

### 6.1 Periciais — sempre lançados como valor informado *(exata)*

`qtd_honorarios_periciais` é lida mas hoje não tem efeito. Por bloco:

`honorarios_periciais_tipo_pericia_pje_calc_{n}` (texto da lista) · `_descricao_{n}` (**`-` pula o bloco**) ·
`_devedor_{n}` (`RECLAMADA` · `RECLAMANTE`) · `_pgto_rcte_{n}` (`DESCONTAR` ou cobrar) · `_data_{n}` (data) ·
`_valor_{n}` (número) · `_nome_credor_{n}` (texto) · **`_cm_{n}` ⚑** (`IPCA-E` troca o índice de correção).

### 6.2 Contratuais *(exata)*

`qtd_honorarios_contratuais`: `0` desliga. Por bloco:

`honorarios_contratuais_tipob_{n}` (texto da lista; **`-` pula**) · `_descricao_{n}` · `_devedor_{n}` (`RECLAMADA` · `RECLAMANTE`) ·
`_partic_{n}` (`DEDUZIR` → descontar; `INFORMAR` pula o bloco) · `_tipo_{n}` (`CALCULADO`; **`INFORMADO` ainda não é lançado**) ·
`_alíquota_{n}` (fração, **com í**) · `_base_{n}` (texto da lista) · **`_nome_{n}` ⚑**.

### 6.3 Sucumbenciais *(contém)*

`qtd_honorarios_sucumbenciais`: `0` desliga. Por bloco:

| chave | tipo | valores |
|---|---|---|
| `honorarios_sucumbenciais_tipo_e_descricao_{n}` | texto, **3 palavras ou mais** | `HONORÁRIOS DE SUCUMBÊNCIA`; **`-` pula** |
| `honorarios_sucumbenciais_descricao_{n}` | texto | |
| `honorarios_sucumbenciais_devedor_{n}` | texto | **`RECLAMADO`** (com O) ou `RECLAMANTE`. ⚠ outro valor **interrompe a automação** |
| `honorarios_sucumbenciais_form_pagto_{n}` | texto | `DESCONTAR` ou cobrar |
| `honorarios_sucumbenciais_tipo_{n}` | texto | `CALCULADO` · `INFORMADO` |
| `honorarios_sucumbenciais_vcto_{n}` | data | informado |
| `honorarios_sucumbenciais_valor_{n}` | número | informado |
| `honorarios_sucumbenciais_aliquota_{n}` | **fração** ou `-` | calculado. ⚠ inteiro derruba a automação — use `0.1`, nunca `10` |
| `honorarios_sucumbenciais_base_{n}` | texto da lista ou `-` | `BRUTO` |
| `honorarios_sucumbenciais_nome_{n}` ⚑ | texto | credor |

---

## 7. Custas Judiciais e Correção, Juros e Multa *(exata)*

### 7.1 Custas

| chave | tipo | valores | v3.41 |
|---|---|---|---|
| `custas_reclamado_conhecimento` | texto | `Não se Aplica` · `Calculada 2%` · `Informada` | `Calculada 2%` |
| `custas_recda_conhecimento_info_vcto` | **texto `dd/mm/aaaa`** (exceção: aqui a data vai como texto) | só com `Informada` | `-` |
| `custas_recda_conhecimento_info_valor` ⚑ | número | só com `Informada` | `-` |
| `qtd_custas_recolhidas` | **inteiro, obrigatório** | ausente ou texto **interrompe a automação** | `1` |
| `custas_recolhidas_rcdo{n}_vencimento` | data | `-` pula | `46168` |
| `custas_recolhidas_rcdo{n}_valor` ⚑ | número | `-` pula | `600` |

Com `qtd_custas_recolhidas = 0` (ou ausente), a escolha das custas do reclamado **é salva** (corrigido em 28/09).

### 7.2 Correção, juros e multa

| chave | tipo | observação | v3.41 |
|---|---|---|---|
| `indice_trabalhista` | texto da lista | | `IPCA-E` |
| `combinar_com_outro_indice` | True/False | | `True` |
| `outro_indice_trabalhista1` | texto da lista | **só um índice adicional é lançado** | `Sem Correção` |
| `outro_indice_trabalhista1_a_partir_de` | data | | `45785` |
| `ignorar_taxa_negativa` ⚑ | True/False | dispara o bloco de índices acima | `False` |
| `aplicar_juros_fase_pre_judicial` | True/False | | `True` |
| `tabelas_de_juros` | texto da lista | | `TRD Juros Simples` |
| `combinar_com_outra_tabela_juros` | True/False | | `True` |
| `tabelas_de_juros2` | texto da lista | **só uma tabela adicional** | `SELIC (Receita Federal)` |
| `outra_tabela_a_partir_de_juros_2` ⚑ | data | dispara o bloco de juros | `45785` |
| `cs_sd_lei_11941` | True/False | | `True` |
| `cs_sd_lei_11941_a_partir_de` | data | `05/03/2009` não é digitado (é o padrão) | `39877` |
| `cs_sd_limitar_multa` | True/False | | `True` |
| `cs_sd_limitar_multa_a_partir_de` | **texto `dd/mm/aaaa`** ou `<em branco>` | exceção: data como texto | `<em branco>` |
| `cs_sd_trabalhista_correcao` ⚑ | True/False | dispara o bloco da Lei 11.941 | `True` |
| `verbas_base_de_juros` | texto da lista | antes da próxima | `Verbas` |
| `cs_sp_previdencia_correcao` | True/False | | `False` |

---

## 8. Outras abas que a automação ainda lê por posição

A `PJE-BD` sozinha **não basta** para uma execução completa. Hoje a automação também lê:

| aba | o que lê | situação para a planilha do SAP |
|---|---|---|
| `PJE HIST-VAL` | Histórico Salarial (quantidade e valores por posição, colunas AF:AP) e a base mensal do INSS da Contribuição Social (AA5 e AB7 em diante) | **obrigatória hoje.** Propomos combinar um layout em tabela (`MES_ANO` + uma coluna por histórico + marcações de FGTS/INSS) e escrevermos o leitor dele — próximo passo |
| `PJE-DIV` | pontos facultativos (B3:D3); desoneração (cabeçalho na linha 8: `DES_INICIO`, `DES_TERMINO`, `DES`, `EMP`, `SAT (%)`); Simples (cabeçalho na linha 21: `SN_INICIO`, `SN_TERMINO`) | **opcional** para pontos facultativos (usamos as chaves do §2 quando ela não existe); **necessária** se `empresa_com_desoneracao` ou `empresa_enquadrada_simples` forem `True` |
| `PJeFaltas` / `PJe Faltas` | exportada inteira como CSV de importação | **aceitamos os dois nomes** e datas de verdade |
| `PJeFérias` / `PJe Férias` | exportada inteira como CSV de importação | idem. Na planilha de 26/09, `PRAZO` saiu `30.0` e `SITUACAO` vazia: gravem `PRAZO` inteiro e `SITUACAO` preenchida (`G`, `I`, …) |

---

## 9. O que mudou do nosso lado nesta rodada

- a planilha base é reconhecida pela aba `CAD` **ou** pela `PJE-BD` (sem `TBCALCULO`); `.xlsm` é aceito;
- `maior_remuneracao` / `ultima_remuneracao`: vazio ou marcador (com ou sem acento) deixa o campo em branco; número é lançado (antes nunca era);
- `aplicar_prescricao_FGTS` lida pela própria chave;
- carga horária, sábado como dia útil, pontos facultativos e as datas aceitam os tipos do `.xlsm`;
- (28/09) chave ausente ou com marcador não desmarca mais nada em FGTS, Contribuição Social e Correção; campos de lista com marcador não são tocados; CNAE ambíguo falha em vez de escolher o primeiro; custas com `qtd_custas_recolhidas = 0` são salvas;
- abas `PJe Faltas` / `PJe Férias` com espaço aceitas, e as datas saem em `dd/mm/aaaa` no CSV.

As chaves presentes na v3.41 e **não lidas** pela automação (135 — `sf_*`, `sd_*`, `prev_privada*`, `ir_*`,
parte de custas e correção) podem continuar sendo geradas; são ignoradas.
