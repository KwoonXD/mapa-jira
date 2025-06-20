import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
from utils.jira_api import JiraAPI

# ── Configuração ────────────────────────────────────────
st.set_page_config(page_title="Mapa FSAs - Aguardando Spare", layout="wide")
jira = JiraAPI(
    email=st.secrets["EMAIL"],
    token=st.secrets["API_TOKEN"],
    url="https://delfia.atlassian.net"
)

def extrair_valor(campo):
    if isinstance(campo, dict) and "value" in campo:
        return campo["value"]
    return campo if isinstance(campo, str) else ""

# ── Buscar chamados diretamente do Jira ─────────────────
chamados = jira.buscar_chamados(
    jql="project = FSA AND status = 'Aguardando Spare'",
    fields="key,customfield_14954,customfield_11994,customfield_11993,customfield_12271,customfield_14829,customfield_12374"
)

# ── Criar DataFrame ─────────────────────────────────────
df = pd.DataFrame([{
    "Chamado": c["key"],
    "Loja": c["fields"].get("customfield_14954", "—"),
    "Cidade": extrair_valor(c["fields"].get("customfield_11994")),
    "Estado": extrair_valor(c["fields"].get("customfield_11993")),
    "Endereço": extrair_valor(c["fields"].get("customfield_12271")),
    "CEP": c["fields"].get("customfield_14829", "—"),
    "Técnico": extrair_valor(c["fields"].get("customfield_12374"))
} for c in chamados])

# ── Montar campo visual de endereço completo ─────────────
df["Endereco"] = df["Endereço"] + ", " + df["Cidade"] + " - " + df["Estado"]

# ── SIDEBAR com filtros ──────────────────────────────────
with st.sidebar:
    st.header("Filtros")
    estados = sorted(df["Estado"].dropna().unique())
    estado_sel = st.multiselect("Estado", estados)

    cidades = sorted(df[df["Estado"].isin(estado_sel)]["Cidade"].dropna().unique()) if estado_sel else sorted(df["Cidade"].dropna().unique())
    cidade_sel = st.multiselect("Cidade", cidades)

    fsa_sel = st.selectbox("🔍 Detalhes da FSA:", df["Chamado"].unique())

# ── Aplicar filtros ao DataFrame ─────────────────────────
df_filtrado = df.copy()
if estado_sel:
    df_filtrado = df_filtrado[df_filtrado["Estado"].isin(estado_sel)]
if cidade_sel:
    df_filtrado = df_filtrado[df_filtrado["Cidade"].isin(cidade_sel)]

# ── MAPA ─────────────────────────────────────────────────
st.title("📍 FSAs em Aguardando Spare")

m = folium.Map(location=[-14.2, -51.9], zoom_start=4)

for _, row in df_filtrado.iterrows():
    folium.CircleMarker(
        location=[-14.2, -51.9],  # posição simbólica
        radius=6,
        color="blue",
        fill=True,
        fill_opacity=0.8,
        tooltip=row["Chamado"]
    ).add_to(m)

st_folium(m, height=500, width=1100)

# ── Detalhes da FSA ──────────────────────────────────────
st.subheader(f"📄 Detalhes do Chamado: {fsa_sel}")
df_sel = df[df["Chamado"] == fsa_sel]
st.dataframe(df_sel, use_container_width=True)
