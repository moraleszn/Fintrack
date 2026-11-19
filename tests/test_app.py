# test_app.py
# Testes do backend do Fintrack

from collections.abc import Iterator
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.app import app, get_db
from backend.database import Base


@pytest.fixture
def client() -> Iterator[TestClient]:
    engine_teste = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine_teste)
    SessaoTeste = sessionmaker(autocommit=False, autoflush=False, bind=engine_teste)

    def get_db_teste() -> Iterator:
        db = SessaoTeste()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = get_db_teste
    try:
        yield TestClient(app)
    finally:
        app.dependency_overrides.clear()
        Base.metadata.drop_all(bind=engine_teste)
        engine_teste.dispose()


def payload_receita(
    descricao: str = "Salario",
    valor: str = "5500.00",
    data: str = "2026-06-26",
    categoria: str = "Trabalho",
) -> dict:
    return {
        "descricao": descricao,
        "valor": valor,
        "data": data,
        "categoria": categoria,
    }


def payload_despesa(
    descricao: str = "Internet",
    valor: str = "120.00",
    data: str = "2026-05-26",
    categoria: str = "Casa",
) -> dict:
    return {
        "descricao": descricao,
        "valor": valor,
        "data": data,
        "categoria": categoria,
    }


def valor_decimal(valor) -> Decimal:
    return Decimal(str(valor))


def test_root(client: TestClient) -> None:
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Bem-vindo ao Fintrack API!"}


def test_criar_e_listar_receitas(client: TestClient) -> None:
    payload = payload_receita()

    create_response = client.post("/receitas", json=payload)
    assert create_response.status_code == 201
    created = create_response.json()
    assert created["descricao"] == payload["descricao"]
    assert valor_decimal(created["valor"]) == Decimal("5500.00")

    list_response = client.get("/receitas")
    assert list_response.status_code == 200
    assert [item["descricao"] for item in list_response.json()] == ["Salario"]


def test_criar_e_listar_despesas(client: TestClient) -> None:
    payload = payload_despesa()

    create_response = client.post("/despesas", json=payload)
    assert create_response.status_code == 201
    created = create_response.json()
    assert created["descricao"] == payload["descricao"]
    assert valor_decimal(created["valor"]) == Decimal("120.00")

    list_response = client.get("/despesas")
    assert list_response.status_code == 200
    assert [item["descricao"] for item in list_response.json()] == ["Internet"]


def test_listar_lancamentos_ordenados_por_data_desc(client: TestClient) -> None:
    assert (
        client.post("/receitas", json=payload_receita("Antiga", data="2026-05-01"))
        .status_code
        == 201
    )
    assert (
        client.post("/receitas", json=payload_receita("Recente", data="2026-05-30"))
        .status_code
        == 201
    )
    assert (
        client.post("/despesas", json=payload_despesa("Antiga", data="2026-05-02"))
        .status_code
        == 201
    )
    assert (
        client.post("/despesas", json=payload_despesa("Recente", data="2026-05-31"))
        .status_code
        == 201
    )

    assert [item["descricao"] for item in client.get("/receitas").json()] == [
        "Recente",
        "Antiga",
    ]
    assert [item["descricao"] for item in client.get("/despesas").json()] == [
        "Recente",
        "Antiga",
    ]


def test_listar_filtra_por_periodo_categoria_e_pagina(client: TestClient) -> None:
    client.post("/receitas", json=payload_receita("A", valor="10.00", data="2026-05-01", categoria="Casa"))
    client.post("/receitas", json=payload_receita("B", valor="20.00", data="2026-06-01", categoria="Casa"))
    client.post("/receitas", json=payload_receita("C", valor="30.00", data="2026-06-02", categoria="Outros"))

    resposta = client.get("/receitas?data_inicio=2026-06-01&data_fim=2026-06-30&categoria=Casa")
    assert [item["descricao"] for item in resposta.json()] == ["B"]

    resposta = client.get("/receitas?limit=2")
    assert len(resposta.json()) == 2

    resposta = client.get("/receitas?limit=1&offset=1")
    assert [item["descricao"] for item in resposta.json()] == ["B"]

    resposta = client.get("/receitas?data_inicio=2026-06-30&data_fim=2026-06-01")
    assert resposta.status_code == 400


def test_buscar_atualizar_e_excluir_receita(client: TestClient) -> None:
    criada = client.post("/receitas", json=payload_receita()).json()
    id_receita = criada["id"]

    resposta = client.get(f"/receitas/{id_receita}")
    assert resposta.status_code == 200
    assert resposta.json()["descricao"] == "Salario"

    resposta = client.patch(
        f"/receitas/{id_receita}",
        json={"descricao": "Salario ajustado", "valor": "6000.50"},
    )
    assert resposta.status_code == 200
    assert resposta.json()["descricao"] == "Salario ajustado"
    assert valor_decimal(resposta.json()["valor"]) == Decimal("6000.50")

    resposta = client.delete(f"/receitas/{id_receita}")
    assert resposta.status_code == 204
    assert resposta.content == b""
    assert client.get(f"/receitas/{id_receita}").status_code == 404
    assert client.get("/receitas").json() == []


