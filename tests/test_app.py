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


def payload_orcamento(
    categoria: str = "Casa",
    valor_limite: str = "1000.00",
    ano: int = 2026,
    mes: int = 5,
) -> dict:
    return {
        "categoria": categoria,
        "valor_limite": valor_limite,
        "ano": ano,
        "mes": mes,
    }


def payload_recorrencia(
    descricao: str = "Aluguel",
    valor: str = "1500.00",
    categoria: str = "Casa",
    tipo: str = "despesa",
    dia_vencimento: int = 31,
    data_inicio: str = "2026-01-15",
    data_fim: str | None = None,
    ativa: bool = True,
) -> dict:
    payload = {
        "descricao": descricao,
        "valor": valor,
        "categoria": categoria,
        "tipo": tipo,
        "dia_vencimento": dia_vencimento,
        "data_inicio": data_inicio,
        "ativa": ativa,
    }
    if data_fim is not None:
        payload["data_fim"] = data_fim
    return payload


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


def test_criar_listar_atualizar_e_excluir_orcamento(client: TestClient) -> None:
    criado = client.post("/orcamentos", json=payload_orcamento()).json()
    id_orcamento = criado["id"]
    assert criado["categoria"] == "Casa"
    assert valor_decimal(criado["valor_limite"]) == Decimal("1000.00")

    listados = client.get("/orcamentos?ano=2026&mes=5").json()
    assert [item["id"] for item in listados] == [id_orcamento]

    duplicado = client.post("/orcamentos", json=payload_orcamento())
    assert duplicado.status_code == 409

    outra_categoria = client.post(
        "/orcamentos", json=payload_orcamento(categoria="Lazer")
    )
    assert outra_categoria.status_code == 201

    resposta = client.patch(
        f"/orcamentos/{id_orcamento}", json={"valor_limite": "1200.50"}
    )
    assert resposta.status_code == 200
    assert valor_decimal(resposta.json()["valor_limite"]) == Decimal("1200.50")

    conflito = client.patch(
        f"/orcamentos/{id_orcamento}", json={"categoria": "Lazer"}
    )
    assert conflito.status_code == 409

    assert client.delete(f"/orcamentos/{id_orcamento}").status_code == 204
    assert client.get(f"/orcamentos/{id_orcamento}").status_code == 404


def test_validacao_orcamento(client: TestClient) -> None:
    casos = [
        payload_orcamento(mes=0),
        payload_orcamento(mes=13),
        payload_orcamento(ano=1999),
        payload_orcamento(valor_limite="0"),
        payload_orcamento(valor_limite="-10.00"),
        payload_orcamento(categoria="   "),
    ]
    for caso in casos:
        resposta = client.post("/orcamentos", json=caso)
        assert resposta.status_code == 422, caso

    assert client.get("/orcamentos/desempenho").status_code == 422
    assert client.get("/orcamentos/desempenho?ano=2026&mes=13").status_code == 422


def test_desempenho_orcamento_mes_passado(client: TestClient) -> None:
    client.post(
        "/despesas",
        json=payload_despesa("Mercado", valor="850.00", data="2026-05-10", categoria="Casa"),
    )
    client.post(
        "/despesas",
        json=payload_despesa("Luz", valor="100.00", data="2026-05-20", categoria="Casa"),
    )
    client.post(
        "/despesas",
        json=payload_despesa("Fora do mes", valor="200.00", data="2026-06-01", categoria="Casa"),
    )
    criado = client.post(
        "/orcamentos", json=payload_orcamento(valor_limite="1000.00", mes=5)
    ).json()

    dados = client.get("/orcamentos/desempenho?ano=2026&mes=5").json()
    assert dados == [
        {
            "id": criado["id"],
            "categoria": "Casa",
            "valor_limite": "1000.00",
            "total_despesas": "950.00",
            "disponivel": "50.00",
            "percentual_usado": "95.00",
            "projecao_fim_mes": "950.00",
            "status": "atencao",
        }
    ]


def test_desempenho_status_estourado_e_ok(client: TestClient) -> None:
    client.post(
        "/despesas",
        json=payload_despesa("Festa", valor="150.00", data="2026-05-10", categoria="Lazer"),
    )
    client.post(
        "/despesas",
        json=payload_despesa("Cinema", valor="50.00", data="2026-05-10", categoria="Cultura"),
    )
    client.post(
        "/orcamentos",
        json=payload_orcamento(categoria="Lazer", valor_limite="100.00"),
    )
    client.post(
        "/orcamentos",
        json=payload_orcamento(categoria="Cultura", valor_limite="1000.00"),
    )

    dados = {
        item["categoria"]: item
        for item in client.get("/orcamentos/desempenho?ano=2026&mes=5").json()
    }

    assert dados["Lazer"]["status"] == "estourado"
    assert dados["Lazer"]["disponivel"] == "-50.00"
    assert dados["Lazer"]["percentual_usado"] == "150.00"

    assert dados["Cultura"]["status"] == "ok"
    assert dados["Cultura"]["disponivel"] == "950.00"

    # ordena do maior percentual para o menor
    assert list(dados) == ["Lazer", "Cultura"]


def test_desempenho_categoria_sem_despesa(client: TestClient) -> None:
    criado = client.post(
        "/orcamentos", json=payload_orcamento(categoria="Viagem", valor_limite="500.00")
    ).json()

    dados = client.get("/orcamentos/desempenho?ano=2026&mes=5").json()
    assert dados == [
        {
            "id": criado["id"],
            "categoria": "Viagem",
            "valor_limite": "500.00",
            "total_despesas": "0.00",
            "disponivel": "500.00",
            "percentual_usado": "0.00",
            "projecao_fim_mes": "0.00",
            "status": "ok",
        }
    ]


