import streamlit as st
import requests
import datetime

# Configuração inicial
st.set_page_config(page_title="Buscador de Passagens", layout="wide")

st.title("✈️ Buscador de Passagens Aéreas")
st.write("Encontre voos baratos usando a API da Amadeus")

# Entrada de dados do usuário
origin = st.text_input("Origem (ex: GRU)", "GRU")
destination = st.text_input("Destino (ex: JFK)", "JFK")
departure_date = st.date_input("Data de partida", datetime.date.today())
adults = st.number_input("Quantidade de adultos", min_value=1, max_value=9, value=1)

# Função para autenticar na API da Amadeus
@st.cache_data(ttl=1800)
def get_access_token():
    url = "https://test.api.amadeus.com/v1/security/oauth2/token"
    data = {
        "grant_type": "client_credentials",
        "client_id": st.secrets["AMADEUS_CLIENT_ID"],
        "client_secret": st.secrets["AMADEUS_CLIENT_SECRET"]
    }
    response = requests.post(url, data=data)
    return response.json().get("access_token")

# Função para buscar voos
def search_flights(origin, destination, departure_date, adults):
    token = get_access_token()
    url = "https://test.api.amadeus.com/v2/shopping/flight-offers"
    params = {
        "originLocationCode": origin,
        "destinationLocationCode": destination,
        "departureDate": str(departure_date),
        "adults": adults,
        "max": 5,
        "currencyCode": "USD"
    }
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(url, headers=headers, params=params)
    return response.json()

# Botão de busca
if st.button("🔍 Buscar Passagens"):
    results = search_flights(origin, destination, departure_date, adults)

    if "data" in results:
        st.subheader("Resultados encontrados:")
        for offer in results["data"]:
            price = offer["price"]["total"]
            currency = offer["price"]["currency"]
            itinerary = offer["itineraries"][0]["segments"]
            st.markdown(f"💰 **Preço:** {price} {currency}")
            for seg in itinerary:
                st.write(f"{seg['departure']['iataCode']} → {seg['arrival']['iataCode']} | "
                         f"{seg['departure']['at']} → {seg['arrival']['at']}")
            st.markdown("---")
    else:
        st.error("Nenhum voo encontrado. Tente outras datas ou aeroportos.")