def test_buscar_atualizar_e_excluir_despesa(client: TestClient) -> None:
    criada = client.post("/despesas", json=payload_despesa()).json()
    id_despesa = criada["id"]

    resposta = client.get(f"/despesas/{id_despesa}")
    assert resposta.status_code == 200

    resposta = client.patch(
        f"/despesas/{id_despesa}",
        json={"categoria": "Moradia", "data": "2026-06-01"},
    )
    assert resposta.status_code == 200
    assert resposta.json()["categoria"] == "Moradia"
    assert resposta.json()["data"] == "2026-06-01"

    resposta = client.delete(f"/despesas/{id_despesa}")
    assert resposta.status_code == 204
    assert client.get(f"/despesas/{id_despesa}").status_code == 404
    assert client.get("/despesas").json() == []


def test_404_em_id_inexistente(client: TestClient) -> None:
    for metodo in ("get", "patch", "delete"):
        kwargs = {"json": {"valor": "1.00"}} if metodo == "patch" else {}
        resposta = getattr(client, metodo)(f"/receitas/999", **kwargs)
        assert resposta.status_code == 404


def test_validacao_rejeita_valor_invalido_e_campos_vazios(client: TestClient) -> None:
    casos = [
        payload_receita(valor="0"),
        payload_receita(valor="-10.00"),
        payload_receita(descricao="   "),
        payload_receita(categoria=""),
        payload_receita(valor="1.234"),
    ]
    for caso in casos:
        resposta = client.post("/receitas", json=caso)
        assert resposta.status_code == 422, caso

    resposta = client.patch("/receitas/1", json={"campo_desconhecido": 1})
    assert resposta.status_code == 422


def test_resumo_retorna_totais_e_saldo(client: TestClient) -> None:
    assert client.get("/resumo").json() == {
        "total_receitas": "0.00",
        "total_despesas": "0.00",
        "saldo": "0.00",
    }

    client.post("/receitas", json=payload_receita(valor="250.10"))
    client.post("/despesas", json=payload_despesa(valor="100.05"))

    dados = client.get("/resumo").json()
    assert valor_decimal(dados["total_receitas"]) == Decimal("250.10")
    assert valor_decimal(dados["total_despesas"]) == Decimal("100.05")
    assert valor_decimal(dados["saldo"]) == Decimal("150.05")


def test_resumo_filtra_por_periodo_e_categoria(client: TestClient) -> None:
    client.post("/receitas", json=payload_receita("Maio", valor="100.00", data="2026-05-20", categoria="Casa"))
    client.post("/receitas", json=payload_receita("Junho", valor="500.00", data="2026-06-10", categoria="Casa"))
    client.post("/despesas", json=payload_despesa("Maio", valor="30.00", data="2026-05-12", categoria="Casa"))
    client.post("/despesas", json=payload_despesa("Junho", valor="80.00", data="2026-06-11", categoria="Casa"))

    resposta = client.get("/resumo?data_inicio=2026-06-01&data_fim=2026-06-30&categoria=Casa")
    assert resposta.status_code == 200
    assert resposta.json() == {
        "total_receitas": "500.00",
        "total_despesas": "80.00",
        "saldo": "420.00",
    }

    resposta = client.get("/resumo?data_inicio=2026-06-30&data_fim=2026-06-01")
    assert resposta.status_code == 400


def test_resumo_por_categoria_consolida_e_filtra_periodo(client: TestClient) -> None:
    client.post("/receitas", json=payload_receita("Freela", valor="1000.00", data="2026-06-10", categoria="Trabalho"))
    client.post("/receitas", json=payload_receita("Venda", valor="200.00", data="2026-05-10", categoria="Outros"))
    client.post("/despesas", json=payload_despesa("Mercado", valor="300.00", data="2026-06-11", categoria="Casa"))
    client.post("/despesas", json=payload_despesa("Imposto", valor="100.00", data="2026-06-11", categoria="Trabalho"))

    dados = client.get("/resumo/categorias?data_inicio=2026-06-01").json()
    por_categoria = {item["categoria"]: item for item in dados}

    assert por_categoria["Trabalho"] == {
        "categoria": "Trabalho",
        "total_receitas": "1000.00",
        "total_despesas": "100.00",
        "saldo": "900.00",
    }
    assert por_categoria["Casa"]["saldo"] == "-300.00"
    assert "Outros" not in por_categoria
