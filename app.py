import streamlit as st
import pandas as pd
from datetime import date
from supabase import create_client, Client

# 1. Configuração da página do Streamlit
st.set_page_config(page_title="Relatório COA - Entrada de Cana", layout="wide")
st.title("🚜 Relatório Diário de Entrada de Cana (COA)")

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

# SOLUÇÃO DEFINITIVA: Busca o acumulado somado filtrando apenas pelas glebas que estão ativas no dia
@st.cache_data(ttl=1800)
def buscar_historico_glebas_ativas(lista_glebas):
    if not lista_glebas:
        return pd.DataFrame(columns=['gleba', 'TC Total Gleba (Histórico)'])
    try:
        # Convertemos para inteiros para garantir compatibilidade com o banco int8
        lista_glebas_int = [int(g) for g in lista_glebas if pd.notna(g)]
        
        # Consultas específicas para as glebas do dia eliminam o problema do limite de linhas do Supabase
        resposta = supabase.table("APP COLHEITA").select("gleba, tc_real").in_("gleba", lista_glebas_int).execute()
        
        if resposta and hasattr(resposta, "data") and resposta.data:
            df_hist = pd.DataFrame(resposta.data)
            df_hist['gleba'] = pd.to_numeric(df_hist['gleba'], errors='coerce')
            df_hist['tc_real'] = pd.to_numeric(df_hist['tc_real'], errors='coerce').fillna(0.0)
            
            # Consolida e soma o histórico total real de cada uma
            df_acumulado = df_hist.groupby('gleba')['tc_real'].sum().reset_index()
            df_acumulado.columns = ['gleba', 'TC Total Gleba (Histórico)']
            return df_acumulado
            
        return pd.DataFrame(columns=['gleba', 'TC Total Gleba (Histórico)'])
    except Exception as erro:
        st.error(f"Erro ao calcular histórico das glebas: {erro}")
        return pd.DataFrame(columns=['gleba', 'TC Total Gleba (Histórico)'])

with st.spinner("Carregando dados da colheita..."):
    dados_banco = buscar_dados_cana(data_selecionada)

# Auxiliar para formatação padrão brasileiro (1.234,56)
def formatar_peso(valor):
    return f"{valor:,.2f}".replace(",", "v").replace(".", ",").replace("v", ".")

# 5. Processamento dos dados
if not dados_banco:
    st.warning(f"Nenhum registro encontrado para o dia {data_selecionada.strftime('%d/%m/%Y')}.")
