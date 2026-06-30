import streamlit as st
import pandas as pd
from supabase import create_client, Client

# =====================================
# CONFIGURAÇÃO
# =====================================

st.set_page_config(
    page_title="Consulta de Glebas",
    page_icon="🌱",
    layout="wide"
)

st.title("🌱 Consulta de Glebas")

# =====================================
# SUPABASE
# =====================================

SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]

supabase: Client = create_client(
    SUPABASE_URL,
    SUPABASE_KEY
)

# =====================================
# CARREGA DADOS
# =====================================

@st.cache_data(ttl=1800)
def carregar_dados():

    resposta = (
        supabase
        .table("APP_COLHEITA")
        .select(
            "gleba,data_saida,tc_real,tc_estimado"
        )
        .execute()
    )

    df = pd.DataFrame(resposta.data)

    if not df.empty:

        df["data_saida"] = pd.to_datetime(
            df["data_saida"]
        )

    return df


dados = carregar_dados()

# =====================================
# SIDEBAR
# =====================================

st.sidebar.header("🔎 Filtro")

gleba = st.sidebar.text_input(
    "Digite a Gleba"
)

# =====================================
# CONSULTA
# =====================================

if gleba:

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

        tabela = resultado.copy()

        tabela["data_saida"] = tabela[
            "data_saida"
        ].dt.strftime("%d/%m/%Y")

        tabela = tabela.sort_values(
            "data_saida"
        )

        st.dataframe(
            tabela[
                [
                    "gleba",
                    "data_saida",
                    "tc_real",
                    "tc_estimado"
                ]
            ],
            use_container_width=True,
            hide_index=True
        )

else:

    st.info("Digite uma gleba no filtro ao lado.")
