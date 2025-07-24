# -*- coding: utf-8 -*-
import random
import string
import time
import requests
import pandas as pd
import streamlit as st
from faker import Faker
import xml.etree.ElementTree as ET

st.set_page_config(page_title="Generatore di Profili Fake", page_icon="👤", layout="centered")

PREDEFINED_IBANS = {
    'IT': ['IT60X0542811101000000123456', 'IT12A0306912345100000067890'],
    'FR': ['FR1420041010050500013M02606', 'FR7630006000011234567890189'],
    'DE': ['DE89370400440532013000', 'DE02100100100006820101'],
    'LU': ['LU280019400644750000', 'LU120010001234567891']
}

# ---------------- EMAIL PROVIDERS ---------------- #

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
        return {"address": address, "token": token_resp.json()['token'], "username": username}
    except:
        return None

def inbox_mailtm(address, token):
    st.subheader(f"📬 Inbox per {address}")
    sleep_and_check("https://api.mail.tm/messages", {'Authorization': f'Bearer {token}'})

# 1secmail
def create_1secmail_account():
    username = ''.join(random.choices(string.ascii_lowercase + string.digits, k=10))
    domain = random.choice(["1secmail.com", "1secmail.net", "1secmail.org"])
    return {"address": f"{username}@{domain}", "username": username, "domain": domain}

def inbox_1secmail(username, domain):
    st.subheader(f"📬 Inbox per {username}@{domain}")
    url = f"https://www.1secmail.com/api/v1/?action=getMessages&login={username}&domain={domain}"
    sleep_and_check(url)

# GuerrillaMail
def create_guerrillamail_account():
    try:
        r = requests.get("https://api.guerrillamail.com/ajax.php?f=get_email_address")
        j = r.json()
        return {"address": j["email_addr"], "sid_token": j["sid_token"]}
    except:
        return None

def inbox_guerrillamail(sid_token):
    st.subheader("📬 Inbox GuerrillaMail")
    url = f"https://api.guerrillamail.com/ajax.php?f=get_email_list&sid_token={sid_token}"
    sleep_and_check(url)

# ---------------- UTILITY ---------------- #

def get_next_iban(cc):
    cc = cc.upper()
    if 'iban_state' not in st.session_state: st.session_state.iban_state = {}
    if cc not in st.session_state.iban_state or st.session_state.iban_state[cc]['index'] >= len(st.session_state.iban_state[cc]['list']):
        lst = PREDEFINED_IBANS.get(cc, ["N/A"]); random.shuffle(lst)
        st.session_state.iban_state[cc] = {'list': lst, 'index': 0}
    st.session_state.iban_state[cc]['index'] += 1
    return st.session_state.iban_state[cc]['list'][st.session_state.iban_state[cc]['index'] - 1]

def generate_profile(country, extra_fields, email_provider, selected_domain=None):
    locs = {'Italia': 'it_IT', 'Francia': 'fr_FR', 'Germania': 'de_DE', 'Lussemburgo': 'fr_LU'}
    codes = {'Italia': 'IT', 'Francia': 'FR', 'Germania': 'DE', 'Lussemburgo': 'LU'}
    locale, code = locs[country], codes[country]
    fake = Faker(locale)
    p = {
        'Nome': fake.first_name(),
        'Cognome': fake.last_name(),
        'Data di Nascita': fake.date_of_birth(minimum_age=18, maximum_age=80).strftime('%d/%m/%Y'),
        'Indirizzo': fake.address().replace("\n", ", "),
        'IBAN': get_next_iban(code),
        'Paese': country
    }

    if 'Email' in extra_fields:
        if email_provider == "mail.tm":
            result = create_mailtm_account(selected_domain)
        elif email_provider == "1secmail":
            result = create_1secmail_account()
        elif email_provider == "GuerrillaMail":
            result = create_guerrillamail_account()
        else:
            result = None

        st.session_state.email_info = result
        p["Email"] = result["address"] if result else "Errore"

    if 'Telefono' in extra_fields: p['Telefono'] = fake.phone_number()
    if 'Codice Fiscale' in extra_fields: p['Codice Fiscale'] = fake.ssn() if locale == 'it_IT' else 'N/A'
    if 'Partita IVA' in extra_fields: p['Partita IVA'] = fake.vat_id() if hasattr(fake, 'vat_id') else 'N/A'
    return pd.DataFrame([p])

