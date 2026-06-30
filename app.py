import streamlit as st

st.set_page_config(
    page_title="COA - Controle Operacional Agrícola",
    page_icon="📋",
    layout="wide"
)

st.title("🚜 Gestão COA")
st.caption("Controle Operacional Agrícola - Menu Principal")

st.subheader("OPERAÇÃO")

col1, col2 = st.columns(2)

with col1:
    if st.button("📋 Hora/Hora Estimado/Realizado", use_container_width=True):
        st.switch_page("pages/1_Hora_Hora.py")

with col2:
    if st.button("🌱 Consulta por Gleba", use_container_width=True):
        st.switch_page("pages/2_Consulta_Glebas.py")

st.divider()

st.subheader("SISTEMA")

st.button("🔄 Atualizar Dados Globais", use_container_width=True)
