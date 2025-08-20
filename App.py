import streamlit as st
import requests
import pandas as pd

# Configurações da página
st.set_page_config(page_title="Buscador de Passagens", layout="wide")

st.title("✈️ Buscador de Passagens Aéreas")
st.write("Comparador de passagens com Travelpayouts API")

# === ENTRADAS ===
origem = st.selectbox("Origem", ["SAO (Todos os aeroportos de SP)", "GRU", "CGH", "VCP"], index=0)
destinos = {
    "Fortaleza": "FOR",
    "Recife": "REC",
    "Salvador": "SSA",
    "Maceió": "MCZ",
    "Natal": "NAT"
}
destino = st.selectbox("Destino (Nordeste)", list(destinos.keys()))
data_ida = st.date_input("Data de Ida")
data_volta = st.date_input("Data de Volta (opcional)", value=None)

# === API CONFIG ===
API_TOKEN = st.secrets["TRAVELPAYOUTS_API"]  # chave salva em secrets.toml
url = "https://api.travelpayouts.com/aviasales/v3/prices_for_dates"

params = {
    "origin": origem.split()[0],
    "destination": destinos[destino],
    "departure_at": data_ida,
    "return_at": data_volta if data_volta else "",
    "token": API_TOKEN,
    "sorting": "price",
    "limit": 10
}

# === BOTÃO ===
if st.button("Buscar Passagens"):
    with st.spinner("Buscando melhores preços..."):
        r = requests.get(url, params=params)

        if r.status_code == 200:
            data = r.json().get("data", [])

            if data:
                df = pd.DataFrame(data)
                df = df[["origin", "destination", "airline", "departure_at", "return_at", "price", "link"]]
                st.success("Resultados encontrados!")
                st.dataframe(df)
            else:
                st.warning("Nenhuma passagem encontrada para esses critérios.")
        else:
            st.error("Erro ao buscar dados da API. Verifique sua chave ou parâmetros.")
