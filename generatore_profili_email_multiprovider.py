# -*- coding: utf-8 -*-
import random
import string
import requests
import pandas as pd
import streamlit as st
from faker import Faker
import time

# --- CONFIGURAZIONE PAGINA ---
st.set_page_config(page_title="Generatore di Profili Multi-Provider", page_icon="🔀", layout="centered")

# --- COSTANTI E DATI PREDEFINITI ---
PREDEFINED_IBANS = {
    'IT': ['IT60X0542811101000000123456', 'IT12A0306912345100000067890'],
    'FR': ['FR1420041010050500013M02606', 'FR7630006000011234567890189'],
    'DE': ['DE89370400440532013000', 'DE02100100100006820101'],
    'LU': ['LU280019400644750000', 'LU120010001234567891']
}
API_HEADERS = {'Accept': 'application/json', 'Content-Type': 'application/json'}
USER_AGENT_HEADER = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
VALID_MAILTM_DOMAINS = ["mailbox.in.ua", "member.buzz", "feeling.perfect", "spam.care"]

# ==============================================================================
#                      FUNZIONI API PER OGNI PROVIDER
# ==============================================================================

# --- Provider 1: Guerrilla Mail (Stabile) ---
def create_guerrillamail_account():
    """Crea un account su Guerrilla Mail."""
    try:
        r = requests.get("https://api.guerrillamail.com/ajax.php?f=get_email_address")
        r.raise_for_status()
        data = r.json()
        return {"address": data['email_addr'], "sid_token": data['sid_token'], "provider": "Guerrilla Mail"}
    except requests.exceptions.RequestException as e:
        st.error(f"Errore Guerrilla Mail: {e}"); return None

def inbox_guerrillamail(info):
    """Mostra l'inbox di Guerrilla Mail."""
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

# --- Provider 2: Mail.tm (Alternativa) ---
def create_mailtm_account(domain):
    """Crea un account su Mail.tm."""
    username = ''.join(random.choices(string.ascii_lowercase + string.digits, k=12))
    password = ''.join(random.choices(string.ascii_letters + string.digits, k=16))
    address = f"{username}@{domain}"
    data = {"address": address, "password": password}
    try:
        requests.post("https://api.mail.tm/accounts", json=data, headers=API_HEADERS).raise_for_status()
        token_resp = requests.post("https://api.mail.tm/token", json=data, headers=API_HEADERS)
        token_resp.raise_for_status()
        return {"address": address, "token": token_resp.json()['token'], "provider": "Mail.tm"}
    except requests.exceptions.RequestException as e:
        st.error(f"Errore Mail.tm: {e}"); return None

def inbox_mailtm(info):
    """Mostra l'inbox di Mail.tm."""
    st.subheader(f"📬 Inbox per [{info['address']}]")
    if st.button("🔁 Controlla inbox (Mail.tm)"):
        with st.spinner("Recupero messaggi..."):
            auth_headers = {**API_HEADERS, 'Authorization': f'Bearer {info["token"]}'}
            try:
                r = requests.get("https://api.mail.tm/messages", headers=auth_headers); r.raise_for_status()
                messages = r.json().get("hydra:member", [])
                if not messages: st.info("📭 Nessun messaggio trovato."); return
                st.success(f"Trovati {len(messages)} messaggi.")
                for m in reversed(messages):
                    with st.expander(f"✉️ **Da:** {m.get('from', {}).get('address', 'N/A')} | **Oggetto:** {m.get('subject', '(Senza oggetto)')}"):
                        st.markdown(f"**Data:** {pd.to_datetime(m.get('createdAt')).strftime('%d/%m/%Y %H:%M')}")
                        st.markdown("---")
                        st.text_area("Anteprima", m.get('intro', 'N/A'), height=150, key=f"msg_{m['id']}")
            except Exception as e: st.error(f"Errore lettura posta: {e}")

# --- Provider 3: 1secmail (Semplice, a volte bloccato) ---
def create_1secmail_account():
    """Crea un account su 1secmail."""
    try:
        r = requests.get("https://www.1secmail.com/api/v1/?action=genRandomMailbox&count=1", headers=USER_AGENT_HEADER)
        r.raise_for_status()
        address = r.json()[0]
        return {"address": address, "provider": "1secmail"}
    except requests.exceptions.RequestException as e:
        st.error(f"Errore 1secmail: {e}"); return None

