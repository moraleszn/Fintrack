# models.py
# Modelos SQLAlchemy e schemas Pydantic do Fintrack

from datetime import date

from pydantic import BaseModel, ConfigDict
from sqlalchemy import Column, Date, Float, Integer, String

from backend.database import Base


class Receita(Base):
    __tablename__ = "receitas"

    id = Column(Integer, primary_key=True, index=True)
    descricao = Column(String, nullable=False)
    valor = Column(Float, nullable=False)
    data = Column(Date, nullable=False)
    categoria = Column(String, nullable=False)


class Despesa(Base):
    __tablename__ = "despesas"

    id = Column(Integer, primary_key=True, index=True)
    descricao = Column(String, nullable=False)
    valor = Column(Float, nullable=False)
    data = Column(Date, nullable=False)
    categoria = Column(String, nullable=False)


class ReceitaCreate(BaseModel):
    descricao: str
    valor: float
    data: date
    categoria: str


class DespesaCreate(BaseModel):
    descricao: str
    valor: float
    data: date
    categoria: str


class ReceitaRead(ReceitaCreate):
    id: int
    model_config = ConfigDict(from_attributes=True)


class DespesaRead(DespesaCreate):
    id: int
    model_config = ConfigDict(from_attributes=True)


class ResumoRead(BaseModel):
    total_receitas: float
    total_despesas: float
    saldo: float


class CategoriaSaldoRead(BaseModel):
    categoria: str
    total_receitas: float
    total_despesas: float
    saldo: float

