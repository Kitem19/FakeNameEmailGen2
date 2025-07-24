# 👤 Generatore di Profili Fake con Email Temporanea

Questa applicazione Streamlit genera profili fittizi completi di dati personali e email temporanee funzionanti da tre provider diversi:

## ✨ Funzionalità

- Selezione del paese (Italia, Francia, Germania, Lussemburgo)
- Dati generati:
  - Nome, Cognome, Data di nascita, Indirizzo, IBAN
  - Email temporanea
  - Opzionali: Telefono, Codice Fiscale, Partita IVA
- Scelta del provider email temporaneo:
  - ✅ `mail.tm` (con dominio selezionabile)
  - ✅ `1secmail.com`
  - ✅ `GuerrillaMail`
- Inbox email integrata per ogni provider
- Esportazione dei profili in formato CSV

## 🚀 Come eseguirlo in locale

1. Clona il repository:
```bash
git clone https://github.com/tuo-username/fake-profile-generator.git
cd fake-profile-generator
```

2. Installa i requisiti:
```bash
pip install -r requirements.txt
```

3. Avvia Streamlit:
```bash
streamlit run generatore_profili_email_multiprovider.py
```

## ☁️ Deploy su Streamlit Cloud

1. Carica il codice su GitHub
2. Vai su [streamlit.io/cloud](https://streamlit.io/cloud)
3. Collega il tuo repo e avvia l'app

## 📦 Requisiti

- Python 3.7+
- Librerie: `streamlit`, `faker`, `pandas`, `requests`

## 📄 Licenza

Questo progetto è open-source per uso educativo e di test. Non utilizzare per scopi illegali o di spam.

---

Creato con ❤️ da [Il Tuo Nome]
