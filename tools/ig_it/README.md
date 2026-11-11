# Strumenti in italiano (11/11/2026)

Adattati da instagram-agent-skill di Jake Schincariol (licenza MIT, in LICENSE-instagram-agent-skill). Girano in locale, senza rete.

- `hookscore_it.py`: valuta gli hook di copertina su 5 proprietà (lunghezza 3-7 parole, concretezza con numeri e nomi di oli e oggetti, tensione, punto forte in testa, chi guarda chiamato in causa). Uso: `python3 hookscore_it.py hook.txt` (un hook per riga, li ordina) oppure `--hook "testo"`, `--json`.
- `humanize_it.py`: pulisce una didascalia: caratteri invisibili, lineette lunghe, frasi fatte da AI in italiano (sostituite o tolte). Uso: `python3 humanize_it.py didascalia.txt > pulita.txt`.
- `detect_it.py`: punteggio "umano" della didascalia (PASS, REVIEW, FLAGGED) su varietà delle frasi, concretezza, frasi fatte, caratteri sospetti, voce diretta. Uso: `python3 detect_it.py didascalia.txt`.
- `slop_it.json`: il lessico italiano usato dai due script. "Essenziale" non è mai trattato come frase fatta.

Limite noto (dall'autore originale): il valutatore distingue bene un hook debole da uno buono, ma non sa scegliere tra due hook discreti. Per questo il report del lunedì confronta il punteggio con la tenuta a 3 secondi reale: dopo 4 settimane sapremo quanto fidarci sulla nostra pagina.