else:
    df_dia = pd.DataFrame(dados_banco)
    df_dia['gleba'] = pd.to_numeric(df_dia['gleba'], errors='coerce')
    colunas_num = ['tc_real', 'atr', 'mineral_pct', 'vegetal_pct']
    df_dia[colunas_num] = df_dia[colunas_num].apply(pd.to_numeric, errors='coerce').fillna(0.0)

    # Coleta a lista de glebas que apareceram hoje para buscar o histórico direcionado delas
    glebas_do_dia = df_dia['gleba'].dropna().unique().tolist()
    df_historico_glebas = buscar_historico_glebas_ativas(glebas_do_dia)

    # Filtro de Frentes em cascata
    lista_frentes = sorted(df_dia['frente'].unique().tolist())
    frentes_selecionadas = st.sidebar.multiselect("Selecione as Frentes:", options=lista_frentes, default=lista_frentes)
    
    df_filtrado = df_dia if not frentes_selecionadas else df_dia[df_dia['frente'].isin(frentes_selecionadas)]

    # --- CARD DE METRICAS ---
    st.subheader(f"📊 Resumo Geral - {data_selecionada.strftime('%d/%m/%Y')}")
    col1, col2, col3, col4 = st.columns(4)
    
    total_tc_real_dia = df_filtrado['tc_real'].sum()
    col1.metric("Total Realizado (Dia)", f"{formatar_peso(total_tc_real_dia)} t")
    col2.metric("Frentes Exibidas", df_filtrado['frente'].nunique())
    col3.metric("Fazendas", df_filtrado['nome_fazenda'].nunique())
    
    df_com_atr = df_filtrado[df_filtrado['atr'] > 0]
    media_atr = df_com_atr['atr'].mean() if not df_com_atr.empty else 0.0
    col4.metric("Média de ATR", f"{media_atr:.2f} kg/t")
    
    st.markdown("---")
    
    # --- DIVISÃO EM ABAS ---
    aba_grafico, aba_tabela, aba_detalhe = st.tabs([
        "📈 Gráfico por Frente", 
        "🧮 Consolidado por Frente", 
        "📋 Romaneios Detalhados"
    ])
    
    # Agrupamento por frente
    df_frentes = df_filtrado.groupby('frente').agg(
        total_tc=('tc_real', 'sum'),
        media_atr=('atr', lambda x: x[x > 0].mean() if any(x > 0) else 0.0),
        impureza_mineral=('mineral_pct', 'mean'),
        impureza_vegetal=('vegetal_pct', 'mean'),
        qtd_viagens=('tc_real', 'count')
    ).reset_index()
    df_frentes.columns = ['Frente', 'Total Real (TC)', 'Média ATR', 'Imp. Mineral (%)', 'Imp. Vegetal (%)', 'Qtd Viagens']

    with aba_grafico:
        if not df_frentes.empty:
            st.bar_chart(data=df_frentes, x='Frente', y='Total Real (TC)', color="#2E7D32")
        else:
            st.info("Sem dados para exibir o gráfico.")

    with aba_tabela:
        st.dataframe(df_frentes.style.format({
            'Total Real (TC)': '{:,.2f}', 'Média ATR': '{:.2f}',
            'Imp. Mineral (%)': '{:.2f}%', 'Imp. Vegetal (%)': '{:.2f}%', 'Qtd Viagens': '{:,.0f}'
        }), use_container_width=True, hide_index=True)

    with aba_detalhe:
        df_visualizacao = df_filtrado.copy()
        
        # Realiza o cruzamento exato com o histórico focado nas glebas do dia
        if not df_historico_glebas.empty:
            df_visualizacao = pd.merge(df_visualizacao, df_historico_glebas, on='gleba', how='left')
        else:
            df_visualizacao['TC Total Gleba (Histórico)'] = 0.0
            
        df_visualizacao['TC Total Gleba (Histórico)'] = df_visualizacao['TC Total Gleba (Histórico)'].fillna(0.0)
        
        # Renomeia e ordena as colunas de exibição
        df_visualizacao = df_visualizacao.rename(columns={
            'frente': 'Frente', 'nome_fazenda': 'Fazenda', 'gleba': 'Gleba',
            'tc_real': 'TC Real (Dia)', 'atr': 'ATR', 'mineral_pct': 'Imp. Mineral', 'vegetal_pct': 'Imp. Vegetal'
        })
        
        ordem_colunas = ['Frente', 'Fazenda', 'Gleba', 'TC Real (Dia)', 'TC Total Gleba (Histórico)', 'ATR', 'Imp. Mineral', 'Imp. Vegetal']
        df_visualizacao = df_visualizacao[ordem_colunas].sort_values(by='Frente')
        
        # Formata o ID da gleba para exibir sem casas decimais (.0)
        df_visualizacao['Gleba'] = df_visualizacao['Gleba'].fillna(0).astype(int).astype(str)
        
        # Formatação final exibindo tudo perfeitamente com separadores de milhares
        st.dataframe(df_visualizacao.style.format({
            'TC Real (Dia)': '{:,.2f}',
            'TC Total Gleba (Histórico)': '{:,.2f}',
            'ATR': '{:.2f}',
            'Imp. Mineral': '{:.2f}',
            'Imp. Vegetal': '{:.2f}'
        }), use_container_width=True, hide_index=True)
