import streamlit as st
import requests
import datetime

# 🔑 Credenciais (configure no Streamlit Secrets)
AMADEUS_API_KEY = st.secrets["AMADEUS_API_KEY"]
AMADEUS_API_SECRET = st.secrets["AMADEUS_API_SECRET"]

# 🌍 Endpoints da Amadeus
TOKEN_URL = "https://test.api.amadeus.com/v1/security/oauth2/token"
AIRPORTS_URL = "https://test.api.amadeus.com/v1/reference-data/locations"
FLIGHTS_URL = "https://test.api.amadeus.com/v2/shopping/flight-offers"

# 🔑 Obter token de acesso
@st.cache_data
def get_access_token():
    data = {
        "grant_type": "client_credentials",
        "client_id": AMADEUS_API_KEY,
        "client_secret": AMADEUS_API_SECRET
    }
    response = requests.post(TOKEN_URL, data=data)
    return response.json().get("access_token")

# 🔎 Buscar aeroportos
def search_airports(keyword, token):
    params = {"subType": "AIRPORT", "keyword": keyword}
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(AIRPORTS_URL, headers=headers, params=params)
    if response.status_code == 200:
        return response.json().get("data", [])
    return []

# ✈️ Buscar voos
def search_flights(origins, destination, departure_date, adults, token, return_date=None):
    results = []
    for origin in origins:
        params = {
            "originLocationCode": origin,
            "destinationLocationCode": destination,
            "departureDate": departure_date,
            "adults": adults,
            "currencyCode": "BRL"
        }
        if return_date:
            params["returnDate"] = return_date
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(FLIGHTS_URL, headers=headers, params=params)
        if response.status_code == 200:
            results.extend(response.json().get("data", []))
    return results

# ⏱️ Calcular duração em horas:min
def format_duration(iso_duration):
    try:
        hours = int(iso_duration[2:iso_duration.index("H")]) if "H" in iso_duration else 0
        minutes = int(iso_duration.split("H")[-1].replace("M", "")) if "M" in iso_duration else 0
        return f"{hours}h {minutes}m"
    except:
        return iso_duration

# 🚀 Interface do app
st.set_page_config(page_title="Buscador de Passagens", page_icon="✈️", layout="wide")
st.title("✈️ Buscador de Passagens Aéreas")
st.write("Encontre voos baratos usando a API da Amadeus")

token = get_access_token()

# Origem
origem_input = st.text_input("Origem (cidade ou aeroporto)", "São Paulo")
aeroportos_origem = search_airports(origem_input, token)

origem_opcoes = []
if aeroportos_origem:
    origem_opcoes.append("Todos os aeroportos")
    origem_opcoes.extend([f"{a['iataCode']} – {a['name']}" for a in aeroportos_origem])

origem_escolha = st.selectbox("Selecione origem", origem_opcoes)
if origem_escolha == "Todos os aeroportos":
    origem_codes = [a['iataCode'] for a in aeroportos_origem]
else:
    origem_codes = [origem_escolha.split(" – ")[0]]

# Destino
destino_input = st.text_input("Destino (cidade ou aeroporto)", "Fortaleza")
aeroportos_destino = search_airports(destino_input, token)

destino_opcoes = []
if aeroportos_destino:
    destino_opcoes.append("Todos os aeroportos")
    destino_opcoes.extend([f"{a['iataCode']} – {a['name']}" for a in aeroportos_destino])

destino_escolha = st.selectbox("Selecione destino", destino_opcoes)
if destino_escolha == "Todos os aeroportos":
    destino_codes = [a['iataCode'] for a in aeroportos_destino]
else:
    destino_codes = [destino_escolha.split(" – ")[0]]

# Datas
col1, col2 = st.columns(2)
with col1:
    data_partida = st.date_input("Data de partida", datetime.date.today() + datetime.timedelta(days=7))
with col2:
    ida_volta = st.checkbox("Incluir volta?")
    data_volta = None
    if ida_volta:
        data_volta = st.date_input("Data de volta", datetime.date.today() + datetime.timedelta(days=14))

# Passageiros
adultos = st.number_input("Quantidade de adultos", min_value=1, value=1)

# Buscar
if st.button("🔍 Buscar Passagens"):
    if origem_codes and destino_codes:
        resultados = []
        for destino_code in destino_codes:
            resultados.extend(search_flights(origem_codes, destino_code, str(data_partida), adultos, token, str(data_volta) if data_volta else None))

        if resultados:
            st.subheader(f"Resultados encontrados ({len(resultados)} opções):")

            for voo in resultados[:10]:  # mostra até 10 voos
                preco = voo["price"]["total"]
                moeda = voo["price"]["currency"]

                itinerario = voo["itineraries"][0]
                partida = itinerario["segments"][0]["departure"]
                chegada = itinerario["segments"][-1]["arrival"]

                horario_partida = partida["at"].replace("T", " ")
                horario_chegada = chegada["at"].replace("T", " ")
                duracao = format_duration(itinerario["duration"])

                companhia = voo["validatingAirlineCodes"][0] if "validatingAirlineCodes" in voo else "N/A"

                # Card
                with st.container():
                    st.markdown(
                        f"""
                        <div style="padding:15px; margin-bottom:10px; border-radius:10px; 
                            box-shadow:0px 2px 6px rgba(0,0,0,0.1); background:white;">
                            <h4>{partida['iataCode']} → {chegada['iataCode']}</h4>
                            <p>🛫 <b>Partida:</b> {horario_partida}</p>
                            <p>🛬 <b>Chegada:</b> {horario_chegada}</p>
                            <p>⏱️ <b>Duração:</b> {duracao}</p>
                            <p>✈️ <b>Companhia:</b> {companhia}</p>
                            <h3 style="color:#007bff;">💰 {preco} {moeda}</h3>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )
        else:
            st.warning("Nenhum voo encontrado para os critérios selecionados.")
    else:
        st.error("Por favor, selecione origem e destino.")
