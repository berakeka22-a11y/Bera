import streamlit as st
import requests
import pandas as pd

st.set_page_config(page_title="Buscador de Passagens Aéreas", page_icon="✈️", layout="centered")

st.title("✈️ Buscador de Passagens Aéreas")
st.write("Comparador de passagens com Travelpayouts API (mês inteiro)")

# 🔑 Pegando chave da Travelpayouts no secrets
API_TOKEN = st.secrets["TRAVELPAYOUTS_API_TOKEN"]

# Dicionário de aeroportos
airports = {
    "São Paulo (Todos)": "SAO",
    "Rio de Janeiro (Todos)": "RIO",
    "Fortaleza": "FOR",
    "Salvador": "SSA",
    "Recife": "REC",
    "Natal": "NAT",
    "Maceió": "MCZ",
    "João Pessoa": "JPA",
}

# Formulário
origem = st.selectbox("Origem", list(airports.keys()))
destino = st.selectbox("Destino", list(airports.keys()))
data_mes = st.date_input("Mês da Viagem (pega o mês inteiro)")

if st.button("🔍 Buscar Passagens"):
    origin_code = airports[origem]
    destination_code = airports[destino]

    # Formatando ano-mês para a API
    month = data_mes.strftime("%Y-%m")

    url = f"https://api.travelpayouts.com/aviasales/v3/prices_for_month"
    params = {
        "origin": origin_code,
        "destination": destination_code,
        "month": month,
        "currency": "BRL",
        "token": API_TOKEN
    }

    response = requests.get(url, params=params)

    if response.status_code == 200:
        data = response.json().get("data", [])

        if not data:
            st.warning("⚠️ Nenhuma passagem encontrada para esse mês.")
        else:
            # Organizar os resultados em DataFrame
            df = pd.DataFrame(data)
            df = df[["origin", "destination", "depart_date", "value", "airline", "gate"]]
            df = df.rename(columns={
                "origin": "Origem",
                "destination": "Destino",
                "depart_date": "Data",
                "value": "Preço (R$)",
                "airline": "Companhia",
                "gate": "Agência"
            })
            st.success(f"✅ {len(df)} opções encontradas!")
            st.dataframe(df)
    else:
        st.error("❌ Erro na API. Verifique sua chave ou tente novamente.")
