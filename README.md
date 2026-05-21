# Fintrack

Uma aplicacao de controle financeiro pessoal com API em Python, persistencia em banco de dados e interfaces para visualizacao de dados.

## Estrutura do Projeto

```text
Fintrack/
├── backend/
│   ├── app.py
│   ├── database.py
│   ├── models.py
│   └── requirements.txt
├── frontend/
│   ├── streamlit_app.py
│   └── react-app/
├── data/
│   └── exemplo.csv
├── notebooks/
│   └── exploracao.ipynb
├── tests/
│   └── test_app.py
├── .gitignore
└── README.md
```

## Estado Atual

- API FastAPI criada
- Configuracao de banco com SQLAlchemy em `backend/database.py`
- Modelos `Receita` e `Despesa` definidos em `backend/models.py`
- Endpoint de criacao de receitas usando sessao do banco (em progresso de migracao)
- Streamlit com dashboard inicial
- Teste inicial do endpoint raiz

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

### 2. Instalar dependencias do backend

```bash
pip install -r backend/requirements.txt
```

### 3. Rodar API

```bash
cd backend
uvicorn app:app --reload
```

A API ficara disponivel em:
- http://127.0.0.1:8000
- Documentacao interativa: http://127.0.0.1:8000/docs

### 4. Rodar testes

Na raiz do projeto:

```bash
pytest -q
```

### 5. Rodar frontend Streamlit

Na raiz do projeto:

```bash
streamlit run frontend/streamlit_app.py
```
