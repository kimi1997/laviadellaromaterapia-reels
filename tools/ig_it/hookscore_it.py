#!/usr/bin/env python3
"""
hookscore_it.py - versione italiana (11/11/2026, La via dell'aromaterapia) di hookscore.py
da instagram-agent-skill di Jake Schincariol, licenza MIT (vedi LICENSE-instagram-agent-skill).

hookscore.py - score the first line of a Reel on the five things strong hooks
have in common, and rank a batch of them against each other.

What this is:  five local heuristics, computed on your machine from the text
alone. They measure properties that hooks which hold attention tend to share -
a length you can say in under three seconds, a concrete marker, something at stake,
the payload at the front rather than the back, and a viewer to aim it at.

What this is NOT:  a view predictor. It was tested against 74 real short-form
hooks, transcribed from the first three seconds of the top eight and bottom
eight performers on five channels. Separating a real hook from a deliberately
bad one it does well: AUC 0.83, and 9 of 10 written-to-be-bad hooks scored
below the real median. Separating a good creator's hits from that same
creator's misses it barely does at all: AUC 0.56, where 0.50 is a coin flip.

So use it for what it measured well. It catches greetings, preambles, hooks
with nothing concrete in them and hooks that take five seconds to say. It will
not tell you which of two decent hooks will travel, and nothing that reads text
can, because that is decided by your face, your edit, your audio and who
Instagram shows it to. Trust the retention graph over this script.

Each check returns 0 to 100. Higher is better.

Usage
  python3 hookscore.py hooks.txt              # one hook per line, ranked
  python3 hookscore.py --hook "I lost $18,000 on one missing contract."
  pbpaste | python3 hookscore.py -
  python3 hookscore.py hooks.txt --json
"""

import argparse
import json
import re
import statistics
import sys

WORD_RE = re.compile(r"[A-Za-zÀ-ÿ0-9€$%'’-]+")
NUMBER_RE = re.compile(
    r"€\s?\d[\d.,]*|\b\d[\d.,]*\s?"
    r"(?:%|€|gocce\b|goccia\b|ml\b|min\b|minuti\b|minuto\b|secondi\b|ore\b|giorni\b"
    r"|settimane\b|mesi\b|anni\b|oli\b|passi\b|modi\b|usi\b|errori\b)?",
    re.IGNORECASE)
PROPER_RE = re.compile(r"(?<!^)\b[A-ZÀ-Ý][a-zà-ÿ]{2,}\b")
HASHTAG_RE = re.compile(r"(?:^|\s)#\w+")
EMOJI_RE = re.compile(r"[\U0001F300-\U0001FAFF☀-➿]")

# Versione italiana per "La via dell'aromaterapia" (11/11/2026): numeri detti a
# parole ("sei" escluso: quasi sempre è il verbo), unità e nomi concreti della
# nicchia (oli, gocce, oggetti), parole che mettono qualcosa in gioco.
SPOKEN_NUMBERS = {
    "zero", "due", "tre", "quattro", "cinque", "sette", "otto", "nove", "dieci",
    "dodici", "quindici", "venti", "trenta", "cento", "mille", "doppio", "metà",
    "mezza", "mezzo", "dozzina", "unica", "unico",
}
MONEY_WORDS = {  # qui: unità e nomi concreti della nicchia
    "euro", "gocce", "goccia", "minuti", "minuto", "secondi", "ml",
    "lavanda", "menta", "limone", "arancio", "arancia", "eucalipto", "rosmarino",
    "cedro", "bergamotto", "camomilla", "cannella", "geranio", "incenso", "pino",
    "mandarino", "salvia", "timo", "ylang", "vaniglia", "agrumi", "pompelmo",
    "diffusore", "vettore", "pietra", "lavica", "sale", "cuscino", "armadio",
    "doccia", "candela", "kit", "flacone", "boccetta",
}
STAKES = {
    "smetti", "smettila", "mai", "sbagli", "sbagliato", "sbagliata", "sbagliano",
    "errore", "errori", "nessuno", "non", "niente", "nulla", "senza", "invece",
    "ma", "però", "solo", "soltanto", "già", "ancora", "prima", "segreto",
    "verità", "vero", "falso", "mito", "perdi", "spreco", "sprechi", "butti",
    "rovini", "rovina", "scade", "scaduto", "attenzione", "troppo", "troppe",
    "troppi", "basta", "bastano", "meno", "contro", "vs", "oppure", "davvero",
    "nascosto", "dimentichi", "evita", "tutti", "nessuna", "dimenticato",
    "funziona", "inutile", "peggiore", "migliore", "unico", "unica", "ultimo",
}
WEAK_OPENERS = [
    "allora", "ok", "okay", "ciao", "ehi", "buongiorno", "buonasera", "benvenuti",
    "benvenute", "oggi", "parliamo", "vediamo", "ecco a voi", "in questo",
    "voglio", "vi voglio", "ti voglio", "volevo", "come promesso", "c'è", "ci sono",
    "questo è", "si tratta", "quando si", "tanti", "molti", "un sacco",
]
IMPERATIVES = {
    "smetti", "prova", "salva", "usa", "metti", "aggiungi", "evita", "guarda",
    "leggi", "prendi", "ruba", "fai", "non", "mai", "sempre", "copia", "mescola",
    "accendi", "versa", "conta", "scegli", "lascia", "apri", "cambia", "tieni",
}

