import streamlit as st
import pandas as pd
from datetime import date, datetime
from supabase import create_client, Client


# =====================================================
# CONFIGURAÇÃO
# =====================================================

st.set_page_config(
    page_title="Relatório COA - Entrada de Cana",
    layout="wide"
)


st.title("📋 Hora/Hora Estimado/Realizado (COA)")



# =====================================================
# ATUALIZAÇÃO MANUAL
# =====================================================

if st.sidebar.button("🔄 Atualizar Agora"):
    st.cache_data.clear()
    st.rerun()



# =====================================================
# AUTO REFRESH 30 MINUTOS
# =====================================================

@st.fragment(run_every=1800)
def atualizacao():

    pass


atualizacao()



# =====================================================
# SUPABASE
# =====================================================

SUPABASE_URL = st.secrets.get(
    "SUPABASE_URL",
    "https://wavgbddjlwcqshohwuwn.supabase.co"
)


SUPABASE_KEY = st.secrets.get(
    "SUPABASE_KEY",
    "SUA_CHAVE_COMPLETA_AQUI"
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
        f"Erro ao conectar ao Supabase: {e}"
    )

    st.stop()



# =====================================================
# FILTROS
# =====================================================

st.sidebar.header(
    "🔍 Filtros de Pesquisa"
)



data_selecionada = st.sidebar.date_input(
    "Selecione a data:",
    date.today()
)



# =====================================================
# BUSCAR DADOS DO DIA
# =====================================================

@st.cache_data(ttl=1800)

def buscar_dados_cana(data_filtro):

    data_str = data_filtro.strftime(
        "%Y-%m-%d"
    )


    try:

        resposta = (

            supabase
            .table("APP COLHEITA")
            .select(
                "frente, nome_fazenda, gleba, atr, mineral_pct, vegetal_pct, tc_real"
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
            f"Erro consulta Supabase: {erro}"
        )


        return []





# =====================================================
# HISTÓRICO GLEBAS
# =====================================================

@st.cache_data(ttl=1800)

def buscar_historico_glebas_ativas(lista_glebas):


    if not lista_glebas:

        return pd.DataFrame(
            columns=[
                'gleba',
                'TC Total Gleba (Histórico)'
            ]
        )



    try:


        lista_glebas_int = [

            int(g)

            for g in lista_glebas

            if pd.notna(g)

        ]



        resposta = (

            supabase
            .table("APP COLHEITA")
            .select(
                "gleba, tc_real"
            )
            .in_(
                "gleba",
                lista_glebas_int
            )
            .execute()

        )



        if resposta.data:


            df_hist = pd.DataFrame(
                resposta.data
            )



            df_hist['gleba'] = pd.to_numeric(
                df_hist['gleba'],
                errors='coerce'
            )



            df_hist['tc_real'] = pd.to_numeric(
                df_hist['tc_real'],
                errors='coerce'
            ).fillna(0)



            df = (

                df_hist
                .groupby('gleba')['tc_real']
                .sum()
                .reset_index()

            )



            df.columns = [

                'gleba',
                'TC Total Gleba (Histórico)'

            ]



            return df



        return pd.DataFrame()



    except Exception as erro:


        st.error(
            f"Erro histórico: {erro}"
        )


        return pd.DataFrame()





# =====================================================
# PROCESSAMENTO
# =====================================================


with st.spinner(
    "Carregando dados..."
):


    dados_banco = buscar_dados_cana(
        data_selecionada
    )



if not dados_banco:


    st.warning(
        f"Nenhum registro encontrado para {data_selecionada.strftime('%d/%m/%Y')}"
    )

    st.stop()



df_dia = pd.DataFrame(
    dados_banco
)



df_dia['gleba'] = pd.to_numeric(
    df_dia['gleba'],
    errors='coerce'
)



colunas_num = [

    'tc_real',
    'atr',
    'mineral_pct',
    'vegetal_pct'

]



df_dia[colunas_num] = (

    df_dia[colunas_num]

    .apply(
        pd.to_numeric,
        errors='coerce'
    )

    .fillna(0)

)





# =====================================================
# FILTRO FRENTES
# =====================================================


lista_frentes = sorted(
    df_dia['frente']
    .unique()
    .tolist()
)



frentes_selecionadas = st.sidebar.multiselect(
    "Selecione as Frentes:",
    options=lista_frentes,
    default=lista_frentes
)



if frentes_selecionadas:


    df_filtrado = df_dia[

        df_dia['frente']
        .isin(frentes_selecionadas)

    ]

else:

    df_filtrado = df_dia





# =====================================================
# CRUZAMENTO HISTÓRICO
# =====================================================


glebas_do_dia = (

    df_filtrado['gleba']
    .dropna()
    .unique()
    .tolist()

)



df_historico = buscar_historico_glebas_ativas(
    glebas_do_dia
)




df_visualizacao = pd.merge(

    df_filtrado,

    df_historico,

    on='gleba',

    how='left'

)



df_visualizacao[
    'TC Total Gleba (Histórico)'
] = (

    df_visualizacao[
        'TC Total Gleba (Histórico)'
    ]

    .fillna(0)

)





# =====================================================
# RENOMEAR COLUNAS
# =====================================================


df_visualizacao = df_visualizacao.rename(

    columns={

        'frente':'Frente',

        'nome_fazenda':'Fazenda',

        'gleba':'Gleba',

        'tc_real':'TC Real (Dia)',

        'atr':'ATR',

        'mineral_pct':'Imp. Mineral',

        'vegetal_pct':'Imp. Vegetal'

    }

)




df_visualizacao = df_visualizacao[

[

'Frente',

'Fazenda',

'Gleba',

'TC Real (Dia)',

'TC Total Gleba (Histórico)',

'ATR',

'Imp. Mineral',

'Imp. Vegetal'

]

]




df_visualizacao = df_visualizacao.sort_values(

    by=[
        'Frente',
        'Fazenda',
        'Gleba'
    ]

)



df_visualizacao['Gleba'] = (

    df_visualizacao['Gleba']

    .fillna(0)

    .astype(int)

    .astype(str)

)





# =====================================================
# PAINEL BI
# =====================================================


col1, col2, col3, col4 = st.columns(4)



with col1:

    st.metric(

        "🚜 TC Real Hoje",

        f"{df_visualizacao['TC Real (Dia)'].sum():,.2f}"

    )



with col2:

    st.metric(

        "🌱 TC Histórico",

        f"{df_visualizacao['TC Total Gleba (Histórico)'].sum():,.2f}"

    )



with col3:

    st.metric(

        "🧪 ATR Médio",

        f"{df_visualizacao['ATR'].mean():.2f}"

    )



with col4:

    st.metric(

        "📍 Glebas",

        df_visualizacao['Gleba'].nunique()

    )




st.divider()



hora_atual = datetime.now().strftime(
    "%H:%M:%S"
)



st.markdown(

    f"""

    <h2 style='text-align:center'>

    📋 Entrada de Cana {data_selecionada.strftime('%d/%m/%Y')}

    </h2>


    <p style='text-align:center'>

    Última atualização: {hora_atual}

    </p>

    """,

    unsafe_allow_html=True

)




# =====================================================
# TABELA FINAL
# =====================================================


st.dataframe(

    df_visualizacao.style.format({

        'TC Real (Dia)': '{:,.2f}',

        'TC Total Gleba (Histórico)': '{:,.2f}',

        'ATR': '{:.2f}',

        'Imp. Mineral': '{:.2f}',

        'Imp. Vegetal': '{:.2f}'

    }),

    width="stretch",

    hide_index=True,

    height=700

)
