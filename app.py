import streamlit as st
import pandas as pd
from datetime import date
from supabase import create_client, Client


# ==============================
# CONFIGURAÇÃO
# ==============================

st.set_page_config(
    page_title="Relatório COA - Entrada de Cana",
    layout="wide"
)

st.title("📋Hora/Hora Estimado/Realizado (COA)")



# Atualização manual

if st.sidebar.button("🔄 Atualizar Agora"):

    st.cache_data.clear()
    st.rerun()



# Auto refresh 1 minuto

st.fragment(run_every=60)



# ==============================
# SUPABASE
# ==============================


SUPABASE_URL = st.secrets.get(
    "SUPABASE_URL",
    "https://wavgbddjlwcqshohwuwn.supabase.co"
)


SUPABASE_KEY = st.secrets.get(
    "SUPABASE_KEY",
    "eyJhbGciOiJI1NiIsInR5cCI6IkpXVCJ9..."
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




# ==============================
# FILTROS
# ==============================


st.sidebar.header(
    "🔍 Filtros de Pesquisa"
)


data_selecionada = st.sidebar.date_input(
    "Selecione a data:",
    date.today()
)



# ==============================
# BUSCA DIA
# ==============================


@st.cache_data(ttl=60)

def buscar_dados_cana(data_filtro):


    data_str = data_filtro.strftime("%Y-%m-%d")


    try:


        resposta = supabase.table(
            "APP COLHEITA"
        ).select(
            """
            frente,
            nome_fazenda,
            gleba,
            atr,
            mineral_pct,
            vegetal_pct,
            tc_real,
            tc_estimado
            """
        ).eq(
            "data_saida",
            data_str
        ).execute()



        return resposta.data if hasattr(resposta,"data") else []



    except Exception as erro:


        st.error(
            f"Erro consulta dia: {erro}"
        )

        return []





# ==============================
# HISTÓRICO
# ==============================


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


        lista = [
            int(g)
            for g in lista_glebas
            if pd.notna(g)
        ]



        resposta = supabase.table(
            "APP COLHEITA"
        ).select(
            "gleba, tc_real"
        ).in_(
            "gleba",
            lista
        ).execute()



        if resposta.data:


            df = pd.DataFrame(
                resposta.data
            )


            df['gleba'] = pd.to_numeric(
                df['gleba'],
                errors='coerce'
            )


            df['tc_real'] = pd.to_numeric(
                df['tc_real'],
                errors='coerce'
            ).fillna(0)



            retorno = (
                df.groupby('gleba')
                ['tc_real']
                .sum()
                .reset_index()
            )


            retorno.columns = [
                'gleba',
                'TC Total Gleba (Histórico)'
            ]


            return retorno



        return pd.DataFrame()



    except Exception as erro:


        st.error(
            f"Erro histórico: {erro}"
        )

        return pd.DataFrame()





# ==============================
# PROCESSAMENTO
# ==============================


with st.spinner(
    "Carregando dados..."
):


    dados_banco = buscar_dados_cana(
        data_selecionada
    )



if not dados_banco:


    st.warning(
        "Nenhum registro encontrado."
    )


else:


    df_dia = pd.DataFrame(
        dados_banco
    )


    df_dia['gleba'] = pd.to_numeric(
        df_dia['gleba'],
        errors='coerce'
    )


    colunas = [

        'tc_estimado',
        'tc_real',
        'atr',
        'mineral_pct',
        'vegetal_pct'

    ]


    df_dia[colunas] = (
        df_dia[colunas]
        .apply(
            pd.to_numeric,
            errors='coerce'
        )
        .fillna(0)
    )



    glebas = (
        df_dia['gleba']
        .dropna()
        .unique()
        .tolist()
    )


    df_hist = buscar_historico_glebas_ativas(
        glebas
    )



    frentes = sorted(
        df_dia['frente']
        .unique()
        .tolist()
    )


    selecionadas = st.sidebar.multiselect(
        "Selecione as Frentes:",
        frentes,
        default=frentes
    )



    df_filtrado = (
        df_dia
        if not selecionadas
        else df_dia[
            df_dia['frente']
            .isin(selecionadas)
        ]
    )



    if not df_hist.empty:


        df_visualizacao = pd.merge(
            df_filtrado,
            df_hist,
            on="gleba",
            how="left"
        )


    else:


        df_visualizacao = df_filtrado.copy()

        df_visualizacao[
            'TC Total Gleba (Histórico)'
        ] = 0





    df_visualizacao[
        'TC Total Gleba (Histórico)'
    ] = (
        df_visualizacao[
            'TC Total Gleba (Histórico)'
        ]
        .fillna(0)
    )




    df_visualizacao = df_visualizacao.rename(
        columns={

            'frente':'Frente',
            'nome_fazenda':'Fazenda',
            'gleba':'Gleba',
            'tc_estimado':'TC Estimado',
            'tc_real':'TC (Dia)',
            'TC Total Gleba (Histórico)':'TC (Acumulado)',
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
        'TC Estimado',
        'TC (Dia)',
        'TC (Acumulado)',
        'ATR',
        'Imp. Mineral',
        'Imp. Vegetal'
        ]

    ]



    df_visualizacao['Gleba'] = (
        df_visualizacao['Gleba']
        .fillna(0)
        .astype(int)
        .astype(str)
    )



    # ==============================
    # RESUMO
    # ==============================


    col1,col2,col3,col4 = st.columns(4)



    col1.metric(
        "🚜 TC Hoje",
        f"{df_visualizacao['TC (Dia)'].sum():,.2f}"
    )


    col2.metric(
        "🚜 Frentes",
        df_visualizacao['Frente'].nunique()
    )


    col3.metric(
        "🏭 Fazendas",
        df_visualizacao['Fazenda'].nunique()
    )



    media_atr = (
        df_visualizacao[
            df_visualizacao['ATR']>0
        ]['ATR'].mean()
    )



    col4.metric(
        "📈 Média ATR",
        f"{media_atr:.2f}"
    )



    st.divider()



    # ==============================
    # ABAS
    # ==============================


    aba_detalhe, aba_consolidado, aba_grafico = st.tabs(

        [
            "📋 Romaneios Detalhados",
            "🧮 Consolidado por Frente",
            "📈 Gráfico por Frente"
        ]

    )




    with aba_detalhe:


        st.dataframe(

            df_visualizacao.style.format(

                {

                'TC Estimado':'{:,.2f}',
                'TC (Dia)':'{:,.2f}',
                'TC (Acumulado)':'{:,.2f}',
                'ATR':'{:.2f}',
                'Imp. Mineral':'{:.2f}',
                'Imp. Vegetal':'{:.2f}'

                }

            ),

            width="stretch",
            hide_index=True,
            height=700

        )





    with aba_consolidado:


        consolidado = (

            df_visualizacao
            .groupby('Frente')
            .agg(

                Total_TC=('TC (Dia)','sum'),
                Media_ATR=('ATR','mean'),
                Mineral=('Imp. Mineral','mean'),
                Vegetal=('Imp. Vegetal','mean')

            )

            .reset_index()

        )



        st.dataframe(

            consolidado.style.format(
                {
                'Total_TC':'{:,.2f}',
                'Media_ATR':'{:.2f}',
                'Mineral':'{:.2f}',
                'Vegetal':'{:.2f}'
                }
            ),

            width="stretch",
            hide_index=True

        )





    with aba_grafico:


        grafico = (

            df_visualizacao
            .groupby('Frente')['TC (Dia)']
            .sum()
            .reset_index()

        )


        st.bar_chart(

            grafico,
            x="Frente",
            y="TC (Dia)"

        )
