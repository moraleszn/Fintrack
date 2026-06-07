# test_app.py
# Testes do backend do Fintrack

from uuid import uuid4
from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.app import app, get_db
from backend.database import Base


@pytest.fixture
def client() -> Iterator[TestClient]:
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def client_db_limpo(tmp_path: pytest.TempPathFactory) -> Iterator[TestClient]:
    db_path = tmp_path / "fintrack_test_empty.db"
    test_engine = create_engine(
        f"sqlite:///{db_path}", connect_args={"check_same_thread": False}
    )
    TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
    Base.metadata.create_all(bind=test_engine)

    def get_test_db() -> Iterator:
        db = TestSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = get_test_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def test_root(client: TestClient) -> None:
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Bem-vindo ao Fintrack API!"}


def test_criar_e_listar_receitas(client: TestClient) -> None:
    payload = {
        "descricao": "Salario",
        "valor": 5500.0,
        "data": "2026-06-26",
        "categoria": "Trabalho",
    }

    create_response = client.post("/receitas", json=payload)
    assert create_response.status_code == 201
    created = create_response.json()
    assert created["descricao"] == payload["descricao"]
    assert created["valor"] == payload["valor"]

    list_response = client.get("/receitas")
    assert list_response.status_code == 200
    data = list_response.json()
    assert isinstance(data, list)
    assert any(item["descricao"] == "Salario" for item in data)


def test_criar_e_listar_despesas(client: TestClient) -> None:
    payload = {
        "descricao": "Internet",
        "valor": 120.0,
        "data": "2026-05-26",
        "categoria": "Casa",
    }

    create_response = client.post("/despesas", json=payload)
    assert create_response.status_code == 201
    created = create_response.json()
    assert created["descricao"] == payload["descricao"]
    assert created["valor"] == payload["valor"]

    list_response = client.get("/despesas")
    assert list_response.status_code == 200
    data = list_response.json()
    assert isinstance(data, list)
    assert any(item["descricao"] == "Internet" for item in data)


def test_listar_receitas_ordenadas_por_data_desc(client: TestClient) -> None:
    sufixo = uuid4().hex[:8]
    receita_antiga = {
        "descricao": f"Receita antiga {sufixo}",
        "valor": 100.0,
        "data": "2026-05-01",
        "categoria": "Teste",
    }
    receita_recente = {
        "descricao": f"Receita recente {sufixo}",
        "valor": 200.0,
        "data": "2026-05-30",
        "categoria": "Teste",
    }

    assert client.post("/receitas", json=receita_antiga).status_code == 201
    assert client.post("/receitas", json=receita_recente).status_code == 201

    list_response = client.get("/receitas")
    assert list_response.status_code == 200

    receitas = list_response.json()
    descricoes_alvo = {
        receita_antiga["descricao"],
        receita_recente["descricao"],
    }
    receitas_alvo = [r for r in receitas if r["descricao"] in descricoes_alvo]

    assert len(receitas_alvo) == 2
    assert receitas_alvo[0]["descricao"] == receita_recente["descricao"]
    assert receitas_alvo[1]["descricao"] == receita_antiga["descricao"]


def test_resumo_retorna_totais_e_saldo(client: TestClient) -> None:
    resumo_inicial = client.get("/resumo")
    assert resumo_inicial.status_code == 200
    dados_iniciais = resumo_inicial.json()

    receita = {
        "descricao": f"Receita resumo {uuid4().hex[:8]}",
        "valor": 250.0,
        "data": "2026-06-01",
        "categoria": "Teste",
    }
    despesa = {
        "descricao": f"Despesa resumo {uuid4().hex[:8]}",
        "valor": 100.0,
        "data": "2026-06-01",
        "categoria": "Teste",
    }

    assert client.post("/receitas", json=receita).status_code == 201
    assert client.post("/despesas", json=despesa).status_code == 201

    resumo_final = client.get("/resumo")
    assert resumo_final.status_code == 200
    dados_finais = resumo_final.json()

    assert dados_finais["total_receitas"] == pytest.approx(
        dados_iniciais["total_receitas"] + receita["valor"]
    )
    assert dados_finais["total_despesas"] == pytest.approx(
        dados_iniciais["total_despesas"] + despesa["valor"]
    )
    assert dados_finais["saldo"] == pytest.approx(
        dados_finais["total_receitas"] - dados_finais["total_despesas"]
    )


