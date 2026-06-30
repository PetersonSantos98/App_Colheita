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
    "eyJhbGciOiJI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6IndhdmdiZGRqbHdjcXNob2h3dXduIiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODI0ODI1MzksImV4cCI6MjA5ODA1ODUzOX0.LPkP2vw0P_CCT5ZIDrzgdlnLCt8aOdEXVxLCY_7QqBw"
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


    data_str = data_filtro.strftime(
        "%Y-%m-%d"
    )


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
                tc_real,
                tc_estimado
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
            f"Erro consulta dia: {erro}"
        )

        return []





# ==============================
# HISTÓRICO GLEBAS
# ==============================


@st.cache_data(ttl=1800)

def buscar_historico_glebas_ativas(lista_glebas):


    if not lista_glebas:

        return pd.DataFrame()



    try:


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



        if resposta.data:


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



            acumulado = (

                df.groupby("gleba")
                ["tc_real"]
                .sum()
                .reset_index()

            )



            acumulado.columns = [

                "gleba",

                "TC Total Gleba (Histórico)"

            ]



            return acumulado



        return pd.DataFrame()



    except Exception as erro:


        st.error(
            f"Erro histórico: {erro}"
        )


        return pd.DataFrame()

# ==============================
# CARREGAMENTO DOS DADOS
# ==============================


with st.spinner("Carregando dados da colheita..."):


    dados_banco = buscar_dados_cana(
        data_selecionada
    )



# ==============================
# PROCESSAMENTO
# ==============================


if not dados_banco:


    st.warning(
        f"Nenhum registro encontrado para {data_selecionada.strftime('%d/%m/%Y')}"
    )


else:


    df_dia = pd.DataFrame(
        dados_banco
    )



    df_dia["gleba"] = pd.to_numeric(
        df_dia["gleba"],
        errors="coerce"
    )



    colunas_num = [

        "tc_estimado",
        "tc_real",
        "atr",
        "mineral_pct",
        "vegetal_pct"

    ]



    df_dia[colunas_num] = (

        df_dia[colunas_num]

        .apply(
            pd.to_numeric,
            errors="coerce"
        )

        .fillna(0)

    )



    # Histórico das glebas

    glebas_do_dia = (

        df_dia["gleba"]

        .dropna()

        .unique()

        .tolist()

    )



    df_historico = buscar_historico_glebas_ativas(
        glebas_do_dia
    )




    # Filtro frentes


    lista_frentes = sorted(

        df_dia["frente"]

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

            df_dia["frente"]

            .isin(frentes_selecionadas)

        ]

    )





    # Junta histórico


    if not df_historico.empty:


        df_visualizacao = pd.merge(

            df_filtrado,

            df_historico,

            on="gleba",

            how="left"

        )


    else:


        df_visualizacao = df_filtrado.copy()


        df_visualizacao[

            "TC Total Gleba (Histórico)"

        ] = 0





    df_visualizacao[

        "TC Total Gleba (Histórico)"

    ] = (

        df_visualizacao[

            "TC Total Gleba (Histórico)"

        ]

        .fillna(0)

    )





    # ==============================
    # RENOMEAR COLUNAS
    # ==============================


    df_visualizacao = df_visualizacao.rename(

        columns={


            "frente":"Frente",

            "nome_fazenda":"Fazenda",

            "gleba":"Gleba",

            "tc_estimado":"TC Estimado",

            "tc_real":"TC (Dia)",

            "TC Total Gleba (Histórico)":"TC (Acumulado)",

            "atr":"ATR",

            "mineral_pct":"Imp. Mineral",

            "vegetal_pct":"Imp. Vegetal"


        }

    )





    ordem = [

        "Frente",

        "Fazenda",

        "Gleba",

        "TC Estimado",

        "TC (Dia)",

        "TC (Acumulado)",

        "ATR",

        "Imp. Mineral",

        "Imp. Vegetal"

    ]



    df_visualizacao = (

        df_visualizacao[ordem]

        .sort_values(

            by=[

                "Frente",

                "Fazenda",

                "Gleba"

            ]

        )

    )




    df_visualizacao["Gleba"] = (

        df_visualizacao["Gleba"]

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

        df_visualizacao["Frente"].nunique()

    )



    col3.metric(

        "🏭 Fazendas",

        df_visualizacao["Fazenda"].nunique()

    )



    media_atr = (

        df_visualizacao[

            df_visualizacao["ATR"] > 0

        ]["ATR"].mean()

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






    # ==============================
    # ABA DETALHADA
    # ==============================


    with aba_detalhe:


        st.markdown(

            f"### 📋 Entrada de Cana {data_selecionada.strftime('%d/%m/%Y')}"

        )



        st.dataframe(

            df_visualizacao.style.format(

                {

                    "TC Estimado":"{:,.2f}",

                    "TC (Dia)":"{:,.2f}",

                    "TC (Acumulado)":"{:,.2f}",

                    "ATR":"{:.2f}",

                    "Imp. Mineral":"{:.2f}",

                    "Imp. Vegetal":"{:.2f}"

                }

            ),

            width="stretch",

            hide_index=True,

            height=700

        )






    # ==============================
    # ABA CONSOLIDADO
    # ==============================


    with aba_consolidado:


        df_consolidado = (

            df_visualizacao

            .groupby("Frente")

            .agg(

                Total_TC=("TC (Dia)","sum"),

                Media_ATR=("ATR","mean"),

                Mineral=("Imp. Mineral","mean"),

                Vegetal=("Imp. Vegetal","mean"),

                Qtd_Glebas=("Gleba","nunique")

            )

            .reset_index()

        )



        st.dataframe(

            df_consolidado.style.format(

                {

                    "Total_TC":"{:,.2f}",

                    "Media_ATR":"{:.2f}",

                    "Mineral":"{:.2f}",

                    "Vegetal":"{:.2f}"

                }

            ),

            width="stretch",

            hide_index=True

        )







    # ==============================
    # ABA GRÁFICO
    # ==============================


    with aba_grafico:


        df_grafico = (

            df_visualizacao

            .groupby("Frente")

            ["TC (Dia)"]

            .sum()

            .reset_index()

        )



        st.bar_chart(

            df_grafico,

            x="Frente",

            y="TC (Dia)"

        )
