import streamlit as st
import pandas as pd
from datetime import datetime
from zoneinfo import ZoneInfo
from supabase import create_client


# ============================================================
# CONFIGURAÇÃO
# ============================================================

st.set_page_config(
    page_title="COA - Manutenções",
    page_icon="🔧",
    layout="wide"
)

FUSO_BR = ZoneInfo("America/Sao_Paulo")


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
# CABEÇALHO
# ============================================================

st.title("🔧 Manutenções - Colheita")

st.caption(
    "Equipamentos atualmente em manutenção no IFROTA"
)


# ============================================================
# ATUALIZAÇÃO
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
            .eq("base", 2026)
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
# CARREGAR
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


if not registros:

    st.warning(
        "Nenhuma manutenção da colheita encontrada."
    )

    st.stop()


df = pd.DataFrame(registros)


# ============================================================
# TRATAR CAMPOS
# ============================================================

for coluna in [
    "tipo_equipamento",
    "frente",
    "local",
    "frota",
    "gleba",
    "motivo"
]:

    if coluna in df.columns:

        df[coluna] = (
            df[coluna]
            .fillna("")
            .astype(str)
            .str.strip()
        )


# ============================================================
# FROTA / GLEBA SEM .0
# ============================================================

def remover_ponto_zero(valor):

    texto = str(valor).strip()

    if texto.endswith(".0"):
        return texto[:-2]

    return texto


df["frota"] = df["frota"].apply(
    remover_ponto_zero
)

