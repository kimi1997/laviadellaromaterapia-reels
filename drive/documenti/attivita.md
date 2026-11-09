# Attività automatiche – istruzioni

Aggiornato al 9 novembre 2026, sera (post del feed, brand identity e template v5). La versione in uso è quella salvata nelle attività pianificate su Claude: questo documento ne è il riassunto ufficiale e va aggiornato a ogni modifica.

| Attività | Quando | Cosa fa | Connettori |
| --- | --- | --- | --- |
| Reel giornaliero oli essenziali (giro pesante) | Ogni giorno 11:57 (Roma) | Crea e pubblica il reel delle 12 + riassunto Facebook; crea la pillola della sera (dom-ven) o il carosello (sab) e li lascia pronti su GitHub; dom, lun, mer, gio, sab programma TikTok su Metricool per le 18:30 (max 19 al mese) | Windsor.ai, Metricool, GitHub |
| Reel della sera oli essenziali (giro leggero) | Ogni giorno 19:23 | Pubblica soltanto: la pillola (dom-ven) o il carosello (sab) preparati a mezzogiorno | Windsor.ai, GitHub |
| Post del feed oli essenziali (9:00 e 16:00) | Ogni giorno 8:53 e 15:53 | Pubblica soltanto il carosello preparato il giorno prima (cartella post/ su GitHub) | Windsor.ai, GitHub |
| Report settimanale Instagram oli essenziali | Lunedì 8:43 | Numeri degli ultimi 28 giorni in 07 Performance + riepilogo, con l'esito della settimana di test; il primo lunedì del mese pulisce GitHub (media più vecchi di 30 giorni) | Windsor.ai, GitHub, Google Drive |

Dal 7/11 pomeriggio: un solo giro pesante al giorno per risparmiare utilizzo di Claude. Dal 9/11, con i post del feed, le esecuzioni sono 29 a settimana (7 pesanti e 22 leggere). Le vecchie attività "Carosello del sabato" e "TikTok" separata non esistono più; il vecchio reel giornaliero è disattivato ([SOSTITUITA]).

Tutte girano con approvazione automatica e mandano una notifica sul telefono.

## Novità del 9/11 sera (brand identity, script v5)

- Tutti i titoli in Lora, testi in Poppins; etichette, numeri e fondi nei colori della stagione, che lo script sceglie da solo dalla data (stampa STAGIONE). Anche la foto di chiusura segue la stagione.
- Un solo stile per tutti i caroselli: il carosello del sabato esce come i post del feed, con l'etichetta IL RITUALE DI STAGIONE.
- Riassunto Facebook rifatto nello stile del brand (1080×1350, foto in alto e pannello con i punti).
- Linguaggio: "rimedio", "ansia", "stress", "relax" permessi come parole di tutti i giorni; restano vietati il linguaggio medico e le promesse (cura, guarisce, terapia, malattie, farmaci, "elimina", "fa sparire").
- Copertine delle storie in evidenza: python3 reel.py cartella --evidenza.
- Regole complete nel Design System del brand (01 Brand e Logo, Brand guidelines).

## Novità del 7/11 sera (audit)

- Script reel.py v4.3: copertina di 2 secondi con zoom del 7% e testo che si muove dal primo fotogramma, tagli secchi tra le scene, durata 20-30 s (rubrica) e 12-18 s (pillola), controllo automatico dei testi prima del video (`python3 reel.py contenuti.json --controllo` deve dire OK).
- Hook di massimo 7 parole con un numero o una tensione; massimo 25 parole per schermata; chiusura che rimanda all'inizio (loop).
- Didascalie con 4-6 hashtag di nicchia e le parole che la gente cerca nella prima riga.
- Piano di test, una variabile a settimana: 9-15/11 base; 16-22/11 durata 15-20 s (campo "durata": [15, 20]); 23-29/11 hook a domanda; 30/11-6/12 CTA "Commenta TABELLA e te la mando" (campo "cta_sub"), con la tabella mandata a mano in direct.
- Il messaggio di mezzogiorno indica la settimana di test, propone la storia del giorno e ricorda i 15 minuti di community.
- Il report del lunedì confronta ogni settimana di test con la base, giudica una rubrica solo dopo 6 contenuti da almeno 300 visualizzazioni e usa come metro skip rate sotto il 60%, 5 salvataggi a contenuto e le email.

## 1. Reel giornaliero

