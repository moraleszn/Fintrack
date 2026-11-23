# models.py
# Modelos SQLAlchemy e schemas Pydantic do Fintrack

from datetime import date
from decimal import Decimal
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, model_validator
from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Column,
    Date,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    UniqueConstraint,
)

from backend.database import Base

ValorPositivo = Annotated[
    Decimal, Field(gt=0, max_digits=12, decimal_places=2)
]
TextoObrigatorio = Annotated[
    str, StringConstraints(strip_whitespace=True, min_length=1)
]


class Recorrencia(Base):
    __tablename__ = "recorrencias"
    __table_args__ = (
        CheckConstraint(
            "tipo IN ('receita', 'despesa')", name="ck_recorrencias_tipo"
        ),
        CheckConstraint(
            "dia_vencimento >= 1 AND dia_vencimento <= 31",
            name="ck_recorrencias_dia_vencimento",
        ),
    )

    id = Column(Integer, primary_key=True, index=True)
    descricao = Column(String, nullable=False)
    valor = Column(Numeric(12, 2), nullable=False)
    categoria = Column(String, nullable=False)
    tipo = Column(String, nullable=False)
    dia_vencimento = Column(Integer, nullable=False)
    data_inicio = Column(Date, nullable=False)
    data_fim = Column(Date, nullable=True)
    ativa = Column(Boolean, nullable=False, default=True)


class Lancamento(Base):
    __abstract__ = True

    id = Column(Integer, primary_key=True, index=True)
    descricao = Column(String, nullable=False)
    valor = Column(Numeric(12, 2), nullable=False)
    data = Column(Date, nullable=False)
    categoria = Column(String, nullable=False)
    recorrencia_id = Column(Integer, ForeignKey("recorrencias.id"), nullable=True)


class Receita(Lancamento):
    __tablename__ = "receitas"
    __table_args__ = (
        Index(
            "uq_receitas_recorrencia_data",
            "recorrencia_id",
            "data",
            unique=True,
        ),
    )


class Despesa(Lancamento):
    __tablename__ = "despesas"
    __table_args__ = (
        Index(
            "uq_despesas_recorrencia_data",
            "recorrencia_id",
            "data",
            unique=True,
        ),
    )


class Orcamento(Base):
    __tablename__ = "orcamentos"
    __table_args__ = (
        UniqueConstraint(
            "categoria", "ano", "mes", name="uq_orcamentos_categoria_periodo"
        ),
        CheckConstraint("mes >= 1 AND mes <= 12", name="ck_orcamentos_mes"),
        CheckConstraint("ano >= 2000", name="ck_orcamentos_ano"),
    )

    id = Column(Integer, primary_key=True, index=True)
    categoria = Column(String, nullable=False)
    valor_limite = Column(Numeric(12, 2), nullable=False)
    ano = Column(Integer, nullable=False)
    mes = Column(Integer, nullable=False)


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
    recorrencia_id: int | None = None


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


class OrcamentoCreate(BaseModel):
    categoria: TextoObrigatorio
    valor_limite: ValorPositivo
    ano: Annotated[int, Field(ge=2000, le=2100)]
    mes: Annotated[int, Field(ge=1, le=12)]


class OrcamentoUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    categoria: TextoObrigatorio | None = None
    valor_limite: ValorPositivo | None = None


class OrcamentoRead(OrcamentoCreate):
    model_config = ConfigDict(from_attributes=True)

    id: int


class OrcamentoDesempenhoRead(BaseModel):
    id: int
    categoria: str
    valor_limite: Decimal
    total_despesas: Decimal
    disponivel: Decimal
    percentual_usado: Decimal
    projecao_fim_mes: Decimal
    status: Literal["ok", "atencao", "estourado"]


TipoRecorrencia = Literal["receita", "despesa"]


class RecorrenciaCreate(BaseModel):
    descricao: TextoObrigatorio
    valor: ValorPositivo
    categoria: TextoObrigatorio
    tipo: TipoRecorrencia
    dia_vencimento: Annotated[int, Field(ge=1, le=31)]
    data_inicio: date
    data_fim: date | None = None
    ativa: bool = True

    @model_validator(mode="after")
    def validar_datas(self) -> "RecorrenciaCreate":
        if self.data_fim is not None and self.data_fim < self.data_inicio:
            raise ValueError("data_fim deve ser maior ou igual a data_inicio.")
        return self


class RecorrenciaUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    descricao: TextoObrigatorio | None = None
    valor: ValorPositivo | None = None
    categoria: TextoObrigatorio | None = None
    dia_vencimento: Annotated[int, Field(ge=1, le=31)] | None = None
    data_fim: date | None = None
    ativa: bool | None = None


class RecorrenciaRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    descricao: str
    valor: Decimal
    categoria: str
    tipo: TipoRecorrencia
    dia_vencimento: int
    data_inicio: date
    data_fim: date | None = None
    ativa: bool


class ProcessamentoRead(BaseModel):
    ate: date
    geradas: int
    ignoradas: int
