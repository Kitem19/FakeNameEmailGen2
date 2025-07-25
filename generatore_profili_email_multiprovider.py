# -*- coding: utf-8 -*-
import random
import string
import requests
import pandas as pd
import streamlit as st
from faker import Faker
import time
import hashlib
import json

# --- CONFIGURAZIONE PAGINA ---
st.set_page_config(page_title="Generatore di Profili Affidabile", page_icon="✅", layout="centered")

# --- COSTANTI E DATI PREDEFINITI ---
PREDEFINED_IBANS = {
    'IT': ['IT60X0542811101000000123456', 'IT12A0306912345100000067890'],
    'FR': ['FR1420041010050500013M02606', 'FR7630006000011234567890189'],
    'DE': ['DE89370400440532013000', 'DE02100100100006820101'],
    'LU': ['LU280019400644750000', 'LU120010001234567891']
}
TEMPMAIL_DOMAINS = ["greencafe24.com", "chacuo.net", "fexpost.com", "shop.megantv.com"]

# ==============================================================================
#                      FUNZIONI API PER OGNI PROVIDER
# ==============================================================================

# --- Provider 1: Guerrilla Mail (Stabile, non richiede chiave) ---
def create_guerrillamail_account():
    try:
        r = requests.get("https://api.guerrillamail.com/ajax.php?f=get_email_address")
        r.raise_for_status()
        data = r.json()
        return {"address": data['email_addr'], "sid_token": data['sid_token'], "provider": "Guerrilla Mail"}
    except requests.exceptions.RequestException as e:
        st.error(f"Errore Guerrilla Mail: {e}"); return None

def inbox_guerrillamail(info):
    st.subheader(f"📬 Inbox per [{info['address']}]")
    if st.button("🔁 Controlla inbox (Guerrilla Mail)"):
        with st.spinner("Recupero messaggi..."):
            try:
                r = requests.get(f"https://api.guerrillamail.com/ajax.php?f=check_email&seq=0&sid_token={info['sid_token']}")
                r.raise_for_status()
                messages = r.json().get("list", [])
                if not messages: st.info("📭 Nessun messaggio trovato."); return
                st.success(f"Trovati {len(messages)} messaggi.")
                for m in reversed(messages):
                    with st.expander(f"✉️ **Da:** {m['mail_from']} | **Oggetto:** {m['mail_subject']}"):
                        email_id = m['mail_id']
                        full_email_resp = requests.get(f"https://api.guerrillamail.com/ajax.php?f=fetch_email&email_id={email_id}&sid_token={info['sid_token']}")
                        full_email_data = full_email_resp.json()
                        timestamp = int(m['mail_timestamp'])
                        date_str = time.strftime('%d/%m/%Y %H:%M:%S', time.localtime(timestamp))
                        st.markdown(f"**Data:** {date_str}"); st.markdown("---")
                        email_body = full_email_data.get('mail_body', '<i>Corpo non disponibile.</i>')
                        st.components.v1.html(email_body, height=400, scrolling=True)
            except Exception as e: st.error(f"Errore lettura posta: {e}")

# --- Provider 2: Temp-Mail.org (API UFFICIALE via RapidAPI) ---
def create_tempmail_account(domain):
    username = ''.join(random.choices(string.ascii_lowercase + string.digits, k=10))
    address = f"{username}@{domain}"
    return {"address": address, "provider": "Temp-Mail.org"}

def inbox_tempmail(info):
    st.subheader(f"📬 Inbox per [{info['address']}]")
    if st.button("🔁 Controlla inbox (Temp-Mail.org)"):
        with st.spinner("Recupero messaggi..."):
            # FIX: Prende la chiave API dai secrets di Streamlit
            api_key = st.secrets.get("rapidapi", {}).get("key")
            if not api_key:
                st.error("Chiave API per Temp-Mail.org non configurata nei secrets di Streamlit.")
                return

            url = "https://privatix-temp-mail-v1.p.rapidapi.com/request/mail/id/"
            md5_hash = hashlib.md5(info['address'].encode('utf-8')).hexdigest()
            full_url = f"{url}{md5_hash}/"
            headers = {"X-RapidAPI-Key": api_key, "X-RapidAPI-Host": "privatix-temp-mail-v1.p.rapidapi.com"}
            
            try:
                r = requests.get(full_url, headers=headers); r.raise_for_status()
                # FIX: Gestione robusta della risposta
                messages = r.json()
                if not isinstance(messages, list):
                    st.error("L'API non ha restituito una lista di messaggi. Risposta ricevuta:")
                    st.json(messages)
                    return
                
                if not messages: st.info("📭 Nessun messaggio trovato."); return
                st.success(f"Trovati {len(messages)} messaggi.")
                for m in reversed(messages):
                     with st.expander(f"✉️ **Da:** {m['mail_from']} | **Oggetto:** {m['mail_subject']}"):
                        st.markdown(f"**Data:** {m['mail_timestamp']}"); st.markdown("---")
                        email_body = m.get('mail_html') or m.get('mail_text') or "<i>Corpo non disponibile.</i>"
                        st.components.v1.html(email_body, height=400, scrolling=True)
            except Exception as e: st.error(f"Errore lettura posta (controlla la chiave API): {e}")

