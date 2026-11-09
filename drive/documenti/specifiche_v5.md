# Specifiche dei template v5

Aggiornato al 7 novembre 2026, sera · In uso dall'8 novembre 2026 (reel delle 12, pillola della sera, carosello del sabato). L'aspetto delle schede è quello delle immagini v42_ in questa cartella; la 4.3 cambia il movimento, i tempi e il controllo dei testi (audit del 7/11). Le versioni precedenti sono in "Archivio template v3".

## Novità della v5 (brand identity del 9/11)

- Titoli sempre in Lora (hook, nomi degli oli, titoli di post e caroselli, chiusure); testi, etichette e handle in Poppins.
- Etichette sempre nell'accento della stagione con testo viola notte; niente più etichette viola, verdi o terracotta (restano solo i bollini VERO e FALSO).
- Colori e foto seguono la stagione, scelta dallo script in base alla data:

| Stagione | Mesi | Accento | Luce | Tinta dei fondi | Foto di chiusura |
| --- | --- | --- | --- | --- | --- |
| Autunno | set-nov | #D4A04E | #FADEA0 | #FBF6EF | foglie e tessuti caldi |
| Inverno | dic-feb | #C3CEE6 | #E3E9F5 | #F7F7FB | candele (a dicembre il Natale) |
| Primavera | mar-mag | #E8B0BF | #F8D9E1 | #FCF6F7 | lavanda e fiori |
| Estate | giu-ago | #E9C255 | #FBE7A6 | #FCFAF1 | limoni e agrumi |

- Un solo stile per tutti i caroselli (post del feed e carosello del sabato).
- Riassunto Facebook 1080×1350 nello stile del brand.
- Storie in evidenza: tre copertine viola notte con la goccia (in 01 Brand e Logo).
- Immagini di esempio: file v5_ in questa cartella (v5_L1 mostra la primavera). I template v4.2 sono in "Archivio template v4".

## Principi

- Solo foto vere (Pexels, licenza libera): niente illustrazioni disegnate che sembrano fatte con l'AI.
- Formato 1080×1920 (9:16), uguale per Instagram e TikTok.
- Tutto il testo resta dentro la zona sicura, lontano da pulsanti, didascalia e barre delle app.
- Zoom lento e fluido (Ken Burns morbido), oppure nessuno zoom.

## Zona sicura (pixel su 1080×1920)

| Margine | Valore | Perché |
| --- | --- | --- |
| Sinistra | 70 | bordo schermo |
| Destra | 880 | colonna dei pulsanti (like, commenti, condividi) |
| Alto | 210 | nome profilo e barra "Seguiti / Per te" |
| Basso | 1460 | didascalia, audio e barra di navigazione |

Se il testo non ci sta, lo script riduce il carattere da solo (fino al 62%) finché tutto rientra.

## Movimento e tempi (v4.3)

- Copertina di 1,8-2,2 secondi: zoom del 7% che parte veloce e rallenta, testo che si assesta dal 105% al 100% nei primi 0,35 secondi. Il primo fotogramma ha già tutto il testo leggibile, perché Instagram lo usa come copertina.
- Altre scene: zoom del 3,5% con accelerazione e frenata morbide, calcolato sotto il pixel (niente tremolio).
- Tagli secchi tra le scene, senza dissolvenze: il reel può ripartire in loop.
- Durata: rubrica 20-30 secondi, pillola 12-18 (oppure il campo "durata" nel JSON, usato nei test). Lo script accorcia le scene se si supera il massimo e avvisa se si resta sotto il minimo.

## Testi (v4.3)

- Hook di massimo 7 parole, con un numero o una tensione.
- Massimo 25 parole per schermata: il dettaglio va in didascalia.
- La chiusura rimanda all'inizio (loop); campo facoltativo "cta_sub" per la riga sotto la CTA (per esempio "La tabella delle gocce, gratis").
- Prima di ogni video lo script controlla i testi (`--controllo`): hook lungo, schermate troppo piene, parole da evitare (salute, terapie, accessori nati per altro).

## Tipi di scheda

| File | Scheda | Uso |
| --- | --- | --- |
| v42_A_copertina | Copertina a tutta foto con hook | Prima scena di ogni reel |
| v42_B_consiglio_momento | Foto in alto, pannello con momento e modo d'uso | Lunedì, "Un olio per ogni momento" |
| v42_C_chiusura | Chiusura scura con CTA e logo | Ultima scena |
| v42_D_blend | Ricetta con oli e gocce | Mercoledì, "Il blend della settimana" |
| v42_E_consiglio | Foto e consiglio numerato | Martedì e giovedì |
| v42_F_vero_falso | Credenza con verdetto VERO / FALSO / DIPENDE | Venerdì, "Vero o falso?" |
| v42_G_rituale | Passo del rituale | Sabato, "Il rituale di stagione" |
| v42_H_scheda_olio | Profumo, abbinamenti, usi, "Se non ce l'hai" | Domenica, "La scheda dell'olio" |
| v42_I_pillola_copertina | Copertina con il nome della serie | Pillola della sera |
| v42_L1/L2/L3 | Copertina, slide e chiusura del carosello | Carosello del sabato |

## Post del feed (dal 10/11)

Caroselli 1080×1350 alle 9:00 e alle 16:00, con uno stile editoriale diverso dai reel:

- Copertina: foto a tutta pagina, etichetta oro con il pilastro (L'ESSERE UMANO, I CINQUE SENSI, STRATEGIA, EMOZIONI, NATURA E COSMO, PIANTE AROMATICHE), titolo in serif bianco, freccia "Scorri".
- Slide di testo: fondo crema, logo viola in alto, numero grande in trasparenza, titolo serif viola, testo fino a 45 parole. Nessuna foto: così le foto stock non si ripetono troppo.
- Chiusura: foto scura con il logo, la domanda per i commenti e "salva il post".

Esempi: v5_L2, v5_L3, v5_L4 in questa cartella.

## Foto

- 70 foto in 18 categorie, nel repository GitHub (stock/, con catalogo.json).
- Il ritaglio segue il soggetto della foto (zone con più dettaglio, preferenza per il centro).
- La copertina non si ripete negli ultimi 7 contenuti; la pillola usa una foto diversa dal reel di mezzogiorno.
- Niente foto con marchi o etichette leggibili, niente oggetti nati per altro.

## Script

reel.py v5, nel Drive in 05 Automazione, nell'archivio su Claude e su GitHub (drive/automazione/reel.py). Opzione --v3 per tornare ai vecchi template in caso di problemi.
