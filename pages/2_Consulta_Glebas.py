import streamlit as st
import pandas as pd
from supabase import create_client

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

supabase = create_client(
    SUPABASE_URL,
    SUPABASE_KEY
)

# ======================================
# CARREGAR DADOS
# ======================================

@st.cache_data(ttl=60)
def carregar_dados():

    resposta = (
        supabase
        .table("APP COLHEITA")
        .select("*")
        .execute()
    )

    df = pd.DataFrame(resposta.data)

    if not df.empty:
        # Garante que a coluna de data seja convertida corretamente
        if "data_saida" in df.columns:
            df["data_saida"] = pd.to_datetime(
                df["data_saida"],
                errors="coerce"
            )
        
        # CORREÇÃO CRÍTICA: Força a coluna gleba a ser inteira, mesmo se houver nulos
        if "gleba" in df.columns:
            df["gleba"] = pd.to_numeric(df["gleba"], errors="coerce").astype("Int64")

    return df


dados = carregar_dados()

if dados.empty:
    st.warning("Nenhum dado encontrado.")
    st.stop()

# ======================================
# FILTRO
# ======================================

# Coleta a lista convertendo estritamente para int padrão do Python para o multiselect
lista_glebas = (
    dados["gleba"]
    .dropna()
    .astype(int)
    .sort_values()
    .unique()
    .tolist()
)

st.sidebar.header("🔎 Pesquisa")

glebas_sel = st.sidebar.multiselect(
    "Pesquise e selecione uma ou mais glebas",
    options=lista_glebas,
    placeholder="Digite a gleba..."
)
# ======================================
# CONSULTA
# ======================================

if glebas_sel:

    # Corrigido a comparação garantindo tipo numérico inteiro
    resultado = dados[
        dados["gleba"].astype(int).isin(glebas_sel)
    ].copy()

    tc_real = resultado["tc_real"].sum()

    # Pega o primeiro estimado de cada gleba para evitar duplicar a meta
    tc_estimado = (
        resultado
        .groupby("gleba")["tc_estimado"]
        .first()
        .sum()
    )

    percentual = (
        (tc_real / tc_estimado) * 100
        if tc_estimado > 0 else 0
    )

    col1, col2, col3 = st.columns(3)

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

    with col3:
        st.metric(
            "📈 % Concluído",
            f"{percentual:.1f}%"
        )

    st.divider()

    # Agrupamento da tabela mantendo o primeiro estimado de cada gleba por frente
    tabela = (
        resultado
        .groupby(
            ["gleba", "frente"],
            as_index=False
        )
        .agg(
            {
                "tc_real": "sum",
                "tc_estimado": "first"
            }
        )
        .sort_values(
            ["gleba", "frente"]
        )
    )

    tabela = tabela.rename(
        columns={
            "gleba": "Gleba",
            "frente": "Frente",
            "tc_real": "TC Real",
            "tc_estimado": "TC Estimado"
        }
    )

    st.dataframe(
        tabela,
        use_container_width=True,
        hide_index=True
    )

else:

    st.info("Selecione uma ou mais glebas na barra lateral.")