# ==============================================================================
#                      LOGICA PRINCIPALE E UI
# ==============================================================================
CREATE_FUNCTIONS = {"Guerrilla Mail": create_guerrillamail_account, "Temp-Mail.org": create_tempmail_account}
INBOX_FUNCTIONS = {"Guerrilla Mail": inbox_guerrillamail, "Temp-Mail.org": inbox_tempmail}

def generate_profile(country, extra_fields, provider, tempmail_domain=None):
    locs = {'Italia': 'it_IT', 'Francia': 'fr_FR', 'Germania': 'de_DE', 'Lussemburgo': 'fr_LU'}
    codes = {'Italia': 'IT', 'Francia': 'FR', 'Germania': 'DE', 'Lussemburgo': 'LU'}; fake = Faker(locs[country])
    p = {'Nome': fake.first_name(), 'Cognome': fake.last_name(), 'Data di Nascita': fake.date_of_birth(minimum_age=18, maximum_age=80).strftime('%d/%m/%Y'), 'Indirizzo': fake.address().replace("\n", ", "), 'IBAN': get_next_iban(codes[country]), 'Paese': country}
    if 'Email' in extra_fields:
        create_func = CREATE_FUNCTIONS[provider]
        result = create_func(tempmail_domain) if provider == "Temp-Mail.org" else create_func()
        st.session_state.email_info = result
        p["Email"] = result["address"] if result else "Creazione email fallita"
    if 'Telefono' in extra_fields: p['Telefono'] = fake.phone_number()
    if 'Codice Fiscale' in extra_fields: p['Codice Fiscale'] = fake.ssn() if locs[country] == 'it_IT' else 'N/A'
    if 'Partita IVA' in extra_fields: p['Partita IVA'] = fake.vat_id() if hasattr(fake, 'vat_id') else 'N/A'
    return pd.DataFrame([p])

def get_next_iban(cc):
    cc = cc.upper();
    if 'iban_state' not in st.session_state: st.session_state.iban_state = {}
    if cc not in st.session_state.iban_state or st.session_state.iban_state[cc]['index'] >= len(st.session_state.iban_state[cc]['list']):
        lst = PREDEFINED_IBANS.get(cc, ["N/A"]); random.shuffle(lst)
        st.session_state.iban_state[cc] = {'list': lst, 'index': 0}
    st.session_state.iban_state[cc]['index'] += 1
    return st.session_state.iban_state[cc]['list'][st.session_state.iban_state[cc]['index'] - 1]

st.title("✅ Generatore di Profili Affidabile")
st.markdown("Genera profili fittizi e scegli tra diversi servizi di email temporanee.")

if 'final_df' not in st.session_state: st.session_state.final_df = None
if 'email_info' not in st.session_state: st.session_state.email_info = None

with st.sidebar:
    st.header("⚙️ Opzioni Generali")
    country = st.selectbox("Paese", ["Italia", "Francia", "Germania", "Lussemburgo"])
    n = st.number_input("Numero di profili", 1, 25, 1)
    fields = st.multiselect("Campi aggiuntivi", ["Email", "Telefono", "Codice Fiscale", "Partita IVA"], default=["Email"])
    st.header("📧 Opzioni Email")
    selected_provider = st.selectbox("Scegli il provider email", ["Guerrilla Mail", "Temp-Mail.org"])
    
    selected_tempmail_domain = None
    is_button_disabled = False
    if selected_provider == "Temp-Mail.org":
        selected_tempmail_domain = st.selectbox("Dominio per Temp-Mail.org", TEMPMAIL_DOMAINS)
        # Controlla se la chiave API è configurata
        if not st.secrets.get("rapidapi", {}).get("key"):
            st.error("La chiave API per Temp-Mail.org non è configurata! Impostala nei Secrets della tua app.")
            is_button_disabled = True
    
    if st.button("🚀 Genera Profili", type="primary", disabled=is_button_disabled):
        with st.spinner("Generazione in corso..."):
            dfs = [generate_profile(country, fields, selected_provider, selected_tempmail_domain) for _ in range(n)]
        st.session_state.final_df = pd.concat([df for df in dfs if not df.empty], ignore_index=True)

if st.session_state.final_df is not None:
    st.success(f"✅ Generati {len(st.session_state.final_df)} profili.")
    st.dataframe(st.session_state.final_df)
    csv = st.session_state.final_df.to_csv(index=False).encode('utf-8')
    st.download_button("📥 Scarica CSV", csv, "profili.csv", "text/csv")
    
    info = st.session_state.email_info
    if 'Email' in st.session_state.final_df.columns and info and "fallita" not in info.get("address", "fallita"):
        inbox_func = INBOX_FUNCTIONS[info['provider']]
        inbox_func(info)
