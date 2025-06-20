import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
from geopy.geocoders import Nominatim
from geopy.extra.rate_limiter import RateLimiter
from utils.jira_api import JiraAPI

# ── Configuração da página ─────────────────────────────────────────────
st.set_page_config(page_title="Mapa de Chamados - Spare", layout="wide")

# ── Conectar ao Jira ────────────────────────────────────────────────────
jira = JiraAPI(
    st.secrets["EMAIL"],
    st.secrets["API_TOKEN"],
    "https://delfia.atlassian.net"
)

# Campos necessários da API do Jira
FIELDS = (
    "summary,customfield_14954,customfield_14829,customfield_14825,"
    "customfield_12271,customfield_11993"
)

# ── Buscar chamados com status 'Aguardando Spare' ───────────────────────
query = 'project = FSA AND status = "Aguardando Spare"'
chamados = jira.buscar_chamados(query, FIELDS)

if not chamados:
    st.warning("Nenhum chamado encontrado com status 'Aguardando Spare'.")
    st.stop()

# ── Transformar dados em DataFrame ──────────────────────────────────────
def extrair(issue):
    f = issue["fields"]
    return {
        "Chamado": issue["key"],
        "Loja": f.get("customfield_14954", {}).get("value", ""),
        "Cidade": f.get("customfield_14829", {}).get("value", ""),
        "Estado": f.get("customfield_14825", {}).get("value", ""),
        "Técnico": f.get("customfield_12271", ""),
        "Equipamento": f.get("customfield_11993", ""),
    }

df = pd.DataFrame([extrair(i) for i in chamados])

# Corrigir nulos e construir endereço para geolocalização
df["Cidade"] = df["Cidade"].fillna("").astype(str)
df["Estado"] = df["Estado"].fillna("").astype(str)
df["Endereco"] = df["Cidade"] + ", " + df["Estado"]

# ── Geolocalização com cache ────────────────────────────────────────────
geolocator = Nominatim(user_agent="geoapi")
geocode = RateLimiter(geolocator.geocode, min_delay_seconds=1)

@st.cache_data(show_spinner=False)
def get_latlon(endereco):
    location = geocode(endereco)
    if location:
        return pd.Series([location.latitude, location.longitude])
    return pd.Series([None, None])

df[["Latitude", "Longitude"]] = df["Endereco"].apply(get_latlon)

# ── Filtros interativos ─────────────────────────────────────────────────
st.sidebar.header("Filtros")
estados = sorted(df["Estado"].dropna().unique())
estado_sel = st.sidebar.multiselect("Estado", options=estados, default=estados)

cidades = sorted(df[df["Estado"].isin(estado_sel)]["Cidade"].dropna().unique())
cidade_sel = st.sidebar.multiselect("Cidade", options=cidades, default=cidades)

df_filt = df[df["Estado"].isin(estado_sel) & df["Cidade"].isin(cidade_sel)]

# ── Seleção de FSA ──────────────────────────────────────────────────────
fsa_sel = st.sidebar.selectbox("🔍 Detalhes da FSA:", options=df_filt["Chamado"].unique())

# ── Mapa interativo com folium ─────────────────────────────────────────
st.title("🗺️ Mapa de Chamados - Aguardando Spare")
m = folium.Map(location=[-14, -52], zoom_start=4)

for _, row in df_filt.iterrows():
    if pd.notnull(row["Latitude"]) and pd.notnull(row["Longitude"]):
        folium.CircleMarker(
            location=[row["Latitude"], row["Longitude"]],
            radius=6,
            color="red",
            fill=True,
            fill_color="red",
            fill_opacity=0.8,
            popup=row["Chamado"]
        ).add_to(m)

st_folium(m, width=900, height=600)

# ── Exibir detalhes do chamado selecionado ─────────────────────────────
st.subheader(f"📄 Detalhes do Chamado: {fsa_sel}")
st.dataframe(df_filt[df_filt["Chamado"] == fsa_sel])
