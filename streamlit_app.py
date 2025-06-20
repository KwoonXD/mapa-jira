import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
from geopy.geocoders import Nominatim
from geopy.extra.rate_limiter import RateLimiter

# Carregar dados
df = pd.read_excel("chamados_tratados_para_powerbi.xlsx")

# Título
st.title("📍 Mapa de Chamados por Loja")

# Filtros laterais
st.sidebar.header("Filtros")

# Filtro: Estado
estado = st.sidebar.multiselect(
    "Estado", options=sorted(df["Estado"].dropna().unique()), default=None
)

# Cidades disponíveis com base no estado selecionado
if estado:
    cidades_disponiveis = sorted(df[df["Estado"].isin(estado)]["Cidade"].dropna().unique())
else:
    cidades_disponiveis = sorted(df["Cidade"].dropna().unique())

# Filtro: Cidade (dependente do estado)
cidade = st.sidebar.multiselect(
    "Cidade", options=cidades_disponiveis, default=cidades_disponiveis
)

# Filtro: Falta técnico
somente_falta_tec = st.sidebar.checkbox("🔴 Apenas chamados com falta de técnico")

# Aplicar filtros
df_filt = df.copy()
if estado:
    df_filt = df_filt[df_filt["Estado"].isin(estado)]
if cidade:
    df_filt = df_filt[df_filt["Cidade"].isin(cidade)]
if somente_falta_tec:
    df_filt = df_filt[df_filt["Flag_Falta_Tecnico"] == True]

# Geolocalização
geolocator = Nominatim(user_agent="geoapi")
geocode = RateLimiter(geolocator.geocode, min_delay_seconds=1)

@st.cache_data(show_spinner=False)
def get_latlon(endereco):
    location = geocode(endereco)
    if location:
        return pd.Series([location.latitude, location.longitude])
    return pd.Series([None, None])

# Adicionar coordenadas se ainda não existirem
if "Latitude" not in df_filt.columns or "Longitude" not in df_filt.columns:
    df_filt[["Latitude", "Longitude"]] = df_filt["Endereco_Completo"].apply(get_latlon)

# Mapa interativo
m = folium.Map(location=[-14, -52], zoom_start=4)

# Listar chamadas para seleção
st.sidebar.markdown("## 🔍 Ver detalhes da FSA")
fsa_opcao = st.sidebar.selectbox("Selecione uma FSA", options=df_filt["Chamado"].unique(), index=0)

# Marcar os pontos no mapa
for _, row in df_filt.iterrows():
    if pd.notnull(row["Latitude"]) and pd.notnull(row["Longitude"]):
        color = "red" if row["Flag_Falta_Tecnico"] else "blue"
        folium.CircleMarker(
            location=[row["Latitude"], row["Longitude"]],
            radius=6,
            color=color,
            fill=True,
            fill_color=color,
            fill_opacity=0.7,
            popup=row["Chamado"]
        ).add_to(m)

# Mostrar mapa
st_folium(m, width=900, height=600)

# Tabela com detalhes da FSA selecionada
st.subheader(f"📄 Detalhes da FSA: {fsa_opcao}")
st.dataframe(df_filt[df_filt["Chamado"] == fsa_opcao])
