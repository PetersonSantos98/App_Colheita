# ==============================
# DASHBOARD VISUAL COA
# ==============================

from datetime import datetime


# KPIs
col1, col2, col3, col4 = st.columns(4)


total_tc_dia = df_visualizacao['TC Real (Dia)'].sum()
total_hist = df_visualizacao['TC Total Gleba (Histórico)'].sum()
atr_medio = df_visualizacao['ATR'].mean()
qtde_glebas = df_visualizacao['Gleba'].nunique()


with col1:
    st.metric(
        "🚜 TC Real Hoje",
        f"{total_tc_dia:,.2f}"
    )

with col2:
    st.metric(
        "🌱 TC Histórico",
        f"{total_hist:,.2f}"
    )

with col3:
    st.metric(
        "🧪 ATR Médio",
        f"{atr_medio:.2f}"
    )

with col4:
    st.metric(
        "📍 Glebas",
        qtde_glebas
    )


st.divider()


hora_atual = datetime.now().strftime("%H:%M:%S")


st.markdown(
    f"""
    <h2 style='text-align:center;'>
    📋 Entrada de Cana - {data_selecionada.strftime('%d/%m/%Y')}
    </h2>
    
    <p style='text-align:center;color:#888'>
    Última atualização: {hora_atual}
    </p>
    """,
    unsafe_allow_html=True
)



# Tabela estilo BI

st.dataframe(

    df_visualizacao.style

    .format({

        'TC Real (Dia)': '{:,.2f}',

        'TC Total Gleba (Histórico)': '{:,.2f}',

        'ATR': '{:.2f}',

        'Imp. Mineral': '{:.2f}',

        'Imp. Vegetal': '{:.2f}'

    })

    .set_properties(
        **{
            'font-size':'13px',
            'text-align':'center'
        }
    ),

    use_container_width=True,

    hide_index=True,

    height=650

)
