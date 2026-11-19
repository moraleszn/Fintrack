# streamlit_app.py
# Dashboard do Fintrack: consome a API e permite gerenciar lancamentos

import os
from datetime import date

import httpx
import pandas as pd
import streamlit as st

st.set_page_config(page_title="Fintrack", layout="wide")
st.title("Fintrack - Controle Financeiro Pessoal")

api_base = st.sidebar.text_input(
    "URL da API",
    value=os.getenv("FINTRACK_API_URL", "http://127.0.0.1:8000"),
)
filtrar_periodo = st.sidebar.checkbox("Filtrar por periodo", value=False)
data_inicio = st.sidebar.date_input("De", value=date.today().replace(day=1))
data_fim = st.sidebar.date_input("Ate", value=date.today())
filtro_categoria = st.sidebar.text_input("Categoria (opcional)")


def parametros(usar_categoria: bool = True) -> dict:
    filtros = {}
    if filtrar_periodo:
        filtros["data_inicio"] = data_inicio.isoformat()
        filtros["data_fim"] = data_fim.isoformat()
    if usar_categoria and filtro_categoria.strip():
        filtros["categoria"] = filtro_categoria.strip()
    return filtros


def api_request(metodo: str, caminho: str, **kwargs):
    url = f"{api_base.rstrip('/')}{caminho}"
    try:
        resposta = httpx.request(metodo, url, timeout=10.0, **kwargs)
    except httpx.RequestError:
        st.error("Nao foi possivel conectar a API. Verifique se o uvicorn esta rodando.")
        st.stop()

    if resposta.is_error:
        try:
            detalhe = resposta.json().get("detail", resposta.text)
        except ValueError:
            detalhe = resposta.text
        st.error(f"Erro {resposta.status_code}: {detalhe}")
        st.stop()

    return resposta.json() if resposta.content else None


def formatar_moeda(valor) -> str:
    return f"R$ {float(valor):,.2f}"


def renderizar_lancamentos(tipo: str) -> None:
    singular = "receita" if tipo == "receitas" else "despesa"

    with st.expander(f"Adicionar {singular}"):
        with st.form(f"form_novo_{tipo}"):
            descricao = st.text_input("Descricao")
            valor = st.number_input("Valor", min_value=0.01, step=0.01, format="%.2f")
            data_lancamento = st.date_input(
                "Data", value=date.today(), key=f"data_novo_{tipo}"
            )
            categoria = st.text_input("Categoria")
            salvo = st.form_submit_button("Salvar")
        if salvo:
            api_request(
                "POST",
                f"/{tipo}",
                json={
                    "descricao": descricao,
                    "valor": f"{float(valor):.2f}",
                    "data": data_lancamento.isoformat(),
                    "categoria": categoria,
                },
            )
            st.success(f"{singular.capitalize()} criada com sucesso.")
            st.rerun()

    lancamentos = api_request("GET", f"/{tipo}", params=parametros())
    if not lancamentos:
        st.info(f"Nenhuma {singular} encontrada com os filtros atuais.")
        return

    tabela = pd.DataFrame(lancamentos)[["data", "descricao", "categoria", "valor"]]
    tabela["valor"] = tabela["valor"].astype(float)
    tabela = tabela.rename(columns={"valor": "Valor (R$)"})
    st.dataframe(tabela, hide_index=True)

    with st.expander(f"Editar ou excluir {tipo}"):
        for item in lancamentos:
            id_item = item["id"]
            titulo = (
                f"{item['data']}  |  {item['descricao']}  |  "
                f"{formatar_moeda(item['valor'])}"
            )
            with st.expander(titulo):
                with st.form(f"form_edicao_{tipo}_{id_item}"):
                    nova_descricao = st.text_input(
                        "Descricao",
                        value=item["descricao"],
                        key=f"descricao_{tipo}_{id_item}",
                    )
                    novo_valor = st.number_input(
                        "Valor",
                        min_value=0.01,
                        step=0.01,
                        value=float(item["valor"]),
                        format="%.2f",
                        key=f"valor_{tipo}_{id_item}",
                    )
                    nova_data = st.date_input(
                        "Data",
                        value=date.fromisoformat(item["data"]),
                        key=f"data_{tipo}_{id_item}",
                    )
                    nova_categoria = st.text_input(
                        "Categoria",
                        value=item["categoria"],
                        key=f"categoria_{tipo}_{id_item}",
                    )
                    alterado = st.form_submit_button("Salvar alteracoes")
                if alterado:
                    api_request(
                        "PATCH",
                        f"/{tipo}/{id_item}",
                        json={
                            "descricao": nova_descricao,
                            "valor": f"{float(novo_valor):.2f}",
                            "data": nova_data.isoformat(),
                            "categoria": nova_categoria,
                        },
                    )
                    st.success("Alteracoes salvas.")
                    st.rerun()
                if st.button("Excluir", key=f"excluir_{tipo}_{id_item}"):
                    api_request("DELETE", f"/{tipo}/{id_item}")
                    st.success("Lancamento excluido.")
                    st.rerun()


aba_resumo, aba_receitas, aba_despesas, aba_categorias = st.tabs(
    ["Resumo", "Receitas", "Despesas", "Por categoria"]
)

with aba_resumo:
    resumo = api_request("GET", "/resumo", params=parametros())
    coluna_receitas, coluna_despesas, coluna_saldo = st.columns(3)
    coluna_receitas.metric("Total de receitas", formatar_moeda(resumo["total_receitas"]))
    coluna_despesas.metric("Total de despesas", formatar_moeda(resumo["total_despesas"]))
    coluna_saldo.metric("Saldo", formatar_moeda(resumo["saldo"]))
    if float(resumo["saldo"]) < 0:
        st.warning("Saldo negativo no periodo selecionado.")
    st.caption("Os totais sao calculados pela API com precisao de centavos.")

with aba_receitas:
    renderizar_lancamentos("receitas")

with aba_despesas:
    renderizar_lancamentos("despesas")

with aba_categorias:
    categorias = api_request(
        "GET", "/resumo/categorias", params=parametros(usar_categoria=False)
    )
    if not categorias:
        st.info("Nenhuma categoria encontrada com os filtros atuais.")
    else:
        tabela_categorias = pd.DataFrame(categorias)[
            ["categoria", "total_receitas", "total_despesas", "saldo"]
        ]
        for coluna in ("total_receitas", "total_despesas", "saldo"):
            tabela_categorias[coluna] = tabela_categorias[coluna].astype(float)
        st.dataframe(tabela_categorias, hide_index=True)
        st.bar_chart(tabela_categorias.set_index("categoria")["saldo"])
