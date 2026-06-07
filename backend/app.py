# app.py
# Ponto de entrada da API do Fintrack

from typing import Generator, List
from datetime import date

from fastapi import Depends, FastAPI, HTTPException
from contextlib import asynccontextmanager
from sqlalchemy import func
from sqlalchemy.orm import Session

from backend.database import Base, SessionLocal, engine
from backend.models import (
    CategoriaSaldoRead,
    Despesa,
    DespesaCreate,
    DespesaRead,
    Receita,
    ReceitaCreate,
    ReceitaRead,
    ResumoRead,
)

@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield

app = FastAPI(title="Fintrack API", version="0.1.0", lifespan=lifespan)

def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.get("/")
def root() -> dict:
    return {"message": "Bem-vindo ao Fintrack API!"}


@app.post("/receitas", response_model=ReceitaRead, status_code=201)
def criar_receita(receita: ReceitaCreate, db: Session = Depends(get_db)) -> Receita:
    db_receita = Receita(
        descricao=receita.descricao,
        valor=receita.valor,
        data=receita.data,
        categoria=receita.categoria,
    )
    db.add(db_receita)
    db.commit()
    db.refresh(db_receita)
    return db_receita


@app.get("/receitas", response_model=List[ReceitaRead])
def listar_receitas(db: Session = Depends(get_db)) -> List[Receita]:
    return db.query(Receita).order_by(Receita.data.desc(), Receita.id.desc()).all()


@app.post("/despesas", response_model=DespesaRead, status_code=201)
def criar_despesa(despesa: DespesaCreate, db: Session = Depends(get_db)) -> Despesa:
    db_despesa = Despesa(
        descricao=despesa.descricao,
        valor=despesa.valor,
        data=despesa.data,
        categoria=despesa.categoria,
    )
    db.add(db_despesa)
    db.commit()
    db.refresh(db_despesa)
    return db_despesa


@app.get("/despesas", response_model=List[DespesaRead])
def listar_despesas(db: Session = Depends(get_db)) -> List[Despesa]:
    return db.query(Despesa).order_by(Despesa.id.desc()).all()


@app.get("/resumo", response_model=ResumoRead)
def resumo_financeiro(
    data_inicio: date | None = None,
    data_fim: date | None = None,
    db: Session = Depends(get_db),
) -> ResumoRead:
    if data_inicio is not None and data_fim is not None and data_inicio > data_fim:
        raise HTTPException(
            status_code=400,
            detail="Periodo invalido: data_inicio deve ser menor ou igual a data_fim.",
        )

    query_receitas = db.query(func.coalesce(func.sum(Receita.valor), 0.0))
    query_despesas = db.query(func.coalesce(func.sum(Despesa.valor), 0.0))

    if data_inicio is not None:
        query_receitas = query_receitas.filter(Receita.data >= data_inicio)
        query_despesas = query_despesas.filter(Despesa.data >= data_inicio)
    if data_fim is not None:
        query_receitas = query_receitas.filter(Receita.data <= data_fim)
        query_despesas = query_despesas.filter(Despesa.data <= data_fim)

    total_receitas = query_receitas.scalar()
    total_despesas = query_despesas.scalar()

    receitas = float(total_receitas or 0.0)
    despesas = float(total_despesas or 0.0)
    return ResumoRead(
        total_receitas=receitas,
        total_despesas=despesas,
        saldo=receitas - despesas,
    )


@app.get("/resumo/categorias", response_model=List[CategoriaSaldoRead])
def resumo_por_categoria(db: Session = Depends(get_db)) -> List[CategoriaSaldoRead]:
    receitas_por_categoria = dict(
        db.query(Receita.categoria, func.sum(Receita.valor))
        .group_by(Receita.categoria)
        .all()
    )
    despesas_por_categoria = dict(
        db.query(Despesa.categoria, func.sum(Despesa.valor))
        .group_by(Despesa.categoria)
        .all()
    )

    categorias = sorted(set(receitas_por_categoria) | set(despesas_por_categoria))
    return [
        CategoriaSaldoRead(
            categoria=categoria,
            total_receitas=float(receitas_por_categoria.get(categoria, 0.0) or 0.0),
            total_despesas=float(despesas_por_categoria.get(categoria, 0.0) or 0.0),
            saldo=float(receitas_por_categoria.get(categoria, 0.0) or 0.0)
            - float(despesas_por_categoria.get(categoria, 0.0) or 0.0),
        )
        for categoria in categorias
    ]

