
import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
from geopy.geocoders import Nominatim
from geopy.extra.rate_limiter import RateLimiter

# Carregar dados
df = pd.read_excel("chamados_tratados_para_powerbi.xlsx")

# Geolocalizar usando cidade + estado se endereço estiver ausente
st.title("Mapa de Chamados por Loja e Equipamento")
st.sidebar.header("Filtros")

estado = st.sidebar.multiselect("Estado", options=sorted(df["Estado"].dropna().unique()), default=None)
cidade = st.sidebar.multiselect("Cidade", options=sorted(df["Cidade"].dropna().unique()), default=None)
equipamento = st.sidebar.multiselect("Equipamento", options=sorted(df["Equipamento pra troca"].dropna().unique()), default=None)
somente_falta_tec = st.sidebar.checkbox("Somente chamados com falta de técnico")

# Filtros
df_filt = df.copy()
if estado:
    df_filt = df_filt[df_filt["Estado"].isin(estado)]
if cidade:
    df_filt = df_filt[df_filt["Cidade"].isin(cidade)]
if equipamento:
    df_filt = df_filt[df_filt["Equipamento pra troca"].isin(equipamento)]
if somente_falta_tec:
    df_filt = df_filt[df_filt["Flag_Falta_Tecnico"] == True]

# Obter coordenadas
geolocator = Nominatim(user_agent="geoapi")
geocode = RateLimiter(geolocator.geocode, min_delay_seconds=1)

@st.cache_data(show_spinner=False)
def get_latlon(endereco):
    location = geocode(endereco)
    if location:
        return pd.Series([location.latitude, location.longitude])
    return pd.Series([None, None])

if "Latitude" not in df_filt.columns or "Longitude" not in df_filt.columns:
    df_filt[["Latitude", "Longitude"]] = df_filt["Endereco_Completo"].apply(get_latlon)

# Criar mapa
m = folium.Map(location=[-14, -52], zoom_start=4)

for _, row in df_filt.iterrows():
    if pd.notnull(row["Latitude"]) and pd.notnull(row["Longitude"]):
        color = "red" if row["Flag_Falta_Tecnico"] else "blue"
        popup_text = f"Loja: {row['Loja']}<br>Equipamento: {row['Equipamento pra troca']}<br>Status: {row['Status']}"
        folium.CircleMarker(
            location=[row["Latitude"], row["Longitude"]],
            radius=6,
            color=color,
            fill=True,
            fill_color=color,
            fill_opacity=0.7,
            popup=popup_text
        ).add_to(m)

st_folium(m, width=900, height=600)

st.subheader("Detalhes dos Chamados")
st.dataframe(df_filt)
