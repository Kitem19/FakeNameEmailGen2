# -*- coding: utf-8 -*-
import random
import string
import requests
import pandas as pd
import streamlit as st
from faker import Faker
import hashlib
from bs4 import BeautifulSoup

st.set_page_config(page_title="Generatore di Profili Multi-Provider", page_icon="🔀", layout="centered")

PREDEFINED_IBANS = {
    'IT': ['IT60X0542811101000000123456', 'IT12A0306912345100000067890'],
    'FR': ['FR1420041010050500013M02606', 'FR7630006000011234567890189'],
    'DE': ['DE89370400440532013000', 'DE02100100100006820101'],
    'LU': ['LU280019400644750000', 'LU120010001234567891']
}
USER_AGENT_HEADER = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'}

# ------------------------------- PROVIDER: GUERRILLA MAIL --------------------------------
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
    st.subheader(f"📬 Inbox per [{info['address']}]")
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

# ----------------------------- PROVIDER: YOPMAIL [solo GET!] ----------------------------
def create_yopmail_account():
    username = ''.join(random.choices(string.ascii_lowercase + string.digits, k=10))
    address = f"{username}@yopmail.com"
    return {"address": address, "provider": "YOPmail"}

def inbox_yopmail(info):
    st.subheader(f"📬 Inbox per [{info['address']}]")
    if st.button("🔁 Controlla inbox (YOPmail)"):
        with st.spinner("Recupero messaggi da YOPmail.com..."):
            try:
                username = info['address'].split('@')[0]
                inbox_url = f"https://yopmail.com/en/{username}"
                inbox_page = requests.get(inbox_url, headers=USER_AGENT_HEADER)
                inbox_page.raise_for_status()
                soup = BeautifulSoup(inbox_page.text, 'lxml')
                messages = soup.find_all('div', class_='m')
                if not messages:
                    st.info("📭 Nessun messaggio trovato.")
                    return
                st.success(f"Trovati {len(messages)} messaggi.")
                for m in reversed(messages):
                    try:
                        sender = m.find('span', class_='s_from').text if m.find('span', class_='s_from') else "(sconosciuto)"
                        subject = m.find('span', class_='s_subject').text if m.find('span', class_='s_subject') else "(nessun oggetto)"
                        href = m.find('a')['href'] if m.find('a') else ""
                        email_id = href.split('id=')[1] if 'id=' in href else None
                        if not email_id:
                            continue
                        with st.expander(f"✉️ **Da:** {sender} | **Oggetto:** {subject}"):
                            with st.spinner("Caricamento corpo del messaggio..."):
                                mail_page = requests.get(f"https://www.yopmail.com/en/mail?id={email_id}", headers=USER_AGENT_HEADER)
                                mail_page.raise_for_status()
                                mail_soup = BeautifulSoup(mail_page.text, 'lxml')
                                email_body = mail_soup.find('div', id='mail')
                                st.components.v1.html(str(email_body) if email_body else "<i>Corpo non disponibile.</i>", height=400, scrolling=True)
                    except Exception:
                        st.warning("Messaggio non completamente leggibile.")
            except Exception as e:
                st.error(f"Errore scraping YOPmail: {e}")

# ------------------------- PROVIDER: TEMP-MAIL.ORG via RapidAPI -------------------------
def create_tempmail_account():
    domain = random.choice(["greencafe24.com", "chacuo.net"])
    username = ''.join(random.choices(string.ascii_lowercase + string.digits, k=10))
    return {"address": f"{username}@{domain}", "provider": "Temp-Mail.org"}

