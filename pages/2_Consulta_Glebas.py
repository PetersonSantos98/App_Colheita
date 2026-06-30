import streamlit as st
import pandas as pd
from supabase import create_client

# ======================================
# CONFIGURAÇÃO DA PÁGINA
# ======================================

st.set_page_config(
    page_title="Consulta de Glebas",
    page_icon="🌱",
    layout="wide"
)

st.title("🌱 Consulta de Glebas")

# ======================================
# CONEXÃO COM O SUPABASE
# ======================================

SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# ======================================
# 1. QUERY ULTRA LEVE: APENAS LISTA DE GLEBAS
# ======================================

@st.cache_data(ttl=60)
def obter_lista_glebas():
    # Puxa apenas a coluna 'gleba' para montar o filtro lateral sem carregar peso
    resposta = (
        supabase
        .table("APP COLHEITA")
        .select("gleba")
        .execute()
    )
    df_fnd = pd.DataFrame(resposta.data)
    if not df_fnd.empty and "gleba" in df_fnd.columns:
        df_fnd["gleba"] = pd.to_numeric(df_fnd["gleba"], errors="coerce")
        return sorted(df_fnd["gleba"].dropna().unique().astype(int).tolist())
    return []

# ======================================
# 2. QUERY DINÂMICA: BUSCA APENAS O NECESSÁRIO
# ======================================

def carregar_dados_filtrados(glebas_selecionadas):
    # Transforma a lista de inteiros em string para a API do Supabase
    lista_busca = [str(g) for g in glebas_selecionadas]
    
    # O banco faz o trabalho duro! Filtra usando o operador .in_
    resposta = (
        supabase
        .table("APP COLHEITA")
        .select("*")
        .in_("gleba", lista_busca)
        .order("data_saida", desc=True)
        .execute()
    )
    
    df = pd.DataFrame(resposta.data)
    
    if not df.empty:
        if "data_saida" in df.columns:
            df["data_saida"] = pd.to_datetime(df["data_saida"], errors="coerce")
        if "gleba" in df.columns:
            df["gleba"] = pd.to_numeric(df["gleba"], errors="coerce").astype(int)
            
    return df

# ======================================
# BARRA LATERAL - FILTROS
# ======================================

lista_glebas = obter_lista_glebas()

st.sidebar.header("🔎 Pesquisa")

glebas_sel = st.sidebar.multiselect(
    "Pesquise e selecione uma ou mais glebas",
    options=lista_glebas,
    placeholder="Digite a gleba..."
)

# ======================================
# PAINEL PRINCIPAL - CONSULTA
# ======================================

if glebas_sel:
    # Busca no banco apenas as linhas das glebas selecionadas (Sem limite de 1000 que quebre o histórico!)
    resultado = carregar_dados_filtrados(glebas_sel)

    if not resultado.empty:
        # Cálculo dos totais reais realizados
        tc_real = resultado["tc_real"].sum()

        # Agrupa por gleba e pega apenas o primeiro valor estimado para não inflar a meta
        tc_estimado = (
            resultado
            .groupby("gleba")["tc_estimado"]
            .first()
            .sum()
        )

        # Cálculo da porcentagem de conclusão de forma segura
        percentual = (
            (tc_real / tc_estimado) * 100
            if tc_estimado > 0 else 0
        )

        # Exibição dos Blocos de KPI (Métricas)
        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric("🌱 TC Acumulado Realizado", f"{tc_real:,.2f}")

        with col2:
            st.metric("📋 TC Estimado", f"{tc_estimado:,.2f}")

        with col3:
            st.metric("📈 % Concluído", f"{percentual:.1f}%")

        st.divider()

        # Construção e agrupamento da tabela detalhada por Frente
        tabela = (
            resultado
            .groupby(["gleba", "frente"], as_index=False)
            .agg({"tc_real": "sum", "tc_estimado": "first"})
            .sort_values(["gleba", "frente"])
        )

        # Renomeação visual das colunas do DataFrame
        tabela = tabela.rename(
            columns={
                "gleba": "Gleba",
                "frente": "Frente",
                "tc_real": "TC Real",
                "tc_estimado": "TC Estimado"
            }
        )

        # Exibição da tabela final formatada
        st.dataframe(tabela, use_container_width=True, hide_index=True)
    else:
        st.warning("Nenhum dado detalhado encontrado para as glebas selecionadas.")

else:
    st.info("Selecione uma ou mais glebas na barra lateral para detalhar os dados.")
