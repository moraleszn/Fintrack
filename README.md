# Fintrack

Aplicacao de controle financeiro pessoal com API FastAPI, persistencia em SQLite e dashboard em Streamlit.

## Estrutura do Projeto

```text
Fintrack/
├── backend/
│   ├── app.py              # rotas da API
│   ├── database.py         # engine, sessao e configuracao do banco
│   ├── models.py           # tabelas SQLAlchemy e schemas Pydantic
│   └── requirements.txt
├── frontend/
│   ├── streamlit_app.py    # dashboard interno de analise
│   └── react-app/          # frontend oficial (Vite + React + TypeScript)
├── data/
│   └── exemplo.csv
├── notebooks/
│   └── exploracao.ipynb
├── tests/
│   └── test_app.py
├── alembic/
│   ├── env.py              # conexao e metadata usados pelas migracoes
│   └── versions/           # migracoes geradas
├── alembic.ini
├── pytest.ini
└── README.md
```

## Funcionalidades

- CRUD completo de receitas e despesas (`POST`, `GET`, `PATCH`, `DELETE`).
- Filtros por periodo e categoria, com paginacao (`limit`/`offset`) nas listagens.
- Resumo de totais e saldo, e consolidacao por categoria.
- Orcamento mensal por categoria com planejado x realizado, projecao de gasto ate o fim do mes e status (`ok`, `atencao`, `estourado`).
- Recorrencias (receita/despesa) com dia de vencimento, inicio/fim e pausa; geracao sob demanda idempotente (rodar de novo nao duplica).
- Valores monetarios com `Decimal` e `Numeric(12, 2)` (evita erros de ponto flutuante).
- Validacao: valor positivo com ate 2 casas decimais e descricao/categoria nao vazias.
- CORS configurado para permitir um frontend React futuro.
- Dashboard Streamlit com metricas, tabelas, formularios de edicao/exclusao e grafico por categoria.
- Frontend React (Vite + TypeScript) com resumo, CRUD de lancamentos, filtros e saldo por categoria.
- Migracoes de banco com Alembic (esquema versionado, sem depender de `create_all`).
- Testes com banco SQLite em memoria, isolados entre si.

## Requisitos

- Python 3.10 ou superior

## Como Executar Localmente

### 1. Criar e ativar ambiente virtual

Linux/macOS:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Windows (PowerShell):

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

### 2. Instalar dependencias

```bash
pip install -r backend/requirements.txt
```

### 3. Rodar migracoes (primeira vez ou apos mudar os modelos)

Na raiz do projeto:

```bash
alembic upgrade head
```

Isso cria/atualiza as tabelas do banco. Em um clone novo, rode antes de subir a API.

### 4. Rodar API

Na raiz do projeto:

```bash
uvicorn backend.app:app --reload
```

- API: http://127.0.0.1:8000
- Documentacao interativa: http://127.0.0.1:8000/docs

### 5. Rodar testes

```bash
pytest -q
```

### 6. Rodar dashboard Streamlit

Em outro terminal, na raiz do projeto:

```bash
streamlit run frontend/streamlit_app.py
```

O dashboard assume que a API esteja em `http://127.0.0.1:8000`. Para trocar, use o campo "URL da API" na sidebar ou a variavel `FINTRACK_API_URL`.

### 7. Rodar frontend React (Vite)

Em outro terminal:

```bash
cd frontend/react-app
npm install
npm run dev
```

- Frontend: http://localhost:5173
- Build de producao: `npm run build` (gera `frontend/react-app/dist`)
- Lint: `npm run lint`

O frontend le `VITE_API_URL` (padrao `http://127.0.0.1:8000`). Copie `.env.example` para `.env` se precisar trocar.

## Variaveis de Ambiente

| Variavel | Padrao | Finalidade |
| --- | --- | --- |
| `FINTRACK_DATABASE_URL` | `sqlite:///./fintrack.db` | URL do banco usado pela API |
| `FINTRACK_CORS_ORIGINS` | `localhost:3000`, `127.0.0.1:3000`, `localhost:5173`, `127.0.0.1:5173`, `localhost:8501`, `127.0.0.1:8501` | Origens permitidas no CORS (separadas por virgula) |
| `FINTRACK_API_URL` | `http://127.0.0.1:8000` | URL usada pelo Streamlit para chamar a API |
| `VITE_API_URL` | `http://127.0.0.1:8000` | URL usada pelo frontend React para chamar a API |

Exemplo (PowerShell):

```powershell
$env:FINTRACK_DATABASE_URL = "sqlite:///./fintrack_dev.db"
```

## Endpoints

