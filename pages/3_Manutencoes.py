import streamlit as st
import pandas as pd

from datetime import datetime
from zoneinfo import ZoneInfo
from supabase import create_client


# ============================================================
# CONFIGURAÇÕES
# ============================================================

st.set_page_config(
    page_title="COA - Manutenções",
    page_icon="🔧",
    layout="wide"
)

FUSO_BR = ZoneInfo("America/Sao_Paulo")


# ============================================================
# TÍTULO
# ============================================================

st.title("🔧 Controle de Manutenções")

st.caption(
    "Equipamentos atualmente registrados em manutenção no IFROTA"
)


# ============================================================
# SUPABASE
# ============================================================

SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]


@st.cache_resource
def conectar_supabase():

    return create_client(
        SUPABASE_URL,
        SUPABASE_KEY
    )


supabase = conectar_supabase()


# ============================================================
# ATUALIZAÇÃO MANUAL
# ============================================================

if st.sidebar.button(
    "🔄 Atualizar Agora",
    use_container_width=True
):

    st.cache_data.clear()
    st.rerun()


# ============================================================
# BUSCAR MANUTENÇÕES
# ============================================================

@st.cache_data(ttl=60)
def buscar_manutencoes():

    registros = []

    inicio = 0
    limite = 1000

    while True:

        resposta = (
            supabase
            .table("manutencoes_ifrota")
            .select(
                "chave,"
                "tipo_equipamento,"
                "base,"
                "classe,"
                "frente,"
                "local,"
                "frota,"
                "gleba,"
                "inicio,"
                "motivo,"
                "atualizado_em"
            )
            .range(
                inicio,
                inicio + limite - 1
            )
            .execute()
        )

        dados = resposta.data

        if not dados:
            break

        registros.extend(dados)

        if len(dados) < limite:
            break

        inicio += limite

    return registros


# ============================================================
# CARREGAMENTO
# ============================================================

with st.spinner(
    "Carregando manutenções..."
):

    try:

        registros = buscar_manutencoes()

    except Exception as erro:

        st.error(
            f"Erro ao consultar as manutenções: {erro}"
        )

        st.stop()


if not registros:

    st.warning(
        "Nenhuma manutenção encontrada."
    )

    st.stop()


df = pd.DataFrame(registros)


# ============================================================
# TRATAMENTO
# ============================================================

for coluna in [
    "frente",
    "local",
    "frota",
    "gleba",
    "motivo",
    "tipo_equipamento"
]:

    if coluna in df.columns:

        df[coluna] = (
            df[coluna]
            .fillna("")
            .astype(str)
            .str.strip()
        )


# ============================================================
# CORRIGIR FROTA / GLEBA
# ============================================================

def remover_decimal(valor):

    if valor is None:
        return ""

    texto = str(valor).strip()

    if texto.endswith(".0"):

        texto = texto[:-2]

    return texto


df["frota"] = df["frota"].apply(
    remover_decimal
)

df["gleba"] = df["gleba"].apply(
    remover_decimal
)


# ============================================================
# DATA DE INÍCIO
# ============================================================

df["inicio"] = pd.to_datetime(
    df["inicio"],
    errors="coerce",
    utc=True
)

df["inicio"] = (
    df["inicio"]
    .dt.tz_convert(FUSO_BR)
)


# ============================================================
# DURAÇÃO
# ============================================================

agora = pd.Timestamp.now(
    tz=FUSO_BR
)


df["duracao_timedelta"] = (
    agora - df["inicio"]
)


# ============================================================
# FORMATAR DURAÇÃO
# ============================================================

def formatar_duracao(valor):

    if pd.isna(valor):

        return ""

    segundos = int(
        valor.total_seconds()
    )

    if segundos < 0:

        return "00:00:00"

    dias = segundos // 86400

    horas = (
        segundos % 86400
    ) // 3600

    minutos = (
        segundos % 3600
    ) // 60

    segundos_restantes = (
        segundos % 60
    )

    # Mantém horas acumuladas,
    # igual ao Excel [h]:mm:ss

    horas_totais = (
        dias * 24
    ) + horas

    return (
        f"{horas_totais:02d}:"
        f"{minutos:02d}:"
        f"{segundos_restantes:02d}"
    )


df["duracao"] = (
    df["duracao_timedelta"]
    .apply(formatar_duracao)
)


# ============================================================
# SIDEBAR
# ============================================================

st.sidebar.header(
    "🔍 Filtros de Manutenção"
)


# ============================================================
# TIPO DE EQUIPAMENTO
# ============================================================

tipos = sorted(
    [
        x
        for x in df[
            "tipo_equipamento"
        ].unique()
        if x
    ]
)


tipos_selecionados = (
    st.sidebar.multiselect(
        "Tipo de equipamento:",
        options=tipos,
        default=tipos
    )
)


# ============================================================
# FRENTE
# ============================================================

frentes = sorted(
    [
        x
        for x in df[
            "frente"
        ].unique()
        if x
    ]
)


frentes_selecionadas = (
    st.sidebar.multiselect(
        "Frente:",
        options=frentes,
        default=frentes
    )
)


# ============================================================
# LOCAL
# ============================================================

locais = sorted(
    [
        x
        for x in df[
            "local"
        ].unique()
        if x
    ]
)


locais_selecionados = (
    st.sidebar.multiselect(
        "Local:",
        options=locais
    )
)


# ============================================================
# PESQUISA POR FROTA
# ============================================================