**A chi parla (dall'analisi community)**

- **Francesca, la principiante con il kit**: come si usa, quante gocce, con cosa sostituire, scade?, quale diffusore.
- **Laura, la mamma che gestisce la casa**: ricette pronte per casa, armadi, bucato, odori, momenti di famiglia.
- **Paola, la cercatrice di rituali**: luna, stagioni, momenti per sé, note di testa, cuore e fondo.

**Posizionamento e neutralità**: "oli essenziali spiegati da chi non te li vende". Nessun marchio, nessuna miscela commerciale con nome proprio, nessun gergo da rete; solo nomi comuni degli oli; i consigli valgono per qualsiasi marca.

**Rubrica dal giorno della settimana**

| Giorno | Codice | Rubrica | Contenuto richiesto |
| --- | --- | --- | --- |
| Lunedì | momento | Un olio per ogni momento | 4 oli, ognuno con momento e modo d'uso |
| Martedì | comesifa | Come si fa | 3-5 consigli sulle domande pratiche di chi inizia |
| Mercoledì | blend | Il blend della settimana | Ricetta con 2-4 oli e gocce (4-8 in totale) + 2-3 consigli d'uso, tra cui l'alternativa se manca un olio |
| Giovedì | faidate | Fai da te per la casa | 3-5 consigli |
| Venerdì | mito | Vero o falso? | 1-3 credenze con verdetto VERO / FALSO / DIPENDE e spiegazione |
| Sabato | rituale | Il rituale di stagione | 3 passi + versione carosello con 4-6 slide |
| Domenica | scheda | La scheda dell'olio | Profumo, abbinamenti, 3 usi, "Se non ce l'hai" + 0-2 consigli |

**Serie ricorrenti**: "Non ce l'ho? Usa questo", "La tabella da salvare", "Il tuo kit, finalmente chiaro", "La valigia aromatica".

**Tema**: dal calendario fino al 6 dicembre (Piano editoriale in 03); poi lo sceglie l'agente per rubrica e persona, partendo dalle domande della community, senza ripetere temi o oli protagonisti delle ultime 8 settimane né il tema della pillola della sera prima (registro temi.csv su GitHub).

**Passi**

1. Sceglie rubrica e tema; clona il repository (che contiene anche le foto stock in stock/) e controlla temi.csv e i file già pubblicati oggi.
2. Scarica dall'archivio su claude.ai lo script reel.py (v4.3), il logo ufficiale e la traccia audio adatta al tema.
3. Scrive contenuti.json nel formato della rubrica, con il campo facoltativo "foto" per scegliere la copertina (categoria o file). Hook max 7 parole con un numero o una tensione, max 25 parole per schermata; CTA che chiude il cerchio con l'hook e alterna salva, condividi e "mandalo a chi ha appena comprato i suoi primi oli". Applica la variante della settimana di test. Lancia il controllo dei testi.
4. Genera il reel con STOCK_DIR puntato alla cartella stock/: copertina a tutta foto di 2 secondi con il testo in movimento, consigli con la foto dell'olio in alto, chiusura scura, tagli secchi. Poi il riassunto Facebook e il sabato il carosello (copertina in foto). Controlla i fotogrammi, la leggibilità del testo sulla foto e che la copertina non sia la stessa degli ultimi 7 contenuti.
5. Scrive le didascalie: Instagram con gancio da una domanda reale, domanda della rubrica e 4-6 hashtag di nicchia; una volta a settimana la frase "Qui gli oli te li spieghiamo, non te li vendiamo"; Facebook con il nome della rubrica nel titolo e 3-5 hashtag; il sabato anche quella del carosello.
6. Carica su GitHub reel, riassunto, (sabato) slide e didascalia del carosello, aggiorna temi.csv (data;rubrica;tema;hook;foto), verifica i link.
7. Pubblica una sola volta: reel su Instagram (copertina = primo fotogramma) e riassunto su Facebook.
8. Manda a Michele video, immagine, esiti, settimana di test, didascalie e la storia del giorno con il promemoria dei 15 minuti di community.

**Regole dei contenuti, sempre valide (anche per il reel della sera)**

- TONO: confidenziale come un'amica, rassicurante, non commerciale, con l'atmosfera di una spa e una curiosità che invita a guardare altri post. "Rimedi", ansia, stress e relax sì, come parole di tutti i giorni; niente linguaggio medico né promesse (cura, guarisce, terapia, malattie, farmaci, medici, gravidanza).
- MISURA: quantità moderate dentro la ricetta; sulla pelle sempre in olio vettore, mai puro; mai ingestione né uso in cucina; nel dubbio si omette.
- ACCESSORI: solo strumenti pensati per gli oli essenziali o materiali naturali assorbenti; mai prodotti nati per altro.
- NEUTRALITÀ: nessun marchio, nessuna miscela commerciale, nessun gergo da rete.

## 1b. Post del feed (creati a mezzogiorno per il giorno dopo, pubblicati alle 9:00 e alle 16:00)

Su Instagram reel e post si alternano: post alle 9:00, reel alle 12, post alle 16:00, reel alle 19:30. I post sono caroselli a sé, mai sullo stesso olio o tema dei reel vicini.

| Pilastro | Di cosa parla |
| --- | --- |
| L'essere umano (umano) | Abitudini, ritmi, pause, il rapporto tra persone e profumi nella storia e nelle culture |
| I cinque sensi (sensi) | Olfatto soprattutto, ma anche gli altri sensi e come si intrecciano con il profumo |
| Strategia (strategia) | Il pensiero dietro le scelte: abitudini, rituali, come costruire il proprio kit nel tempo |
| Emozioni (emozione) | Stati d'animo, atmosfere, profumi e ricordi |
| Natura e cosmo (cosmo) | Luna, stagioni, elementi, energie e tradizioni: sempre come racconto, mai come promessa |
| Piante aromatiche (pianta) | Curiosità su una pianta: nome, botanica, storia, leggende, distillazione (niente ricette) |

Rotazione (mattina / pomeriggio): lunedì umano / cosmo · martedì sensi / pianta · mercoledì emozione / pianta · giovedì strategia / sensi · venerdì cosmo / umano · sabato pianta / emozione · domenica strategia / pianta.

Formato: titolo max 9 parole, 4-6 slide di testo (max 45 parole l'una), domanda finale; copertina e chiusura in foto, slide di testo su crema con titoli serif. Comando: `python3 reel.py post.json cartella` (il controllo dei testi con `--controllo`). File su GitHub in post/AAAA-MM-GG-mattina/ e post/AAAA-MM-GG-pomeriggio/ con slide, didascalia.txt e contenuti.json; riga "post" in temi.csv.

## 2. Pillola della sera (creata a mezzogiorno, pubblicata alle 19:30; 12-18 secondi, 1-2 consigli)

**Serie per giorno**

| Giorno | Serie |
| --- | --- |
| Lunedì | Non ce l'ho? Usa questo |
| Martedì | Il tuo kit, finalmente chiaro |
| Mercoledì | La tabella da salvare |
| Giovedì | Casa profumata in 1 minuto |
| Venerdì | L'errore da principiante |
| Sabato | Il profumo della sera |
| Domenica | La valigia aromatica / Prepara la settimana (alternate) |

1. Il giro di mezzogiorno legge temi.csv (riga del giorno e pillole delle ultime 6 settimane).
2. Sceglie un tema nella serie, collegato al reel di mezzogiorno ma senza ripeterne i consigli.
3. Scrive contenuti.json con rubrica "pillola", il campo "serie" (mostrato in copertina) e 1-3 consigli; sceglie una copertina diversa da quella di mezzogiorno.
4. Genera il reel (12-18 secondi) con le foto stock, controlla tutti i fotogrammi.
5. Didascalia con gancio, 2-4 righe, una domanda, "Ogni sera alle 19:30 una nuova pillola" e 4-6 hashtag con #pilloladellasera.
6. Carica su GitHub reels/reel_AAAA-MM-GG-sera.mp4 e sera/AAAA-MM-GG/didascalia.txt e aggiorna temi.csv. Alle 19:23 il giro leggero pubblica una sola volta su Instagram, scrive pubblicato.txt e avvisa Michele. Il sabato niente pillola: alle 19:30 esce il carosello.

## 3. TikTok (dentro il giro di mezzogiorno)

1. Clona il repository e conta i post del mese in tiktok/registro.csv: con 19 o più si ferma (piano gratuito Metricool: 20 al mese).
2. Prende reels/reel_AAAA-MM-GG.mp4 (il reel di mezzogiorno) e la riga di oggi in temi.csv.
3. Scrive una didascalia TikTok breve (max 300 caratteri, 3-5 hashtag) con le stesse regole di tono e neutralità.
4. Programma il post su Metricool per le 18:30, una sola volta, aggiorna il registro e avvisa Michele.
5. TikTok è collegato a Metricool (brand 7939577); Windsor serve solo per leggere i numeri.

## 4. Carosello del sabato (pubblicato dal giro leggero alle 19:30)

1. Clona il repository e cerca caroselli/AAAA-MM-GG/ con le slide e didascalia.txt.
2. Se mancano i file, o se c'è già pubblicato.txt, non pubblica e avvisa.
3. Verifica i link e pubblica una sola volta come carosello.
4. Scrive pubblicato.txt con l'id e avvisa Michele.

## 5. Report del lunedì (con pulizia mensile di GitHub il primo lunedì del mese)

1. Legge da Windsor i dati di ogni contenuto degli ultimi 28 giorni: visualizzazioni, copertura, like, commenti, salvataggi, condivisioni, tempo medio di visione, skip rate; legge anche i follower.
2. Abbina ogni contenuto alla sua rubrica e fascia (mezzogiorno, sera, carosello) tramite temi.csv e l'ora di pubblicazione; i contenuti di prova del 5-6 novembre sono esclusi dalle medie.
3. Crea il foglio "Report AAAA-MM-GG" in 07 Performance (con medie per rubrica e "Mezzogiorno vs sera") e salva una copia in report/ su GitHub.
4. Manda a Michele 5-7 righe: skip rate, visione in % sulla durata, salvataggi, follower, esito della settimana di test, confronto mezzogiorno/sera, una proposta che rispetti il piano di test e (dal 23/11) l'eventuale reel da sponsorizzare. Una rubrica si giudica solo dopo 6 contenuti da almeno 300 visualizzazioni. Le proposte non si applicano da sole.

## File in questa cartella

- reel.py (v5) – lo script generatore (copia di tools/reel.py.txt nell'archivio e di drive/automazione/reel.py su GitHub)
- esempio_sera_pillola.json, esempio_domenica_scheda.json, esempio_post.json – esempi del formato dei contenuti
- Le foto stock e catalogo.json sono nel repository GitHub, cartella stock/ (troppo pesanti per duplicarle qui)
