#!/usr/bin/env python3
"""Da eseguire UNA VOLTA sul tuo PC: ottiene il refresh token di TikTok.
Chiave e segreto restano sul tuo computer (nessuno li vede). Uso: python3 tiktok_auth.py
"""
import getpass, json, secrets, urllib.parse, urllib.request, webbrowser

REDIRECT = "https://kimi1997.github.io/laviadellaromaterapia-reels/callback"
SCOPES = "user.info.basic,video.upload,video.publish"

key = input("Client key: ").strip()
sec = getpass.getpass("Client secret (non si vede mentre scrivi): ").strip()
state = secrets.token_urlsafe(8)
url = "https://www.tiktok.com/v2/auth/authorize/?" + urllib.parse.urlencode({
    "client_key": key, "scope": SCOPES, "response_type": "code",
    "redirect_uri": REDIRECT, "state": state})
print("\nSi apre il browser: accedi a TikTok e premi Autorizza.")
print("Poi finirai su una pagina 'non trovata': e' normale. Copia l'INTERO indirizzo dalla barra.\n")
webbrowser.open(url)
back = input("Incolla qui l'indirizzo: ").strip()
q = urllib.parse.parse_qs(urllib.parse.urlparse(back).query)
if q.get("state", [""])[0] != state or "code" not in q:
    raise SystemExit("Indirizzo non valido o state diverso.")
body = urllib.parse.urlencode({"client_key": key, "client_secret": sec, "code": q["code"][0],
                               "grant_type": "authorization_code", "redirect_uri": REDIRECT}).encode()
req = urllib.request.Request("https://open.tiktokapis.com/v2/oauth/token/", body,
                             {"Content-Type": "application/x-www-form-urlencoded"})
d = json.loads(urllib.request.urlopen(req).read())
if "refresh_token" not in d:
    raise SystemExit("Errore: " + json.dumps({k: v for k, v in d.items() if "token" not in k}))
print("\nOttimo. Salva questo valore nel segreto TIKTOK_REFRESH_TOKEN del repository (non incollarlo in chat):\n")
print(d["refresh_token"])
