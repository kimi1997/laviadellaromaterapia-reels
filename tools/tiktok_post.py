#!/usr/bin/env python3
"""Carica un reel su TikTok con la Content Posting API (solo libreria standard).

Uso:
  python3 tools/tiktok_post.py --quale sera [--data AAAA-MM-GG] [--modo inbox|direct] [--dry-run]
  python3 tools/tiktok_post.py --video reels/x.mp4 --didascalia-file sera/x/didascalia.txt

Variabili d'ambiente (segreti del repository, mai nel codice):
  TIKTOK_CLIENT_KEY, TIKTOK_CLIENT_SECRET, TIKTOK_REFRESH_TOKEN

Modo inbox (predefinito): il video arriva nelle bozze di TikTok e si pubblica con un tocco.
Modo direct: pubblica subito; finche' l'app non supera l'audit TikTok risulta privato.
"""
import argparse, json, os, sys, time, urllib.request, urllib.parse, urllib.error
from datetime import datetime
from zoneinfo import ZoneInfo

API = "https://open.tiktokapis.com"
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def http(url, data=None, headers=None, method=None):
    req = urllib.request.Request(url, data=data, headers=headers or {}, method=method)
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            body = r.read().decode("utf-8", "replace")
            return r.status, body
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8", "replace")


def jpost(url, payload, token):
    st, body = http(url, json.dumps(payload).encode(), {
        "Authorization": "Bearer " + token,
        "Content-Type": "application/json; charset=UTF-8"}, "POST")
    try:
        return st, json.loads(body)
    except ValueError:
        return st, {"raw": body}


def refresh_token():
    key, sec, rt = (os.environ.get(k, "") for k in
                    ("TIKTOK_CLIENT_KEY", "TIKTOK_CLIENT_SECRET", "TIKTOK_REFRESH_TOKEN"))
    if not (key and sec and rt):
        sys.exit("Mancano TIKTOK_CLIENT_KEY / TIKTOK_CLIENT_SECRET / TIKTOK_REFRESH_TOKEN")
    body = urllib.parse.urlencode({"client_key": key, "client_secret": sec,
                                   "grant_type": "refresh_token", "refresh_token": rt}).encode()
    st, txt = http(API + "/v2/oauth/token/", body,
                   {"Content-Type": "application/x-www-form-urlencoded"}, "POST")
    d = json.loads(txt)
    if "access_token" not in d:
        sys.exit("Token non ottenuto (%s): %s" % (st, {k: v for k, v in d.items() if "token" not in k}))
    if d.get("refresh_token") and d["refresh_token"] != rt:
        print("ATTENZIONE: TikTok ha emesso un nuovo refresh token; aggiorna il segreto TIKTOK_REFRESH_TOKEN.")
    return d["access_token"]


def scegli(args):
    oggi = args.data or datetime.now(ZoneInfo("Europe/Rome")).strftime("%Y-%m-%d")
    if args.video:
        return args.video, args.didascalia_file
    if args.quale == "sera":
        return "reels/reel_%s-sera.mp4" % oggi, "sera/%s/didascalia.txt" % oggi
    return "reels/reel_%s.mp4" % oggi, None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--quale", choices=["sera", "mezzogiorno"], default="sera")
    ap.add_argument("--data")
    ap.add_argument("--video")
    ap.add_argument("--didascalia-file")
    ap.add_argument("--modo", choices=["inbox", "direct"], default="inbox")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()

    video, capf = scegli(a)
    video = os.path.join(ROOT, video)
    if not os.path.isfile(video):
        sys.exit("Video non trovato: " + video)
    didasc = ""
    if capf and os.path.isfile(os.path.join(ROOT, capf)):
        didasc = open(os.path.join(ROOT, capf), encoding="utf-8").read().strip()
    didasc = didasc[:2200]
    size = os.path.getsize(video)
    print("Video: %s (%.1f MB) | modo: %s | didascalia: %d caratteri" % (
        os.path.basename(video), size / 1e6, a.modo, len(didasc)))
    if size > 64 * 1024 * 1024:
        sys.exit("Video oltre 64 MB: serve il caricamento a blocchi, non gestito.")
    if a.dry_run:
        print("Dry-run: nessuna chiamata a TikTok."); return

    tok = refresh_token()
    source = {"source": "FILE_UPLOAD", "video_size": size, "chunk_size": size, "total_chunk_count": 1}
    if a.modo == "inbox":
        st, d = jpost(API + "/v2/post/publish/inbox/video/init/", {"source_info": source}, tok)
    else:
        st, ci = jpost(API + "/v2/post/publish/creator_info/query/", {}, tok)
        opts = (ci.get("data") or {}).get("privacy_level_options") or ["SELF_ONLY"]
        privacy = "PUBLIC_TO_EVERYONE" if "PUBLIC_TO_EVERYONE" in opts else opts[0]
        print("Privacy consentita:", privacy)
        st, d = jpost(API + "/v2/post/publish/video/init/", {
            "post_info": {"title": didasc, "privacy_level": privacy},
            "source_info": source}, tok)
    err = d.get("error", {})
    if err.get("code") != "ok":
        sys.exit("Init fallito (%s): %s" % (st, json.dumps(d, ensure_ascii=False)))
    pid, url = d["data"]["publish_id"], d["data"]["upload_url"]

    with open(video, "rb") as f:
        blob = f.read()
    st, txt = http(url, blob, {"Content-Type": "video/mp4",
                               "Content-Length": str(size),
                               "Content-Range": "bytes 0-%d/%d" % (size - 1, size)}, "PUT")
    print("Upload HTTP", st)
    if st not in (200, 201, 206):
        sys.exit("Upload fallito: " + txt[:300])

    for _ in range(20):
        time.sleep(5)
        st, s = jpost(API + "/v2/post/publish/status/fetch/", {"publish_id": pid}, tok)
        stato = (s.get("data") or {}).get("status")
        print("Stato:", stato)
        if stato in ("PUBLISH_COMPLETE", "SEND_TO_USER_INBOX", "FAILED"):
            if stato == "FAILED":
                sys.exit("Fallito: " + json.dumps(s, ensure_ascii=False))
            break
    if a.modo == "inbox":
        print("Fatto: il video e' nelle bozze di TikTok. Didascalia da incollare:\n\n" + didasc)


main()
