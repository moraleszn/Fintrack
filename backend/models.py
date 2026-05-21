# models.py
# Definições iniciais de modelos para o Fintrack

from sqlalchemy import Column, Integer, String, Float, Date, create_engine
from sqlalchemy.ext.declarative import declarative_base
from pydantic import BaseModel

Base = declarative_base()

class Receita(Base):
    __tablename__ = 'receitas'
    id = Column(Integer, primary_key=True)
    descricao = Column(String)
    valor = Column(Float)
    data = Column(Date)
    categoria = Column(String)

class Despesa(Base):
    __tablename__ = 'despesas'
    id = Column(Integer, primary_key=True)
    descricao = Column(String)
    valor = Column(Float)
    data = Column(Date)
    categoria = Column(String)

# Modelos de entrada para receitas e despesas
class ReceitaCreate(BaseModel):
    descricao: str
    valor: float
    data: str
    categoria: str

class DespesaCreate(BaseModel):
    descricao: str
    valor: float
    data: str
    categoria: str

