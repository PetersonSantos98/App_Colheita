import streamlit as st
import pandas as pd
from supabase import create_client, Client

# ==================================
# CONFIGURAÇÃO DA PÁGINA
# ==================================

st.set_page_config(
    page_title="Consulta de Glebas",
    page_icon="🌱",
    layout="wide"
)

st.title("🌱 Consulta de Glebas")

# ==================================
# CONEXÃO SUPABASE
# ==================================

SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]

supabase: Client = create_client(
    SUPABASE_URL,
    SUPABASE_KEY
)

# ==================================
# CARREGA DADOS
# ==================================

@st.cache_data(ttl=1800)
def carregar_dados():

    resposta = (
        supabase
        .table("APP COLHEITA")
        .select("gleba, tc_real, tc_estimado")
        .execute()
    )

    return pd.DataFrame(resposta.data)


dados = carregar_dados()

# ==================================
# SIDEBAR
# ==================================

st.sidebar.header("🔎 Filtro")

if dados.empty:
    st.warning("Nenhum dado encontrado.")
    st.stop()

lista_glebas = sorted(
    dados["gleba"]
    .dropna()
    .unique()
    .tolist()
)

glebas = st.sidebar.multiselect(
    "Selecione a Gleba",
    lista_glebas
)

# ==================================
# RESULTADO
# ==================================

if glebas:

    resultado = dados[
        dados["gleba"].isin(glebas)
    ]

    tc_real = resultado["tc_real"].sum()

    tc_estimado = (
        resultado
        .groupby("gleba")["tc_estimado"]
        .first()
        .sum()
    )

    col1, col2 = st.columns(2)

    with col1:
        st.metric(
            "🌱 TC Acumulado Realizado",
            f"{tc_real:,.2f}"
        )

    with col2:
        st.metric(
            "📋 TC Estimado",
            f"{tc_estimado:,.2f}"
        )

    st.divider()

    st.subheader("Dados encontrados")

    st.dataframe(
        resultado.sort_values("gleba"),
        use_container_width=True,
        hide_index=True
    )

else:

    st.info("Selecione uma ou mais glebas na barra lateral.")
