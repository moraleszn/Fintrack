# app.py
# Ponto de entrada da API do Fintrack

from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from database import SessionLocal
from typing import List
from models import Receita, Despesa, ReceitaCreate, DespesaCreate


# Endpoints de API para o Fintrack
app = FastAPI()

# Função para obter a sessão do banco em cada requisição
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.post("/receitas", response_model=ReceitaCreate)
def criar_receita(receita: ReceitaCreate, db: Session = Depends(get_db)):
    # Cria um objeto Receita do SQLAlchemy
    db_receita = Receita(
        descricao=receita.descricao,
        valor=receita.valor,
        data=receita.data,
        categoria=receita.categoria
    )

@app.post("/despesas")
def criar_despesa(despesa: DespesaCreate):
    despesas.append(despesa)
    return despesa

@app.get("/receitas")
def listar_receitas(receita: Receita):
    return receitas

@app.get("/despesas")
def listar_despesas(despesa: Despesa):
    return despesas

