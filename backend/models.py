# models.py
# Modelos SQLAlchemy e schemas Pydantic do Fintrack

from datetime import date
from decimal import Decimal
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, StringConstraints
from sqlalchemy import Column, Date, Integer, Numeric, String

from backend.database import Base

ValorPositivo = Annotated[
    Decimal, Field(gt=0, max_digits=12, decimal_places=2)
]
TextoObrigatorio = Annotated[
    str, StringConstraints(strip_whitespace=True, min_length=1)
]


class Lancamento(Base):
    __abstract__ = True

    id = Column(Integer, primary_key=True, index=True)
    descricao = Column(String, nullable=False)
    valor = Column(Numeric(12, 2), nullable=False)
    data = Column(Date, nullable=False)
    categoria = Column(String, nullable=False)


class Receita(Lancamento):
    __tablename__ = "receitas"


class Despesa(Lancamento):
    __tablename__ = "despesas"


class LancamentoCreate(BaseModel):
    descricao: TextoObrigatorio
    valor: ValorPositivo
    data: date
    categoria: TextoObrigatorio


class LancamentoUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    descricao: TextoObrigatorio | None = None
    valor: ValorPositivo | None = None
    data: date | None = None
    categoria: TextoObrigatorio | None = None


class LancamentoRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    descricao: str
    valor: Decimal
    data: date
    categoria: str


class ReceitaCreate(LancamentoCreate):
    pass


class ReceitaUpdate(LancamentoUpdate):
    pass


class ReceitaRead(LancamentoRead):
    pass


class DespesaCreate(LancamentoCreate):
    pass


class DespesaUpdate(LancamentoUpdate):
    pass


class DespesaRead(LancamentoRead):
    pass


class ResumoRead(BaseModel):
    total_receitas: Decimal
    total_despesas: Decimal
    saldo: Decimal


class CategoriaSaldoRead(BaseModel):
    categoria: str
    total_receitas: Decimal
    total_despesas: Decimal
    saldo: Decimal
