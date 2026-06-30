import streamlit as st

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

# ==============================
# SEÇÃO: OPERAÇÃO
# ==============================
st.subheader("OPERAÇÃO")
col1, col2 = st.columns(2)

with col1:
    try:
        st.page_link(
            "pages/1_Hora_Hora.py",
            label="📋 Hora/Hora Estimado/Realizado",
            use_container_width=True
        )
    except Exception:
        # Plano B caso o cache do servidor do Streamlit ainda não tenha atualizado a rota
        if st.button("📋 Acessar Hora/Hora (Forçar Entrada)", use_container_width=True):
            st.switch_page("pages/1_Hora_Hora.py")

with col2:
    try:
        st.page_link(
            "pages/2_Consulta_Glebas.py",
            label="🌱 Consulta por Gleba",
            use_container_width=True
        )
    except Exception:
        # Plano B caso o cache do servidor do Streamlit ainda não tenha atualizado a rota
        if st.button("🌱 Acessar Consulta por Gleba (Forçar Entrada)", use_container_width=True):
            st.switch_page("pages/2_Consulta_Glebas.py")

# ==============================
# SEÇÃO: INDICADORES
# ==============================
st.subheader("INDICADORES")
col3, col4 = st.columns(2)

with col3:
    st.button("📊 Produção", use_container_width=True)

with col4:
    st.button("📈 Eficiência", use_container_width=True)

# ==============================
# SEÇÃO: SISTEMA
# ==============================
st.subheader("SISTEMA")
st.button("🔄 Atualizar Dados Globais", use_container_width=True)