| Metodo | Rota | Descricao |
| --- | --- | --- |
| `GET` | `/` | Mensagem de boas-vindas |
| `POST` | `/receitas` | Cria receita |
| `GET` | `/receitas` | Lista receitas com filtros e paginacao |
| `GET` | `/receitas/{id}` | Busca uma receita |
| `PATCH` | `/receitas/{id}` | Atualiza campos enviados |
| `DELETE` | `/receitas/{id}` | Exclui receita (204) |
| `POST` | `/despesas` | Cria despesa |
| `GET` | `/despesas` | Lista despesas com filtros e paginacao |
| `GET` | `/despesas/{id}` | Busca uma despesa |
| `PATCH` | `/despesas/{id}` | Atualiza campos enviados |
| `DELETE` | `/despesas/{id}` | Exclui despesa (204) |
| `GET` | `/resumo` | Totais e saldo, com filtros |
| `GET` | `/resumo/categorias` | Totais e saldo por categoria, com filtro de periodo |
| `POST` | `/orcamentos` | Cria orcamento mensal (409 se ja existir para a categoria no periodo) |
| `GET` | `/orcamentos` | Lista orcamentos, filtravel por `ano` e `mes` |
| `GET` | `/orcamentos/{id}` | Busca um orcamento |
| `PATCH` | `/orcamentos/{id}` | Atualiza categoria e/ou limite |
| `DELETE` | `/orcamentos/{id}` | Exclui orcamento (204) |
| `GET` | `/orcamentos/desempenho` | Planejado x realizado, projecao e status por categoria (`ano` e `mes` obrigatorios) |
| `POST` | `/recorrencias` | Cria recorrencia (receita ou despesa) |
| `GET` | `/recorrencias` | Lista recorrencias, filtravel por `tipo` e `ativa` |
| `GET` | `/recorrencias/{id}` | Busca uma recorrencia |
| `PATCH` | `/recorrencias/{id}` | Atualiza valor, categoria, dia, data fim ou pausa |
| `DELETE` | `/recorrencias/{id}` | Exclui a recorrencia mantendo os lancamentos ja gerados |
| `POST` | `/recorrencias/processar` | Gera lancamentos ate `ate` (padrao hoje); idempotente |

Exemplo de corpo para criacao:

```json
{
  "descricao": "Salario",
  "valor": "5500.00",
  "data": "2026-06-26",
  "categoria": "Trabalho"
}
```

## Decisoes que valem estudar

- **Decimal em vez de float:** `0.1 + 0.2` em ponto flutuante nao da `0.3`. Em dinheiro isso gera divergencia; `Decimal` com 2 casas resolve. Note que a API serializa `Decimal` como string JSON (`"5500.00"`), por isso o Streamlit converte com `float()` ao exibir.
- **Testes isolados:** a fixture `client` cria um banco SQLite em memoria (`StaticPool`) e substitui a dependencia `get_db` com `app.dependency_overrides`. Nenhum teste escreve no banco de desenvolvimento.
- **Schemas separados:** `Create`, `Update` e `Read` evitam que o cliente envie `id` ou campos que nao deveria. No `PATCH`, `exclude_unset=True` so atualiza o que foi enviado.
- **Heranca de modelos:** `Receita` e `Despesa` herdam de `Lancamento` (abstrato), evitando repetir as mesmas colunas.
- **Status calculado no backend:** `estourado` compara realizado x limite; `atencao` cobre 80%+ do limite ou projecao acima dele. A projecao usa `realizado / dias_decorridos * dias_no_mes`, entao meses passados resultam em projecao igual ao realizado. Manter essa regra no backend evita divergencia entre React, Streamlit e futuros clientes.
- **Unicidade no banco, nao so no codigo:** `UniqueConstraint(categoria, ano, mes)` garante um orcamento por categoria/mes mesmo com requisicoes concorrentes; a API traduz `IntegrityError` em `409 Conflict`.
- **Ordem de rotas:** `/orcamentos/desempenho` e `/recorrencias/processar` sao declaradas antes de `/{id}` porque `{id}` recebe `int`; se viessem antes, o nome cairia no validador e retornaria 422.
- **Idempotencia:** gerar recorrencias checa as datas ja existentes por `recorrencia_id`, e um indice unico em `(recorrencia_id, data)` e a rede de seguranca contra concorrencia. Rodar `/recorrencias/processar` duas vezes nao duplica.
- **Exclusao preserva historico:** apagar uma recorrencia apenas desvincula (`recorrencia_id = NULL`) os lancamentos gerados; o passado continua no resumo.
- **Batch mode no SQLite:** SQLite nao suporta `ALTER TABLE ADD CONSTRAINT`, entao a migracao que cria a FK usa `op.batch_alter_table` (recria a tabela copiando os dados). Vale entender esse limite antes de rodar migracoes em SQLite.
- **Alembic em vez de `create_all`:** o esquema do banco e versionado em migracoes (`alembic/versions`). Para criar uma nova migracao apos mudar `models.py`, rode `alembic revision --autogenerate -m "descricao"` e revise o arquivo antes de aplicar com `alembic upgrade head`.

## Observacoes

- O diretorio `frontend/react-app` foi migrado do Create React App para Vite + React + TypeScript e ja consome a API.
- O Streamlit permanece como dashboard interno de analise, enquanto o React e o frontend oficial.
- O banco padrao `fintrack.db` e criado pelas migracoes (`alembic upgrade head`) e esta ignorado pelo Git. A API nao cria mais o schema automaticamente.
