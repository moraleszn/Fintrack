# app.py
# Ponto de entrada da API do Fintrack

import os
from datetime import date
from decimal import Decimal
from typing import Generator, List

from fastapi import Depends, FastAPI, HTTPException, Query, Response, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from backend.database import SessionLocal
from backend.models import (
    CategoriaSaldoRead,
    Despesa,
    DespesaCreate,
    DespesaRead,
    DespesaUpdate,
    Receita,
    ReceitaCreate,
    ReceitaRead,
    ReceitaUpdate,
    ResumoRead,
)


app = FastAPI(title="Fintrack API", version="0.1.0")

origens_permitidas = [
    origem.strip()
    for origem in os.getenv(
        "FINTRACK_CORS_ORIGINS",
        "http://localhost:3000,http://127.0.0.1:3000,http://localhost:5173,http://127.0.0.1:5173,http://localhost:8501,http://127.0.0.1:8501",
    ).split(",")
    if origem.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origens_permitidas,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def validar_periodo(data_inicio: date | None, data_fim: date | None) -> None:
    if data_inicio is not None and data_fim is not None and data_inicio > data_fim:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Periodo invalido: data_inicio deve ser menor ou igual a data_fim.",
        )


def buscar_ou_404(db: Session, modelo, id_lancamento: int):
    lancamento = db.get(modelo, id_lancamento)
    if lancamento is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Lancamento {id_lancamento} nao encontrado.",
        )
    return lancamento


def para_moeda(valor) -> Decimal:
    return Decimal(str(valor if valor is not None else Decimal("0"))).quantize(
        Decimal("0.01")
    )


def aplicar_filtros_resumo(stmt, modelo, data_inicio, data_fim, categoria):
    if data_inicio is not None:
        stmt = stmt.where(modelo.data >= data_inicio)
    if data_fim is not None:
        stmt = stmt.where(modelo.data <= data_fim)
    if categoria is not None:
        stmt = stmt.where(modelo.categoria == categoria)
    return stmt


@app.get("/")
def root() -> dict:
    return {"message": "Bem-vindo ao Fintrack API!"}


@app.post(
    "/receitas", response_model=ReceitaRead, status_code=status.HTTP_201_CREATED
)
def criar_receita(receita: ReceitaCreate, db: Session = Depends(get_db)) -> Receita:
    db_receita = Receita(**receita.model_dump())
    db.add(db_receita)
    db.commit()
    db.refresh(db_receita)
    return db_receita


@app.get("/receitas", response_model=List[ReceitaRead])
def listar_receitas(
    data_inicio: date | None = None,
    data_fim: date | None = None,
    categoria: str | None = None,
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
) -> List[Receita]:
    validar_periodo(data_inicio, data_fim)
    stmt = select(Receita)
    if data_inicio is not None:
        stmt = stmt.where(Receita.data >= data_inicio)
    if data_fim is not None:
        stmt = stmt.where(Receita.data <= data_fim)
    if categoria is not None:
        stmt = stmt.where(Receita.categoria == categoria)
    stmt = stmt.order_by(Receita.data.desc(), Receita.id.desc()).limit(limit).offset(offset)
    return list(db.execute(stmt).scalars().all())


@app.get("/receitas/{id_receita}", response_model=ReceitaRead)
def buscar_receita(id_receita: int, db: Session = Depends(get_db)) -> Receita:
    return buscar_ou_404(db, Receita, id_receita)


@app.patch("/receitas/{id_receita}", response_model=ReceitaRead)
def atualizar_receita(
    id_receita: int, receita: ReceitaUpdate, db: Session = Depends(get_db)
) -> Receita:
    db_receita = buscar_ou_404(db, Receita, id_receita)
    for campo, valor in receita.model_dump(exclude_unset=True, exclude_none=True).items():
        setattr(db_receita, campo, valor)
    db.commit()
    db.refresh(db_receita)
    return db_receita


@app.delete("/receitas/{id_receita}", status_code=status.HTTP_204_NO_CONTENT)
def excluir_receita(id_receita: int, db: Session = Depends(get_db)) -> Response:
    db_receita = buscar_ou_404(db, Receita, id_receita)
    db.delete(db_receita)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@app.post(
    "/despesas", response_model=DespesaRead, status_code=status.HTTP_201_CREATED
)
def criar_despesa(despesa: DespesaCreate, db: Session = Depends(get_db)) -> Despesa:
    db_despesa = Despesa(**despesa.model_dump())
    db.add(db_despesa)
    db.commit()
    db.refresh(db_despesa)
    return db_despesa