def test_resumo_retorna_zero_em_base_vazia(client_db_limpo: TestClient) -> None:
    response = client_db_limpo.get("/resumo")
    assert response.status_code == 200
    assert response.json() == {
        "total_receitas": 0.0,
        "total_despesas": 0.0,
        "saldo": 0.0,
    }


def test_resumo_filtra_por_periodo(client_db_limpo: TestClient) -> None:
    assert (
        client_db_limpo.post(
            "/receitas",
            json={
                "descricao": "Receita maio",
                "valor": 100.0,
                "data": "2026-05-20",
                "categoria": "Teste",
            },
        ).status_code
        == 201
    )
    assert (
        client_db_limpo.post(
            "/receitas",
            json={
                "descricao": "Receita junho",
                "valor": 500.0,
                "data": "2026-06-10",
                "categoria": "Teste",
            },
        ).status_code
        == 201
    )
    assert (
        client_db_limpo.post(
            "/despesas",
            json={
                "descricao": "Despesa maio",
                "valor": 30.0,
                "data": "2026-05-12",
                "categoria": "Teste",
            },
        ).status_code
        == 201
    )
    assert (
        client_db_limpo.post(
            "/despesas",
            json={
                "descricao": "Despesa junho",
                "valor": 80.0,
                "data": "2026-06-11",
                "categoria": "Teste",
            },
        ).status_code
        == 201
    )

    response = client_db_limpo.get(
        "/resumo?data_inicio=2026-06-01&data_fim=2026-06-30"
    )
    assert response.status_code == 200
    assert response.json() == {
        "total_receitas": 500.0,
        "total_despesas": 80.0,
        "saldo": 420.0,
    }


def test_resumo_retorna_400_quando_periodo_invalido(client_db_limpo: TestClient) -> None:
    response = client_db_limpo.get("/resumo?data_inicio=2026-06-30&data_fim=2026-06-01")
    assert response.status_code == 400
    assert response.json() == {
        "detail": "Periodo invalido: data_inicio deve ser menor ou igual a data_fim."
    }


def test_resumo_por_categoria_consolida_receitas_e_despesas(
    client_db_limpo: TestClient,
) -> None:
    assert (
        client_db_limpo.post(
            "/receitas",
            json={
                "descricao": "Freela",
                "valor": 1000.0,
                "data": "2026-06-10",
                "categoria": "Trabalho",
            },
        ).status_code
        == 201
    )
    assert (
        client_db_limpo.post(
            "/receitas",
            json={
                "descricao": "Venda usada",
                "valor": 200.0,
                "data": "2026-06-10",
                "categoria": "Outros",
            },
        ).status_code
        == 201
    )
    assert (
        client_db_limpo.post(
            "/despesas",
            json={
                "descricao": "Mercado",
                "valor": 300.0,
                "data": "2026-06-11",
                "categoria": "Casa",
            },
        ).status_code
        == 201
    )
    assert (
        client_db_limpo.post(
            "/despesas",
            json={
                "descricao": "Imposto",
                "valor": 100.0,
                "data": "2026-06-11",
                "categoria": "Trabalho",
            },
        ).status_code
        == 201
    )

    response = client_db_limpo.get("/resumo/categorias")
    assert response.status_code == 200
    dados = response.json()

    por_categoria = {item["categoria"]: item for item in dados}

    assert por_categoria["Trabalho"] == {
        "categoria": "Trabalho",
        "total_receitas": 1000.0,
        "total_despesas": 100.0,
        "saldo": 900.0,
    }
    assert por_categoria["Outros"] == {
        "categoria": "Outros",
        "total_receitas": 200.0,
        "total_despesas": 0.0,
        "saldo": 200.0,
    }
    assert por_categoria["Casa"] == {
        "categoria": "Casa",
        "total_receitas": 0.0,
        "total_despesas": 300.0,
        "saldo": -300.0,
    }
