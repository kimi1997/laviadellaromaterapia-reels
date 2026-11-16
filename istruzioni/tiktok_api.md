# TikTok via API: i tuoi passaggi (circa 15 minuti)

1. Vai su https://developers.tiktok.com, accedi con l'account TikTok @laviadellaromater1 e accetta i termini sviluppatori.
2. "Manage apps" > "Connect an app" (o "Create app"). Nome: La via dell'aromaterapia. Categoria: Lifestyle. Descrizione: "Strumento personale per caricare i miei video".
3. Dentro l'app: "Add products" > "Login Kit" e "Content Posting API". Su Content Posting API attiva "Direct Post" solo se la voce c'è; per iniziare basta l'upload in bozza.
4. Login Kit > Redirect URI: https://kimi1997.github.io/laviadellaromaterapia-reels/callback
5. Scopes: user.info.basic, video.upload, video.publish.
6. Se l'app e' in "Sandbox/Development": aggiungi il tuo account TikTok tra i "Target users".
7. Invia l'app in revisione se te lo chiede il pannello (puo' servire per i permessi video).
8. Sul tuo PC: scarica tools/tiktok_auth.py ed eseguilo (python3 tiktok_auth.py). Chiede Client key e Client secret (copiali dalla pagina dell'app) e stampa il refresh token.
9. GitHub > repository > Settings > Secrets and variables > Actions > New secret. Crea: TIKTOK_CLIENT_KEY, TIKTOK_CLIENT_SECRET, TIKTOK_REFRESH_TOKEN.
10. Repository > Actions > "TikTok pillola della sera" > Run workflow: prova prima con dry_run = true, poi con dry_run = false e la data di oggi.

Non incollare mai chiave, segreto o token in chat.
