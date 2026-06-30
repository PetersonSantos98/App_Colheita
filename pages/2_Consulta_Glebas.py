import streamlit as st
import pandas as pd
from supabase import create_client


# ======================================
# CONFIG
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
# BUSCA APENAS GLEBAS
# ======================================

@st.cache_data(ttl=300)
def buscar_glebas():

    resposta = (
        supabase
        .table("APP COLHEITA")
        .select("gleba")
        .execute()
    )

    df = pd.DataFrame(resposta.data)

    if df.empty:
        return []

    df["gleba"] = pd.to_numeric(
        df["gleba"],
        errors="coerce"
    )

    df = df.dropna()

    return (
        df["gleba"]
        .astype(int)
        .unique()
        .tolist()
    )


# ======================================
# BUSCA SOMENTE A GLEBA ESCOLHIDA
# ======================================

@st.cache_data(ttl=60)
def buscar_dados_gleba(lista_glebas):

    resposta = (
        supabase
        .table("APP COLHEITA")
        .select("*")
        .in_("gleba", lista_glebas)
        .execute()
    )


    df = pd.DataFrame(resposta.data)


    if not df.empty:

        df["gleba"] = pd.to_numeric(
            df["gleba"],
            errors="coerce"
        )

        df["tc_real"] = pd.to_numeric(
            df["tc_real"],
            errors="coerce"
        )

        df["tc_estimado"] = pd.to_numeric(
            df["tc_estimado"],
            errors="coerce"
        )

    return df



# ======================================
# FILTRO
# ======================================


lista = buscar_glebas()


st.sidebar.header("🔎 Filtro")

glebas = st.sidebar.multiselect(
    "Selecione a gleba",
    lista
)



# ======================================
# RESULTADO
# ======================================

if glebas:


    dados = buscar_dados_gleba(
        glebas
    )


    if dados.empty:

        st.warning(
            "Nenhum dado encontrado."
        )

        st.stop()



    tc_real = dados["tc_real"].sum()


    tc_estimado = (
        dados
        .groupby("gleba")
        ["tc_estimado"]
        .first()
        .sum()
    )


    percentual = (
        tc_real / tc_estimado * 100
        if tc_estimado > 0
        else 0
    )



    c1,c2,c3 = st.columns(3)


    c1.metric(
        "🌱 Realizado",
        f"{tc_real:,.2f}"
    )


    c2.metric(
        "📋 Estimado",
        f"{tc_estimado:,.2f}"
    )


    c3.metric(
        "📈 Concluído",
        f"{percentual:.1f}%"
    )



    st.divider()



    tabela = (
        dados
        .groupby(
            ["gleba","frente"],
            as_index=False
        )
        .agg(
            {
                "tc_real":"sum",
                "tc_estimado":"first"
            }
        )
    )


    tabela.columns = [
        "Gleba",
        "Frente",
        "TC Real",
        "TC Estimado"
    ]


    st.dataframe(
        tabela,
        use_container_width=True,
        hide_index=True
    )


else:

    st.info(
        "Selecione uma gleba."
    )