def inbox_1secmail(info):
    """Mostra l'inbox di 1secmail."""
    st.subheader(f"📬 Inbox per [{info['address']}]")
    if st.button("🔁 Controlla inbox (1secmail)"):
        with st.spinner("Recupero messaggi..."):
            try:
                login, domain = info['address'].split('@')
                r = requests.get(f"https://www.1secmail.com/api/v1/?action=getMessages&login={login}&domain={domain}", headers=USER_AGENT_HEADER)
                r.raise_for_status()
                messages = r.json()
                if not messages: st.info("📭 Nessun messaggio trovato."); return
                st.success(f"Trovati {len(messages)} messaggi.")
                for m in reversed(messages):
                    with st.expander(f"✉️ **Da:** {m['from']} | **Oggetto:** {m['subject']}"):
                        msg_id = m['id']
                        full_msg_resp = requests.get(f"https://www.1secmail.com/api/v1/?action=readMessage&login={login}&domain={domain}&id={msg_id}", headers=USER_AGENT_HEADER)
                        full_msg_data = full_msg_resp.json()
                        st.markdown(f"**Data:** {full_msg_data['date']}"); st.markdown("---")
                        st.components.v1.html(full_msg_data.get('htmlBody', full_msg_data.get('body')), height=400, scrolling=True)
            except Exception as e: st.error(f"Errore lettura posta: {e}")

# ==============================================================================
#                      LOGICA PRINCIPALE E UI
# ==============================================================================

# Dizionari per mappare la selezione dell'utente alle funzioni corrette
CREATE_FUNCTIONS = {
    "Guerrilla Mail": create_guerrillamail_account,
    "Mail.tm": create_mailtm_account,
    "1secmail": create_1secmail_account
}
INBOX_FUNCTIONS = {
    "Guerrilla Mail": inbox_guerrillamail,
    "Mail.tm": inbox_mailtm,
    "1secmail": inbox_1secmail
}

def generate_profile(country, extra_fields, provider, mailtm_domain=None):
    locs = {'Italia': 'it_IT', 'Francia': 'fr_FR', 'Germania': 'de_DE', 'Lussemburgo': 'fr_LU'}
    codes = {'Italia': 'IT', 'Francia': 'FR', 'Germania': 'DE', 'Lussemburgo': 'LU'}
    locale, code = locs[country], codes[country]; fake = Faker(locale)
    p = {'Nome': fake.first_name(), 'Cognome': fake.last_name(), 'Data di Nascita': fake.date_of_birth(minimum_age=18, maximum_age=80).strftime('%d/%m/%Y'), 'Indirizzo': fake.address().replace("\n", ", "), 'IBAN': get_next_iban(code), 'Paese': country}

    if 'Email' in extra_fields:
        create_func = CREATE_FUNCTIONS[provider]
        if provider == "Mail.tm":
            result = create_func(mailtm_domain)
        else:
            result = create_func()
        st.session_state.email_info = result
        p["Email"] = result["address"] if result else "Creazione email fallita"
        
    if 'Telefono' in extra_fields: p['Telefono'] = fake.phone_number()
    if 'Codice Fiscale' in extra_fields: p['Codice Fiscale'] = fake.ssn() if locale == 'it_IT' else 'N/A'
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

st.title("🔀 Generatore di Profili Multi-Provider")
st.markdown("Genera profili fittizi e scegli tra diversi servizi di email temporanee.")

if 'final_df' not in st.session_state: st.session_state.final_df = None
if 'email_info' not in st.session_state: st.session_state.email_info = None

with st.sidebar:
    st.header("⚙️ Opzioni Generali")
    country = st.selectbox("Paese", ["Italia", "Francia", "Germania", "Lussemburgo"])
    n = st.number_input("Numero di profili", 1, 25, 1)
    fields = st.multiselect("Campi aggiuntivi", ["Email", "Telefono", "Codice Fiscale", "Partita IVA"], default=["Email"])
    
    st.header("📧 Opzioni Email")
    selected_provider = st.selectbox("Scegli il provider email", ["Guerrilla Mail", "Mail.tm", "1secmail"])
    
    # Mostra opzioni specifiche solo per il provider selezionato
    selected_mailtm_domain = None
    if selected_provider == "Mail.tm":
        selected_mailtm_domain = st.selectbox("Dominio per Mail.tm", VALID_MAILTM_DOMAINS)
    elif selected_provider == "1secmail":
        st.info("1secmail è semplice ma potrebbe essere bloccato da alcuni siti.")
    
    if st.button("🚀 Genera Profili", type="primary"):
        with st.spinner("Generazione in corso..."):
            dfs = [generate_profile(country, fields, selected_provider, selected_mailtm_domain) for _ in range(n)]
        st.session_state.final_df = pd.concat([df for df in dfs if not df.empty], ignore_index=True)

if st.session_state.final_df is not None:
    st.success(f"✅ Generati {len(st.session_state.final_df)} profili.")
    st.dataframe(st.session_state.final_df)
    csv = st.session_state.final_df.to_csv(index=False).encode('utf-8')
    st.download_button("📥 Scarica CSV", csv, "profili.csv", "text/csv")

    info = st.session_state.email_info
    if 'Email' in st.session_state.final_df.columns and info and "fallita" not in info.get("address", "fallita"):
        # Chiama la funzione inbox corretta in base al provider salvato nello stato
        inbox_func = INBOX_FUNCTIONS[info['provider']]
        inbox_func(info)
