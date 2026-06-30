import streamlit as st

st.set_page_config(
    page_title="COA - Consulta Glebas",
    page_icon="🌱",
    layout="wide"
)

st.title("🌱 Consulta por Glebas")

# Filtros específicos de Glebas na barra lateral
with st.sidebar:
    st.header("🔍 Busca por Localização")
    cod_gleba = st.text_input("Digite o código da Gleba:")
    filtro_fazenda = st.text_input("Filtrar por Fazenda:")

st.info("Insira a lógica de consulta histórica detalhada de Glebas e Fazendas aqui.")
