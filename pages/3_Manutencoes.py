import streamlit as st
import pandas as pd

from datetime import datetime
from zoneinfo import ZoneInfo
from supabase import create_client


# ============================================================
# CONFIGURAÇÃO DA PÁGINA
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

st.title("🔧 Manutenções - Colheita")

st.caption(
    "Equipamentos atualmente em manutenção no IFROTA"
)


# ============================================================
# CONEXÃO SUPABASE
# ============================================================

SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]


@st.cache_resource
def conectar_supabase():

    return create_client(
        SUPABASE_URL,
        SUPABASE_KEY
    )


try:

    supabase = conectar_supabase()

except Exception as erro:

    st.error(
        f"Erro ao conectar ao Supabase: {erro}"
    )

    st.stop()


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
            .eq(
                "base",
                2026
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

        registros.extend(
            dados
        )

        if len(dados) < limite:
            break

        inicio += limite

    return registros


# ============================================================
# CARREGAR DADOS
# ============================================================

try:

    with st.spinner(
        "Carregando manutenções..."
    ):

        registros = buscar_manutencoes()

except Exception as erro:

    st.error(
        f"Erro ao consultar Supabase: {erro}"
    )

    st.stop()


# ============================================================
# VERIFICAR SE EXISTEM REGISTROS
# ============================================================

if not registros:

    st.warning(
        "Nenhuma manutenção da colheita encontrada."
    )

    st.stop()


# ============================================================
# DATAFRAME
# ============================================================

df = pd.DataFrame(
    registros
)


# ============================================================
# TRATAR CAMPOS DE TEXTO
# ============================================================

colunas_texto = [
    "tipo_equipamento",
    "frente",
    "local",
    "frota",
    "gleba",
    "motivo"
]


for coluna in colunas_texto:

    if coluna in df.columns:

        df[coluna] = (
            df[coluna]
            .fillna("")
            .astype(str)
            .str.strip()
        )


# ============================================================
# REMOVER .0 DE FROTA E GLEBA
# ============================================================

def remover_ponto_zero(valor):

    if valor is None:
        return ""

    texto = str(valor).strip()

    if texto.endswith(".0"):
        return texto[:-2]

    return texto


df["frota"] = (
    df["frota"]
    .apply(remover_ponto_zero)
)


df["gleba"] = (
    df["gleba"]
    .apply(remover_ponto_zero)
)


# ============================================================
# CLASSE
# ============================================================

df["classe"] = pd.to_numeric(
    df["classe"],
    errors="coerce"
)


# ============================================================
# DATA/HORA DE INÍCIO
# ============================================================

# O Supabase retorna timestamp com timezone.
# Primeiro convertemos para UTC e depois para São Paulo.

df["inicio_dt"] = pd.to_datetime(
    df["inicio"],
    errors="coerce",
    utc=True
)


df["inicio_dt"] = (
    df["inicio_dt"]
    .dt.tz_convert(
        "America/Sao_Paulo"
    )
)


# ============================================================
# DURAÇÃO
# ============================================================

# AGORA também possui timezone.
# Isso evita erro entre tz-naive e tz-aware.

agora = pd.Timestamp.now(
    tz="America/Sao_Paulo"
)


df["duracao_segundos"] = (
    agora
    - df["inicio_dt"]
).dt.total_seconds()


df["duracao_segundos"] = (
    df["duracao_segundos"]
    .fillna(0)
    .clip(lower=0)
)


# ============================================================
# FORMATAR DURAÇÃO
# ============================================================

def formatar_duracao(segundos):

    try:

        segundos = int(
            segundos
        )

    except (
        ValueError,
        TypeError
    ):

        return ""

    horas = (
        segundos
        // 3600
    )

    minutos = (
        segundos
        % 3600
    ) // 60

    return (
        f"{horas:02d}:"
        f"{minutos:02d}"
    )


df["duracao"] = (
    df["duracao_segundos"]
    .apply(
        formatar_duracao
    )
)


# ============================================================
# CLASSIFICAÇÃO PARA O APP
# ============================================================

df["grupo_app"] = None


# ============================================================
# CAMINHÕES
# CLASSE 1
# ============================================================

df.loc[
    df["classe"] == 1,
    "grupo_app"
] = "Caminhões"


# ============================================================
# CARRETAS
# CLASSE 5
# ============================================================

df.loc[
    df["classe"] == 5,
    "grupo_app"
] = "Carretas"


# ============================================================
# IDENTIFICAR FRENTE
# ============================================================

def identificar_frente(valor):

    texto = (
        str(valor)
        .upper()
        .strip()
    )

    # --------------------------------------------------------
    # FRENTE 1
    # --------------------------------------------------------

    if (
        "FRENTE 1" in texto
        or texto == "1"
    ):

        return "Frente 1"

    # --------------------------------------------------------
    # FRENTE 2
    # --------------------------------------------------------

    if (
        "FRENTE 2" in texto
        or texto == "2"
    ):

        return "Frente 2"

    # --------------------------------------------------------
    # FRENTE 3
    # --------------------------------------------------------

    if (
        "FRENTE 3" in texto
        or texto == "3"
    ):

        return "Frente 3"

    # --------------------------------------------------------
    # FRENTE 4
    # --------------------------------------------------------

    if (
        "FRENTE 4" in texto
        or texto == "4"
    ):

        return "Frente 4"

    # --------------------------------------------------------
    # FRENTE 5
    # --------------------------------------------------------

    if (
        "FRENTE 5" in texto
        or texto == "5"
    ):

        return "Frente 5"

    return None


# ============================================================
# TRATORES E MÁQUINAS
# USAM A FRENTE DO IFROTA
# ============================================================

mascara_frentes = (
    df["classe"]
    .isin(
        [
            2,
            4
        ]
    )
)


df.loc[
    mascara_frentes,
    "grupo_app"
] = (
    df.loc[
        mascara_frentes,
        "frente"
    ]
    .apply(
        identificar_frente
    )
)


# ============================================================
# GRUPOS DO APP
# ============================================================

GRUPOS = [
    "Frente 1",
    "Frente 2",
    "Frente 3",
    "Frente 4",
    "Frente 5",
    "Carretas",
    "Caminhões"
]


# ============================================================
# DADOS PARA EXIBIÇÃO
# ============================================================

# Não existem mais filtros nesta página.
# Todos os registros da BASE 2026 serão utilizados.

df_filtrado = df.copy()


# ============================================================
# INDICADORES
# ============================================================

total = len(
    df_filtrado
)


tratores = len(
    df_filtrado[
        df_filtrado[
            "classe"
        ] == 2
    ]
)


maquinas = len(
    df_filtrado[
        df_filtrado[
            "classe"
        ] == 4
    ]
)


carretas = len(
    df_filtrado[
        df_filtrado[
            "classe"
        ] == 5
    ]
)


caminhoes = len(
    df_filtrado[
        df_filtrado[
            "classe"
        ] == 1
    ]
)


# ============================================================
# EXIBIR INDICADORES
# ============================================================

col1, col2, col3, col4, col5 = (
    st.columns(5)
)


col1.metric(
    "🔧 Total",
    total
)


col2.metric(
    "🚜 Tratores",
    tratores
)


col3.metric(
    "🌾 Máquinas",
    maquinas
)


col4.metric(
    "🚛 Carretas",
    carretas
)


col5.metric(
    "🚚 Caminhões",
    caminhoes
)


st.divider()


# ============================================================
# FUNÇÃO - NOME DO TIPO
# ============================================================

def nome_tipo(classe):

    if classe == 1:

        return "CAMINHÃO"

    if classe == 2:

        return "TRATOR"

    if classe == 4:

        return "MÁQUINA"

    if classe == 5:

        return "CARRETA"

    return ""


# ============================================================
# FUNÇÃO - MONTAR TABELA
# ============================================================

def montar_tabela(
    dados
):

    if dados.empty:

        return pd.DataFrame()

    tabela = (
        dados.copy()
    )


    # ========================================================
    # TIPO
    # ========================================================

    tabela["TIPO"] = (
        tabela["classe"]
        .apply(
            nome_tipo
        )
    )


    # ========================================================
    # DATA/HORA
    # ========================================================

    tabela["INÍCIO"] = (
        tabela[
            "inicio_dt"
        ]
        .dt.strftime(
            "%d/%m/%Y %H:%M"
        )
    )


    # ========================================================
    # RENOMEAR COLUNAS
    # ========================================================

    tabela = (
        tabela.rename(
            columns={

                "frota":
                    "FROTA",

                "motivo":
                    "MOTIVO",

                "gleba":
                    "GLEBA",

                "local":
                    "LOCAL",

                "duracao":
                    "DURAÇÃO"

            }
        )
    )


    # ========================================================
    # COLUNAS
    # ========================================================

    tabela = tabela[
        [
            "FROTA",
            "TIPO",
            "MOTIVO",
            "INÍCIO",
            "GLEBA",
            "LOCAL",
            "DURAÇÃO",
            "duracao_segundos"
        ]
    ]


    # ========================================================
    # ORDENAR PELA MAIOR DURAÇÃO
    # ========================================================

    tabela = (
        tabela.sort_values(
            by="duracao_segundos",
            ascending=False
        )
    )


    # ========================================================
    # REMOVER COLUNA AUXILIAR
    # ========================================================

    tabela = (
        tabela.drop(
            columns=[
                "duracao_segundos"
            ]
        )
    )


    return tabela


# ============================================================
# ABAS
# ============================================================

abas = st.tabs(
    [
        "🚜 Frente 1",
        "🚜 Frente 2",
        "🚜 Frente 3",
        "🚜 Frente 4",
        "🚜 Frente 5",
        "🚛 Carretas",
        "🚚 Caminhões"
    ]
)


# ============================================================
# EXIBIR GRUPOS
# ============================================================

for aba, grupo in zip(
    abas,
    GRUPOS
):

    with aba:

        dados_grupo = (
            df_filtrado[
                df_filtrado[
                    "grupo_app"
                ] == grupo
            ]
            .copy()
        )


        quantidade = len(
            dados_grupo
        )


        # ====================================================
        # TÍTULO
        # ====================================================

        st.markdown(
            f"### {grupo}"
        )


        # ====================================================
        # QUANTIDADE
        # ====================================================

        st.caption(
            f"{quantidade} equipamento(s) "
            "em manutenção"
        )


        # ====================================================
        # SEM MANUTENÇÃO
        # ====================================================

        if dados_grupo.empty:

            st.success(
                "Nenhum equipamento em manutenção."
            )

            continue


        # ====================================================
        # MONTAR TABELA
        # ====================================================

        tabela = (
            montar_tabela(
                dados_grupo
            )
        )


        # ====================================================
        # EXIBIR TABELA
        # ====================================================

        st.dataframe(
            tabela,
            width="stretch",
            hide_index=True,
            height=min(
                700,
                70
                + len(tabela) * 36
            ),
            column_config={

                "FROTA":
                    st.column_config.TextColumn(
                        "FROTA",
                        width="small"
                    ),

                "TIPO":
                    st.column_config.TextColumn(
                        "TIPO",
                        width="small"
                    ),

                "MOTIVO":
                    st.column_config.TextColumn(
                        "MOTIVO",
                        width="large"
                    ),

                "INÍCIO":
                    st.column_config.TextColumn(
                        "INÍCIO",
                        width="medium"
                    ),

                "GLEBA":
                    st.column_config.TextColumn(
                        "GLEBA",
                        width="small"
                    ),

                "LOCAL":
                    st.column_config.TextColumn(
                        "LOCAL",
                        width="medium"
                    ),

                "DURAÇÃO":
                    st.column_config.TextColumn(
                        "DURAÇÃO",
                        width="small"
                    )
            }
        )


# ============================================================
# REGISTROS SEM CLASSIFICAÇÃO
# ============================================================

nao_classificados = (
    df_filtrado[
        df_filtrado[
            "grupo_app"
        ].isna()
    ]
)


if not nao_classificados.empty:

    st.divider()

    with st.expander(
        "⚠️ Registros sem classificação"
    ):

        st.warning(
            f"Existem "
            f"{len(nao_classificados)} "
            "registro(s) cuja frente não foi "
            "identificada como Frente 1 a Frente 5."
        )


        tabela_nao_classificados = (
            nao_classificados[
                [
                    "frente",
                    "classe",
                    "tipo_equipamento",
                    "frota",
                    "motivo"
                ]
            ]
            .copy()
        )


        tabela_nao_classificados = (
            tabela_nao_classificados.rename(
                columns={

                    "frente":
                        "FRENTE ORIGINAL",

                    "classe":
                        "CLASSE",

                    "tipo_equipamento":
                        "TIPO ORIGINAL",

                    "frota":
                        "FROTA",

                    "motivo":
                        "MOTIVO"

                }
            )
        )


        st.dataframe(
            tabela_nao_classificados,
            width="stretch",
            hide_index=True
        )


# ============================================================
# RODAPÉ
# ============================================================

st.divider()


st.caption(
    "Tela atualizada em "
    + datetime.now(
        FUSO_BR
    ).strftime(
        "%d/%m/%Y %H:%M:%S"
    )
)
