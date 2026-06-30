import streamlit as st
import pandas as pd
from supabase import create_client, Client

# ======================================
# CONFIGURAÇÃO
# ======================================

st.set_page_config(
    page_title="Consulta de Glebas",
    page_icon="🌱",
    layout="wide"
)

st.title("🌱 Consulta de Glebas")

# ======================================
# SUPABASE
# ======================================

SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]

supabase: Client = create_client(
    SUPABASE_URL,
    SUPABASE_KEY
)

# ======================================
# BUSCAR DADOS
# ======================================

@st.cache_data(ttl=1800)
def carregar_dados():

    try:

        resposta = (
            supabase
            .table("APP COLHEITA")
            .select("*")
            .execute()
        )

        df = pd.DataFrame(resposta.data)

        if df.empty:
            st.warning("A tabela está vazia.")
            return df

        # Converte data caso exista
        if "data_saida" in df.columns:
            df["data_saida"] = pd.to_datetime(
                df["data_saida"],
                errors="coerce"
            )

        return df

    except Exception as e:

        st.error("Erro ao consultar o Supabase:")
        st.exception(e)
        return pd.DataFrame()


dados = carregar_dados()

# ======================================
# SIDEBAR
# ======================================

st.sidebar.header("🔎 Pesquisa")

gleba = st.sidebar.text_input(
    "Digite a Gleba"
)

# ======================================
# CONSULTA
# ======================================

if not dados.empty and gleba:

    resultado = dados[
        dados["gleba"]
        .astype(str)
        .str.contains(
            gleba,
            case=False,
            na=False
        )
    ]

    if resultado.empty:

        st.warning("Nenhuma gleba encontrada.")

    else:

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

        colunas = [
            c for c in [
                "data_saida",
                "frente",
                "nome_fazenda",
                "gleba",
                "tc_real",
                "tc_estimado"
            ] if c in resultado.columns
        ]

        tabela = resultado[colunas].copy()

        if "data_saida" in tabela.columns:
            tabela["data_saida"] = tabela["data_saida"].dt.strftime("%d/%m/%Y")

        st.dataframe(
            tabela,
            use_container_width=True,
            hide_index=True
        )

elif dados.empty:
    st.stop()

else:
    st.info("Digite uma gleba no campo de pesquisa.")
