import streamlit as st
import pandas as pd
from supabase import create_client

st.set_page_config(
    page_title="Consulta de Glebas",
    page_icon="🌱",
    layout="wide"
)

st.title("🌱 Consulta de Glebas")

SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)


@st.cache_data(ttl=1800)
def carregar_dados():

    resposta = (
        supabase
        .table("APP COLHEITA")
        .select("*")
        .execute()
    )

    return pd.DataFrame(resposta.data)


try:
    dados = carregar_dados()

except Exception as e:
    st.exception(e)
    st.stop()


# ======== DIAGNÓSTICO ========

st.write("Quantidade de registros:", len(dados))

if not dados.empty:
    st.write("Colunas:")
    st.write(dados.columns.tolist())

    st.write("Primeiras linhas:")
    st.dataframe(dados.head())

# =============================

if dados.empty:
    st.error("Nenhum registro encontrado.")
    st.stop()


# Converte data
if "data_saida" in dados.columns:
    dados["data_saida"] = pd.to_datetime(
        dados["data_saida"],
        errors="coerce"
    )

# Lista de glebas
glebas = (
    dados["gleba"]
    .dropna()
    .astype(str)
    .sort_values()
    .unique()
    .tolist()
)

st.sidebar.header("🔎 Pesquisa")

gleba = st.sidebar.selectbox(
    "Selecione ou pesquise a Gleba",
    [""] + glebas
)

if gleba != "":

    resultado = dados[dados["gleba"].astype(str) == gleba]

    tc_real = resultado["tc_real"].sum()

    tc_estimado = resultado["tc_estimado"].iloc[0]

    c1, c2 = st.columns(2)

    c1.metric(
        "🌱 TC Acumulado Realizado",
        f"{tc_real:,.2f}"
    )

    c2.metric(
        "📋 TC Estimado",
        f"{tc_estimado:,.2f}"
    )

    tabela = resultado.copy()

    if "data_saida" in tabela.columns:
        tabela["data_saida"] = tabela["data_saida"].dt.strftime("%d/%m/%Y")

    colunas = [
        "data_saida",
        "frente",
        "nome_fazenda",
        "gleba",
        "tc_real",
        "tc_estimado"
    ]

    colunas = [c for c in colunas if c in tabela.columns]

    st.dataframe(
        tabela[colunas],
        use_container_width=True,
        hide_index=True
    )
