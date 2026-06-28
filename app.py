import streamlit as st
import pandas as pd
from datetime import date, datetime
from supabase import create_client, Client


# =====================================================
# CONFIGURAÇÃO DA PÁGINA
# =====================================================

st.set_page_config(
    page_title="Relatório COA - Entrada de Cana",
    layout="wide",
    initial_sidebar_state="expanded"
)


# Auto refresh 30 minutos
@st.fragment(run_every=1800)
def atualizacao_auto():
    pass

atualizacao_auto()


# =====================================================
# TÍTULO
# =====================================================

st.markdown(
    """
    <h1 style='text-align:center'>
    📋 Hora/Hora Estimado/Realizado (COA)
    </h1>
    """,
    unsafe_allow_html=True
)



# =====================================================
# BOTÃO ATUALIZAR
# =====================================================

if st.sidebar.button("🔄 Atualizar Agora"):
    st.cache_data.clear()
    st.rerun()



# =====================================================
# SUPABASE
# =====================================================

SUPABASE_URL = st.secrets.get(
    "SUPABASE_URL",
    "https://wavgbddjlwcqshohwuwn.supabase.co"
)


SUPABASE_KEY = st.secrets.get(
    "SUPABASE_KEY",
    "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
)


@st.cache_resource
def init_connection():

    return create_client(
        SUPABASE_URL,
        SUPABASE_KEY
    )


try:

    supabase: Client = init_connection()

except Exception as e:

    st.error(
        f"Erro conexão Supabase: {e}"
    )

    st.stop()



# =====================================================
# FILTROS
# =====================================================

st.sidebar.header("🔍 Filtros de Pesquisa")


data_selecionada = st.sidebar.date_input(
    "Selecione a data:",
    date.today()
)



# =====================================================
# BUSCA DADOS DO DIA
# =====================================================

@st.cache_data(ttl=1800)
def buscar_dados_cana(data_filtro):

    data_str = data_filtro.strftime("%Y-%m-%d")

    try:

        resposta = (
            supabase
            .table("APP COLHEITA")
            .select(
                """
                frente,
                nome_fazenda,
                gleba,
                atr,
                mineral_pct,
                vegetal_pct,
                tc_real
                """
            )
            .eq(
                "data_saida",
                data_str
            )
            .execute()
        )


        return resposta.data


    except Exception as erro:

        st.error(
            f"Erro consulta: {erro}"
        )

        return []



# =====================================================
# HISTÓRICO DAS GLEBAS
# =====================================================


@st.cache_data(ttl=1800)
def buscar_historico_glebas(lista_glebas):


    if not lista_glebas:

        return pd.DataFrame()



    lista = [
        int(x)
        for x in lista_glebas
        if pd.notna(x)
    ]



    resposta = (
        supabase
        .table("APP COLHEITA")
        .select(
            "gleba, tc_real"
        )
        .in_(
            "gleba",
            lista
        )
        .execute()
    )



    if not resposta.data:

        return pd.DataFrame()



    df = pd.DataFrame(
        resposta.data
    )



    df["gleba"] = pd.to_numeric(
        df["gleba"],
        errors="coerce"
    )


    df["tc_real"] = pd.to_numeric(
        df["tc_real"],
        errors="coerce"
    ).fillna(0)



    df = (
        df
        .groupby("gleba")
        ["tc_real"]
        .sum()
        .reset_index()
    )



    df.columns = [
        "gleba",
        "TC Total Gleba (Histórico)"
    ]



    return df



# =====================================================
# CARREGAMENTO
# =====================================================


with st.spinner(
    "Carregando dados..."
):


    dados = buscar_dados_cana(
        data_selecionada
    )



if not dados:


    st.warning(
        "Nenhum registro encontrado."
    )

    st.stop()



# =====================================================
# TRATAMENTO
# =====================================================


df = pd.DataFrame(dados)



for coluna in [
    "tc_real",
    "atr",
    "mineral_pct",
    "vegetal_pct"
]:

    df[coluna] = pd.to_numeric(
        df[coluna],
        errors="coerce"
    ).fillna(0)



df["gleba"] = pd.to_numeric(
    df["gleba"],
    errors="coerce"
)



# =====================================================
# FILTRO FRENTES
# =====================================================


frentes = sorted(
    df["frente"]
    .dropna()
    .unique()
    .tolist()
)


selecionadas = st.sidebar.multiselect(
    "Selecione as Frentes:",
    frentes,
    default=frentes
)



if selecionadas:

    df = df[
        df["frente"]
        .isin(selecionadas)
    ]



# =====================================================
# HISTÓRICO
# =====================================================


historico = buscar_historico_glebas(
    df["gleba"].unique()
)



df_final = pd.merge(
    df,
    historico,
    on="gleba",
    how="left"
)



df_final[
    "TC Total Gleba (Histórico)"
] = (
    df_final[
        "TC Total Gleba (Histórico)"
    ]
    .fillna(0)
)



# =====================================================
# RENOMEAR
# =====================================================


df_final = df_final.rename(
    columns={

        "frente":"Frente",
        "nome_fazenda":"Fazenda",
        "gleba":"Gleba",
        "tc_real":"TC Real (Dia)",
        "atr":"ATR",
        "mineral_pct":"Imp. Mineral",
        "vegetal_pct":"Imp. Vegetal"

    }
)



df_final = df_final[
[
"Frente",
"Fazenda",
"Gleba",
"TC Real (Dia)",
"TC Total Gleba (Histórico)",
"ATR",
"Imp. Mineral",
"Imp. Vegetal"
]
]



df_final["Gleba"] = (
    df_final["Gleba"]
    .fillna(0)
    .astype(int)
    .astype(str)
)



# =====================================================
# KPIs
# =====================================================


col1,col2,col3,col4 = st.columns(4)



with col1:

    st.metric(
        "🚜 TC Real Hoje",
        f"{df_final['TC Real (Dia)'].sum():,.2f}"
    )


with col2:

    st.metric(
        "🌱 TC Histórico",
        f"{df_final['TC Total Gleba (Histórico)'].sum():,.2f}"
    )


with col3:

    st.metric(
        "🧪 ATR Médio",
        f"{df_final['ATR'].mean():.2f}"
    )


with col4:

    st.metric(
        "📍 Glebas",
        df_final["Gleba"].nunique()
    )



st.divider()



# =====================================================
# TABELA FINAL
# =====================================================


hora = datetime.now().strftime(
    "%H:%M:%S"
)


st.markdown(
    f"""
    <h2 style='text-align:center'>
    Entrada de Cana - {data_selecionada.strftime('%d/%m/%Y')}
    </h2>

    <p style='text-align:center'>
    Última atualização: {hora}
    </p>
    """,
    unsafe_allow_html=True
)



st.dataframe(

    df_final.style.format({

        "TC Real (Dia)":"{:,.2f}",
        "TC Total Gleba (Histórico)":"{:,.2f}",
        "ATR":"{:.2f}",
        "Imp. Mineral":"{:.2f}",
        "Imp. Vegetal":"{:.2f}"

    }),

    use_container_width=True,

    hide_index=True,

    height=650
)