df["gleba"] = df["gleba"].apply(
    remover_ponto_zero
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

# O Oracle está enviando o horário operacional local.
# Portanto não tratamos o valor como UTC.

df["inicio_dt"] = pd.to_datetime(
    df["inicio"],
    errors="coerce"
)


# ============================================================
# DURAÇÃO
# ============================================================

agora = datetime.now(FUSO_BR).replace(
    tzinfo=None
)


df["duracao_segundos"] = (
    agora - df["inicio_dt"]
).dt.total_seconds()


df["duracao_segundos"] = (
    df["duracao_segundos"]
    .fillna(0)
    .clip(lower=0)
)


def formatar_duracao(segundos):

    try:
        segundos = int(segundos)
    except:
        return ""

    horas = segundos // 3600

    minutos = (
        segundos % 3600
    ) // 60

    return (
        f"{horas:02d}:"
        f"{minutos:02d}"
    )


df["duracao"] = (
    df["duracao_segundos"]
    .apply(formatar_duracao)
)


# ============================================================
# PADRONIZAÇÃO DAS CATEGORIAS
# ============================================================

# Caminhões
df.loc[
    df["classe"] == 1,
    "grupo_app"
] = "Caminhões"


# Carretas / caixas
df.loc[
    df["classe"] == 5,
    "grupo_app"
] = "Carretas"


# ============================================================
# IDENTIFICAR FRENTE 1 A 5
# ============================================================

def identificar_frente(valor):

    texto = str(valor).upper().strip()

    # Ordem importante:
    # primeiro 1, 2, 3 etc.

    if (
        "FRENTE 1" in texto
        or texto == "1"
    ):
        return "Frente 1"

    if (
        "FRENTE 2" in texto
        or texto == "2"
    ):
        return "Frente 2"

    if (
        "FRENTE 3" in texto
        or texto == "3"
    ):
        return "Frente 3"

    if (
        "FRENTE 4" in texto
        or texto == "4"
    ):
        return "Frente 4"

    if (
        "FRENTE 5" in texto
        or texto == "5"
    ):
        return "Frente 5"

    return None


# Tratores e máquinas usam a frente
mascara_frentes = (
    df["classe"].isin([2, 4])
)


df.loc[
    mascara_frentes,
    "grupo_app"
] = (
    df.loc[
        mascara_frentes,
        "frente"
    ]
    .apply(identificar_frente)
)


# ============================================================
# ORDEM DOS GRUPOS
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
# FILTROS
# ============================================================

st.sidebar.header(
    "🔍 Filtros"
)


# ------------------------------------------------------------
# PESQUISA FROTA
# ------------------------------------------------------------

pesquisa_frota = (
    st.sidebar
    .text_input(
        "Pesquisar Frota"
    )
    .strip()
)


# ------------------------------------------------------------
# MOTIVO
# ------------------------------------------------------------

motivos = sorted(
    [
        x
        for x in df["motivo"].unique()
        if x
    ]
)


motivos_selecionados = (
    st.sidebar.multiselect(
        "Motivo",
        options=motivos
    )
)


# ------------------------------------------------------------
# LOCAL
# ------------------------------------------------------------

locais = sorted(
    [
        x
        for x in df["local"].unique()
        if x
    ]
)


locais_selecionados = (
    st.sidebar.multiselect(
        "Local",
        options=locais
    )
)


# ============================================================
# APLICAR FILTROS
# ============================================================

df_filtrado = df.copy()


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


if motivos_selecionados:

    df_filtrado = (
        df_filtrado[
            df_filtrado[
                "motivo"
            ].isin(
                motivos_selecionados
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


# ============================================================
# INDICADORES
# ============================================================

total = len(df_filtrado)

tratores = len(
    df_filtrado[
        df_filtrado["classe"] == 2
    ]
)

maquinas = len(
    df_filtrado[
        df_filtrado["classe"] == 4
    ]
)

carretas = len(
    df_filtrado[
        df_filtrado["classe"] == 5
    ]
)

caminhoes = len(
    df_filtrado[
        df_filtrado["classe"] == 1
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
# FUNÇÃO PARA MONTAR TABELA
# ============================================================

def montar_tabela(dados):

    if dados.empty:
        return pd.DataFrame()

    tabela = dados.copy()

    # --------------------------------------------------------
    # TIPO
    # --------------------------------------------------------

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

    tabela["TIPO"] = (
        tabela["classe"]
        .apply(nome_tipo)
    )

    # --------------------------------------------------------
    # DATA
    # --------------------------------------------------------

    tabela["INÍCIO"] = (
        tabela["inicio_dt"]
        .dt.strftime(
            "%d/%m/%Y %H:%M"
        )
    )

    # --------------------------------------------------------
    # RENOMEAR
    # --------------------------------------------------------

    tabela = tabela.rename(
        columns={
            "frota": "FROTA",
            "motivo": "MOTIVO",
            "gleba": "GLEBA",
            "local": "LOCAL",
            "duracao": "DURAÇÃO"
        }
    )

    # --------------------------------------------------------
    # ORDEM
    # --------------------------------------------------------

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

    # Mais antiga primeiro
    tabela = tabela.sort_values(
        "duracao_segundos",
        ascending=False
    )

    tabela = tabela.drop(
        columns=[
            "duracao_segundos"
        ]
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
# EXIBIR CADA GRUPO
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

        st.markdown(
            f"### {grupo}"
        )

        st.caption(
            f"{quantidade} equipamento(s) "
            "em manutenção"
        )

        if dados_grupo.empty:

            st.success(
                "Nenhum equipamento em manutenção."
            )

            continue

        tabela = montar_tabela(
            dados_grupo
        )

        st.dataframe(
            tabela,
            width="stretch",
            hide_index=True,
            height=min(
                700,
                70 + len(tabela) * 36
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
# REGISTROS NÃO CLASSIFICADOS
# ============================================================

nao_classificados = (
    df_filtrado[
        df_filtrado[
            "grupo_app"
        ].isna()
    ]
)


if not nao_classificados.empty:

    with st.expander(
        "⚠️ Registros sem classificação"
    ):

        st.warning(
            f"Existem "
            f"{len(nao_classificados)} "
            "registro(s) cuja frente não foi "
            "identificada como Frente 1 a 5."
        )

        st.dataframe(
            nao_classificados[
                [
                    "frente",
                    "classe",
                    "frota",
                    "motivo"
                ]
            ],
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
