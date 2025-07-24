# -*- coding: utf-8 -*-
import random
import string
import requests
import pandas as pd
import streamlit as st
from faker import Faker
import time # Importiamo time per la gestione della data

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

# --- FUNZIONI API per Guerrilla Mail (API stabile) ---

def create_guerrillamail_account():
    """Crea un account email temporaneo su Guerrilla Mail."""
    try:
        r = requests.get("https://api.guerrillamail.com/ajax.php?f=get_email_address")
        r.raise_for_status()
        data = r.json()
        return {"address": data['email_addr'], "sid_token": data['sid_token']}
    except requests.exceptions.RequestException as e:
        st.error(f"Errore nella creazione dell'account Guerrilla Mail: {e}")
        return None

def inbox_guerrillamail(address, sid_token):
    """Mostra l'interfaccia per controllare la casella di posta di Guerrilla Mail."""
    st.subheader(f"📬 Inbox per [{address}](mailto:{address})")
    
    if st.button("🔁 Controlla inbox (Guerrilla Mail)"):
        with st.spinner("Recupero messaggi..."):
            try:
                r = requests.get(f"https://api.guerrillamail.com/ajax.php?f=check_email&seq=0&sid_token={sid_token}")
                r.raise_for_status()
                messages = r.json().get("list", [])
                
                if not messages:
                    st.info("📭 Nessun messaggio trovato."); return

                st.success(f"Trovati {len(messages)} messaggi.")
                for m in reversed(messages): # Mostra i più recenti per primi
                    with st.expander(f"✉️ **Da:** {m['mail_from']} | **Oggetto:** {m['mail_subject']}"):
                        
                        # --- FIX DEFINITIVO: Convertiamo il timestamp da stringa a intero ---
                        try:
                            timestamp = int(m['mail_timestamp'])
                            date_str = time.strftime('%d/%m/%Y %H:%M:%S', time.localtime(timestamp))
                        except (ValueError, KeyError):
                            date_str = "Data non disponibile"
                        
                        st.markdown(f"**Data:** {date_str}")
                        st.markdown("---")
                        # L'API base fornisce solo un estratto. Per il corpo completo servirebbe un'altra chiamata.
                        st.code(m['mail_excerpt'], language=None)
            except Exception as e:
                st.error(f"Errore nella lettura della posta: {e}")

# --- FUNZIONI DI LOGICA ---
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
    locale, code = locs[country], codes[country]
    fake = Faker(locale)
    p = {'Nome': fake.first_name(), 'Cognome': fake.last_name(), 'Data di Nascita': fake.date_of_birth(minimum_age=18, maximum_age=80).strftime('%d/%m/%Y'), 'Indirizzo': fake.address().replace("\n", ", "), 'IBAN': get_next_iban(code), 'Paese': country}
    
    if 'Email' in extra_fields:
        result = create_guerrillamail_account(); st.session_state.email_info = result
        p["Email"] = result["address"] if result else "Creazione email fallita"
        
    if 'Telefono' in extra_fields: p['Telefono'] = fake.phone_number()
    if 'Codice Fiscale' in extra_fields: p['Codice Fiscale'] = fake.ssn() if locale == 'it_IT' else 'N/A'
    if 'Partita IVA' in extra_fields: p['Partita IVA'] = fake.vat_id() if hasattr(fake, 'vat_id') else 'N/A'
    return pd.DataFrame([p])

# --- INTERFACCIA UTENTE (UI) ---
st.title("📨 Generatore di Profili Fake")
st.markdown("Genera profili fittizi con email temporanee reali tramite **Guerrilla Mail**.")

if 'final_df' not in st.session_state: st.session_state.final_df = None
if 'email_info' not in st.session_state: st.session_state.email_info = None

with st.sidebar:
    st.header("⚙️ Opzioni")
    country = st.selectbox("Paese", ["Italia", "Francia", "Germania", "Lussemburgo"])
    n = st.number_input("Numero di profili", 1, 25, 1)
    fields = st.multiselect("Campi aggiuntivi", ["Email", "Telefono", "Codice Fiscale", "Partita IVA"], default=["Email"])
    
    if st.button("🚀 Genera Profili", type="primary"):
        with st.spinner("Generazione in corso..."):
            dfs = [generate_profile(country, fields) for _ in range(n)]
        st.session_state.final_df = pd.concat([df for df in dfs if not df.empty], ignore_index=True)

if st.session_state.final_df is not None:
    st.success(f"✅ Generati {len(st.session_state.final_df)} profili.")
    st.dataframe(st.session_state.final_df)
    csv = st.session_state.final_df.to_csv(index=False).encode('utf-8')
    st.download_button("📥 Scarica CSV", csv, "profili.csv", "text/csv")

    info = st.session_state.email_info
    if 'Email' in st.session_state.final_df.columns and info and "fallita" not in info.get("address", "fallita"):
        inbox_guerrillamail(info["address"], info["sid_token"])