@app.get("/despesas", response_model=List[DespesaRead])
def listar_despesas(
    data_inicio: date | None = None,
    data_fim: date | None = None,
    categoria: str | None = None,
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
) -> List[Despesa]:
    validar_periodo(data_inicio, data_fim)
    stmt = select(Despesa)
    if data_inicio is not None:
        stmt = stmt.where(Despesa.data >= data_inicio)
    if data_fim is not None:
        stmt = stmt.where(Despesa.data <= data_fim)
    if categoria is not None:
        stmt = stmt.where(Despesa.categoria == categoria)
    stmt = stmt.order_by(Despesa.data.desc(), Despesa.id.desc()).limit(limit).offset(offset)
    return list(db.execute(stmt).scalars().all())


@app.get("/despesas/{id_despesa}", response_model=DespesaRead)
def buscar_despesa(id_despesa: int, db: Session = Depends(get_db)) -> Despesa:
    return buscar_ou_404(db, Despesa, id_despesa)


@app.patch("/despesas/{id_despesa}", response_model=DespesaRead)
def atualizar_despesa(
    id_despesa: int, despesa: DespesaUpdate, db: Session = Depends(get_db)
) -> Despesa:
    db_despesa = buscar_ou_404(db, Despesa, id_despesa)
    for campo, valor in despesa.model_dump(exclude_unset=True, exclude_none=True).items():
        setattr(db_despesa, campo, valor)
    db.commit()
    db.refresh(db_despesa)
    return db_despesa


@app.delete("/despesas/{id_despesa}", status_code=status.HTTP_204_NO_CONTENT)
def excluir_despesa(id_despesa: int, db: Session = Depends(get_db)) -> Response:
    db_despesa = buscar_ou_404(db, Despesa, id_despesa)
    db.delete(db_despesa)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@app.get("/resumo", response_model=ResumoRead)
def resumo_financeiro(
    data_inicio: date | None = None,
    data_fim: date | None = None,
    categoria: str | None = None,
    db: Session = Depends(get_db),
) -> ResumoRead:
    validar_periodo(data_inicio, data_fim)

    stmt_receitas = aplicar_filtros_resumo(
        select(func.coalesce(func.sum(Receita.valor), Decimal("0"))),
        Receita,
        data_inicio,
        data_fim,
        categoria,
    )
    stmt_despesas = aplicar_filtros_resumo(
        select(func.coalesce(func.sum(Despesa.valor), Decimal("0"))),
        Despesa,
        data_inicio,
        data_fim,
        categoria,
    )

    receitas = para_moeda(db.scalar(stmt_receitas))
    despesas = para_moeda(db.scalar(stmt_despesas))
    return ResumoRead(
        total_receitas=receitas,
        total_despesas=despesas,
        saldo=receitas - despesas,
    )


@app.get("/resumo/categorias", response_model=List[CategoriaSaldoRead])
def resumo_por_categoria(
    data_inicio: date | None = None,
    data_fim: date | None = None,
    db: Session = Depends(get_db),
) -> List[CategoriaSaldoRead]:
    validar_periodo(data_inicio, data_fim)

    stmt_receitas = select(Receita.categoria, func.sum(Receita.valor)).group_by(
        Receita.categoria
    )
    stmt_despesas = select(Despesa.categoria, func.sum(Despesa.valor)).group_by(
        Despesa.categoria
    )

    if data_inicio is not None:
        stmt_receitas = stmt_receitas.where(Receita.data >= data_inicio)
        stmt_despesas = stmt_despesas.where(Despesa.data >= data_inicio)
    if data_fim is not None:
        stmt_receitas = stmt_receitas.where(Receita.data <= data_fim)
        stmt_despesas = stmt_despesas.where(Despesa.data <= data_fim)

    receitas_por_categoria = {
        categoria: para_moeda(total)
        for categoria, total in db.execute(stmt_receitas).all()
    }
    despesas_por_categoria = {
        categoria: para_moeda(total)
        for categoria, total in db.execute(stmt_despesas).all()
    }

    categorias = sorted(set(receitas_por_categoria) | set(despesas_por_categoria))
    return [
        CategoriaSaldoRead(
            categoria=categoria,
            total_receitas=receitas_por_categoria.get(categoria, Decimal("0")),
            total_despesas=despesas_por_categoria.get(categoria, Decimal("0")),
            saldo=receitas_por_categoria.get(categoria, Decimal("0"))
            - despesas_por_categoria.get(categoria, Decimal("0")),
        )
        for categoria in categorias
    ]
