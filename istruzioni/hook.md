# Formule degli hook (v1 · 11 novembre 2026)

Adattate all'italiano e alla nostra pagina dalle 26 formule della libreria open source "instagram-agent-skill" (licenza MIT, di Jake Schincariol). Tenute solo quelle che funzionano senza volto, senza marchi, senza promesse mediche e senza storie personali inventate. L'id resta quello originale, così il report confronta le formule nel tempo.

## Regole

- Due hook partono insieme: la copertina (max 7 parole, la regola del progetto) e la prima riga della didascalia (le parole che la gente cerca). Non sono la stessa frase.
- Niente preamboli: si parte dalla frase che di solito arriverebbe al sesto secondo.
- Un numero vero batte "tanto" o "molte": gocce, minuti, oli, passi.
- La promessa dell'hook si mantiene entro metà video.
- Niente numeri o statistiche inventate: la formula 23 solo con dati certi e verificabili, altrimenti un'altra.
- Vietate le formule su soldi guadagnati, storie personali ("ho fatto", "ho perso"), insider, risultati di altre persone: non abbiamo un volto né una storia da raccontare e non vogliamo inventarla.

## Le formule

| id | nome | schema | esempio per la pagina | adatta a |
| --- | --- | --- | --- | --- |
| 2 | Ordine al contrario | Smetti di {gesto comune}. Fai {alternativa}. | Smetti di mettere 10 gocce. Ne bastano 4. | come si fa, errore da principiante |
| 3 | Nessuno te lo dice | Nessuno ti dice che {verità scomoda}. | Nessuno ti dice che l'olio scade. | mito, scheda |
| 5 | Tempo ridotto | Prima {tempo lungo}, ora {tempo corto}. | Casa profumata in 1 minuto, non in 10. | fai da te, casa profumata |
| 7 | Sbagliato, non per colpa tua | Lo fai nel modo sbagliato e non è colpa tua. | Usi il diffusore al contrario. Non è colpa tua. | come si fa |
| 9 | Prendilo e basta | Salva questo {strumento}. | Salva questa tabella delle gocce. | tabella da salvare, blend |
| 10 | Se ti succede, guarda | Se {situazione precisa}, questi {secondi} risolvono. | Se il diffusore non profuma, guarda qui. | come si fa, domanda (settimana 3) |
| 11 | Elenco con preferito | {N} {cose}. La numero {k} non la usa nessuno. | 3 usi della lavanda. Il terzo lo sbagliano tutti. | scheda, blend |
| 12 | L'obiezione | "{Obiezione vera}." Ecco la versione che funziona lo stesso. | "Non ho il diffusore." Ecco 2 modi senza. | non ce l'ho, domanda (settimana 3) |
| 13 | Prima e dopo | {Prima}. {Dopo}. {La leva in una frase}. | Stessa stanza, 2 gocce in più di cedro. | blend, rituale |
| 14 | Chiamata diretta | {Gruppo preciso}, questo è per te. | Hai appena comprato il kit? Questo è per te. | kit finalmente chiaro |
| 16 | La domanda vera | "{Domanda esatta come la fanno}" | "Quante gocce nel diffusore?" | domanda (settimana 3), tabella |
| 17 | Testa a testa | {A} o {B}? Uno dei due vince netto. | Lavanda o camomilla per la sera? | blend, non ce l'ho |
| 18 | Si parte dall'azione | {Già nel gesto}. Guarda cosa succede. | 3 gocce sul sale grosso. Guarda. | fai da te |
| 20 | Permesso | Non ti serve {ciò che tutti dicono}. | Non ti servono 20 oli. Te ne bastano 3. | kit, errore da principiante |
| 22 | Detto al contrario | {Detto noto, capovolto}. | Meno gocce, più profumo. | mito, momento |
| 23 | Il dato | {N}% di {gruppo} {fatto sorprendente}. | Solo con dati certi, altrimenti un'altra formula. | mito, scheda |
| 24 | La rivelazione | Questo è {la cosa}. | Questo è il blend dell'autunno. | blend, rituale, scheda |
| 26 | Il superlativo | Il modo più {veloce/semplice} per {risultato} è {risposta}. | Il modo più semplice per profumare l'armadio. | fai da te, casa profumata |

## Come si usano

- Ogni reel (mezzogiorno e pillola) usa una formula: scegli quella che si adatta meglio al tema, non ripetere la stessa formula due giorni di fila sulla stessa fascia e prova tutte le formule adatte nell'arco di due settimane.
- Settimana di test 3 (23-29/11, hook a domanda): solo le formule 10, 12, 16, 17.
- Per ogni reel scrivi 3 hook candidati (formule diverse o varianti della stessa) e valutali tutti insieme con `python3 tools/ig_it/hookscore_it.py <file con un hook per riga>`. Usa il primo in classifica; se il primo è sotto 60, riscrivi i candidati una volta partendo dalla proprietà più debole indicata dallo script. A parità di punteggio (meno di 5 punti di differenza) scegli tu: lo script non sa distinguere tra hook discreti.
- Scrivi l'id nel campo "formula" del contenuto e aggiungi una riga a hook_log.csv: data;fascia;formula;hook;punteggio (fascia = mezzogiorno o sera; punteggio = quello di hookscore_it.py).
