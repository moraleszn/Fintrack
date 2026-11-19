# Fintrack

Aplicacao de controle financeiro pessoal: API FastAPI + SQLAlchemy (SQLite por padrao), frontend React (Vite + TypeScript) e dashboard interno em Streamlit.

## Comandos

Rodar a partir da raiz do projeto, usando o venv `.venv`.

```powershell
# API (dev, com reload)
.venv\Scripts\python.exe -m uvicorn backend.app:app --reload

# Testes
.venv\Scripts\python.exe -m pytest -q

# Migracoes (Alembic)
.venv\Scripts\python.exe -m alembic upgrade head                       # aplica migracoes
.venv\Scripts\python.exe -m alembic revision --autogenerate -m "..."   # gera apos mudar models.py
.venv\Scripts\python.exe -m alembic current                             # mostra a revisao atual

# Dashboard interno (Streamlit)
.venv\Scripts\streamlit.exe run frontend/streamlit_app.py

# Frontend React
cd frontend\react-app
npm.cmd run dev      # http://localhost:5173
npm.cmd run build
npm.cmd run lint
```

Observacao: `npm` (o `.ps1`) e bloqueado pela ExecutionPolicy do PowerShell. Usar `npm.cmd` ou `Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned`.

## Estrutura

```text
backend/
  app.py         # rotas da API
  models.py      # tabelas SQLAlchemy + schemas Pydantic
  database.py    # engine, session, Base
alembic/
  env.py         # aponta para Base.metadata e FINTRACK_DATABASE_URL
  versions/      # migracoes versionadas
alembic.ini
frontend/
  streamlit_app.py     # dashboard interno de analise
  react-app/           # frontend oficial (Vite + React + TS)
tests/
  test_app.py          # testes do backend (SQLite em memoria)
```

## Convencoes de backend

- Dinheiro SEMPRE com `Decimal` e `Numeric(12, 2)`; nunca `float`.
- A API serializa `Decimal` como string JSON (ex.: `"5500.00"`). O frontend converte com `Number()` para exibir.
- Schemas Pydantic separados: `Create`, `Update` e `Read`. No `PATCH`, usar `exclude_unset=True`.
- `Receita` e `Despesa` herdam de `Lancamento` (classe abstrata).
- Esquema do banco versionado com Alembic. Apos mudar `models.py`, gerar migracao com `alembic revision --autogenerate` e revisar o arquivo antes de `alembic upgrade head`. A API nao usa mais `create_all`.
- Testes: banco SQLite em memoria (`StaticPool`) e `app.dependency_overrides` no `get_db`. Nenhum teste toca o banco de dev.
- Mensagens de erro e nomes de variavel em portugues sem acentos (padrao ja existente no codigo).

## Convencoes de frontend

- Cliente HTTP em `src/api.ts` (fetch nativo, sem Axios por enquanto).
- Tipos compartilhados em `src/types.ts`.
- `useApiData` (em `src/useApiData.ts`) para buscar dados; nao fazer `setState` sincrono dentro de `useEffect`.
- Valores monetarios formatados com `Intl.NumberFormat` em `src/format.ts`.
- Porta de dev fixa `5173` (CORS do backend ja configurado).

## Regras importantes

- Nao comitar segredos, `.env`, banco (`*.db`) nem `node_modules/`/`dist/`.
- Manter testes verdes antes de encerrar uma tarefa.
- O Streamlit e ferramenta interna; o produto e o React.
