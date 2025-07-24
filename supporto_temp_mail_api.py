
import random
import string
import requests
import streamlit as st

# ========== TEMP-MAIL SUPPORT ==========
def create_tempmail_address():
    domain_resp = requests.get("https://privatix-temp-mail-v1.p.rapidapi.com/request/domains/",
        headers={
            "X-RapidAPI-Key": "eef0bc5beemsh95a4b94fdf020c5p1cb535jsn10c7bf23be2f",
            "X-RapidAPI-Host": "privatix-temp-mail-v1.p.rapidapi.com"
        })
    domains = domain_resp.json()
    username = ''.join(random.choices(string.ascii_lowercase + string.digits, k=10))
    address = username + random.choice(domains)
    return address, username

def inbox_tempmail(address):
    st.subheader("📬 Inbox per Temp-Mail: " + address)
    inbox_url = f"https://privatix-temp-mail-v1.p.rapidapi.com/request/mail/id/{address}/"
    headers = {
        "X-RapidAPI-Key": "eef0bc5beemsh95a4b94fdf020c5p1cb535jsn10c7bf23be2f",
        "X-RapidAPI-Host": "privatix-temp-mail-v1.p.rapidapi.com"
    }
    try:
        r = requests.get(inbox_url, headers=headers)
        if r.status_code != 200:
            st.warning("⚠️ Nessun messaggio trovato o indirizzo non ancora attivo.")
            return
        mails = r.json()
        if not mails:
            st.info("📭 Casella vuota.")
        for msg in mails:
            with st.expander(f"✉️ {msg.get('mail_from')} | {msg.get('mail_subject')}"):
                st.markdown(f"**Oggetto:** {msg.get('mail_subject')}")
                st.markdown(f"**Mittente:** {msg.get('mail_from')}")
                st.markdown(f"**Data:** {msg.get('mail_timestamp')}")
                st.markdown("---")
                st.markdown("**Contenuto:**")
                st.code(msg.get("mail_text_only", "Nessun contenuto"))
    except Exception as e:
        st.error(f"Errore nel recupero messaggi Temp-Mail: {e}")
