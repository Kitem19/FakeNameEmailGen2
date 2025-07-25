# -*- coding: utf-8 -*-
import random
import string
import requests
import pandas as pd
import streamlit as st
from faker import Faker

st.set_page_config(page_title="Generatore di Profili Guerrilla Mail", page_icon="🔀", layout="centered")

USER_AGENT_HEADER = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'}

# --- Funzioni Guerrilla Mail ---

def create_guerrillamail_account():
    try:
        r = requests.get("https://api.guerrillamail.com/ajax.php?f=get_email_address", headers=USER_AGENT_HEADER)
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
                r = requests.get(f"https://api.guerrillamail.com/ajax.php?f=check_email&seq=0&sid_token={info['sid_token']}", headers=USER_AGENT_HEADER)
                r.raise_for_status()
                messages = r.json().get("list", [])
                if not messages:
                    st.info("📭 Nessun messaggio trovato.")
                    return
                
                # Creiamo una lista di dict per la tabella
                data = []
                for m in reversed(messages):
                    data.append({
                        "ID": m['mail_id'],
                        "Da": m['mail_from'],
                        "Oggetto": m['mail_subject'],
                        "Data": m['mail_date']
                    })
                
                df_msgs = pd.DataFrame(data)

                # Visualizzo la tabella messaggi (senza id)
                st.dataframe(df_msgs.drop(columns=['ID']), use_container_width=True)
                
                # Seleziona un messaggio per mostrare corpo mail
                selected_id = st.selectbox("Seleziona il messaggio per visualizzare il corpo", options=df_msgs["ID"])
                
                if selected_id:
                    full_email_resp = requests.get(
                        f"https://api.guerrillamail.com/ajax.php?f=fetch_email&email_id={selected_id}&sid_token={info['sid_token']}",
                        headers=USER_AGENT_HEADER)
                    full_email_resp.raise_for_status()
                    email_body = full_email_resp.json().get('mail_body', '<i>Corpo non disponibile.</i>')
                    st.markdown("### Corpo del messaggio")
                    st.components.v1.html(email_body, height=400, scrolling=True)

            except Exception as e:
                st.error(f"Errore lettura posta Guerrilla Mail: {e}")

# ------- Generatore semplice di profili con email Guerrilla

def generate_profile(country, extra_fields):
    locs = {'Italia': 'it_IT', 'Francia': 'fr_FR', 'Germania': 'de_DE', 'Lussemburgo': 'fr_LU'}
    fake = Faker(locs[country])
    profile = {
        'Nome': fake.first_name(),
        'Cognome': fake.last_name(),
    }
    if 'Email' in extra_fields:
        result = create_guerrillamail_account()
        if not result or not result.get("address"):
            profile["Email"] = "Creazione email fallita"
            st.session_state.email_info = None
        else:
            profile["Email"] = result["address"]
            st.session_state.email_info = result
    if 'Telefono' in extra_fields:
        profile['Telefono'] = fake.phone_number()
    return profile

# --- UI ---

st.title("🔀 Generatore di Profili Guerrilla Mail")
st.markdown("Genera profili fittizi e usa Guerrilla Mail come email temporanea.")

if 'final_profiles' not in st.session_state:
    st.session_state.final_profiles = []
if 'email_info' not in st.session_state:
    st.session_state.email_info = None

with st.sidebar:
    st.header("⚙️ Opzioni")
    country = st.selectbox("Paese", ["Italia", "Francia", "Germania", "Lussemburgo"])
    n = st.number_input("Numero di profili", 1, 10, 1)
    fields = st.multiselect("Campi aggiuntivi", ["Email", "Telefono"], default=["Email"])
    
    if st.button("🚀 Genera Profili"):
        st.session_state.final_profiles = []
        for _ in range(n):
            prof = generate_profile(country, fields)
            st.session_state.final_profiles.append(prof)

if st.session_state.final_profiles:
    df_profiles = pd.DataFrame(st.session_state.final_profiles)
    st.success(f"✅ Generati {len(df_profiles)} profili.")
    st.dataframe(df_profiles, use_container_width=True)

    csv = df_profiles.to_csv(index=False, encoding='utf-8-sig').encode('utf-8-sig')
    st.download_button("📥 Scarica CSV", csv, "profili.csv", "text/csv")

    info = st.session_state.email_info
    if info and info.get("provider") == "Guerrilla Mail":
        inbox_guerrillamail(info)
