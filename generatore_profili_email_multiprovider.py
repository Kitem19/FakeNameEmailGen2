# -*- coding: utf-8 -*-
import random
import string
import requests
import pandas as pd
import streamlit as st
from faker import Faker
import time

# --- CONFIGURAZIONE PAGINA ---
st.set_page_config(page_title="Generatore di Profili (Guerrilla Mail)", page_icon="📫", layout="centered")

# --- COSTANTI E DATI PREDEFINITI ---
PREDEFINED_IBANS = {
    'IT': ['IT60X0542811101000000123456', 'IT12A0306912345100000067890'],
    'FR': ['FR1420041010050500013M02606', 'FR7630006000011234567890189'],
    'DE': ['DE89370400440532013000', 'DE02100100100006820101'],
    'LU': ['LU280019400644750000', 'LU120010001234567891']
}
USER_AGENT_HEADER = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}

# ==============================================================================
#                      FUNZIONI API PER GUERRILLA MAIL
# ==============================================================================
def create_guerrillamail_account():
    """Crea un account email temporaneo su Guerrilla Mail."""
    try:
        r = requests.get("https://api.guerrillamail.com/ajax.php?f=get_email_address", headers=USER_AGENT_HEADER)
        r.raise_for_status()
        data = r.json()
        return {"address": data['email_addr'], "sid_token": data['sid_token']}
    except requests.exceptions.RequestException as e:
        st.error(f"Errore nella creazione dell'email con Guerrilla Mail: {e}")
        return None

def inbox_guerrillamail(info):
    """Gestisce la logica e la visualizzazione dell'inbox."""
    st.subheader(f"📬 Inbox per: `{info['address']}`")
    
    # --- FIX: Il pulsante ora aggiorna solo lo stato ---
    if st.button("🔁 Controlla/Aggiorna messaggi"):
        with st.spinner("Recupero messaggi..."):
            try:
                r = requests.get(f"https://api.guerrillamail.com/ajax.php?f=check_email&seq=0&sid_token={info['sid_token']}", headers=USER_AGENT_HEADER)
                r.raise_for_status()
                # Salviamo i messaggi nello stato della sessione
                st.session_state.messages = r.json().get("list", [])
            except Exception as e:
                st.error(f"Errore durante la lettura della posta: {e}")
                st.session_state.messages = [] # Resetta in caso di errore

    # --- FIX: La visualizzazione è separata e legge sempre dallo stato ---
    if 'messages' in st.session_state and st.session_state.messages is not None:
        messages = st.session_state.messages
        if not messages:
            st.info("📭 La casella di posta è vuota.")
        else:
            st.success(f"Trovati {len(messages)} messaggi.")
            for m in reversed(messages):
                with st.expander(f"✉️ **Da:** {m['mail_from']} | **Oggetto:** {m['mail_subject']}"):
                    with st.spinner("Caricamento corpo del messaggio..."):
                        email_id = m['mail_id']
                        full_email_resp = requests.get(f"https://api.guerrillamail.com/ajax.php?f=fetch_email&email_id={email_id}&sid_token={info['sid_token']}", headers=USER_AGENT_HEADER)
                        full_email_data = full_email_resp.json()
                    
                    timestamp = int(m['mail_timestamp'])
                    date_str = time.strftime('%d/%m/%Y %H:%M:%S', time.localtime(timestamp))
                    
                    st.markdown(f"**Data:** {date_str}")
                    st.markdown("---")
                    
                    email_body = full_email_data.get('mail_body', '<i>Corpo del messaggio non disponibile.</i>')
                    st.components.v1.html(email_body, height=400, scrolling=True)

# ==============================================================================
#                      FUNZIONI DI LOGICA E UI
# ==============================================================================
def get_next_iban(cc):
    cc = cc.upper()
    if 'iban_state' not in st.session_state: st.session_state.iban_state = {}
    if cc not in st.session_state.iban_state or st.session_state.iban_state[cc]['index'] >= len(st.session_state.iban_state[cc]['list']):
        lst = PREDEFINED_IBANS.get(cc, ["N/A"]); random.shuffle(lst)
        st.session_state.iban_state[cc] = {'list': lst, 'index': 0}
    st.session_state.iban_state[cc]['index'] += 1
    return st.session_state.iban_state[cc]['list'][st.session_state.iban_state[cc]['index'] - 1]

