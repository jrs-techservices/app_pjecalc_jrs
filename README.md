# app_pjecalc_jrs — Rôberto, automação do PJe-Calc

Preenche, liquida e exporta cálculos trabalhistas no **PJe-Calc** (versão desktop, `localhost:9257`) sem digitação manual.
Recebe os dados do cálculo e devolve o **`.PJC`** e o **relatório em PDF**.

## Como é usado

| forma | para quem | entrada |
|---|---|---|
| **Serviço HTTP** (principal) | SAP / Sistema de Cálculo | pedido na API com a **planilha base**, a **planilha de verbas** e/ou o **`.json` de lançamentos** |
| **Rôberto desktop** (`main.py`) | equipe, uso manual | janela para escolher as planilhas |

O serviço tem fila (um cálculo por vez), painel web para acompanhar as execuções em tempo real e captura de tela quando algo falha.

## O que a automação preenche

Dados do Cálculo · Faltas · Férias · Histórico Salarial · Verbas e reflexos · FGTS · Contribuição Social ·
Multas e Indenizações · Honorários · Custas · Correção, Juros e Multa → **Liquidar → Imprimir (PDF) → Exportar (.PJC)**.

O que pode ser enviado e os valores aceitos em cada campo estão em
[`docs/integracao/VALORES-ACEITOS-PJECALC.md`](docs/integracao/VALORES-ACEITOS-PJECALC.md).
Pedido com valor fora da lista é **recusado na entrada** (`400`), com o campo e os valores aceitos — não falha no meio da execução.

## Requisitos

- Windows, com o **PJe-Calc aberto** na mesma sessão de usuário
- Firefox
- Python 3.13 e as dependências de `requirements.txt`
- Arquivo de permissão `C:\Windows\System32\FilePathJRS.txt` (sem ele a automação não roda)

## Instalação

```bat
python -m venv env
env\Scripts\pip install -r requirements.txt
copy .env.example .env
```

No `.env`, preencha ao menos **`PJECALC_API_TOKEN`** (token que os clientes enviam no cabeçalho `X-API-Token`).

| variável | uso | padrão |
|---|---|---|
| `PJECALC_API_TOKEN` | token da API (**obrigatório**) | — |
| `PJECALC_PORTA` / `PJECALC_HOST` | porta e interface do serviço | `9300` / `0.0.0.0` |
| `PJECALC_URL` | endereço do PJe-Calc (usado no `/health`) | `http://localhost:9257/...` |
| `PJECALC_RAIZES_PERMITIDAS` | pastas de onde o serviço aceita arquivos, separadas por `;` (vazio = qualquer uma) | vazio |

## Executar

```bat
iniciar_servico.bat
```

Sobe o serviço, grava o console em `logs\` e o reinicia se cair. **Painel:** `http://<máquina>:9300/` ·
**API:** `http://<máquina>:9300/api/v1`.

## API (resumo)

Todas as rotas, exceto `/health`, exigem o cabeçalho `X-API-Token`.

| rota | o que faz |
|---|---|
| `GET /health` | serviço, fila e PJe-Calc estão de pé? |
| `POST /calculos` | enfileira um cálculo |
| `GET /calculos` · `GET /calculos/{id}` | lista / situação, log e arquivos gerados |
| `GET /calculos/{id}/arquivos/{n}` | baixa o `.PJC` ou o PDF |
| `GET /calculos/{id}/captura` | captura de tela da falha |
| `POST /calculos/{id}/cancelar` | cancela um pedido na fila |
| `GET /fila` · `GET /indicadores` | fila atual e números do painel |

Exemplo de pedido:

```json
POST /api/v1/calculos
{
  "lancamentos": "\\\\servidor\\Acervo\\17329_...\\02_gerados\\17329_lancamentos_pjecalc.json",
  "planilha_base": null,
  "planilha_verbas": null,
  "solicitante": "nome@jrspericia.com.br",
  "origem": "sap",
  "navegador": "oculto"
}
```

`navegador`: `oculto` (padrão) ou `interativo` (mostra o Firefox). Situações de um pedido:
`na_fila` → `executando` → `concluido` | `falhou` | `cancelado`. O `.PJC` e o PDF são gravados na pasta do pedido; `concluido` exige os dois. O bloco `pendencias` do `GET /calculos/{id}` lista o que o PJe-Calc recusou ou a automação contornou.

## Estrutura

| pasta / arquivo | conteúdo |
|---|---|
| `server.py`, `servico/` | serviço HTTP: API, fila, execução, painel, leitura do `.json` |
| `Calculo/` | preenchimento de cada tela do PJe-Calc |
| `Operacoes/` | liquidar, imprimir e exportar |
| `pjecalc_main_*.py` | fluxos: só base, só verbas, completo |
| `Tools/` | janela do Rôberto desktop e utilitários |
| `docs/integracao/` | contratos com o SAP |
| `db-sqlite/`, `logs/`, `diagnostico/` | dados locais das execuções (fora do repositório) |

## Cuidados

- Uma execução por vez: o PJe-Calc é um só. Não use o PJe-Calc na mesma máquina enquanto o serviço estiver executando.
- Segredos ficam só no `.env` (fora do repositório).
- A lista de verbas do *Lançamento Expresso* muda quando o PJe-Calc atualiza suas tabelas; se a entrada recusar um item que existe na tela, a lista precisa ser relida (ver a §5 do documento de valores aceitos).
