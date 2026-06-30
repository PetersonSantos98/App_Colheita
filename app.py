import streamlit as st


# ==============================
# CONFIGURAÇÃO
# ==============================

st.set_page_config(
    page_title="COA - Controle Operacional Agrícola",
    page_icon="📋",
    layout="wide"
)


# ==============================
# ESTILO
# ==============================

st.markdown("""
<style>

.card {
    border: 1px solid #444;
    padding: 25px;
    border-radius: 12px;
    text-align: center;
    background: #11141a;
}

.block-container {
    padding-top: 2rem;
}

h2 {
    margin-top: 1.5rem !important;
    margin-bottom: 1rem !important;
}

</style>
""", unsafe_allow_html=True)


# ==============================
# MENU PRINCIPAL
# ==============================

st.title("🚜 Gestão COA")

st.caption(
    "Controle Operacional Agrícola - Menu Principal"
)


# ==============================
# OPERAÇÃO
# ==============================

st.subheader("OPERAÇÃO")


col1, col2 = st.columns(2)


with col1:

    st.page_link(
        "pages/1_Hora_Hora.py",
        label="📋 Hora/Hora Estimado/Realizado",
        icon="📋"
    )


with col2:

    st.page_link(
        "pages/2_Consulta_Glebas.py",
        label="🌱 Consulta por Gleba",
        icon="🌱"
    )


# ==============================
# SISTEMA
# ==============================

st.divider()

st.subheader("SISTEMA")


if st.button(
    "🔄 Atualizar Dados Globais",
    use_container_width=True
):

    st.cache_data.clear()

    st.success(
        "Cache atualizado com sucesso!"
    )