def generate_profile(country, extra_fields):
    locs = {'Italia': 'it_IT', 'Francia': 'fr_FR', 'Germania': 'de_DE', 'Lussemburgo': 'fr_LU'}
    codes = {'Italia': 'IT', 'Francia': 'FR', 'Germania': 'DE', 'Lussemburgo': 'LU'}
    locale, code = locs[country], codes[country]; fake = Faker(locale)
    p = {'Nome': fake.first_name(), 'Cognome': fake.last_name(), 'Data di Nascita': fake.date_of_birth(minimum_age=18, maximum_age=80).strftime('%d/%m/%Y'), 'Indirizzo': fake.address().replace("\n", ", "), 'IBAN': get_next_iban(code), 'Paese': country}
    
    if 'Email' in extra_fields:
        result = create_guerrillamail_account(); st.session_state.email_info = result
        p["Email"] = result["address"] if result else "Creazione email fallita"
        
    if 'Telefono' in extra_fields: p['Telefono'] = fake.phone_number()
    if 'Codice Fiscale' in extra_fields: p['Codice Fiscale'] = fake.ssn() if locale == 'it_IT' else 'N/A'
    if 'Partita IVA' in extra_fields: p['Partita IVA'] = fake.vat_id() if hasattr(fake, 'vat_id') else 'N/A'
    return pd.DataFrame([p])

def display_profile_card(profile_data):
    st.subheader("📄 Dettagli del Profilo Generato")
    col1, col2 = st.columns(2)
    with col1: st.text_input("Nome", value=profile_data.get("Nome"), disabled=True, key="nome")
    with col2: st.text_input("Cognome", value=profile_data.get("Cognome"), disabled=True, key="cognome")
    st.text_input("Data di Nascita", value=profile_data.get("Data di Nascita"), disabled=True, key="data_nascita")
    st.text_input("Indirizzo", value=profile_data.get("Indirizzo"), disabled=True, key="indirizzo")
    st.text_input("IBAN", value=profile_data.get("IBAN"), disabled=True, key="iban")
    if "Telefono" in profile_data: st.text_input("Telefono", value=profile_data.get("Telefono"), disabled=True, key="telefono")
    if "Codice Fiscale" in profile_data: st.text_input("Codice Fiscale", value=profile_data.get("Codice Fiscale"), disabled=True, key="cf")
    if "Partita IVA" in profile_data: st.text_input("Partita IVA", value=profile_data.get("Partita IVA"), disabled=True, key="piva")
    if "Email" in profile_data and "fallita" not in profile_data["Email"]:
        st.markdown(f"**Email:** [{profile_data['Email']}](mailto:{profile_data['Email']})")
    st.markdown("---")

# --- INTERFACCIA UTENTE (UI) ---
st.title("📫 Generatore di Profili con Guerrilla Mail")
st.markdown("Genera profili fittizi completi di un'email temporanea funzionante e affidabile.")

# Inizializza lo stato se non esiste
if 'final_df' not in st.session_state: st.session_state.final_df = None
if 'email_info' not in st.session_state: st.session_state.email_info = None
if 'messages' not in st.session_state: st.session_state.messages = None
if 'show_success' not in st.session_state: st.session_state.show_success = False

with st.sidebar:
    st.header("⚙️ Opzioni")
    country = st.selectbox("Paese", ["Italia", "Francia", "Germania", "Lussemburgo"])
    n = st.number_input("Numero di profili", 1, 25, 1)
    fields = st.multiselect("Campi aggiuntivi", ["Email", "Telefono", "Codice Fiscale", "Partita IVA"], default=["Email"])
    
    if st.button("🚀 Genera Profili", type="primary"):
        with st.spinner("Generazione in corso..."):
            dfs = [generate_profile(country, fields) for _ in range(n)]
        st.session_state.final_df = pd.concat([df for df in dfs if not df.empty], ignore_index=True)
        # Resetta lo stato dei messaggi precedenti e imposta il flag per il messaggio di successo
        st.session_state.messages = None
        st.session_state.show_success = True

# La visualizzazione principale ora legge sempre dallo stato
if st.session_state.final_df is not None:
    # FIX: Mostra il messaggio di successo solo una volta
    if st.session_state.show_success:
        st.success(f"✅ Generati {len(st.session_state.final_df)} profili.")
        st.session_state.show_success = False # "Consuma" il flag
    
    if len(st.session_state.final_df) == 1:
        display_profile_card(st.session_state.final_df.iloc[0])
    else:
        st.dataframe(st.session_state.final_df)
    
    csv = st.session_state.final_df.to_csv(index=False).encode('utf-8')
    st.download_button("📥 Scarica CSV", csv, "profili.csv", "text/csv")

    info = st.session_state.email_info
    if 'Email' in st.session_state.final_df.columns and info and "fallita" not in info.get("address", "fallita"):
        inbox_guerrillamail(info)
