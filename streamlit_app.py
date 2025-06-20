import streamlit as st
import pandas as pd
import pydeck as pdk
from collections import defaultdict
from utils.jira_api import JiraAPI

st.set_page_config(page_title="Mapa Chamados - Aguardando Spare", layout="wide")

# ── Jira API ─────────────────────────
jira = JiraAPI(
    st.secrets["EMAIL"],
    st.secrets["API_TOKEN"],
    "https://delfia.atlassian.net"
)

# ── Buscar chamados ─────────────────
FSA_FIELDS = (
    "summary,customfield_14954,customfield_12374,"
    "customfield_14825,customfield_11993,customfield_12279,"
    "customfield_14829"
)

chamados = jira.buscar_chamados(
    'project = FSA AND status = "Aguardando Spare"',
    FSA_FIELDS
)

# ── Preparar DataFrame ──────────────
dados = []
for issue in chamados:
    f = issue["fields"]
    dados.append({
        "Chamado": issue["key"],
        "Loja": f.get("customfield_14954", {}).get("value", ""),
        "Cidade": f.get("customfield_12374", {}).get("value", ""),
        "Estado": f.get("customfield_14825", {}).get("value", ""),  # <- Aqui está o ESTADO corretamente
        "Técnico": f.get("customfield_12279", {}).get("content", [{}])[0].get("content", [{}])[0].get("text", ""),
        "Equipamento": f.get("summary", ""),
        "Endereço": f.get("customfield_11993", ""),
    })

df = pd.DataFrame(dados)

# ── Sidebar de Filtros ───────────────
with st.sidebar:
    st.title("Filtros")

    estados = sorted(df["Estado"].dropna().unique())
    estado_sel = st.selectbox("Estado", ["Todos"] + estados)

    cidades = sorted(df["Cidade"].dropna().unique())
    cidade_sel = st.selectbox("Cidade", ["Todos"] + cidades)

    fsa_sel = st.selectbox("🔎 Detalhes da FSA:", ["Selecione"] + df["Chamado"].tolist())

# ── Aplicar filtros ──────────────────
df_filtrado = df.copy()
if estado_sel != "Todos":
    df_filtrado = df_filtrado[df_filtrado["Estado"] == estado_sel]
if cidade_sel != "Todos":
    df_filtrado = df_filtrado[df_filtrado["Cidade"] == cidade_sel]

# ── Contagem por Endereço ────────────
contagem = df_filtrado.groupby("Endereço").size().reset_index(name="Chamados")

# ── Mapa com Bolhas (fake lat/lon) ──
contagem["lat"] = range(len(contagem))  # Fake lat
contagem["lon"] = range(len(contagem))  # Fake lon

st.title("📍 Mapa de Chamados - Aguardando Spare")

st.pydeck_chart(pdk.Deck(
    map_style=None,
    initial_view_state=pdk.ViewState(
        latitude=0, longitude=0, zoom=2,
    ),
    layers=[
        pdk.Layer(
            "ScatterplotLayer",
            data=contagem,
            pickable=True,
            get_position='[lon, lat]',
            get_fill_color='[30, 136, 229, 160]',
            get_radius="Chamados * 5000",
        )
    ],
    tooltip={"text": "{Chamados} FSAs em {Endereço}"}
))

# ── Mostrar Detalhes da FSA Selecionada ───
if fsa_sel != "Selecione":
    fsa_info = df[df["Chamado"] == fsa_sel]
    st.markdown(f"### 📄 Detalhes do Chamado: `{fsa_sel}`")
    st.dataframe(fsa_info.reset_index(drop=True))