def inbox_tempmail(info):
    st.subheader(f"📬 Inbox per [{info['address']}]")
    if st.button("🔁 Controlla inbox (Temp-Mail.org)"):
        with st.spinner("Recupero messaggi..."):
            api_key = st.secrets.get("rapidapi", {}).get("key")
            if not api_key:
                st.error("Chiave API non configurata!")
                return
            url = f"https://privatix-temp-mail-v1.p.rapidapi.com/request/mail/id/{hashlib.md5(info['address'].encode('utf-8')).hexdigest()}/"
            headers = {"X-RapidAPI-Key": api_key, "X-RapidAPI-Host": "privatix-temp-mail-v1.p.rapidapi.com"}
            try:
                r = requests.get(url, headers=headers)
                r.raise_for_status()
                messages = r.json()
                if not isinstance(messages, list):
                    st.error(f"Risposta inattesa dall'API: {messages}")
                    return
                if not messages:
                    st.info("📭 Nessun messaggio trovato.")
                    return
                st.success(f"Trovati {len(messages)} messaggi.")
                for m in reversed(messages):
                    with st.expander(f"✉️ **Da:** {m['mail_from']} | **Oggetto:** {m['mail_subject']}"):
                        email_body = m.get('mail_html') or m.get('mail_text') or "<i>Corpo non disponibile.</i>"
                        st.components.v1.html(email_body, height=400, scrolling=True)
            except Exception as e:
                st.error(f"Errore lettura posta Temp-Mail: {e}")

# ----------------------------------- MAPPATURA PROVIDERS ---------------------------------
PROVIDERS = {
    "Guerrilla Mail": (create_guerrillamail_account, inbox_guerrillamail),
    "YOPmail": (create_yopmail_account, inbox_yopmail),
    "Temp-Mail.org": (create_tempmail_account, inbox_tempmail)
}

# ------------------------------------- PROFILE GENERATOR ---------------------------------
def generate_profile(country, extra_fields, provider):
    locs = {'Italia': 'it_IT', 'Francia': 'fr_FR', 'Germania': 'de_DE', 'Lussemburgo': 'fr_LU'}
    codes = {'Italia': 'IT', 'Francia': 'FR', 'Germania': 'DE', 'Lussemburgo': 'LU'}
    fake = Faker(locs[country])
    p = {
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
            p["Email"] = "Creazione email fallita"
            st.session_state.email_info = None
        else:
            p["Email"] = result["address"]
            st.session_state.email_info = result
    if 'Telefono' in extra_fields:
        p['Telefono'] = fake.phone_number()
    if 'Codice Fiscale' in extra_fields:
        try:
            p['Codice Fiscale'] = fake.ssn() if locs[country] == 'it_IT' else 'N/A'
        except Exception:
            p['Codice Fiscale'] = 'N/A'
    if 'Partita IVA' in extra_fields:
        try:
            p['Partita IVA'] = fake.vat_id() if hasattr(fake, 'vat_id') else 'N/A'
        except Exception:
            p['Partita IVA'] = 'N/A'
    return pd.DataFrame([p])

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

# ----------------------------------------- UI --------------------------------------------
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
    is_button_disabled = False
    if selected_provider == "Temp-Mail.org":
        if not st.secrets.get("rapidapi", {}).get("key"):
            st.error("Per usare Temp-Mail.org, imposta la chiave API nei Secrets.")
            is_button_disabled = True
    if st.button("🚀 Genera Profili", type="primary", disabled=is_button_disabled):
        with st.spinner("Generazione in corso..."):
            dfs = [generate_profile(country, fields, selected_provider) for _ in range(n)]
        st.session_state.final_df = pd.concat([df for df in dfs if not df.empty], ignore_index=True)

if st.session_state.final_df is not None:
    st.success(f"✅ Generati {len(st.session_state.final_df)} profili.")
    st.dataframe(st.session_state.final_df)
    csv = st.session_state.final_df.to_csv(index=False, encoding='utf-8-sig').encode('utf-8-sig')
    st.download_button("📥 Scarica CSV", csv, "profili.csv", "text/csv")
    info = st.session_state.email_info
    # Mostra inbox solo se la mail è OK
    if 'Email' in st.session_state.final_df.columns and info and "fallita" not in str(info.get("address", "")).lower():
        _, inbox_func = PROVIDERS[info['provider']]
        inbox_func(info)
