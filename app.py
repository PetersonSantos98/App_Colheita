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
# PÁGINAS
# ==============================

paginas = {

    "OPERAÇÃO": [
        st.Page(
            "pages/1_Hora_Hora.py",
            title="📋 Hora/Hora Estimado/Realizado"
        ),

        st.Page(
            "pages/2_Consulta_Glebas.py",
            title="🌱 Consulta por Gleba"
        ),

        st.Page(
            "pages/3_Manutencoes.py",
            title="🔧 Manutenções"
        )
    ]

}


# ==============================
# NAVEGAÇÃO
# ==============================

pg = st.navigation(paginas)


# ==============================
# MENU PRINCIPAL
# ==============================

if pg:

    pg.run()

else:

    st.title("🚜 Gestão COA")

    st.caption(
        "Controle Operacional Agrícola - Menu Principal"
    )

    st.subheader("OPERAÇÃO")

    col1, col2, col3 = st.columns(3)

    with col1:

        st.info(
            "📋 Hora/Hora Estimado/Realizado\n\n"
            "Use o menu lateral para acessar."
        )

    with col2:

        st.info(
            "🌱 Consulta por Gleba\n\n"
            "Use o menu lateral para acessar."
        )

    with col3:

        st.info(
            "🔧 Manutenções\n\n"
            "Use o menu lateral para acessar."
        )