def test_criar_listar_atualizar_e_excluir_recorrencia(client: TestClient) -> None:
    criada = client.post("/recorrencias", json=payload_recorrencia()).json()
    id_recorrencia = criada["id"]
    assert criada["tipo"] == "despesa"
    assert criada["ativa"] is True

    listadas = client.get("/recorrencias?tipo=despesa&ativa=true").json()
    assert [item["id"] for item in listadas] == [id_recorrencia]

    resposta = client.patch(
        f"/recorrencias/{id_recorrencia}",
        json={"valor": "1600.00", "dia_vencimento": 10, "ativa": False},
    )
    assert resposta.status_code == 200
    assert valor_decimal(resposta.json()["valor"]) == Decimal("1600.00")
    assert resposta.json()["dia_vencimento"] == 10
    assert resposta.json()["ativa"] is False

    assert client.delete(f"/recorrencias/{id_recorrencia}").status_code == 204
    assert client.get(f"/recorrencias/{id_recorrencia}").status_code == 404


def test_validacao_recorrencia(client: TestClient) -> None:
    casos = [
        payload_recorrencia(tipo="investimento"),
        payload_recorrencia(dia_vencimento=0),
        payload_recorrencia(dia_vencimento=32),
        payload_recorrencia(valor="0"),
        payload_recorrencia(data_inicio="2026-03-01", data_fim="2026-02-01"),
    ]
    for caso in casos:
        resposta = client.post("/recorrencias", json=caso)
        assert resposta.status_code == 422, caso

    criada = client.post("/recorrencias", json=payload_recorrencia()).json()
    resposta = client.patch(
        f"/recorrencias/{criada['id']}", json={"data_fim": "2025-12-31"}
    )
    assert resposta.status_code == 400

    assert client.get("/recorrencias?tipo=pix").status_code == 422


def test_processar_recorrencias_gera_e_e_idempotente(client: TestClient) -> None:
    criada = client.post("/recorrencias", json=payload_recorrencia()).json()

    primeira = client.post("/recorrencias/processar?ate=2026-03-15")
    assert primeira.status_code == 200
    assert primeira.json() == {
        "ate": "2026-03-15",
        "geradas": 2,
        "ignoradas": 0,
    }

    despesas = client.get("/despesas").json()
    assert [item["data"] for item in despesas] == ["2026-02-28", "2026-01-31"]
    assert all(item["recorrencia_id"] == criada["id"] for item in despesas)

    segunda = client.post("/recorrencias/processar?ate=2026-03-15").json()
    assert segunda == {"ate": "2026-03-15", "geradas": 0, "ignoradas": 2}

    resumo = client.get("/resumo?data_inicio=2026-01-01&data_fim=2026-03-31").json()
    assert valor_decimal(resumo["total_despesas"]) == Decimal("3000.00")


def test_processar_respeita_data_fim_e_recorrencia_inativa(
    client: TestClient,
) -> None:
    client.post(
        "/recorrencias",
        json=payload_recorrencia(
            descricao="Assinatura",
            valor="50.00",
            categoria="Lazer",
            dia_vencimento=10,
            data_inicio="2026-01-01",
            data_fim="2026-02-28",
        ),
    )
    client.post(
        "/recorrencias",
        json=payload_recorrencia(
            descricao="Pausada",
            valor="999.00",
            categoria="Outros",
            dia_vencimento=5,
            data_inicio="2026-01-01",
            ativa=False,
        ),
    )

    resultado = client.post("/recorrencias/processar?ate=2026-06-30").json()
    assert resultado["geradas"] == 2

    despesas = client.get("/despesas").json()
    assert [item["descricao"] for item in despesas] == ["Assinatura", "Assinatura"]
    assert [item["data"] for item in despesas] == ["2026-02-10", "2026-01-10"]


def test_processar_receita_entra_no_resumo(client: TestClient) -> None:
    client.post(
        "/recorrencias",
        json=payload_recorrencia(
            descricao="Salario",
            valor="5000.00",
            categoria="Trabalho",
            tipo="receita",
            dia_vencimento=5,
            data_inicio="2026-01-01",
        ),
    )

    resultado = client.post("/recorrencias/processar?ate=2026-02-28").json()
    assert resultado["geradas"] == 2

    resumo = client.get("/resumo").json()
    assert valor_decimal(resumo["total_receitas"]) == Decimal("10000.00")
    assert valor_decimal(resumo["total_despesas"]) == Decimal("0.00")


def test_processar_antes_do_inicio_nao_gera(client: TestClient) -> None:
    client.post("/recorrencias", json=payload_recorrencia(data_inicio="2026-05-01"))

    resultado = client.post("/recorrencias/processar?ate=2026-04-30").json()
    assert resultado == {"ate": "2026-04-30", "geradas": 0, "ignoradas": 0}
    assert client.get("/despesas").json() == []


def test_excluir_recorrencia_preserva_lancamentos(client: TestClient) -> None:
    criada = client.post("/recorrencias", json=payload_recorrencia()).json()
    client.post("/recorrencias/processar?ate=2026-01-31")

    assert client.delete(f"/recorrencias/{criada['id']}").status_code == 204

    despesas = client.get("/despesas").json()
    assert len(despesas) == 1
    assert despesas[0]["recorrencia_id"] is None
