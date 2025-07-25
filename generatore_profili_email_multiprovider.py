
# -*- coding: utf-8 -*-
import random
import string
import requests
import pandas as pd
import streamlit as st
from faker import Faker
import time
import xml.etree.ElementTree as ET

# CONFIGURAZIONE
st.set_page_config(page_title="Fake Profile Generator", page_icon="📨", layout="centered")

PREDEFINED_IBANS = {
    'IT': ['IT60X0542811101000000123456', 'IT12A0306912345100000067890'],
    'FR': ['FR1420041010050500013M02606', 'FR7630006000011234567890189'],
    'DE': ['DE89370400440532013000', 'DE02100100100006820101'],
    'LU': ['LU280019400644750000', 'LU120010001234567891']
}

# GUERRILLA MAIL
def create_guerrillamail_account():
    try:
        r = requests.get("https://api.guerrillamail.com/ajax.php?f=get_email_address")
        r.raise_for_status()
        data = r.json()
        return {"address": data['email_addr'], "sid_token": data['sid_token']}
    except Exception as e:
        st.error(f"Errore Guerrilla: {e}")
        return None

def inbox_guerrillamail(address, sid_token):
    st.subheader(f"📬 Inbox per [{address}](mailto:{address})")
    if st.button("🔁 Controlla inbox (Guerrilla Mail)"):
        with st.spinner("Recupero messaggi..."):
            try:
                r = requests.get(f"https://api.guerrillamail.com/ajax.php?f=check_email&seq=0&sid_token={sid_token}")
                r.raise_for_status()
                messages = r.json().get("list", [])
                if not messages:
                    st.info("📭 Nessun messaggio trovato.")
                    return
                st.success(f"Trovati {len(messages)} messaggi.")
                for m in reversed(messages):
                    with st.expander(f"✉️ {m['mail_from']} | {m['mail_subject']}"):
                        email_id = m['mail_id']
                        full = requests.get(f"https://api.guerrillamail.com/ajax.php?f=fetch_email&email_id={email_id}&sid_token={sid_token}").json()
                        date_str = time.strftime('%d/%m/%Y %H:%M:%S', time.localtime(int(m['mail_timestamp'])))
                        st.markdown(f"**Data:** {date_str}")
                        st.markdown("---")
                        st.components.v1.html(full.get('mail_body', ''), height=400, scrolling=True)
            except Exception as e:
                st.error(f"Errore nella lettura: {e}")

# MAIL.TM
def get_mailtm_domains():
    try:
        r = requests.get("https://api.mail.tm/domains", headers={'Accept': 'application/xml'})
        r.raise_for_status()
        xml_root = ET.fromstring(r.text)
        return list({el.text for el in xml_root.findall(".//domain")})
    except:
        return []

def create_mailtm_account(domain):
    username = ''.join(random.choices(string.ascii_lowercase + string.digits, k=10))
    password = ''.join(random.choices(string.ascii_letters + string.digits, k=16))
    address = f"{username}@{domain}"
    data = {"address": address, "password": password}
    try:
        requests.post("https://api.mail.tm/accounts", json=data).raise_for_status()
        token_resp = requests.post("https://api.mail.tm/token", json=data)
        token_resp.raise_for_status()
        return {"address": address, "token": token_resp.json()['token']}
    except:
        return None

def inbox_mailtm(address, token):
    st.subheader(f"📬 Inbox per [{address}](mailto:{address})")
    if st.button("🔁 Controlla inbox (mail.tm)"):
        headers = {'Authorization': f'Bearer {token}'}
        try:
            r = requests.get("https://api.mail.tm/messages", headers=headers)
            messages = r.json().get("hydra:member", [])
            if not messages:
                st.info("📭 Nessun messaggio trovato.")
                return
            for msg in messages:
                msg_id = msg["id"]
                detail = requests.get(f"https://api.mail.tm/messages/{msg_id}", headers=headers).json()
                with st.expander(f"✉️ {msg.get('from', {}).get('address')} | {msg.get('subject')}"):
                    st.markdown(f"**Oggetto:** {msg.get('subject', '(Senza oggetto)')}")
                    st.markdown(f"**Mittente:** {msg.get('from', {}).get('address', 'N/A')}")
                    st.markdown(f"**Data:** {msg.get('createdAt', '')}")
                    html_content = detail.get("html", "")
                    if html_content:
                        st.components.v1.html(html_content, height=400, scrolling=True)
                    elif detail.get("text"):
                        st.code(detail["text"])
                    else:
                        st.info("Messaggio senza contenuto.")
        except Exception as e:
            st.warning(f"Errore nella lettura: {e}")



# 10MINUTEMAIL (mockato via sito - nessuna API stabile ufficiale)
def create_10minutemail_account():
    st.warning("⚠️ 10MinuteMail non ha un'API ufficiale. Questo è solo un placeholder.")
    return {"address": "user@10minutemail.com", "sid_token": "N/A"}

