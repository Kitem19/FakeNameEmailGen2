# -*- coding: utf-8 -*-
import random
import string
import requests
import pandas as pd
import streamlit as st
from faker import Faker

st.set_page_config(page_title="Generatore di Profili Multi-Provider", page_icon="🔀", layout="centered")

PREDEFINED_IBANS = {
    'IT': ['IT60X0542811101000000123456', 'IT12A0306912345100000067890'],
    'FR': ['FR1420041010050500013M02606', 'FR7630006000011234567890189'],
    'DE': ['DE89370400440532013000', 'DE02100100100006820101'],
    'LU': ['LU280019400644750000', 'LU120010001234567891']
}
USER_AGENT_HEADER = {
    'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'
}

# --------------------- GUERRILLA MAIL ---------------------

def create_guerrillamail_account():
    try:
        r = requests.get(
            "https://api.guerrillamail.com/ajax.php?f=get_email_address",
            headers=USER_AGENT_HEADER)
        r.raise_for_status()
        data = r.json()
        return {"address": data['email_addr'], "sid_token": data['sid_token'], "provider": "Guerrilla Mail"}
    except Exception as e:
        st.error(f"Errore Guerrilla Mail: {e}")
        return None

def inbox_guerrillamail(info):
    st.subheader(f"📬 Inbox per [{info['address']}] (Guerrilla Mail)")
    if st.button("🔁 Controlla inbox (Guerrilla Mail)"):
        with st.spinner("Recupero messaggi..."):
            try:
                r = requests.get(
                    f"https://api.guerrillamail.com/ajax.php?f=check_email&seq=0&sid_token={info['sid_token']}",
                    headers=USER_AGENT_HEADER
                )
                r.raise_for_status()
                messages = r.json().get("list", [])
                if not messages:
                    st.info("📭 Nessun messaggio trovato.")
                    return
                st.success(f"Trovati {len(messages)} messaggi.")
                for m in reversed(messages):
                    with st.expander(f"✉️ **Da:** {m['mail_from']} | **Oggetto:** {m['mail_subject']}"):
                        full_email_resp = requests.get(
                            f"https://api.guerrillamail.com/ajax.php?f=fetch_email&email_id={m['mail_id']}&sid_token={info['sid_token']}",
                            headers=USER_AGENT_HEADER)
                        email_body = full_email_resp.json().get('mail_body', '<i>Corpo non disponibile.</i>')
                        st.components.v1.html(email_body, height=400, scrolling=True)
            except Exception as e:
                st.error(f"Errore lettura posta Guerrilla Mail: {e}")

# --------------------- FAKEMAIL (esempio base) ---------------------

def create_fakemail_account():
    # Fakemail.net usa tipicamente indirizzi username@fakemail.net
    username = ''.join(random.choices(string.ascii_lowercase + string.digits, k=10))
    domain = "fakemail.net"
    address = f"{username}@{domain}"
    return {"address": address, "username": username, "provider": "Fakemail"}

def inbox_fakemail(info):
    st.subheader(f"📬 Inbox per [{info['address']}] (Fakemail)")
    if st.button("🔁 Controlla inbox (Fakemail)"):
        with st.spinner("Recupero messaggi (scraping da implementare)..."):
            try:
                inbox_url = f"https://fakemail.net/inbox/{info['username']}"
                resp = requests.get(inbox_url, headers=USER_AGENT_HEADER)
                resp.raise_for_status()
                # TODO: Implementare parsing dettagliato con BeautifulSoup
                st.write("La funzione di parsing della inbox di Fakemail non è ancora implementata.")
                st.write("HTML ricevuto (prime 500 caratteri):")
                st.code(resp.text[:500], language='html')
            except Exception as e:
                st.error(f"Errore lettura posta Fakemail: {e}")

# --------------------- DISPOSABLEEMAIL (esempio base) ---------------------

def create_disposableemail_account():
    username = ''.join(random.choices(string.ascii_lowercase + string.digits, k=10))
    domain = "tempmailo.com"  # Cambia con dominio reale supportato dal servizio che userai
    address = f"{username}@{domain}"
    return {"address": address, "username": username, "provider": "DisposableEmail"}

def inbox_disposableemail(info):
    st.subheader(f"📬 Inbox per [{info['address']}] (DisposableEmail)")
    if st.button("🔁 Controlla inbox (DisposableEmail)"):
        with st.spinner("Recupero messaggi (da implementare)..."):
            try:
                # Inserisci qui chiamata API o scraping per recuperare messaggi
                st.write("La funzione di lettura inbox DisposableEmail non è implementata.")
                # Es. potresti usare requests.get() su endpoint API
            except Exception as e:
                st.error(f"Errore lettura posta DisposableEmail: {e}")

