# app.py
# Ponto de entrada da API do Fintrack

import calendar
import os
from datetime import date
from decimal import Decimal
from typing import Generator, List

from fastapi import Depends, FastAPI, HTTPException, Query, Response, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import func, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from backend.database import SessionLocal
from backend.models import (
    CategoriaSaldoRead,
    Despesa,
    DespesaCreate,
    DespesaRead,
    DespesaUpdate,
    Orcamento,
    OrcamentoCreate,
    OrcamentoDesempenhoRead,
    OrcamentoRead,
    OrcamentoUpdate,
    ProcessamentoRead,
    Receita,
    ReceitaCreate,
    ReceitaRead,
    ReceitaUpdate,
    Recorrencia,
    RecorrenciaCreate,
    RecorrenciaRead,
    RecorrenciaUpdate,
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


def periodo_do_mes(ano: int, mes: int) -> tuple[date, date]:
    ultimo_dia = calendar.monthrange(ano, mes)[1]
    return date(ano, mes, 1), date(ano, mes, ultimo_dia)


def gerar_ocorrencias(recorrencia: Recorrencia, ate: date) -> list[date]:
    """Datas de vencimento da recorrencia ate a data limite (inclusive)."""
    limite = ate
    if recorrencia.data_fim is not None and recorrencia.data_fim < limite:
        limite = recorrencia.data_fim
    if limite < recorrencia.data_inicio:
        return []

    datas: list[date] = []
    ano, mes = recorrencia.data_inicio.year, recorrencia.data_inicio.month
    while (ano, mes) <= (limite.year, limite.month):
        ultimo_dia = calendar.monthrange(ano, mes)[1]
        dia = min(recorrencia.dia_vencimento, ultimo_dia)
        data_ocorrencia = date(ano, mes, dia)
        if recorrencia.data_inicio <= data_ocorrencia <= limite:
            datas.append(data_ocorrencia)
        mes += 1
        if mes > 12:
            mes = 1
            ano += 1
    return datas


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


@app.post(
    "/orcamentos", response_model=OrcamentoRead, status_code=status.HTTP_201_CREATED
)
def criar_orcamento(
    orcamento: OrcamentoCreate, db: Session = Depends(get_db)
) -> Orcamento:
    db_orcamento = Orcamento(**orcamento.model_dump())
    db.add(db_orcamento)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "Ja existe orcamento para esta categoria no periodo "
                f"{orcamento.mes:02d}/{orcamento.ano}."
            ),
        )
    db.refresh(db_orcamento)
    return db_orcamento


@app.get("/orcamentos", response_model=List[OrcamentoRead])
def listar_orcamentos(
    ano: int | None = Query(default=None, ge=2000, le=2100),
    mes: int | None = Query(default=None, ge=1, le=12),
    db: Session = Depends(get_db),
) -> List[Orcamento]:
    stmt = select(Orcamento)
    if ano is not None:
        stmt = stmt.where(Orcamento.ano == ano)
    if mes is not None:
        stmt = stmt.where(Orcamento.mes == mes)
    stmt = stmt.order_by(Orcamento.ano, Orcamento.mes, Orcamento.categoria)
    return list(db.execute(stmt).scalars().all())


@app.get("/orcamentos/desempenho", response_model=List[OrcamentoDesempenhoRead])
def desempenho_orcamentos(
    ano: int = Query(ge=2000, le=2100),
    mes: int = Query(ge=1, le=12),
    db: Session = Depends(get_db),
) -> List[OrcamentoDesempenhoRead]:
    inicio, fim = periodo_do_mes(ano, mes)

    stmt_gastos = (
        select(Despesa.categoria, func.sum(Despesa.valor))
        .where(Despesa.data >= inicio, Despesa.data <= fim)
        .group_by(Despesa.categoria)
    )
    gastos = {
        categoria: para_moeda(total)
        for categoria, total in db.execute(stmt_gastos).all()
    }

    orcamentos = list(
        db.execute(
            select(Orcamento).where(Orcamento.ano == ano, Orcamento.mes == mes)
        )
        .scalars()
        .all()
    )

    hoje = date.today()
    dias_no_mes = calendar.monthrange(ano, mes)[1]
    if (ano, mes) < (hoje.year, hoje.month):
        dias_decorridos = dias_no_mes
    elif (ano, mes) == (hoje.year, hoje.month):
        dias_decorridos = hoje.day
    else:
        dias_decorridos = 0

    resultado: list[OrcamentoDesempenhoRead] = []
    for orcamento in orcamentos:
        realizado = gastos.get(orcamento.categoria, Decimal("0.00"))
        limite = para_moeda(orcamento.valor_limite)
        percentual = para_moeda(realizado / limite * Decimal("100"))
        if dias_decorridos > 0:
            projecao = para_moeda(
                realizado * Decimal(dias_no_mes) / Decimal(dias_decorridos)
            )
        else:
            projecao = realizado

        if realizado > limite:
            situacao = "estourado"
        elif percentual >= Decimal("80") or projecao > limite:
            situacao = "atencao"
        else:
            situacao = "ok"

        resultado.append(
            OrcamentoDesempenhoRead(
                id=orcamento.id,
                categoria=orcamento.categoria,
                valor_limite=limite,
                total_despesas=realizado,
                disponivel=para_moeda(limite - realizado),
                percentual_usado=percentual,
                projecao_fim_mes=projecao,
                status=situacao,
            )
        )

    resultado.sort(key=lambda item: item.percentual_usado, reverse=True)
    return resultado


