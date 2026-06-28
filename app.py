import streamlit as st
import pandas as pd
from datetime import date
from supabase import create_client, Client

# 1. Configuração da página do Streamlit
st.set_page_config(page_title="Estimado/Realizado - Hora/Hora", layout="wide")
st.title("📋 Estimado/Realizado - Hora/Hora")

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

# Exibe a data de atualização baseada na data selecionada no topo do relatório
st.markdown(f"#### Entrada de Cana: {data_selecionada.strftime('%d/%m/%Y')}")

# 4. Busca dos dados do dia selecionado (Cache de 30 min)
@st.cache_data(ttl=1800)
def buscar_dados_cana(data_filtro):
    data_str = data_filtro.strftime("%Y-%m-%d")
    try:
        resposta = supabase.table("APP COLHEITA").select("frente, nome_fazenda, gleba, atr, mineral_pct, vegetal_pct, tc_real, tc_estimado").eq("data_saida", data_str).execute()
        if resposta and hasattr(resposta, "data"):
            return resposta.data
        return []
    except Exception as erro:
        st.error(f"Erro na consulta do Supabase (Dados do Dia): {erro}")
        return []

# Busca o acumulado somado e o estimado fixo por gleba ativa
@st.cache_data(ttl=1800)
def buscar_historico_e_estimado_glebas(lista_glebas):
    if not lista_glebas:
        return pd.DataFrame(columns=['gleba', 'TC Total Gleba (Histórico)', 'TC Estimado Fixo'])
    try:
        lista_glebas_int = [int(g) for g in lista_glebas if pd.notna(g)]
        resposta = supabase.table("APP COLHEITA").select("gleba, tc_real, tc_estimado").in_("gleba", lista_glebas_int).execute()
        
        if resposta and hasattr(resposta, "data") and resposta.data:
            df_hist = pd.DataFrame(resposta.data)
            df_hist['gleba'] = pd.to_numeric(df_hist['gleba'], errors='coerce')
            df_hist['tc_real'] = pd.to_numeric(df_hist['tc_real'], errors='coerce').fillna(0.0)
            df_hist['tc_estimado'] = pd.to_numeric(df_hist['tc_estimado'], errors='coerce').fillna(0.0)
            
            # Histórico: Soma de todas as linhas daquela gleba no banco
            df_soma_historico = df_hist.groupby('gleba')['tc_real'].sum().reset_index()
            df_soma_historico.columns = ['gleba', 'TC Total Gleba (Histórico)']
            
            # Estimado Fixo: Evita duplicar ou multiplicar se a gleba aparecer mais de uma vez
            df_fixo_estimado = df_hist.groupby('gleba')['tc_estimado'].max().reset_index()
            df_fixo_estimado.columns = ['gleba', 'TC Estimado Fixo']
            
            # Junta os indicadores consolidados da gleba
            df_consolidado_gleba = pd.merge(df_soma_historico, df_fixo_estimado, on='gleba', how='left')
            return df_consolidado_gleba
            
        return pd.DataFrame(columns=['gleba', 'TC Total Gleba (Histórico)', 'TC Estimado Fixo'])
    except Exception as erro:
        st.error(f"Erro ao calcular parâmetros das glebas: {erro}")
        return pd.DataFrame(columns=['gleba', 'TC Total Gleba (Histórico)', 'TC Estimado Fixo'])

with st.spinner("Carregando dados da colheita..."):
    dados_banco = buscar_dados_cana(data_selecionada)

# 5. Processamento e Exibição Direta dos Dados
if not dados_banco:
    st.warning(f"Nenhum registro encontrado para o dia {data_selecionada.strftime('%d/%m/%Y')}.")
else:
    df_dia = pd.DataFrame(dados_banco)
    df_dia['gleba'] = pd.to_numeric(df_dia['gleba'], errors='coerce')
    colunas_num = ['tc_real', 'atr', 'mineral_pct', 'vegetal_pct', 'tc_estimado']
    df_dia[colunas_num] = df_dia[colunas_num].apply(pd.to_numeric, errors='coerce').fillna(0.0)

    # Coleta a lista de glebas únicas do dia atual
    glebas_do_dia = df_dia['gleba'].dropna().unique().tolist()
    df_parametros_glebas = buscar_historico_e_estimado_glebas(glebas_do_dia)

    # Filtro dinâmico de frentes na barra lateral
    lista_frentes = sorted(df_dia['frente'].unique().tolist())
    frentes_selecionadas = st.sidebar.multiselect("Selecione as Frentes:", options=lista_frentes, default=lista_frentes)
    
    df_filtrado = df_dia if not frentes_selecionadas else df_dia[df_dia['frente'].isin(frentes_selecionadas)]

    # Realiza o cruzamento exato trazendo o Histórico e o Estimado único da Gleba
    if not df_parametros_glebas.empty:
        # Removemos a coluna bruta temporária antes do merge para herdar o valor tratado e fixado por gleba
        df_filtrado_base = df_filtrado.drop(columns=['tc_estimado'], errors='ignore')
        df_visualizacao = pd.merge(df_filtrado_base, df_parametros_glebas, on='gleba', how='left')
    else:
        df_visualizacao = df_filtrado.copy()
        df_visualizacao['TC Total Gleba (Histórico)'] = 0.0
        df_visualizacao['TC Estimado Fixo'] = 0.0
        
    df_visualizacao['TC Total Gleba (Histórico)'] = df_visualizacao['TC Total Gleba (Histórico)'].fillna(0.0)
    df_visualizacao['TC Estimado Fixo'] = df_visualizacao['TC Estimado Fixo'].fillna(0.0)
    
    # Renomeia os cabeçalhos para o padrão do relatório visual
    df_visualizacao = df_visualizacao.rename(columns={
        'frente': 'Frente', 'nome_fazenda': 'Fazenda', 'gleba': 'Gleba',
        'TC Estimado Fixo': 'TC Estimado', 'tc_real': 'TC Real (Dia)', 
        'atr': 'ATR', 'mineral_pct': 'Imp. Mineral', 'vegetal_pct': 'Imp. Vegetal'
    })
    
    # Ordem de colunas idêntica à imagem solicitada
    ordem_colunas = ['Frente', 'Fazenda', 'Gleba', 'TC Estimado', 'TC Real (Dia)', 'TC Total Gleba (Histórico)', 'ATR', 'Imp. Mineral', 'Imp. Vegetal']
    df_visualizacao = df_visualizacao[ordem_colunas].sort_values(by=['Frente', 'Fazenda', 'Gleba'])
    
    # Formata o código da gleba como string inteira limpa
    df_visualizacao['Gleba'] = df_visualizacao['Gleba'].fillna(0).astype(int).astype(str)
    
    # Renderiza a tabela limpa ocupando o container completo da página
    st.dataframe(df_visualizacao.style.format({
        'TC Estimado': '{:,.2f}',
        'TC Real (Dia)': '{:,.2f}',
        'TC Total Gleba (Histórico)': '{:,.2f}',
        'ATR': '{:.2f}',
        'Imp. Mineral': '{:.2f}',
        'Imp. Vegetal': '{:.2f}'
    }), use_container_width=True, hide_index=True)