pesquisa_frota = (
    st.sidebar.text_input(
        "🔎 Pesquisar Frota:"
    )
    .strip()
)


# ============================================================
# APLICAR FILTROS
# ============================================================

df_filtrado = df.copy()


if tipos_selecionados:

    df_filtrado = (
        df_filtrado[
            df_filtrado[
                "tipo_equipamento"
            ].isin(
                tipos_selecionados
            )
        ]
    )


if frentes_selecionadas:

    df_filtrado = (
        df_filtrado[
            df_filtrado[
                "frente"
            ].isin(
                frentes_selecionadas
            )
        ]
    )


if locais_selecionados:

    df_filtrado = (
        df_filtrado[
            df_filtrado[
                "local"
            ].isin(
                locais_selecionados
            )
        ]
    )


if pesquisa_frota:

    df_filtrado = (
        df_filtrado[
            df_filtrado[
                "frota"
            ].str.contains(
                pesquisa_frota,
                case=False,
                na=False
            )
        ]
    )


# ============================================================
# INDICADORES
# ============================================================

total = len(
    df_filtrado
)


total_geral = len(
    df_filtrado[
        df_filtrado[
            "tipo_equipamento"
        ] == "GERAL"
    ]
)


total_tratores = len(
    df_filtrado[
        df_filtrado[
            "tipo_equipamento"
        ] == "TRATOR"
    ]
)


total_maquinas = len(
    df_filtrado[
        df_filtrado[
            "tipo_equipamento"
        ] == "MAQUINA"
    ]
)


total_caixas = len(
    df_filtrado[
        df_filtrado[
            "tipo_equipamento"
        ] == "CAIXA"
    ]
)


col1, col2, col3, col4, col5 = (
    st.columns(5)
)


col1.metric(
    "🔧 Total",
    total
)

col2.metric(
    "🛠️ Geral",
    total_geral
)

col3.metric(
    "🚜 Tratores",
    total_tratores
)

col4.metric(
    "🚜 Máquinas",
    total_maquinas
)

col5.metric(
    "📦 Caixas",
    total_caixas
)


st.divider()


# ============================================================
# ABAS
# ============================================================

aba_frentes, aba_tabela = st.tabs(
    [
        "🔧 Manutenções por Frente",
        "📋 Todas as Manutenções"
    ]
)


# ============================================================
# ABA 1 - POR FRENTE
# ============================================================

with aba_frentes:

    if df_filtrado.empty:

        st.info(
            "Nenhuma manutenção encontrada "
            "com os filtros selecionados."
        )

    else:

        lista_frentes = sorted(
            df_filtrado[
                "frente"
            ]
            .fillna("")
            .unique()
        )

        for frente in lista_frentes:

            if frente == "":

                nome_frente = (
                    "SEM FRENTE"
                )

            else:

                nome_frente = frente


            df_frente = (
                df_filtrado[
                    df_filtrado[
                        "frente"
                    ] == frente
                ]
                .copy()
            )


            st.markdown(
                f"### 🚜 {nome_frente}"
            )


            tabela = (
                df_frente[
                    [
                        "frota",
                        "motivo",
                        "inicio",
                        "gleba",
                        "local",
                        "tipo_equipamento",
                        "duracao"
                    ]
                ]
                .copy()
            )


            tabela["inicio"] = (
                tabela["inicio"]
                .dt.strftime(
                    "%d/%m/%Y %H:%M"
                )
            )


            tabela = tabela.rename(
                columns={
                    "frota": "FROTA",
                    "motivo": "MOTIVO",
                    "inicio": "INÍCIO",
                    "gleba": "GLEBA",
                    "local": "LOCAL",
                    "tipo_equipamento": "TIPO",
                    "duracao": "DURAÇÃO"
                }
            )


            tabela = tabela.sort_values(
                by="DURAÇÃO",
                ascending=False
            )


            st.dataframe(
                tabela,
                width="stretch",
                hide_index=True
            )


            st.write("")


# ============================================================
# ABA 2 - TODAS
# ============================================================

with aba_tabela:

    tabela_completa = (
        df_filtrado[
            [
                "tipo_equipamento",
                "frente",
                "frota",
                "motivo",
                "inicio",
                "gleba",
                "local",
                "duracao"
            ]
        ]
        .copy()
    )


    tabela_completa[
        "inicio"
    ] = (
        tabela_completa[
            "inicio"
        ]
        .dt.strftime(
            "%d/%m/%Y %H:%M"
        )
    )


    tabela_completa = (
        tabela_completa.rename(
            columns={
                "tipo_equipamento":
                    "TIPO",

                "frente":
                    "FRENTE",

                "frota":
                    "FROTA",

                "motivo":
                    "MOTIVO",

                "inicio":
                    "INÍCIO",

                "gleba":
                    "GLEBA",

                "local":
                    "LOCAL",

                "duracao":
                    "DURAÇÃO"
            }
        )
    )


    tabela_completa = (
        tabela_completa.sort_values(
            by=[
                "FRENTE",
                "FROTA"
            ]
        )
    )


    st.dataframe(
        tabela_completa,
        width="stretch",
        hide_index=True,
        height=700
    )


# ============================================================
# RODAPÉ
# ============================================================

st.caption(
    "Última atualização da tela: "
    + datetime.now(
        FUSO_BR
    ).strftime(
        "%d/%m/%Y %H:%M:%S"
    )
)