@app.get("/orcamentos/{id_orcamento}", response_model=OrcamentoRead)
def buscar_orcamento(
    id_orcamento: int, db: Session = Depends(get_db)
) -> Orcamento:
    return buscar_ou_404(db, Orcamento, id_orcamento)


@app.patch("/orcamentos/{id_orcamento}", response_model=OrcamentoRead)
def atualizar_orcamento(
    id_orcamento: int, orcamento: OrcamentoUpdate, db: Session = Depends(get_db)
) -> Orcamento:
    db_orcamento = buscar_ou_404(db, Orcamento, id_orcamento)
    for campo, valor in orcamento.model_dump(
        exclude_unset=True, exclude_none=True
    ).items():
        setattr(db_orcamento, campo, valor)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Ja existe orcamento para esta categoria no periodo.",
        )
    db.refresh(db_orcamento)
    return db_orcamento


@app.delete(
    "/orcamentos/{id_orcamento}", status_code=status.HTTP_204_NO_CONTENT
)
def excluir_orcamento(
    id_orcamento: int, db: Session = Depends(get_db)
) -> Response:
    db_orcamento = buscar_ou_404(db, Orcamento, id_orcamento)
    db.delete(db_orcamento)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@app.post(
    "/recorrencias",
    response_model=RecorrenciaRead,
    status_code=status.HTTP_201_CREATED,
)
def criar_recorrencia(
    recorrencia: RecorrenciaCreate, db: Session = Depends(get_db)
) -> Recorrencia:
    db_recorrencia = Recorrencia(**recorrencia.model_dump())
    db.add(db_recorrencia)
    db.commit()
    db.refresh(db_recorrencia)
    return db_recorrencia


@app.get("/recorrencias", response_model=List[RecorrenciaRead])
def listar_recorrencias(
    tipo: str | None = Query(default=None, pattern="^(receita|despesa)$"),
    ativa: bool | None = None,
    db: Session = Depends(get_db),
) -> List[Recorrencia]:
    stmt = select(Recorrencia)
    if tipo is not None:
        stmt = stmt.where(Recorrencia.tipo == tipo)
    if ativa is not None:
        stmt = stmt.where(Recorrencia.ativa.is_(ativa))
    stmt = stmt.order_by(Recorrencia.descricao)
    return list(db.execute(stmt).scalars().all())


@app.post("/recorrencias/processar", response_model=ProcessamentoRead)
def processar_recorrencias(
    ate: date | None = None, db: Session = Depends(get_db)
) -> ProcessamentoRead:
    limite = ate if ate is not None else date.today()
    geradas = 0
    ignoradas = 0

    recorrencias = list(
        db.execute(
            select(Recorrencia).where(Recorrencia.ativa.is_(True))
        )
        .scalars()
        .all()
    )

    for recorrencia in recorrencias:
        modelo = Receita if recorrencia.tipo == "receita" else Despesa
        datas = gerar_ocorrencias(recorrencia, limite)
        if not datas:
            continue

        existentes = set(
            db.execute(
                select(modelo.data).where(
                    modelo.recorrencia_id == recorrencia.id,
                    modelo.data.in_(datas),
                )
            )
            .scalars()
            .all()
        )

        for data_ocorrencia in datas:
            if data_ocorrencia in existentes:
                ignoradas += 1
                continue
            db.add(
                modelo(
                    descricao=recorrencia.descricao,
                    valor=recorrencia.valor,
                    data=data_ocorrencia,
                    categoria=recorrencia.categoria,
                    recorrencia_id=recorrencia.id,
                )
            )
            geradas += 1

    db.commit()
    return ProcessamentoRead(ate=limite, geradas=geradas, ignoradas=ignoradas)


@app.get("/recorrencias/{id_recorrencia}", response_model=RecorrenciaRead)
def buscar_recorrencia(
    id_recorrencia: int, db: Session = Depends(get_db)
) -> Recorrencia:
    return buscar_ou_404(db, Recorrencia, id_recorrencia)


@app.patch("/recorrencias/{id_recorrencia}", response_model=RecorrenciaRead)
def atualizar_recorrencia(
    id_recorrencia: int,
    recorrencia: RecorrenciaUpdate,
    db: Session = Depends(get_db),
) -> Recorrencia:
    db_recorrencia = buscar_ou_404(db, Recorrencia, id_recorrencia)
    for campo, valor in recorrencia.model_dump(
        exclude_unset=True, exclude_none=True
    ).items():
        setattr(db_recorrencia, campo, valor)

    if (
        db_recorrencia.data_fim is not None
        and db_recorrencia.data_fim < db_recorrencia.data_inicio
    ):
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="data_fim deve ser maior ou igual a data_inicio.",
        )

    db.commit()
    db.refresh(db_recorrencia)
    return db_recorrencia


@app.delete(
    "/recorrencias/{id_recorrencia}", status_code=status.HTTP_204_NO_CONTENT
)
def excluir_recorrencia(
    id_recorrencia: int, db: Session = Depends(get_db)
) -> Response:
    db_recorrencia = buscar_ou_404(db, Recorrencia, id_recorrencia)

    for modelo in (Receita, Despesa):
        db.execute(
            update(modelo)
            .where(modelo.recorrencia_id == id_recorrencia)
            .values(recorrencia_id=None)
        )

    db.delete(db_recorrencia)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