DEALBREAKERS = [
    (re.compile(r"(?i)^\s*(?:non scorrere|fermati|aspetta)"),
     "Apre chiedendo attenzione (\"non scorrere\"): chiederla dimostra di non averla guadagnata."),
    (re.compile(r"(?i)\b(?:in questo (?:video|reel|post)|oggi (?:vi|ti) (?:mostro|parlo|spiego)|(?:vi|ti) mostro come)\b"),
     "Preambolo: toglilo e parti dal punto."),
    (re.compile(r"(?i)^\s*(?:ciao|ehi|buongiorno|buonasera|benvenut)"),
     "Saluto: nessuno è venuto nel feed per essere salutato."),
    (HASHTAG_RE, "Hashtag nell'hook: vanno in fondo alla didascalia."),
    (EMOJI_RE, "Emoji nell'hook: in copertina c'è spazio per le parole, non per entrambe."),
]


def clamp(n):
    return max(0.0, min(100.0, n))


def words(text):
    # "$18,000" is one word when it is spoken, so it is one word here too.
    return WORD_RE.findall(re.sub(r"(?<=\d),(?=\d)", "", text))


def check_length(text):
    """A hook has to land before the thumb moves. Roughly two seconds."""
    w = words(text)
    n = len(w)
    secs = n / 2.75                      # ~165 words per minute, spoken
    chars = len(text.strip())
    if 3 <= n <= 7:                      # regola del progetto: copertina max 7 parole
        score = 100.0
    elif n < 3:
        score = clamp(100 - (3 - n) * 25)
    else:
        score = clamp(100 - (n - 7) * 15)
    if chars > 42:                       # due righe di testo grande in copertina
        score -= 12
    return clamp(score), f"{n} parole, {chars} caratteri, ~{secs:.1f}s (ideale 3-7 parole)"


def check_specificity(text):
    """One concrete thing beats three abstract ones."""
    nums = [n.strip() for n in NUMBER_RE.findall(text) if n.strip()]
    propers = set(PROPER_RE.findall(text))
    low = [w.lower().strip("'’") for w in words(text)]
    spoken = [w for w in low if w in SPOKEN_NUMBERS or w in MONEY_WORDS]
    hits = len(nums) + len(propers) + len(spoken)
    score = 15.0 if hits == 0 else clamp(45 + hits * 30)
    found = ", ".join(nums[:2] + sorted(propers)[:2] + spoken[:2])
    return score, (f"{hits} concrete marker(s)" + (f": {found}" if found else
                   " - no number, no name, nothing checkable"))


def check_stakes(text):
    """Tension, cost, negation. Something the viewer might lose."""
    w = [x.lower().strip("'’") for x in words(text)]
    hits = [x for x in w if x in STAKES]
    markers = sorted(set(hits))
    if re.search(r"[€$]\s?\d", text):
        markers.append("un prezzo")
    if len(re.findall(r"\d+", text)) >= 2:
        markers.append("contrasto tra due numeri")
    if "?" in text:
        markers.append("domanda")
    n = len(markers)
    score = {0: 20.0, 1: 70.0}.get(n, 100.0)
    detail = f"{n} tension marker(s)" + (f": {', '.join(markers[:4])}" if markers else
                                         " - nothing is at stake in this line")
    return clamp(score), detail


def check_frontload(text):
    """The interesting word cannot be in position nine."""
    w = words(text)
    if not w:
        return 0.0, "empty"
    low = [x.lower().strip("'’") for x in w]
    opener = " ".join(low[:2])
    penalty = 0
    hit_opener = None
    for weak in WEAK_OPENERS:
        if opener.startswith(weak) or low[0] == weak:
            penalty, hit_opener = 30, weak
            break
    payload = None
    for i, token in enumerate(low):
        if (token in STAKES or token in SPOKEN_NUMBERS or token in MONEY_WORDS
                or NUMBER_RE.match(w[i]) or (i and PROPER_RE.match(w[i]))):
            payload = i
            break
    if payload is None:
        base = 30.0
        where = "no payload word anywhere in the line"
    elif payload <= 3:
        base = 100.0
        where = f"payload at word {payload + 1}"
    elif payload <= 6:
        base = 70.0
        where = f"payload at word {payload + 1}, could move forward"
    else:
        base = 40.0
        where = f"payload at word {payload + 1}, too late"
    detail = where + (f"; weak opener \"{hit_opener}\"" if hit_opener else "")
    return clamp(base - penalty), detail


