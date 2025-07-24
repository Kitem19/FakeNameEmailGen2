# -*- coding: utf-8 -*-
import random
import string
import requests
import pandas as pd
import streamlit as st
from faker import Faker

# --- CONFIGURAZIONE PAGINA ---
st.set_page_config(page_title="Generatore Profili Fake", page_icon="📨", layout="centered")

# --- COSTANTI E DATI PREDEFINITI ---
PREDEFINED_IBANS = {
    'IT': ['IT60X0542811101000000123456', 'IT12A0306912345100000067890'],
    'FR': ['FR1420041010050500013M02606', 'FR7630006000011234567890189'],
    'DE': ['DE89370400440532013000', 'DE02100100100006820101'],
    'LU': ['LU280019400644750000', 'LU120010001234567891']
}
API_HEADERS = {'Accept': 'application/json', 'Content-Type': 'application/json'}

# --- FIX DEFINITIVO: Lista di domini noti e funzionanti ---
# Abbiamo rimosso la chiamata all'API /domains che era instabile.
VALID_MAILTM_DOMAINS = ["mailbox.in.ua", "member.buzz"]


# --- FUNZIONI API per mail.tm ---

def create_mailtm_account(domain):
    """Crea un account email e ottiene il token."""
    username = ''.join(random.choices(string.ascii_lowercase + string.digits, k=12))
    password = ''.join(random.choices(string.ascii_letters + string.digits, k=16))
    address = f"{username}@{domain}"
    data = {"address": address, "password": password}

    try:
        # Crea l'account
        requests.post("https://api.mail.tm/accounts", json=data, headers=API_HEADERS).raise_for_status()
        
        # Ottieni il token
        token_resp = requests.post("https://api.mail.tm/token", json=data, headers=API_HEADERS)
        token_resp.raise_for_status()
        
        return {"address": address, "token": token_resp.json()['token']}
    except requests.exceptions.RequestException as e:
        st.error(f"Errore nella creazione dell'account mail.tm: {e}")
        if e.response:
            st.warning(f"Dettagli errore API: {e.response.text}")
        return None

def inbox_mailtm(address, token):
    """Mostra l'interfaccia per controllare la casella di posta."""
    st.subheader(f"📬 Inbox per [{address}](mailto:{address})")
    if st.button("🔁 Controlla inbox (mail.tm)"):
        auth_headers = {**API_HEADERS, 'Authorization': f'Bearer {token}'}
        try:
            r = requests.get("https://api.mail.tm/messages", headers=auth_headers)
            r.raise_for_status()
            messages = r.json().get("hydra:member", [])
            
            if not messages:
                st.info("📭 Nessun messaggio trovato."); return

            st.success(f"Trovati {len(messages)} messaggi.")
            for m in reversed(messages):
                msg_id = m["id"]
                with st.spinner(f"Caricamento messaggio {msg_id}..."):
                    detail_resp = requests.get(f"https://api.mail.tm/messages/{msg_id}", headers=auth_headers)
                    detail_resp.raise_for_status()
                    msg = detail_resp.json()

                with st.expander(f"✉️ **Da:** {msg.get('from', {}).get('address', 'N/A')} | **Oggetto:** {msg.get('subject', '(Senza oggetto)')}"):
                    st.code(f"A: {', '.join([to['address'] for to in msg.get('to', [])])}\nData: {pd.to_datetime(msg.get('createdAt')).strftime('%d/%m/%Y %H:%M')}", language=None)
                    html_content_list = msg.get("html", [])
                    if html_content_list and isinstance(html_content_list, list):
                        st.components.v1.html(html_content_list[0], height=400, scrolling=True)
                    elif msg.get("text"):
                        st.text_area("Contenuto (Testo)", msg["text"], height=250, key=f"text_{msg_id}")
                    if msg.get("attachments"):
                        st.markdown("**📎 Allegati:**")
                        for att in msg["attachments"]: st.markdown(f"- [{att.get('filename')}]({att.get('downloadUrl')})")
        except Exception as e: st.error(f"Errore nella lettura della posta: {e}")

