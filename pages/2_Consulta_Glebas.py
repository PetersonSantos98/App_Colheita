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

supabase = create_client(
    SUPABASE_URL,
    SUPABASE_KEY
)

# ======================================
# FUNÇÃO PARA CARREGAR DADOS (CACHE: 60s)
# ======================================

@st.cache_data(ttl=60)
def carregar_dados():
    # Coleta os registros trazendo as datas mais recentes primeiro 
    # Isso evita que os dados novos sumam devido ao limite de linhas do Supabase
    resposta = (
        supabase
        .table("APP COLHEITA")
        .select("*")
        .order("data_saida", desc=True)
        .execute()
    )

    df = pd.DataFrame(resposta.data)

    if not df.empty:
        # Formata a coluna de data de saída
        if "data_saida" in df.columns:
            df["data_saida"] = pd.to_datetime(
                df["data_saida"],
                errors="coerce"
            )
        
        # Faz a limpeza e garante o tipo inteiro puro para a coluna de glebas
        if "gleba" in df.columns:
            df["gleba"] = pd.to_numeric(df["gleba"], errors="coerce")
            df = df.dropna(subset=["gleba"])
            df["gleba"] = df["gleba"].astype(int)

    return df


# Executa a carga de dados
dados = carregar_dados()

if dados.empty:
    st.warning("Nenhum dado encontrado na tabela 'APP COLHEITA'.")
    st.stop()

# ======================================
# BARRA LATERAL - FILTROS
# ======================================

# Monta a lista única de glebas inteiras presentes no dataframe
lista_glebas = (
    dados["gleba"]
    .sort_values()
    .unique()
    .tolist()
)

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
    # Filtra as linhas com base nas glebas selecionadas na lista lateral
    resultado = dados[dados["gleba"].isin(glebas_sel)].copy()

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
        st.metric(
            "🌱 TC Acumulado Realizado",
            f"{tc_real:,.2f}"
        )

    with col2:
        st.metric(
            "📋 TC Estimado",
            f"{tc_estimado:,.2f}"
        )

    with col3:
        st.metric(
            "📈 % Concluído",
            f"{percentual:.1f}%"
        )

    st.divider()

    # Construção e agrupamento da tabela detalhada por Frente
    tabela = (
        resultado
        .groupby(
            ["gleba", "frente"],
            as_index=False
        )
        .agg(
            {
                "tc_real": "sum",
                "tc_estimado": "first"
            }
        )
        .sort_values(
            ["gleba", "frente"]
        )
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
    st.dataframe(
        tabela,
        use_container_width=True,
        hide_index=True
    )

else:
    # Mensagem informativa padrão enquanto nenhuma opção estiver ativa
    st.info("Selecione uma ou mais glebas na barra lateral para detalhar os dados.")
