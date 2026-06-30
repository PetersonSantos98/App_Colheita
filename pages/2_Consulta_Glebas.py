import streamlit as st
import pandas as pd
from supabase import create_client, Client


# ==============================
# CONFIGURAÇÃO
# ==============================

st.set_page_config(
    page_title="Consulta Glebas - COA",
    page_icon="🌱",
    layout="wide"
)


st.title("🌱 Consulta por Gleba")



# ==============================
# SUPABASE
# ==============================

SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]

supabase: Client = create_client(
    SUPABASE_URL,
    SUPABASE_KEY
)



# ==============================
# BUSCAR GLEBAS
# ==============================

@st.cache_data(ttl=1800)
def buscar_glebas():

    try:

        resposta = (
            supabase
            .table("sua_tabela_glebas")
            .select("*")
            .execute()
        )

        return pd.DataFrame(
            resposta.data
        )


    except Exception as e:

        st.error(e)

        return pd.DataFrame()



dados_glebas = buscar_glebas()



# ==============================
# FILTRO LATERAL
# ==============================

st.sidebar.header("🔎 Filtro")


if not dados_glebas.empty:


    lista_glebas = (
        dados_glebas["gleba"]
        .dropna()
        .unique()
        .tolist()
    )


    gleba_sel = st.sidebar.multiselect(
        "Selecione a Gleba",
        lista_glebas
    )


else:

    st.sidebar.warning(
        "Nenhuma gleba encontrada"
    )

    gleba_sel = []



# ==============================
# CONSULTA
# ==============================

if gleba_sel:


    resultado = dados_glebas[
        dados_glebas["gleba"].isin(
            gleba_sel
        )
    ]


    st.subheader("Resultado")


    col1, col2 = st.columns(2)


    with col1:

        st.metric(
            "🌱 TC Acumulado Realizado",
            f"{resultado['TC'].sum():,.0f}"
        )


    with col2:

        # NÃO SOMA ESTIMADO
        estimado = resultado["Estimado"].iloc[0]


        st.metric(
            "📋 Estimado",
            f"{estimado:,.0f}"
        )



    st.dataframe(
        resultado,
        use_container_width=True
    )


else:

    st.info(
        "Selecione uma gleba no filtro lateral"
    )
