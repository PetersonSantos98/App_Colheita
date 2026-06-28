import streamlit as st

import pandas as pd

from datetime import date

from supabase import create_client, Client



# 1. Configuração da página do Streamlit

st.set_page_config(page_title="Relatório COA - Entrada de Cana", layout="wide")

st.title("📋Hora/Hora Estimado/Realizado (COA)")



# Botão manual de emergência na barra lateral

if st.sidebar.button("🔄 Atualizar Agora"):

    st.rerun()



# Configuração do Auto-refresh de 30 minutos (1800 segundos) para atualizar a tela

st.fragment(run_every=1800)



# 2. Conexão com o Supabase

SUPABASE_URL = st.secrets.get("SUPABASE_URL", "https://wavgbddjlwcqshohwuwn.supabase.co")

SUPABASE_KEY = st.secrets.get("SUPABASE_KEY", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6IndhdmdiZGRqbHdjcXNob2h3dXduIiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODI0ODI1MzksImV4cCI6MjA5ODA1ODUzOX0.LPkP2vw0P_CCT5ZIDrzgdlnLCt8aOdEXVxLCY_7QqBw")



@st.cache_resource

def init_connection():

    return create_client(SUPABASE_URL, SUPABASE_KEY)



try:

    supabase: Client = init_connection()

except Exception as e:

    st.error(f"Erro ao conectar ao Supabase: {e}")

    st.stop()



# 3. FILTROS NA BARRA LATERAL

st.sidebar.header("🔍 Filtros de Pesquisa")

data_selecionada = st.sidebar.date_input("Selecione a data:", date.today())



# 4. Busca dos dados do dia selecionado (Cache de 30 min)

@st.cache_data(ttl=1800)

def buscar_dados_cana(data_filtro):

    data_str = data_filtro.strftime("%Y-%m-%d")

    try:

        resposta = supabase.table("APP COLHEITA").select("frente, nome_fazenda, gleba, atr, mineral_pct, vegetal_pct, tc_real").eq("data_saida", data_str).execute()

        if resposta and hasattr(resposta, "data"):

            return resposta.data

        return []

    except Exception as erro:

        st.error(f"Erro na consulta do Supabase (Dados do Dia): {erro}")

        return []



# Busca o acumulado somado filtrando apenas pelas glebas que estão ativas no dia

@st.cache_data(ttl=1800)

def buscar_historico_glebas_ativas(lista_glebas):

    if not lista_glebas:

        return pd.DataFrame(columns=['gleba', 'TC Total Gleba (Histórico)'])

    try:

        lista_glebas_int = [int(g) for g in lista_glebas if pd.notna(g)]

        resposta = supabase.table("APP COLHEITA").select("gleba, tc_real").in_("gleba", lista_glebas_int).execute()

        

        if resposta and hasattr(resposta, "data") and resposta.data:

            df_hist = pd.DataFrame(resposta.data)

            df_hist['gleba'] = pd.to_numeric(df_hist['gleba'], errors='coerce')

            df_hist['tc_real'] = pd.to_numeric(df_hist['tc_real'], errors='coerce').fillna(0.0)

            

            df_acumulado = df_hist.groupby('gleba')['tc_real'].sum().reset_index()

            df_acumulado.columns = ['gleba', 'TC Total Gleba (Histórico)']

            return df_acumulado

            

        return pd.DataFrame(columns=['gleba', 'TC Total Gleba (Histórico)'])

    except Exception as erro:

        st.error(f"Erro ao calcular histórico das glebas: {erro}")

        return pd.DataFrame(columns=['gleba', 'TC Total Gleba (Histórico)'])



with st.spinner("Carregando dados da colheita..."):

    dados_banco = buscar_dados_cana(data_selecionada)



# 5. Processamento e Exibição Direta dos Dados
if not dados_banco:
    st.warning(f"Nenhum registro encontrado para o dia {data_selecionada.strftime('%d/%m/%Y')}.")
else:
    df_dia = pd.DataFrame(dados_banco)
    df_dia['gleba'] = pd.to_numeric(df_dia['gleba'], errors='coerce')
    colunas_num = ['tc_real', 'atr', 'mineral_pct', 'vegetal_pct']
    df_dia[colunas_num] = df_dia[colunas_num].apply(pd.to_numeric, errors='coerce').fillna(0.0)

    # Coleta o histórico cirúrgico das glebas do dia
    glebas_do_dia = df_dia['gleba'].dropna().unique().tolist()
    df_historico_glebas = buscar_historico_glebas_ativas(glebas_do_dia)

    # Filtro de Frentes na barra lateral
    lista_frentes = sorted(df_dia['frente'].unique().tolist())
    frentes_selecionadas = st.sidebar.multiselect("Selecione as Frentes:", options=lista_frentes, default=lista_frentes)
    
    df_filtrado = df_dia if not frentes_selecionadas else df_dia[df_dia['frente'].isin(frentes_selecionadas)]

    # Realiza o cruzamento exato com o histórico
    if not df_historico_glebas.empty:
        df_visualizacao = pd.merge(df_filtrado, df_historico_glebas, on='gleba', how='left')
    else:
        df_visualizacao = df_filtrado.copy()
        df_visualizacao['TC Total Gleba (Histórico)'] = 0.0
        
    df_visualizacao['TC Total Gleba (Histórico)'] = df_visualizacao['TC Total Gleba (Histórico)'].fillna(0.0)
    
    # Renomeia e ordena as colunas de exibição conforme solicitado
    df_visualizacao = df_visualizacao.rename(columns={
        'frente': 'Frente',
        'nome_fazenda': 'Fazenda',
        'gleba': 'Gleba',
        'tc_real': 'TC (Dia)',
        'TC Total Gleba (Histórico)': 'TC (Acumulado)',
        'atr': 'ATR',
        'mineral_pct': 'Imp. Mineral',
        'vegetal_pct': 'Imp. Vegetal'
    })
    
    ordem_colunas = [
        'Frente',
        'Fazenda',
        'Gleba',
        'TC (Dia)',
        'TC (Acumulado)',
        'ATR',
        'Imp. Mineral',
        'Imp. Vegetal'
    ]
    df_visualizacao = df_visualizacao[ordem_colunas].sort_values(by=['Frente', 'Fazenda', 'Gleba'])
    
    # Formata o ID da gleba para exibir limpo (como número inteiro em formato texto)
    df_visualizacao['Gleba'] = df_visualizacao['Gleba'].fillna(0).astype(int).astype(str)
    
    # ==============================
    # VISUAL BI - SOMENTE APRESENTAÇÃO (Movido para dentro do ELSE)
    # ==============================
    col1, col2, col3, col4 = st.columns(4)

    col1.metric(
        "🚜 TC Hoje",
        f"{df_visualizacao['TC (Dia)'].sum():,.2f}"
    )

    col4.metric(
        "📍 Glebas",
        df_visualizacao['Gleba'].nunique()
    )

    st.divider()

    st.markdown(
        f"### 📋 Entrada de Cana {data_selecionada.strftime('%d/%m/%Y')}"
    )

    # Nota: Atualizado de use_container_width para width conforme os warnings do log
    st.dataframe(
        df_visualizacao.style.format({
            'TC (Dia)': '{:,.2f}',
            'TC (Acumulado)': '{:,.2f}',
            'ATR': '{:.2f}',
            'Imp. Mineral': '{:.2f}',
            'Imp. Vegetal': '{:.2f}'
        }),
        width="stretch",
        hide_index=True,
        height=700
    )