def check_address(text):
    """Aimed at one viewer, or floating in the air."""
    low = text.lower()
    w = [x.lower().strip("'’") for x in words(text)]
    if re.search(r"\b(tu|ti|te|tuo|tua|tuoi|tue|hai|sei|fai|usi|metti|vuoi|puoi|sai|sbagli|compri|conosci)\b", low):
        return 100.0, "parla a chi guarda"
    if w and w[0] in IMPERATIVES:
        return 90.0, f"apre con un imperativo (\"{w[0]}\")"
    if re.search(r"\b(io|mio|mia|miei|noi|nostro|nostra|ho|abbiamo)\b", low):
        return 70.0, "prima persona, nessuno chiamato in causa"
    if "?" in text:
        return 80.0, "domanda diretta"
    return 35.0, "terza persona, nessuno nella stanza"


CHECKS = ["LENGTH", "SPECIFICITY", "STAKES", "FRONTLOAD", "ADDRESS"]


def run(text):
    results = {
        "LENGTH": check_length(text),
        "SPECIFICITY": check_specificity(text),
        "STAKES": check_stakes(text),
        "FRONTLOAD": check_frontload(text),
        "ADDRESS": check_address(text),
    }
    flags = [msg for pattern, msg in DEALBREAKERS if pattern.search(text)]
    scores = [results[c][0] for c in CHECKS]
    # The weakest property caps the hook, same logic as detect.py: one bad
    # property is enough for the thumb to keep moving.
    overall = statistics.mean(scores) * 0.6 + min(scores) * 0.4 - len(flags) * 15
    overall = clamp(overall)
    verdict = "STRONG" if overall >= 70 and min(scores) >= 55 and not flags else (
        "OK" if overall >= 50 else "WEAK")
    return results, overall, verdict, flags


def bar(score, width=24):
    filled = round(score / 100 * width)
    return "#" * filled + "." * (width - filled)


def render_one(text, results, overall, verdict, flags, out=sys.stdout):
    print("\nHOOK SCORE", file=out)
    print("=" * 62, file=out)
    print(f"  \"{text.strip()}\"\n", file=out)
    for name in CHECKS:
        score, detail = results[name]
        print(f"  {name:<13} {bar(score)} {score:5.1f}", file=out)
        print(f"  {'':<13} {detail}", file=out)
    print("-" * 62, file=out)
    print(f"  {'HOOK SCORE':<13} {bar(overall)} {overall:5.1f}   {verdict}", file=out)
    for f in flags:
        print(f"\n  DEALBREAKER  {f}", file=out)
    if verdict != "STRONG":
        weakest = min(CHECKS, key=lambda c: results[c][0])
        print(f"\n  Weakest property: {weakest}. Fix that one and re-run.", file=out)
    print("", file=out)


def render_table(rows, out=sys.stdout):
    print("\nHOOK RANKING\n" + "=" * 78, file=out)
    for i, r in enumerate(rows, 1):
        mark = "->" if i == 1 else "  "
        hook = r["hook"] if len(r["hook"]) <= 62 else r["hook"][:59] + "..."
        print(f"{mark} {r['score']:5.1f} {r['verdict']:<7} {hook}", file=out)
        print(f"        weakest: {r['weakest']} ({r['checks'][r['weakest']]['score']:.0f})", file=out)
        for f in r["flags"]:
            print(f"        dealbreaker: {f}", file=out)
    print("\nUsa il primo. Se il primo è sotto 50, nessuno di questi è l'hook giusto.\n",
          file=out)


def main():
    ap = argparse.ArgumentParser(description="Score a Reel hook on five properties.")
    ap.add_argument("input", nargs="?", default="-", help="file with one hook per line, or -")
    ap.add_argument("--hook", help="score a single hook given on the command line")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    if args.hook:
        lines = [args.hook]
    else:
        raw = sys.stdin.read() if args.input == "-" else open(args.input, encoding="utf-8").read()
        lines = [l.strip() for l in raw.splitlines() if l.strip()]
    if not lines:
        print("nothing to score", file=sys.stderr)
        sys.exit(2)

    payload = []
    for line in lines:
        results, overall, verdict, flags = run(line)
        payload.append({
            "hook": line,
            "checks": {k: {"score": round(v[0], 1), "detail": v[1]} for k, v in results.items()},
            "weakest": min(CHECKS, key=lambda c: results[c][0]),
            "flags": flags,
            "score": round(overall, 1),
            "verdict": verdict,
        })

    if args.json:
        print(json.dumps(payload if len(payload) > 1 else payload[0], indent=2, ensure_ascii=False))
        return

    if len(payload) == 1:
        results, overall, verdict, flags = run(lines[0])
        render_one(lines[0], results, overall, verdict, flags)
    else:
        render_table(sorted(payload, key=lambda r: -r["score"]))

    sys.exit(0 if max(p["score"] for p in payload) >= 70 else 1)


if __name__ == "__main__":
    main()
