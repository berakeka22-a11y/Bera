import streamlit as st
import os
from amadeus import Client, ResponseError

# Inicializa cliente Amadeus com as chaves do secrets
amadeus = Client(
    client_id=os.getenv("AMADEUS_CLIENT_ID"),
    client_secret=os.getenv("AMADEUS_CLIENT_SECRET")
)

st.set_page_config(page_title="✈️ Buscador de Passagens", layout="wide")

st.title("✈️ Buscador de Passagens Aéreas")
st.write("Encontre voos baratos usando a API da Amadeus")

# Dicionário de cidades e aeroportos
CIDADES_AEROPORTOS = {
    "São Paulo": ["GRU", "CGH", "VCP"],  # Guarulhos, Congonhas, Viracopos
    "Rio de Janeiro": ["GIG", "SDU"],    # Galeão, Santos Dumont
    "Belo Horizonte": ["CNF", "PLU"],    # Confins, Pampulha
    "Brasília": ["BSB"],
    "Salvador": ["SSA"],
    "Recife": ["REC"],
    "Fortaleza": ["FOR"],
    "Maceió": ["MCZ"],
    "Porto Alegre": ["POA"],
    "Curitiba": ["CWB"],
    "Florianópolis": ["FLN"]
}

# Entrada de dados
col1, col2 = st.columns(2)

with col1:
    cidade_origem = st.selectbox("Origem (cidade)", list(CIDADES_AEROPORTOS.keys()))
    aeroportos_origem = CIDADES_AEROPORTOS[cidade_origem]
    origem = st.selectbox("Selecione o aeroporto de origem", ["Todos"] + aeroportos_origem)

with col2:
    cidade_destino = st.selectbox("Destino (cidade)", list(CIDADES_AEROPORTOS.keys()))
    aeroportos_destino = CIDADES_AEROPORTOS[cidade_destino]
    destino = st.selectbox("Selecione o aeroporto de destino", ["Todos"] + aeroportos_destino)

data_ida = st.date_input("Data de ida")
ida_e_volta = st.checkbox("Viagem de ida e volta?")

data_volta = None
if ida_e_volta:
    data_volta = st.date_input("Data de volta")

# Botão para buscar voos
if st.button("🔍 Buscar Passagens"):
    origem_codes = aeroportos_origem if origem == "Todos" else [origem]
    destino_codes = aeroportos_destino if destino == "Todos" else [destino]

    st.write("### Resultados da busca:")

    try:
        for o in origem_codes:
            for d in destino_codes:
                response = amadeus.shopping.flight_offers_search.get(
                    originLocationCode=o,
                    destinationLocationCode=d,
                    departureDate=str(data_ida),
                    returnDate=str(data_volta) if data_volta else None,
                    adults=1,
                    max=5,
                    currencyCode="BRL"
                )

                results = response.data
                if not results:
                    st.warning(f"Nenhum voo encontrado de {o} para {d}")
                    continue

                for r in results:
                    preco = r["price"]["total"]
                    companhia = r["itineraries"][0]["segments"][0]["carrierCode"]
                    partida = r["itineraries"][0]["segments"][0]["departure"]["at"]
                    chegada = r["itineraries"][0]["segments"][-1]["arrival"]["at"]

                    with st.container():
                        st.markdown(
                            f"""
                            <div style="padding:15px; border-radius:10px; background:#f8f9fa; margin-bottom:10px; box-shadow: 0 2px 5px rgba(0,0,0,0.1)">
                                <b>🛫 {o} → {d}</b><br>
                                📅 Ida: {partida}<br>
                                {"📅 Volta: " + chegada if ida_e_volta else ""}<br>
                                🏷️ Companhia: {companhia}<br>
                                💰 Preço: R$ {preco}
                            </div>
                            """,
                            unsafe_allow_html=True
                        )

    except ResponseError as error:
        st.error(f"Erro na busca: {error}")
