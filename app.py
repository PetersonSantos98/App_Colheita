import streamlit as st
import pandas as pd
from datetime import date, datetime
from supabase import create_client, Client

SUPABASE_URL = st.secrets.get(
    "SUPABASE_URL",
    "https://wavgbddjlwcqshohwuwn.supabase.co"
)

SUPABASE_KEY = st.secrets.get(
    "SUPABASE_KEY",
    "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJ3YXZnYmRkamx3Y3Nob2h3dXduIiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODI0ODI1MzksImV4cCI6MjA5ODA1ODUzOX0.LPkP2vw0P_CCT5ZIDrzgdlnCt8aOdEXVxLCY_7QqBw"
)
# 1. Configuração da página do Streamlit

st.set_page_config(
    page_title="Relatório COA - Entrada de Cana",
    layout="wide"
)

st.title("📋 Hora/Hora Estimado/Realizado (COA)")



# Botão manual

if st.sidebar.button("🔄 Atualizar Agora"):

    st.rerun()



# Auto refresh 30 minutos

@st.fragment(run_every=1800)
def refresh():

    pass


refresh()



# 2. Conexão com Supabase

SUPABASE_URL = st.secrets.get(
    "SUPABASE_URL",
    "https://wavgbddjlwcqshohwuwn.supabase.co"
)


SUPABASE_KEY = st.secrets.get(
    "SUPABASE_KEY",
    "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJ3YXZnYmRkamx3Y3FzaG9od3V3biIsInJvbGUiOiJhbm9uIiwiaWF0IjoxNzgyNDgyNTM5LCJleHAiOjIwOTgwNTg1Mzl9.LPkP2vw0P_CCT5ZIDrzgdlnCt8aOdEXVxLCY_7QqBw"
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





# 3. FILTROS

st.sidebar.header(
    "🔍 Filtros de Pesquisa"
)



data_selecionada = st.sidebar.date_input(
    "Selecione a data:",
    date.today()
)





# 4. Buscar dados do dia

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


        if resposta and hasattr(resposta,"data"):

            return resposta.data


        return []



    except Exception as erro:

        st.error(
            f"Erro na consulta do Supabase (Dados do Dia): {erro}"
        )

        return []







# Histórico glebas

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



        if resposta and hasattr(resposta,"data") and resposta.data:


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



            df_acumulado = (

                df_hist
                .groupby('gleba')['tc_real']
                .sum()
                .reset_index()

            )



            df_acumulado.columns = [

                'gleba',
                'TC Total Gleba (Histórico)'

            ]



            return df_acumulado



        return pd.DataFrame()



    except Exception as erro:


        st.error(
            f"Erro ao calcular histórico das glebas: {erro}"
        )


        return pd.DataFrame()






# Carregamento

with st.spinner(
    "Carregando dados da colheita..."
):

    dados_banco = buscar_dados_cana(
        data_selecionada
    )






if not dados_banco:


    st.warning(
        f"Nenhum registro encontrado para o dia {data_selecionada.strftime('%d/%m/%Y')}."
    )


else:


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





    # Histórico

    glebas_do_dia = (

        df_dia['gleba']
        .dropna()
        .unique()
        .tolist()

    )


    df_historico_glebas = buscar_historico_glebas_ativas(
        glebas_do_dia
    )





    # Filtro frentes

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



    df_filtrado = (

        df_dia

        if not frentes_selecionadas

        else df_dia[
            df_dia['frente']
            .isin(frentes_selecionadas)
        ]

    )





    # Merge histórico

    if not df_historico_glebas.empty:


        df_visualizacao = pd.merge(

            df_filtrado,

            df_historico_glebas,

            on='gleba',

            how='left'

        )


    else:


        df_visualizacao = df_filtrado.copy()


        df_visualizacao[
            'TC Total Gleba (Histórico)'
        ] = 0.0





    df_visualizacao[
        'TC Total Gleba (Histórico)'
    ] = (

        df_visualizacao[
            'TC Total Gleba (Histórico)'
        ]

        .fillna(0)

    )






    # Renomear

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




    ordem_colunas = [

        'Frente',
        'Fazenda',
        'Gleba',
        'TC Real (Dia)',
        'TC Total Gleba (Histórico)',
        'ATR',
        'Imp. Mineral',
        'Imp. Vegetal'

    ]



    df_visualizacao = (

        df_visualizacao[ordem_colunas]

        .sort_values(
            by=[
                'Frente',
                'Fazenda',
                'Gleba'
            ]
        )

    )




    df_visualizacao['Gleba'] = (

        df_visualizacao['Gleba']

        .fillna(0)

        .astype(int)

        .astype(str)

    )






    # ==============================
    # VISUAL BI
    # ==============================


    c1,c2,c3,c4 = st.columns(4)



    c1.metric(
        "🚜 TC Real Hoje",
        f"{df_visualizacao['TC Real (Dia)'].sum():,.2f}"
    )


    c2.metric(
        "🌱 TC Histórico",
        f"{df_visualizacao['TC Total Gleba (Histórico)'].sum():,.2f}"
    )


    c3.metric(
        "🧪 ATR Médio",
        f"{df_visualizacao['ATR'].mean():.2f}"
    )


    c4.metric(
        "📍 Glebas",
        df_visualizacao['Gleba'].nunique()
    )



    st.divider()



    hora_atual = datetime.now().strftime(
        "%H:%M:%S"
    )


    st.markdown(
        f"### 📋 Entrada de Cana {data_selecionada.strftime('%d/%m/%Y')} - Atualizado {hora_atual}"
    )




    st.dataframe(

        df_visualizacao.style.format({

            'TC Real (Dia)': '{:,.2f}',

            'TC Total Gleba (Histórico)': '{:,.2f}',

            'ATR': '{:.2f}',

            'Imp. Mineral': '{:.2f}',

            'Imp. Vegetal': '{:.2f}'

        }),

        use_container_width=True,

        hide_index=True,

        height=700

    )
