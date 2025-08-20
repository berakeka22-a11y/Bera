# app.py
import os
import datetime as dt
import requests
import streamlit as st

# =========================
# Config & tema
# =========================
st.set_page_config(
    page_title="✈️ Buscador de Passagens",
    page_icon="✈️",
    layout="centered",
)

ACCENT = "#22c55e"
st.markdown(
    f"""
    <style>
      .stApp {{ background: #0f172a; color: #e2e8f0; }}
      .stTextInput > div > div input, .stNumberInput input, .stDateInput input {{
          background: #1e293b; color: #e2e8f0; border-radius: 12px;
      }}
      .stSelectbox > div > div {{ background: #1e293b; color: #e2e8f0; border-radius: 12px; }}
      .stButton>button {{
          background:{ACCENT}; color:#0b1220; border:0; border-radius:12px; padding:0.6rem 1rem; font-weight:700;
      }}
      .price {{ font-size:28px; font-weight:800; color:{ACCENT}; }}
      .card {{ border:1px solid #334155; border-radius:16px; padding:14px; background:#0b1220; }}
      .muted {{ color:#94a3b8 }}
      a.buy {{ text-decoration:none; background:#3b82f6; color:white; padding:8px 12px; border-radius:10px; font-weight:700; }}
      a.buy:hover {{ opacity:.9 }}
    </style>
    """,
    unsafe_allow_html=True,
)

# =========================
# Credenciais Amadeus
# =========================
AMADEUS_CLIENT_ID = st.secrets.get("AMADEUS_CLIENT_ID", os.getenv("AMADEUS_CLIENT_ID"))
AMADEUS_CLIENT_SECRET = st.secrets.get("AMADEUS_CLIENT_SECRET", os.getenv("AMADEUS_CLIENT_SECRET"))
AMADEUS_HOST = "https://test.api.amadeus.com"

if not AMADEUS_CLIENT_ID or not AMADEUS_CLIENT_SECRET:
    st.error("⚠️ Adicione suas chaves Amadeus em *Settings › Secrets* como `AMADEUS_CLIENT_ID` e `AMADEUS_CLIENT_SECRET`.")
    st.stop()

# =========================
# Helpers Amadeus
# =========================
@st.cache_data(ttl=60 * 25)
def get_access_token() -> str:
    url = f"{AMADEUS_HOST}/v1/security/oauth2/token"
    data = {
        "grant_type": "client_credentials",
        "client_id": AMADEUS_CLIENT_ID,
        "client_secret": AMADEUS_CLIENT_SECRET,
    }
    r = requests.post(url, data=data, timeout=30)
    r.raise_for_status()
    return r.json()["access_token"]

def _headers():
    return {"Authorization": f"Bearer {get_access_token()}"}

@st.cache_data(ttl=60 * 60)
def search_locations(keyword: str):
    if not keyword or len(keyword) < 2:
        return []
    url = f"{AMADEUS_HOST}/v1/reference-data/locations"
    params = {"subType": "CITY,AIRPORT", "keyword": keyword, "view": "LIGHT", "page[limit]": 10}
    r = requests.get(url, headers=_headers(), params=params, timeout=30)
    if r.status_code != 200:
        return []
    data = r.json().get("data", [])
    data.sort(key=lambda x: (x.get("subType") != "AIRPORT", x.get("name", "")))
    return data

def fmt_duration(iso: str) -> str:
    if not iso or not iso.startswith("PT"):
        return ""
    iso = iso[2:]
    h, m = 0, 0
    if "H" in iso:
        parts = iso.split("H")
        h = int(parts[0]) if parts[0] else 0
        iso = parts[1] if len(parts) > 1 else ""
    if "M" in iso:
        parts = iso.split("M")
        m = int(parts[0]) if parts[0] else 0
    return f"{h}h{m:02d}"

def google_flights_link(origin: str, dest: str, date: str, adults: int) -> str:
    return f"https://www.google.com/travel/flights?q=Flights%20from%20{origin}%20to%20{dest}%20on%20{date}%20adults%3D{adults}"

@st.cache_data(ttl=60)
def search_offers(origin, destination, date, adults=1, currency="BRL", non_stop=False, max_results=20):
    url = f"{AMADEUS_HOST}/v2/shopping/flight-offers"
    params = {
        "originLocationCode": origin,
        "destinationLocationCode": destination,
        "departureDate": date,
        "adults": adults,
        "currencyCode": currency,
        "max": max_results,
    }
    if non_stop:
        params["nonStop"] = "true"
    r = requests.get(url, headers=_headers(), params=params, timeout=60)
    if r.status_code != 200:
        return {"error": r.text}
    return r.json()

# =========================
# UI
# =========================
st.title("✈️ Buscador de Passagens Aéreas")

with st.form("search"):
    col1, col2 = st.columns(2)
    with col1:
        origin_text = st.text_input("Origem (cidade ou aeroporto)", value="São Paulo")
        origin_matches = search_locations(origin_text)
        origin_choice = st.selectbox("Selecione origem", [f"{x['iataCode']} — {x['name']}" for x in origin_matches] or [""])
    with col2:
        dest_text = st.text_input("Destino (cidade ou aeroporto)", value="Maceió")
        dest_matches = search_locations(dest_text)
        dest_choice = st.selectbox("Selecione destino", [f"{x['iataCode']} — {x['name']}" for x in dest_matches] or [""])

    col3, col4, col5 = st.columns([1, 1, 1])
    with col3:
        date = st.date_input("Data de partida", value=(dt.date.today() + dt.timedelta(days=21)))
    with col4:
        adults = st.number_input("Adultos", 1, 9, 1)
    with col5:
        currency = st.selectbox("Moeda", ["BRL", "USD", "EUR"], index=0)

    non_stop = st.checkbox("Somente voos diretos", value=False)
    submitted = st.form_submit_button("🔎 Buscar")

def extract_iata(selection: str) -> str:
    return selection.split("—")[0].strip() if selection and "—" in selection else ""

if submitted:
    origin_iata = extract_iata(origin_choice)
    dest_iata = extract_iata(dest_choice)
    date_str = date.strftime("%Y-%m-%d")

    if not origin_iata or not dest_iata:
        st.warning("Selecione origem e destino válidos.")
        st.stop()

    with st.spinner("Buscando voos..."):
        resp = search_offers(origin_iata, dest_iata, date_str, adults, currency, non_stop)

    if "error" in resp:
        st.error("Erro: " + resp["error"])
        st.stop()

    offers = resp.get("data", [])
    if not offers:
        st.info("Nenhum voo encontrado.")
        st.stop()

    offers.sort(key=lambda o: float(o["price"]["grandTotal"]))
    for of in offers:
        total = of["price"]["grandTotal"]
        currency_code = of["price"]["currency"]
        it = of["itineraries"][0]
        duration = fmt_duration(it.get("duration", ""))
        segs = it.get("segments", [])
        legs = [f"{s['departure']['iataCode']} → {s['arrival']['iataCode']} ({fmt_duration(s.get('duration',''))})" for s in segs]
        stops = len(segs) - 1

        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown(f'<div class="price">{currency_code} {float(total):,.2f}</div>'.replace(",", "X").replace(".", ",").replace("X", "."), unsafe_allow_html=True)
        st.markdown(f"<div class='muted'>{'Direto' if stops==0 else f'{stops} escala(s)'} • {duration}</div>", unsafe_allow_html=True)
        st.markdown(" · ".join(legs))
        url = google_flights_link(origin_iata, dest_iata, date_str, adults)
        st.markdown(f"[Abrir no Google Flights]({url}){{: .buy }}", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
        st.markdown("")
