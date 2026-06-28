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

# 2. Conexão otimizada com o Supabase
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

# 3. FILTROS NA BARRA LATERAL (Data e Frente)
st.sidebar.header("🔍 Filtros de Pesquisa")
data_selecionada = st.sidebar.date_input("Selecione a data:", date.today())

# 4. Busca cirúrgica no Supabase (Cache de 30 min)
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

# Função rápida para calcular a soma histórica total de toneladas direto no banco (Performance)
@st.cache_data(ttl=1800)
def buscar_tc_historico_total():
    try:
        # Traz apenas a coluna tc_real de toda a tabela para somar
        resposta = supabase.table("APP COLHEITA").select("tc_real").execute()
        if resposta and hasattr(resposta, "data") and resposta.data:
            df_total = pd.DataFrame(resposta.data)
            return pd.to_numeric(df_total['tc_real'], errors='coerce').sum()
        return 0.0
    except Exception as erro:
        st.error(f"Erro ao calcular TC Histórico: {erro}")
        return 0.0

with st.spinner("Carregando dados da colheita..."):
    dados_banco = buscar_dados_cana(data_selecionada)
    tc_historico_total = buscar_tc_historico_total()

# Auxiliar para formatação de moeda/número padrão brasileiro (1.234,56)
def formatar_peso(valor):
    return f"{valor:,.2f}".replace(",", "v").replace(".", ",").replace("v", ".")

# 5. Processamento leve dos dados
if not dados_banco:
    st.warning(f"Nenhum registro encontrado para o dia {data_selecionada.strftime('%d/%m/%Y')}.")
    
    # Mesmo sem dados no dia, exibe o acumulado histórico se houver
    if tc_historico_total > 0:
        st.subheader(f"📊 Acumulado Geral do Banco")
        st.metric("TC Total Histórico (Todas as Datas)", f"{formatar_peso(tc_historico_total)} t")
else:
    # Criando o DataFrame convertendo tipos de forma eficiente (otimização de memória)
    df_dia = pd.DataFrame(dados_banco)
    colunas_num = ['tc_real', 'atr', 'mineral_pct', 'vegetal_pct']
    df_dia[colunas_num] = df_dia[colunas_num].apply(pd.to_numeric, errors='coerce').fillna(0.0)

    # Filtro de Frentes em cascata (não gera nova requisição ao banco)
    lista_frentes = sorted(df_dia['frente'].unique().tolist())
    frentes_selecionadas = st.sidebar.multiselect("Selecione as Frentes:", options=lista_frentes, default=lista_frentes)
    
    df_filtrado = df_dia if not frentes_selecionadas else df_dia[df_dia['frente'].isin(frentes_selecionadas)]

    # --- CARD DE METRICAS (Sempre visível no topo) ---
    st.subheader(f"📊 Resumo Geral - {data_selecionada.strftime('%d/%m/%Y')}")
    col1, col2, col3, col4, col5 = st.columns(5)
    
    # TC Real (Soma estrita do Dia Selecionado)
    total_tc_real_dia = df_filtrado['tc_real'].sum()
    col1.metric("TC Real (No Dia)", f"{formatar_peso(total_tc_real_dia)} t")
    
    # TC Total (Soma de todos os registros do banco independente da data)
    col2.metric("TC Total Histórico", f"{formatar_peso(tc_historico_total)} t")
    
    col3.metric("Frentes Exibidas", df_filtrado['frente'].nunique())
    col4.metric("Fazendas", df_filtrado['nome_fazenda'].nunique())
    
    df_com_atr = df_filtrado[df_filtrado['atr'] > 0]
    media_atr = df_com_atr['atr'].mean() if not df_com_atr.empty else 0.0
    col5.metric("Média de ATR", f"{media_atr:.2f} kg/t")
    
    st.markdown("---")
    
    # --- DIVISÃO EM ABAS ---
    aba_grafico, aba_tabela, aba_detalhe = st.tabs([
        "📈 Gráfico por Frente", 
        "🧮 Consolidado por Frente", 
        "📋 Romaneios Detalhados"
    ])
    
    # Processamento do agrupamento por frente
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
        df_visualizacao = df_filtrado[['frente', 'nome_fazenda', 'gleba', 'tc_real', 'atr', 'mineral_pct', 'vegetal_pct']].sort_values(by='frente')
        df_visualizacao.columns = ['Frente', 'Fazenda', 'Gleba', 'TC Real', 'ATR', 'Imp. Mineral', 'Imp. Vegetal']
        st.dataframe(df_visualizacao, use_container_width=True, hide_index=True)