def sleep_and_check(url, headers=None):
    if st.button("🔁 Aggiorna ogni 5s per 1 min"):
        st.info("⏳ Attendi... controllo ogni 5 secondi per 60 secondi")
        for i in range(12):
            try:
                r = requests.get(url, headers=headers)
                try:
                    data = r.json()
                    if isinstance(data, dict) and "hydra:member" in data:
                        messages = data["hydra:member"]
                    elif isinstance(data, dict) and "list" in data:
                        messages = data["list"]
                    elif isinstance(data, list):
                        messages = data
                    else:
                        messages = []

                    if messages:
                        st.success(f"📩 Trovati {len(messages)} messaggi!")
                        for m in messages:
                            with st.expander(str(m)):
                                st.json(m)
                        break
                    else:
                        st.write(f"[{(i+1)*5}s] Nessun messaggio...")
                except Exception as e:
                    st.warning(f"[{(i+1)*5}s] Risposta non valida o vuota.")
            except Exception as e:
                st.error(f"Errore: {e}")
            time.sleep(5)

# ---------------- UI ---------------- #

st.title("👤 Generatore di Profili Fake con Email Temporanea")

if 'final_df' not in st.session_state: st.session_state.final_df = None
if 'email_info' not in st.session_state: st.session_state.email_info = None

with st.sidebar:
    st.header("⚙️ Opzioni")
    country = st.selectbox("Paese", ["Italia", "Francia", "Germania", "Lussemburgo"])
    n = st.number_input("Numero di profili", 1, 25, 1)
    fields = st.multiselect("Campi aggiuntivi", ["Email", "Telefono", "Codice Fiscale", "Partita IVA"], default=["Email"])
    email_provider = st.selectbox("Provider Email", ["mail.tm", "1secmail", "GuerrillaMail"])

    selected_domain = None
    if email_provider == "mail.tm":
        all_domains = get_mailtm_domains()
        if not all_domains:
            st.error("⚠️ Nessun dominio disponibile da mail.tm")
        else:
            selected_domain = st.selectbox("Dominio mail.tm", all_domains)

    if st.button("🚀 Genera Profili"):
        dfs = [generate_profile(country, fields, email_provider, selected_domain) for _ in range(n)]
        st.session_state.final_df = pd.concat(dfs, ignore_index=True)

if st.session_state.final_df is not None:
    st.success(f"✅ Generati {len(st.session_state.final_df)} profili.")
    st.dataframe(st.session_state.final_df)
    csv = st.session_state.final_df.to_csv(index=False).encode('utf-8')
    st.download_button("📥 Scarica CSV", csv, "profili.csv", "text/csv")

    info = st.session_state.email_info
    if 'Email' in st.session_state.final_df.columns and info:
        if email_provider == "mail.tm" and "token" in info:
            inbox_mailtm(info["address"], info["token"])
        elif email_provider == "1secmail":
            inbox_1secmail(info["username"], info["domain"])
        elif email_provider == "GuerrillaMail":
            inbox_guerrillamail(info["sid_token"])

# TEST EMAIL BUTTON
st.markdown("---")
st.subheader("📨 Test Email")
if st.session_state.get("email_info"):
    to_addr = st.session_state.email_info["address"]
    if st.button("✉️ Inviami una test email"):
        r = requests.post("https://httpbin.org/post", json={"to": to_addr, "subject": "Test", "body": "Messaggio di test"})
        st.success(f"Test inviato a {to_addr} (simulazione)")
        st.code(r.json(), language="json")