# ------- PROVIDER CHOICE MAPPING -------

PROVIDERS = {
    "Guerrilla Mail": (create_guerrillamail_account, inbox_guerrillamail),
    "Fakemail": (create_fakemail_account, inbox_fakemail),
    "DisposableEmail": (create_disposableemail_account, inbox_disposableemail)
}

# ---------- PROFILE GENERATOR ----------

def generate_profile(country, extra_fields, provider):
    locs = {'Italia': 'it_IT', 'Francia': 'fr_FR', 'Germania': 'de_DE', 'Lussemburgo': 'fr_LU'}
    codes = {'Italia': 'IT', 'Francia': 'FR', 'Germania': 'DE', 'Lussemburgo': 'LU'}
    fake = Faker(locs[country])
    profile = {
        'Nome': fake.first_name(),
        'Cognome': fake.last_name(),
        'Data di Nascita': fake.date_of_birth(minimum_age=18, maximum_age=80).strftime('%d/%m/%Y'),
        'Indirizzo': fake.address().replace("\n", ", "),
        'IBAN': get_next_iban(codes[country]),
        'Paese': country
    }

    if 'Email' in extra_fields:
        create_func, _ = PROVIDERS[provider]
        result = create_func()
        if not result or not result.get("address"):
            profile["Email"] = "Creazione email fallita"
            st.session_state.email_info = None
        else:
            profile["Email"] = result["address"]
            st.session_state.email_info = result
    if 'Telefono' in extra_fields:
        profile['Telefono'] = fake.phone_number()
    if 'Codice Fiscale' in extra_fields:
        try:
            profile['Codice Fiscale'] = fake.ssn() if locs[country] == 'it_IT' else 'N/A'
        except Exception:
            profile['Codice Fiscale'] = 'N/A'
    if 'Partita IVA' in extra_fields:
        try:
            profile['Partita IVA'] = fake.vat_id() if hasattr(fake, 'vat_id') else 'N/A'
        except Exception:
            profile['Partita IVA'] = 'N/A'
    return pd.DataFrame([profile])

def get_next_iban(cc):
    cc = cc.upper()
    if 'iban_state' not in st.session_state:
        st.session_state.iban_state = {}
    if cc not in st.session_state.iban_state or st.session_state.iban_state[cc]['index'] >= len(st.session_state.iban_state[cc]['list']):
        lst = PREDEFINED_IBANS.get(cc, ["N/A"])
        random.shuffle(lst)
        st.session_state.iban_state[cc] = {'list': lst, 'index': 0}
    st.session_state.iban_state[cc]['index'] += 1
    return st.session_state.iban_state[cc]['list'][st.session_state.iban_state[cc]['index'] - 1]

# ----------------------------------- UI ------------------------------------

st.title("🔀 Generatore di Profili Multi-Provider")
st.markdown("Genera profili fittizi e scegli tra diversi servizi di email temporanee.")

if 'final_df' not in st.session_state:
    st.session_state.final_df = None
if 'email_info' not in st.session_state:
    st.session_state.email_info = None

with st.sidebar:
    st.header("⚙️ Opzioni Generali")
    country = st.selectbox("Paese", ["Italia", "Francia", "Germania", "Lussemburgo"])
    n = st.number_input("Numero di profili", 1, 25, 1)
    fields = st.multiselect(
        "Campi aggiuntivi",
        ["Email", "Telefono", "Codice Fiscale", "Partita IVA"],
        default=["Email"]
    )
    st.header("📧 Opzioni Email")
    selected_provider = st.selectbox("Scegli il provider email", list(PROVIDERS.keys()))
    if st.button("🚀 Genera Profili", type="primary"):
        with st.spinner("Generazione in corso..."):
            dfs = [generate_profile(country, fields, selected_provider) for _ in range(n)]
        st.session_state.final_df = pd.concat([df for df in dfs if not df.empty], ignore_index=True)

if st.session_state.final_df is not None:
    st.success(f"✅ Generati {len(st.session_state.final_df)} profili.")
    st.dataframe(st.session_state.final_df)
    csv = st.session_state.final_df.to_csv(index=False, encoding='utf-8-sig').encode('utf-8-sig')
    st.download_button("📥 Scarica CSV", csv, "profili.csv", "text/csv")

    info = st.session_state.email_info
    if ('Email' in st.session_state.final_df.columns and info and
        "fallita" not in str(info.get("address", "")).lower()):
        _, inbox_func = PROVIDERS[info['provider']]
        inbox_func(info)