# --- FUNZIONI DI LOGICA ---
def get_next_iban(cc):
    cc = cc.upper()
    if 'iban_state' not in st.session_state: st.session_state.iban_state = {}
    if cc not in st.session_state.iban_state or st.session_state.iban_state[cc]['index'] >= len(st.session_state.iban_state[cc]['list']):
        lst = PREDEFINED_IBANS.get(cc, ["N/A"]); random.shuffle(lst)
        st.session_state.iban_state[cc] = {'list': lst, 'index': 0}
    st.session_state.iban_state[cc]['index'] += 1
    return st.session_state.iban_state[cc]['list'][st.session_state.iban_state[cc]['index'] - 1]

def generate_profile(country, extra_fields, selected_domain):
    locs = {'Italia': 'it_IT', 'Francia': 'fr_FR', 'Germania': 'de_DE', 'Lussemburgo': 'fr_LU'}
    codes = {'Italia': 'IT', 'Francia': 'FR', 'Germania': 'DE', 'Lussemburgo': 'LU'}
    locale, code = locs[country], codes[country]
    fake = Faker(locale)
    p = {'Nome': fake.first_name(), 'Cognome': fake.last_name(), 'Data di Nascita': fake.date_of_birth(minimum_age=18, maximum_age=80).strftime('%d/%m/%Y'), 'Indirizzo': fake.address().replace("\n", ", "), 'IBAN': get_next_iban(code), 'Paese': country}
    if 'Email' in extra_fields:
        result = create_mailtm_account(selected_domain); st.session_state.email_info = result
        p["Email"] = result["address"] if result else "Creazione email fallita"
    if 'Telefono' in extra_fields: p['Telefono'] = fake.phone_number()
    if 'Codice Fiscale' in extra_fields: p['Codice Fiscale'] = fake.ssn() if locale == 'it_IT' else 'N/A'
    if 'Partita IVA' in extra_fields: p['Partita IVA'] = fake.vat_id() if hasattr(fake, 'vat_id') else 'N/A'
    return pd.DataFrame([p])

# --- INTERFACCIA UTENTE (UI) ---
st.title("📨 Generatore di Profili Fake")
st.markdown("Genera profili fittizi con email temporanee reali tramite **mail.tm**.")

if 'final_df' not in st.session_state: st.session_state.final_df = None
if 'email_info' not in st.session_state: st.session_state.email_info = None

with st.sidebar:
    st.header("⚙️ Opzioni")
    country = st.selectbox("Paese", ["Italia", "Francia", "Germania", "Lussemburgo"])
    n = st.number_input("Numero di profili", 1, 25, 1)
    fields = st.multiselect("Campi aggiuntivi", ["Email", "Telefono", "Codice Fiscale", "Partita IVA"], default=["Email"])

    # Usa la nostra lista di domini sicura invece di chiamare l'API
    selected_domain = st.selectbox("Dominio per l'email", VALID_MAILTM_DOMAINS)

    if st.button("🚀 Genera Profili", type="primary"):
        with st.spinner("Generazione in corso..."):
            dfs = [generate_profile(country, fields, selected_domain) for _ in range(n)]
        st.session_state.final_df = pd.concat([df for df in dfs if not df.empty], ignore_index=True)

if st.session_state.final_df is not None:
    st.success(f"✅ Generati {len(st.session_state.final_df)} profili.")
    st.dataframe(st.session_state.final_df)
    csv = st.session_state.final_df.to_csv(index=False).encode('utf-8')
    st.download_button("📥 Scarica CSV", csv, "profili.csv", "text/csv")

    info = st.session_state.email_info
    if 'Email' in st.session_state.final_df.columns and info and "fallita" not in info.get("address", "fallita"):
        inbox_mailtm(info["address"], info["token"])
