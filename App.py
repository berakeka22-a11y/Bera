import streamlit as st
from amadeus import Client, ResponseError
import datetime

# Inicializa cliente Amadeus com as chaves salvas no secrets do Streamlit
amadeus = Client(
    client_id=st.secrets["AMADEUS_API_KEY"],
    client_secret=st.secrets["AMADEUS_API_SECRET"]
)

st.set_page_config(page_title="✈️ Buscador de Passagens Aéreas", layout="wide")

st.title("✈️ Buscador de Passagens Aéreas")
st.write("Encontre voos baratos usando a API da Amadeus.")

# Dicionário de cidades e aeroportos
CIDADES_AEROPORTOS = {
    "São Paulo": ["GRU", "CGH", "VCP"],  # Guarulhos, Congonhas, Viracopos
    "Rio de Janeiro": ["GIG", "SDU"],    # Galeão, Santos Dumont
    "Brasília": ["BSB"],
    "Salvador": ["SSA"],
    "Fortaleza": ["FOR"],
    "Belo Horizonte": ["CNF"],
    "Recife": ["REC"],
    "Curitiba": ["CWB"],
    "Porto Alegre": ["POA"],
    "Maceió": ["MCZ"]
}

# Seleção de origem e destino
origem = st.selectbox("Origem", list(CIDADES_AEROPORTOS.keys()))
destino = st.selectbox("Destino", list(CIDADES_AEROPORTOS.keys()))

# Opções de datas
col1, col2 = st.columns(2)
with col1:
    data_ida = st.date_input("Data de Ida", min_value=datetime.date.today())
with col2:
    incluir_volta = st.checkbox("Incluir volta?")
    data_volta = None
    if incluir_volta:
        data_volta = st.date_input("Data de Volta", min_value=data_ida)

# Botão para buscar voos
if st.button("🔎 Buscar Passagens"):
    aeroportos_origem = CIDADES_AEROPORTOS[origem]
    aeroportos_destino = CIDADES_AEROPORTOS[destino]

    st.info(f"Buscando voos de **{origem} ({', '.join(aeroportos_origem)})** para **{destino} ({', '.join(aeroportos_destino)})**")

    try:
        # Lista para armazenar os resultados
        resultados = []

        for o in aeroportos_origem:
            for d in aeroportos_destino:
                try:
                    response = amadeus.shopping.flight_offers_search.get(
                        originLocationCode=o,
                        destinationLocationCode=d,
                        departureDate=data_ida.strftime("%Y-%m-%d"),
                        returnDate=data_volta.strftime("%Y-%m-%d") if data_volta else None,
                        adults=1,
                        currencyCode="BRL",
                        max=5
                    )
                    for r in response.data:
                        preco = r["price"]["total"]
                        moeda = r["price"]["currency"]
                        duracao = r["itineraries"][0]["duration"]
                        resultados.append(f"🛫 {o} → {d} | 💲 {preco} {moeda} | ⏱ {duracao}")
                except Exception:
                    pass

        if resultados:
            st.success("✅ Voos encontrados:")
            for r in resultados:
                st.write(r)
        else:
            st.warning("Nenhum voo encontrado para os critérios escolhidos.")

    except ResponseError as error:
        st.error(f"Erro ao buscar voos: {error}")
