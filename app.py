import streamlit as st
from pathlib import Path

st.set_page_config(
    page_title="COA - Controle Operacional Agrícola",
    page_icon="📋",
    layout="wide"
)

# Estilização CSS para os cards do menu principal
st.markdown("""
<style>
.card {
    border: 1px solid #444;
    padding: 25px;
    border-radius: 12px;
    text-align: center;
    background: #11141a;
}
.block-container { padding-top: 2rem; }
h2 { margin-top: 1.5rem !important; margin-bottom: 1rem !important; }
</style>
""", unsafe_allow_html=True)

st.title("🚜 Gestão COA")
st.caption("Controle Operacional Agrícola - Menu Principal")

# Descobre o caminho absoluto do diretório onde o app.py está rodando
BASE_DIR = Path(__file__).parent
HORA_HORA_PATH = str(BASE_DIR / "pages" / "1_Hora_Hora.py")
GLEBAS_PATH = str(BASE_DIR / "pages" / "2_Consulta_Glebas.py")

# ==============================
# SEÇÃO: OPERAÇÃO
# ==============================
st.subheader("OPERAÇÃO")
col1, col2 = st.columns(2)

with col1:
    try:
        st.page_link(
            HORA_HORA_PATH,
            label="📋 Hora/Hora Estimado/Realizado",
            use_container_width=True
        )
    except Exception:
        if st.button("📋 Acessar Hora/Hora (Forçar)", use_container_width=True):
            st.switch_page(HORA_HORA_PATH)

with col2:
    try:
        st.page_link(
            GLEBAS_PATH,
            label="🌱 Consulta por Gleba",
            use_container_width=True
        )
    except Exception:
        if st.button("🌱 Acessar Consulta por Gleba (Forçar)", use_container_width=True):
            st.switch_page(GLEBAS_PATH)

st.divider()

# ==============================
# SEÇÃO: SISTEMA
# ==============================
st.subheader("SISTEMA")
st.button("🔄 Atualizar Dados Globais", use_container_width=True)
