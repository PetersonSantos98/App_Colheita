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
# BUSCAR TODAS AS GLEBAS COM PAGINAÇÃO
# ======================================

@st.cache_data(ttl=300)
def buscar_glebas():

    registros = []

    inicio = 0
    limite = 1000


    while True:

        resposta = (
            supabase
            .table("APP COLHEITA")
            .select("gleba")
            .range(
                inicio,
                inicio + limite - 1
            )
            .execute()
        )


        dados = resposta.data


        if not dados:
            break


        registros.extend(dados)


        if len(dados) < limite:
            break


        inicio += limite



    df = pd.DataFrame(registros)


    if df.empty:
        return []


    df["gleba"] = pd.to_numeric(
        df["gleba"],
        errors="coerce"
    )


    df = df.dropna()


    return sorted(
        df["gleba"]
        .astype(int)
        .unique()
        .tolist()
    )



# ======================================
# BUSCAR DADOS DAS GLEBAS SELECIONADAS
# ======================================

@st.cache_data(ttl=60)
def buscar_dados_gleba(glebas):


    registros = []

    inicio = 0
    limite = 1000


    while True:


        resposta = (
            supabase
            .table("APP COLHEITA")
            .select("*")
            .in_(
                "gleba",
                glebas
            )
            .range(
                inicio,
                inicio + limite - 1
            )
            .execute()
        )


        dados = resposta.data


        if not dados:
            break


        registros.extend(dados)


        if len(dados) < limite:
            break


        inicio += limite



    df = pd.DataFrame(registros)



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

lista_glebas = buscar_glebas()


st.sidebar.header("🔎 Filtro")


glebas_selecionadas = st.sidebar.multiselect(
    "Selecione a Gleba",
    options=lista_glebas
)



# ======================================
# RESULTADO
# ======================================

if glebas_selecionadas:


    dados = buscar_dados_gleba(
        glebas_selecionadas
    )


    if dados.empty:

        st.warning(
            "Nenhum registro encontrado."
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
        (tc_real / tc_estimado) * 100
        if tc_estimado > 0
        else 0
    )



    col1,col2,col3 = st.columns(3)



    col1.metric(
        "🌱 TC Realizado",
        f"{tc_real:,.2f}"
    )


    col2.metric(
        "📋 TC Estimado",
        f"{tc_estimado:,.2f}"
    )


    col3.metric(
        "📈 % Concluído",
        f"{percentual:.1f}%"
    )



    st.divider()



    tabela = (
        dados
        .groupby(
            [
                "gleba",
                "frente"
            ],
            as_index=False
        )
        .agg(
            {
                "tc_real":"sum",
                "tc_estimado":"first"
            }
        )
    )



    tabela = tabela.rename(
        columns={
            "gleba":"Gleba",
            "frente":"Frente",
            "tc_real":"TC Real",
            "tc_estimado":"TC Estimado"
        }
    )



    st.dataframe(
        tabela,
        use_container_width=True,
        hide_index=True
    )


else:


    st.info(
        "Selecione uma gleba no filtro lateral."
    )