def inbox_10minutemail(address, sid_token):
    st.markdown(f"📬 Visita manualmente [10MinuteMail.com](https://10minutemail.com/) per controllare l'inbox: `{address}`")


# LOGICA
def get_next_iban(cc):
    cc = cc.upper()
    if 'iban_state' not in st.session_state:
        st.session_state.iban_state = {}
    if cc not in st.session_state.iban_state or st.session_state.iban_state[cc]['index'] >= len(st.session_state.iban_state[cc]['list']):
        lst = PREDEFINED_IBANS.get(cc, ["N/A"]); random.shuffle(lst)
        st.session_state.iban_state[cc] = {'list': lst, 'index': 0}
    st.session_state.iban_state[cc]['index'] += 1
    return st.session_state.iban_state[cc]['list'][st.session_state.iban_state[cc]['index'] - 1]

def generate_profile(country, extra_fields, provider, domain=None):
    locs = {'Italia': 'it_IT', 'Francia': 'fr_FR', 'Germania': 'de_DE', 'Lussemburgo': 'fr_LU'}
    codes = {'Italia': 'IT', 'Francia': 'FR', 'Germania': 'DE', 'Lussemburgo': 'LU'}
    locale, code = locs[country], codes[country]
    fake = Faker(locale)
    p = {'Nome': fake.first_name(), 'Cognome': fake.last_name(), 'Data di Nascita': fake.date_of_birth(minimum_age=18, maximum_age=80).strftime('%d/%m/%Y'), 'Indirizzo': fake.address().replace("\n", ", "), 'IBAN': get_next_iban(code), 'Paese': country}

    if 'Email' in extra_fields:
        if provider == "Guerrilla Mail":
            result = create_guerrillamail_account()
            st.session_state.email_info = result
            st.session_state.email_provider = "guerrilla"
            p["Email"] = result["address"] if result else "Errore"
        elif provider == "Mail.tm":
            result = create_mailtm_account(domain)
            st.session_state.email_info = result
            st.session_state.email_provider = "mailtm"
            p["Email"] = result["address"] if result else "Errore"
        elif provider == "10MinuteMail":
            result = create_10minutemail_account()
            st.session_state.email_info = result
            st.session_state.email_provider = "10min"
            p["Email"] = result["address"] if result else "Errore"
            result = create_mailtm_account(domain)
            st.session_state.email_info = result
            st.session_state.email_provider = "mailtm"
            p["Email"] = result["address"] if result else "Errore"

    if 'Telefono' in extra_fields: p['Telefono'] = fake.phone_number()
    if 'Codice Fiscale' in extra_fields: p['Codice Fiscale'] = fake.ssn() if locale == 'it_IT' else 'N/A'
    if 'Partita IVA' in extra_fields: p['Partita IVA'] = fake.vat_id() if hasattr(fake, 'vat_id') else 'N/A'
    return pd.DataFrame([p])

# UI
st.title("📨 Generatore Profili Fake")

if 'final_df' not in st.session_state: st.session_state.final_df = None
if 'email_info' not in st.session_state: st.session_state.email_info = None
if 'email_provider' not in st.session_state: st.session_state.email_provider = None

with st.sidebar:
    st.header("⚙️ Opzioni")
    country = st.selectbox("Paese", ["Italia", "Francia", "Germania", "Lussemburgo"])
    n = st.number_input("Numero di profili", 1, 25, 1)
    fields = st.multiselect("Campi aggiuntivi", ["Email", "Telefono", "Codice Fiscale", "Partita IVA"], default=["Email"])
    provider = st.selectbox("Provider email temporanea", ["Guerrilla Mail", "Mail.tm", "10MinuteMail"])
    domain = None
    if provider == "Mail.tm":
        all_domains = get_mailtm_domains()
        if all_domains:
            domain = st.selectbox("Dominio Mail.tm", all_domains)
        else:
            st.warning("Nessun dominio mail.tm disponibile.")

    if st.button("🚀 Genera Profili", type="primary"):
        with st.spinner("Generazione in corso..."):
            dfs = [generate_profile(country, fields, provider, domain) for _ in range(n)]
        st.session_state.final_df = pd.concat(dfs, ignore_index=True)

if st.session_state.final_df is not None:
    st.success(f"✅ Generati {len(st.session_state.final_df)} profili.")
    st.dataframe(st.session_state.final_df)
    csv = st.session_state.final_df.to_csv(index=False).encode('utf-8')
    st.download_button("📥 Scarica CSV", csv, "profili.csv", "text/csv")

    info = st.session_state.email_info
    if 'Email' in st.session_state.final_df.columns and info:
        if st.session_state.email_provider == "guerrilla":
            inbox_guerrillamail(info["address"], info["sid_token"])
        elif st.session_state.email_provider == "mailtm":
        inbox_mailtm(info["address"], info["token"])
    elif st.session_state.email_provider == "10min":
        inbox_10minutemail(info["address"], info.get("sid_token"))
