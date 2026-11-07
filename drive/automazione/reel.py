#!/usr/bin/env python3
"""La via dell'aromaterapia - generatore di contenuti.
Reel 1080x1920:      python3 reel.py contenuti.json out.mp4 [audio.mp3] [--frames]
Immagini 1080x1350:  python3 reel.py contenuti.json --carousel cartella_output
   (slide_01.jpg ... slide_NN.jpg + riassunto.jpg per Facebook)
JSON: {"hook", "sub", "tips": [{"title", "body"}], "cta", "cta_post"?, "handle"}
Template v3 (rubriche, movimento) e v4.2 (foto stock, Ken Burns, solo foto, zone sicure Reels/TikTok) descritti in fondo al file.
Template (v2): hook e CTA stile "carosello lilla", consigli stile "capitolo rosa con goccia",
riassunto stile "copertina guida". Niente foto: solo forme, testo ad alto contrasto.
"""
import json, math, os, subprocess, sys, tempfile
from PIL import Image, ImageDraw, ImageFont, ImageFilter

W, H, FPS = 1080, 1920, 30
# Palette (contrasti testo verificati >= 4.5:1 sullo sfondo)
OFF = (251, 248, 246)        # sfondo chiaro hook/CTA
PURPLE = (74, 31, 122)       # titoli
GREEN = (74, 101, 42)        # sottotitoli, handle
PINK = (238, 214, 228)       # sfondo consigli
LILAC = (196, 181, 222)      # gocce piene
LAV = (75, 56, 112)          # logo
LOGO_DROP = (185, 163, 227)
BODY = (43, 36, 48)          # testo corrente
CREAM = (250, 241, 225)      # sfondo riassunto
TERRA = (160, 84, 36)        # titolo riassunto
BEIGE = (233, 213, 182)      # badge
GREYLILAC = (226, 223, 238)  # seconda goccia del riassunto
GOLD = (205, 160, 82)        # stelline
STEM = (122, 140, 104)       # steli lavanda
BUDS = [(150, 112, 196), (124, 86, 176), (176, 146, 214)]

F = "/usr/share/fonts/truetype/google-fonts/"
FALLBACK = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
def font(name, size):
    for p in (F + name, FALLBACK):
        if os.path.exists(p):
            return ImageFont.truetype(p, int(size))
    return ImageFont.load_default()

def wrap(d, text, fnt, maxw):
    words, lines, cur = text.split(), [], ""
    for w in words:
        t = (cur + " " + w).strip()
        if d.textlength(t, font=fnt) <= maxw: cur = t
        else: lines.append(cur); cur = w
    if cur: lines.append(cur)
    return lines

def block(d, text, fnt, y, color, maxw=880, gap=1.22, x=None, width=W):
    """Testo a capo: centrato se x e' None, altrimenti allineato a sinistra da x."""
    lh = int(fnt.size * gap)
    for ln in wrap(d, text, fnt, maxw):
        xx = (width - d.textlength(ln, font=fnt)) / 2 if x is None else x
        d.text((xx, y), ln, font=fnt, fill=color); y += lh
    return y

# ---------- forme ----------
def layer(w, h): return Image.new("RGBA", (w, h), (0, 0, 0, 0))

def drop_pts(cx, top, r, tip_h, steps=48):
    """Contorno di una goccia: punta in (cx, top), cerchio di raggio r sotto."""
    cy = top + tip_h
    D = tip_h; b = math.acos(min(0.999, r / D))
    a0, a1 = -math.pi / 2 + b, 3 * math.pi / 2 - b
    pts = [(cx, top)]
    for i in range(steps + 1):
        a = a0 + (a1 - a0) * i / steps
        pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    return pts

def paste_drop(im, cx, top, r, tip_h, fill=None, outline=None, width=6, alpha=255):
    S = 3; w, h = im.size
    L = layer(w * S, h * S); d = ImageDraw.Draw(L)
    pts = [(x * S, y * S) for x, y in drop_pts(cx, top, r, tip_h)]
    if fill: d.polygon(pts, fill=(*fill, alpha))
    if outline: d.line(pts + [pts[0]], fill=(*outline, alpha), width=width * S, joint="curve")
    L = L.resize((w, h), Image.LANCZOS); im.paste(L, (0, 0), L)

def glow(im, cx, cy, rx, ry, color, alpha=110, blur=60):
    # il livello parte dal colore stesso con alfa 0: la sfocatura non porta grigio ai bordi
    L = Image.new("RGBA", im.size, (*color, 0)); ImageDraw.Draw(L).ellipse((cx - rx, cy - ry, cx + rx, cy + ry), fill=(*color, alpha))
    L = L.filter(ImageFilter.GaussianBlur(blur)); im.paste(L, (0, 0), L)

def sparkle(d, x, y, s, color=GOLD):
    k = s * 0.22
    d.polygon([(x, y - s), (x + k, y - k), (x + s, y), (x + k, y + k), (x, y + s), (x - k, y + k), (x - s, y), (x - k, y - k)], fill=color)

CALYX = (88, 60, 130); PETALS = [(132, 98, 190), (156, 122, 208), (182, 154, 224), (206, 186, 236)]
LEAF = (138, 158, 118); LEAF_DARK = (104, 126, 88)

def ell_poly(cx, cy, a, b, rot, n=18):
    c, s = math.cos(rot), math.sin(rot)
    return [(cx + a * math.cos(t) * c - b * math.sin(t) * s, cy + a * math.cos(t) * s + b * math.sin(t) * c)
            for t in (2 * math.pi * k / n for k in range(n))]

def _one_stem(d, S, x0, y0, length, ang, scale, bend, seed):
    """Uno stelo: curva leggera, spiga di verticilli fioriti, foglie strette alla base."""
    a = math.radians(ang)
    ux, uy = math.cos(a), -math.sin(a); px, py = -uy, ux
    def pt(t):  # curva quadratica con piccola flessione laterale
        off = bend * length * 4 * t * (1 - t)
        return (x0 + ux * length * t + px * off, y0 + uy * length * t + py * off)
    pts = [pt(i / 40) for i in range(41)]
    d.line([(x * S, y * S) for x, y in pts], fill=(*STEM, 255), width=max(2, int(2.6 * scale * S)), joint="curve")
    # foglie lanceolate vicino alla base
    for t, side, ln in ((0.12, 1, 70), (0.2, -1, 62), (0.3, 1, 48)):
        bx, by = pt(t); la = a + side * math.radians(28)
        lx, ly = math.cos(la), -math.sin(la)
        L = ln * scale; cx, cy = bx + lx * L / 2, by + ly * L / 2
        d.polygon([(x * S, y * S) for x, y in ell_poly(cx, cy, L / 2, 4.2 * scale, math.atan2(ly, lx))], fill=(*LEAF, 235))
        d.line([(bx * S, by * S), ((bx + lx * L * 0.85) * S, (by + ly * L * 0.85) * S)], fill=(*LEAF_DARK, 200), width=max(1, int(0.8 * scale * S)))
    # spiga: verticilli via via piu' fitti e piccoli verso la punta
    whorls = 9
    for k in range(whorls):
        f = k / (whorls - 1)
        t = 0.50 + 0.47 * (f ** 0.8)
        bx, by = pt(t)
        size = scale * (1.0 - 0.45 * f)
        # calice scuro al centro del verticillo
        d.polygon([(x * S, y * S) for x, y in ell_poly(bx, by, 4.2 * size, 6.5 * size, math.atan2(uy, ux) + math.pi / 2)], fill=(*CALYX, 255))
        florets = 6 if f < 0.8 else 4
        for j in range(florets):
            side = -1 if j % 2 == 0 else 1
            spread = (0.55 + 0.35 * ((j // 2) % 3) / 2) * side
            fa = math.atan2(uy, ux) + spread + ((seed * 7 + j * 3 + k) % 5 - 2) * 0.06
            dist = (7.5 + 2.5 * ((j + k) % 2)) * size
            fx, fy = bx + math.cos(fa) * dist, by + math.sin(fa) * dist
            col = PETALS[(j + k + seed) % len(PETALS)]
            d.polygon([(x * S, y * S) for x, y in ell_poly(fx, fy, 6.0 * size, 3.6 * size, fa)], fill=(*col, 245))
            # piccolo petalo superiore piu' chiaro
            d.polygon([(x * S, y * S) for x, y in ell_poly(fx + math.cos(fa) * 3 * size, fy + math.sin(fa) * 3 * size, 2.8 * size, 2.0 * size, fa)], fill=(*PETALS[-1], 230))
    # boccioli in punta
    for k, tt in enumerate((0.985, 1.0)):
        bx, by = pt(tt)
        d.polygon([(x * S, y * S) for x, y in ell_poly(bx, by, 3.0 * scale, 5.2 * scale, math.atan2(uy, ux) + math.pi / 2)], fill=(*PETALS[k], 255))

def sprig(im, x0, y0, length, angle_deg, scale=1.0):
    """Mazzetto di lavanda disegnato (nessuna foto): tre steli con spighe fiorite e foglie."""
    S = 3; w, h = im.size; L = layer(w * S, h * S); d = ImageDraw.Draw(L)
    for i, (da, lf, bend) in enumerate(((-9, 0.86, 0.05), (9, 0.80, -0.06), (0, 1.0, 0.03))):
        _one_stem(d, S, x0, y0, length * lf, angle_deg + da, scale, bend, i)
    L = L.resize((w, h), Image.LANCZOS); im.paste(L, (0, 0), L)

# ---------- logo ufficiale: goccia divisa da una curva a S ----------
LOGO_BG = (82, 62, 115); LOGO_LEFT = (245, 237, 250); LOGO_RIGHT = (191, 166, 231)
# linea della S, nelle coordinate del file del logo ufficiale (922x912): parte dal bordo destro
# della goccia (dove nasce la punta lilla) e scende fino al fondo
_S_CURVE = [(519, 210), (495, 244), (473, 268), (469, 292), (484, 317), (507, 339), (513, 366),
            (501, 391), (478, 413), (457, 436), (452, 461), (467, 483), (495, 500), (522, 512)]

def _catmull(pts, steps=14):
    out = []
    P = [pts[0]] + pts + [pts[-1]]
    for i in range(1, len(P) - 2):
        p0, p1, p2, p3 = P[i - 1], P[i], P[i + 1], P[i + 2]
        for s in range(steps):
            t = s / steps; t2, t3 = t * t, t * t * t
            out.append(tuple(0.5 * (2 * p1[j] + (-p0[j] + p2[j]) * t + (2 * p0[j] - 5 * p1[j] + 4 * p2[j] - p3[j]) * t2
                                    + (-p0[j] + 3 * p1[j] - 3 * p2[j] + p3[j]) * t3) for j in (0, 1)))
    out.append(pts[-1]); return out

def _teardrop(cx, top, bottom, half_w, m=1.6, n=160):
    """Goccia con i fianchi incurvati verso la punta (curva a lacrima classica)."""
    raw = [(math.sin(t) * math.sin(t / 2) ** m, math.cos(t)) for t in (2 * math.pi * i / n for i in range(n))]
    mx = max(abs(x) for x, _ in raw)
    return [(cx + x / mx * half_w, top + (1 - y) / 2 * (bottom - top)) for x, y in raw]

def drop_symbol(size):
    """Simbolo del logo ufficiale (goccia bianco-lilla con divisione a S), sfondo trasparente."""
    from PIL import ImageChops
    S = 4; Z = size * S
    k = Z / 380.0  # la goccia ufficiale e' alta ~345 px nel file: la scalo in un quadrato
    ox, oy = Z / 2 - 490 * k, Z / 2 - 322 * k
    T = lambda p: (ox + p[0] * k, oy + p[1] * k)
    drop = [T(p) for p in _teardrop(490, 150, 495, 113)]
    mask = Image.new("L", (Z, Z), 0); ImageDraw.Draw(mask).polygon(drop, fill=255)
    curve = [T(p) for p in _catmull(_S_CURVE)]
    right = Image.new("L", (Z, Z), 0)
    ImageDraw.Draw(right).polygon(curve + [(Z, curve[-1][1]), (Z, curve[0][1])], fill=255)
    gap = Image.new("L", (Z, Z), 0); ImageDraw.Draw(gap).line(curve, fill=255, width=int(11 * k), joint="curve")
    from PIL import ImageChops
    right_m = ImageChops.multiply(ImageChops.subtract(right, gap), mask)
    left_m = ImageChops.subtract(ImageChops.subtract(mask, right), gap)
    out = Image.new("RGBA", (Z, Z), (*LOGO_LEFT, 0))
    out.paste(Image.new("RGBA", (Z, Z), (*LOGO_LEFT, 255)), (0, 0), left_m)
    out.paste(Image.new("RGBA", (Z, Z), (*LOGO_RIGHT, 255)), (0, 0), right_m)
    return out.resize((size, size), Image.LANCZOS)

LOGO_FILE = os.environ.get("LOGO_FILE") or os.path.join(os.path.dirname(os.path.abspath(__file__)), "logo-ufficiale.jpg")

def logo(size):
    """Badge rotondo viola con il simbolo ufficiale. Usa il file del logo ufficiale (goccia ritagliata
    dal fondo viola, che ha lo stesso colore del badge); se manca, ripiega sul simbolo ridisegnato."""
    S = 4; Z = size * S
    if os.path.exists(LOGO_FILE):
        src = Image.open(LOGO_FILE).convert("RGB")
        sw, sh = src.size; k = sw / 922.0  # coordinate riferite al file ufficiale 922x912
        box = (int(269 * k), int(101 * k), int(711 * k), int(543 * k))
        sym = src.crop(box).resize((Z, Z), Image.LANCZOS).convert("RGBA")
        m = Image.new("L", (Z, Z), 0); ImageDraw.Draw(m).ellipse((0, 0, Z - 1, Z - 1), fill=255)
        out = Image.new("RGBA", (Z, Z), (*LOGO_BG, 0)); out.paste(sym, (0, 0), m)
        return out.resize((size, size), Image.LANCZOS)
    L = Image.new("RGBA", (Z, Z), (*LOGO_BG, 0)); ImageDraw.Draw(L).ellipse((0, 0, Z - 1, Z - 1), fill=(*LOGO_BG, 255))
    sym = drop_symbol(int(size * 0.78) * S)
    L.paste(sym, ((Z - sym.size[0]) // 2, (Z - sym.size[1]) // 2), sym)
    return L.resize((size, size), Image.LANCZOS)

def serif(size, weight="SemiBold"):
    f = font("Lora-Variable.ttf", size)
    try: f.set_variation_by_name(weight)
    except Exception: pass
    return f

def spaced(d, xy, text, fnt, fill, track=0.12):
    """Testo maiuscolo con spaziatura tra le lettere, come nel marchio."""
    x, y = xy
    for ch in text:
        d.text((x, y), ch, font=fnt, fill=fill); x += d.textlength(ch, font=fnt) + fnt.size * track
    return x

def brand(im, x, y, size=72, fs=30):
    lg = logo(size); im.paste(lg, (int(x), int(y)), lg)
    d = ImageDraw.Draw(im)
    tx = x + size + 16
    spaced(d, (tx, y + size * 0.0), "LA VIA", serif(fs * 1.25, "Bold"), PURPLE, 0.10)
    spaced(d, (tx, y + size * 0.64), "DELL’AROMATERAPIA", serif(fs * 0.62, "Medium"), PURPLE, 0.16)

def pill(d, text, right, top, fs=34):
    f = font("Poppins-Bold.ttf", fs); tw = d.textlength(text, font=f)
    x1 = right; x0 = right - tw - 48; y1 = top + fs + 30
    d.rounded_rectangle((x0, top, x1, y1), radius=(y1 - top) / 2, fill=(236, 226, 244))
    d.text((x0 + 24, top + 12), text, font=f, fill=PURPLE)

def arrow_label(d, label, right, y, fs=36, color=PURPLE):
    f = font("Poppins-Bold.ttf", fs); tw = d.textlength(label, font=f)
    x = right - tw - 54; d.text((x, y), label, font=f, fill=color)
    ax = x + tw + 14; ay = y + fs * 0.72
    d.line((ax, ay, ax + 30, ay), fill=color, width=5)
    d.polygon([(ax + 38, ay), (ax + 24, ay - 11), (ax + 24, ay + 11)], fill=color)

# ---------- template A: hook / CTA (sfondo chiaro, goccia, lavanda) ----------
def frame_light(h, counter=None):
    im = Image.new("RGB", (W, h), OFF)
    glow(im, W + 60, int(h * 0.12), 420, 300, (226, 210, 240), 120, 90)
    glow(im, -80, int(h * 0.86), 420, 280, (224, 232, 214), 110, 90)
    sprig(im, 10, int(h * 0.31), int(h * 0.17), 52, 1.15)
    sprig(im, W - 20, int(h * 0.86), int(h * 0.16), 112, 1.05)
    d = ImageDraw.Draw(im)
    for fx, fy, s in ((0.66, 0.135, 16), (0.23, 0.26, 10), (0.13, 0.77, 15), (0.56, 0.88, 14)):
        sparkle(d, W * fx, h * fy, s)
    brand(im, 66, int(h * 0.05), 72, 38)
    if counter: pill(d, counter, W - 66, int(h * 0.05) + 8)
    return im

def scene_hook(c, h=H, counter=None, scroll=False):
    im = frame_light(h, counter)
    cy = int(h * 0.30)
    glow(im, W // 2, cy, 150, 150, (240, 214, 236), 150, 45)
    paste_drop(im, W // 2, cy - 130, 74, 150, outline=PURPLE, width=5)
    d = ImageDraw.Draw(im); s = h / H if h < H else 1
    y = block(d, c["hook"], font("Poppins-Bold.ttf", 104 * max(s, .85)), int(h * 0.42), PURPLE, maxw=900, gap=1.12)
    if c.get("sub"): block(d, c["sub"], font("Poppins-Bold.ttf", 52 * max(s, .85)), y + 36, GREEN, maxw=880)
    f = font("Poppins-Bold.ttf", 40)
    hd = c.get("handle", "")
    if scroll:
        d.text((W / 2 - d.textlength(hd, font=f) / 2 - 120, h - 150), hd, font=f, fill=GREEN)
        arrow_label(d, "Scorri", W - 60, h - 150)
    else:
        d.text(((W - d.textlength(hd, font=f)) / 2, h - 170), hd, font=f, fill=GREEN)
    return im

def scene_cta(c, h=H, counter=None, text=None):
    im = frame_light(h, counter)
    cy = int(h * 0.30)
    glow(im, W // 2, cy, 150, 150, (240, 214, 236), 150, 45)
    paste_drop(im, W // 2, cy - 130, 74, 150, fill=LILAC)
    paste_drop(im, W // 2, cy - 130, 74, 150, outline=PURPLE, width=5)
    d = ImageDraw.Draw(im); s = h / H if h < H else 1
    y = block(d, text or c["cta"], font("Poppins-Bold.ttf", 88 * max(s, .85)), int(h * 0.42), PURPLE, maxw=880, gap=1.14)
    # sotto la call to action: invito a seguire la pagina (nessuna avvertenza)
    note = c.get("note") or "Un consiglio pratico ogni giorno"
    block(d, note, font("Poppins-Bold.ttf", 42), y + 60, GREEN, maxw=820)
    f = font("Poppins-Bold.ttf", 40); hd = c.get("handle", "")
    d.text(((W - d.textlength(hd, font=f)) / 2, h - 170), hd, font=f, fill=GREEN)
    return im

# ---------- template B: consiglio (capitolo rosa, numero nella goccia) ----------
def scene_tip(t, i, n, handle, h=H):
    im = Image.new("RGB", (W, h), PINK)
    glow(im, W - 40, int(h * 0.9), 360, 260, (246, 232, 240), 150, 80)
    s = h / H if h < H else 1
    r, tip = int(165 * max(s, .8)), int(300 * max(s, .8))
    top = int(h * 0.07)
    paste_drop(im, 260, top, r, tip, fill=LILAC)
    d = ImageDraw.Draw(im)
    num = f"{i + 1:02d}"; fn = font("Poppins-Bold.ttf", 150 * max(s, .8))
    d.text((260 - d.textlength(num, font=fn) / 2 + 6, top + tip - fn.size * 0.62), num, font=fn, fill=(255, 255, 255))
    y = top + tip + r + int(90 * s)
    y = block(d, t["title"], font("Poppins-BoldItalic.ttf", 84 * max(s, .82)), y, PURPLE, maxw=860, gap=1.15, x=110)
    block(d, t["body"], font("Poppins-Regular.ttf", 58 * max(s, .82)), y + 44, BODY, maxw=860, gap=1.45, x=110)
    sprig(im, W - 70, int(h * 0.90), int(h * 0.14), 112, 1.0)
    d = ImageDraw.Draw(im); sparkle(d, W * 0.72, h * 0.76, 13); sparkle(d, W * 0.12, h * 0.86, 10)
    pill(d, f"{i + 1}/{n}", W - 70, int(h * 0.05) + 8)
    lg = logo(60); im.paste(lg, (70, h - 160), lg)
    f = font("Poppins-Bold.ttf", 36); d.text((144, h - 150), handle or "", font=f, fill=PURPLE)
    return im

# ---------- template C: riassunto (copertina guida) ----------
CH = 1350
def slide_summary(c):
    im = Image.new("RGB", (W, CH), CREAM)
    paste_drop(im, 300, 120, 400, 780, fill=(240, 212, 226), alpha=170)
    paste_drop(im, 1010, -60, 330, 640, fill=GREYLILAC, alpha=200)
    d = ImageDraw.Draw(im)
    tips = c["tips"]
    d.text((80, 70), globals().get("RUBRICHE", {}).get(c.get("rubrica"), "Il consiglio del giorno"), font=font("Poppins-Bold.ttf", 34), fill=(108, 84, 168))
    # badge
    bx, by, br = 900, 190, 120
    d.ellipse((bx - br, by - br, bx + br, by + br), fill=BEIGE)
    fb = font("Poppins-Bold.ttf", 30)
    for k, ln in enumerate([f"{len(tips)}", "CONSIGLI", "PRATICI"]):
        ff = font("Poppins-Bold.ttf", 64) if k == 0 else fb
        d.text((bx - d.textlength(ln, font=ff) / 2, by - 78 + (0 if k == 0 else 50 + 36 * k)), ln, font=ff, fill=TERRA)
    y0 = block(d, c["hook"].upper(), font("Poppins-Bold.ttf", 70), 200, TERRA, maxw=700, gap=1.1, x=80) + 40
    limit = CH - 190  # sopra la fascia del marchio
    for ts, bs in ((46, 34), (42, 31), (38, 28), (34, 25), (30, 22)):  # riduce i caratteri finche' la lista entra
        ft, fbdy = font("Poppins-Bold.ttf", ts), font("Poppins-Regular.ttf", bs)
        y = y0
        for t in tips:
            y += int(ts * 1.3) + len(wrap(d, t["body"], fbdy, 860)) * int(bs * 1.32) + 22
        if y <= limit: break
    y = y0
    for i, t in enumerate(tips):
        d.text((80, y), f"{i + 1}.", font=ft, fill=TERRA)
        d.text((140, y), t["title"], font=ft, fill=PURPLE)
        yy = y + int(ft.size * 1.3)
        for ln in wrap(d, t["body"], fbdy, 860):
            d.text((140, yy), ln, font=fbdy, fill=BODY); yy += int(fbdy.size * 1.32)
        y = yy + 22
    brand(im, 80, CH - 176, 68, 30)
    d.text((80, CH - 86), "@laviadellaromaterapia · un consiglio pratico ogni giorno", font=font("Poppins-Medium.ttf", 25), fill=GREEN)
    return im

def carousel(c, outdir):
    os.makedirs(outdir, exist_ok=True); tips = c["tips"]; n = len(tips); tot = n + 2
    slides = [scene_hook(c, CH, f"1/{tot}", scroll=True)]
    slides += [scene_tip(t, i, n, c.get("handle"), CH) for i, t in enumerate(tips)]
    cta = c.get("cta_post") or c["cta"].replace("il video", "il post").replace("questo video", "questo post")
    slides += [scene_cta(c, CH, f"{tot}/{tot}", cta)]
    paths = []
    for k, im in enumerate(slides):
        p = os.path.join(outdir, f"slide_{k + 1:02d}.jpg"); im.save(p, "JPEG", quality=90); paths.append(p)
    s = os.path.join(outdir, "riassunto.jpg"); slide_summary(c).save(s, "JPEG", quality=90)
    print("\n".join(paths + [s]))

# ---------- video ----------
def secs_for(text, lo=3.2, hi=6.5):
    return max(lo, min(hi, 1.6 + len(text.split()) * 0.32))

def render(png, dur, out, fade_in=True):
    part = out[:-4] + ".part.mp4"
    # la prima scena parte gia' piena: il primo fotogramma del reel e' l'hook del giorno
    fin = "fade=t=in:st=0:d=0.35:color=0xFBF8F6," if fade_in else ""
    vf = f"format=yuv420p,loop=-1:1,trim=duration={dur:.2f},{fin}fade=t=out:st={dur-0.35:.2f}:d=0.35:color=0xFBF8F6"
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-framerate", str(FPS), "-i", png, "-vf", vf,
                    "-r", str(FPS), "-c:v", "libx264", "-crf", "20", "-preset", "veryfast", "-pix_fmt", "yuv420p", part], check=True)
    os.replace(part, out)


# =====================================================================
# TEMPLATE v3 (dal 7 novembre 2026): rubriche settimanali + movimento
# JSON v3: {"rubrica": "momento|comesifa|blend|faidate|mito|rituale|scheda",
#   "hook", "sub", "cta", "handle", "tips": [{"title", "body", "momento"?}],
#   "blend"?: {"nome", "quando", "oli": [{"olio", "gocce"}], "note"},
#   "mito"?: [{"claim", "verdetto", "spiegazione"}],
#   "rituale"?: {"titolo", "sub", "passi": ["..."]},
#   "scheda"?: {"olio", "famiglia", "profumo", "abbinamenti", "usi": ["", "", ""], "sostituti"?}}
# Reel:      python3 reel.py contenuti.json out.mp4 audio.mp3 [--frames]
# Riassunto: python3 reel.py contenuti.json --carousel cartella   (riassunto.jpg per Facebook)
# Carosello del sabato: python3 reel.py contenuti.json --weekly-carousel cartella
# =====================================================================
import random
DEEP = (46, 30, 78); MOONC = (246, 236, 214)
RUBRICHE = {"momento": "Un olio per ogni momento", "comesifa": "Come si fa", "blend": "Il blend della settimana",
            "faidate": "Fai da te per la casa", "mito": "Vero o falso?", "rituale": "Il rituale di stagione",
            "scheda": "La scheda dell'olio"}
GIORNI = {"momento": "lunedì", "comesifa": "martedì", "blend": "mercoledì", "faidate": "giovedì", "mito": "venerdì", "rituale": "sabato", "scheda": "domenica"}
MOMENT_COLS = [(182, 154, 224), (236, 170, 120), (150, 186, 140), (230, 160, 190), (170, 190, 230)]
DROP_COLS = [(236, 150, 70), (170, 190, 90), (110, 170, 140), (182, 154, 224), (230, 160, 190)]

def texture(w, h, base, blobs, seed=3, grain=6):
    rnd = random.Random(seed)
    im = Image.new("RGB", (w, h), base)
    lay = Image.new("RGBA", (w, h), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    for col, a in blobs:
        for _ in range(3):
            cx, cy = rnd.randint(-200, w + 200), rnd.randint(-200, h + 200)
            r = rnd.randint(int(w * .35), int(w * .7))
            d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=tuple(col) + (a,))
    lay = lay.filter(ImageFilter.GaussianBlur(160)); im.paste(lay, (0, 0), lay)
    noise = Image.effect_noise((w, h), grain * 6).convert("L")
    return Image.blend(im, Image.merge("RGB", [noise] * 3), 0.025)

BG = {"light": (OFF, [(LILAC, 120), (PINK, 140), (BEIGE, 90)]),
      "pink": (PINK, [((255, 255, 255), 120), (LILAC, 110)]),
      "cream": (CREAM, [((255, 255, 255), 130), (BEIGE, 120)]),
      "night": (DEEP, [((92, 64, 140), 160), ((150, 112, 196), 90)]),
      "lilac": ((241, 235, 248), [((255, 255, 255), 140), (PINK, 120)])}
def bg(kind, w=W, h=H, seed=3):
    base, blobs = BG[kind]; return texture(w, h, base, blobs, seed, 8 if kind == "night" else 6)

def label(d, text, x, y, bgc=PURPLE, fg=(255, 255, 255), fs=34):
    f = font("Poppins-Bold.ttf", fs); tw = d.textlength(text, font=f)
    d.rounded_rectangle([x, y, x + tw + 56, y + fs + 34], radius=(fs + 34) // 2, fill=bgc)
    d.text((x + 28, y + 14), text, font=f, fill=fg); return y + fs + 34

def header(im, dark=False):
    if not dark: brand(im, 70, 70, 72, 38); return
    lg = logo(72); im.paste(lg, (70, 70), lg)
    d = ImageDraw.Draw(im)
    spaced(d, (160, 76), "LA VIA", serif(30, "Bold"), (240, 232, 250))
    spaced(d, (160, 112), "DELL’AROMATERAPIA", serif(17), (210, 198, 235))

def footer(d, h=H, dark=False):
    f = font("Poppins-Bold.ttf", 38); t = "@laviadellaromaterapia"
    d.text(((W - d.textlength(t, font=f)) / 2, h - 140), t, font=f, fill=(230, 220, 245) if dark else GREEN)

def fit(d, text, name, size, maxw, max_lines):
    """riduce il corpo finche' il testo sta in max_lines righe"""
    s = size
    while s > size * 0.6 and len(wrap(d, text, font(name, s), maxw)) > max_lines: s -= 4
    return font(name, s)

def stars(d, seed, n, ymax, w=W):
    rnd = random.Random(seed)
    for _ in range(n): sparkle(d, rnd.randint(40, w - 40), rnd.randint(40, ymax), rnd.randint(5, 14), GOLD)

def moon(im, cx, cy, r):
    glow(im, cx, cy, r + 60, r + 60, MOONC, alpha=120, blur=80)
    d = ImageDraw.Draw(im); d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=MOONC)
    d.ellipse([cx - r * .55, cy - r * .55, cx - r * .18, cy - r * .18], fill=(232, 220, 196))
    d.ellipse([cx + r * .2, cy + r * .15, cx + r * .5, cy + r * .45], fill=(232, 220, 196))

# ----- scene: ognuna restituisce (sfondo, scena completa) -----
def v3_cover(c):
    night = c.get("rubrica") == "rituale"
    b = bg("night" if night else "light", seed=3); im = b.copy()
    if night: stars(ImageDraw.Draw(im), 8, 22, 640); moon(im, 800, 420, 160)
    header(im, night); d = ImageDraw.Draw(im)
    y = label(d, RUBRICHE.get(c.get("rubrica"), "Il consiglio del giorno").upper(), 70, 700 if night else 560,
              bgc=GOLD if night else PURPLE, fg=DEEP if night else (255, 255, 255), fs=32)
    fh = fit(d, c["hook"], "Poppins-Bold.ttf", 110, 920, 5)
    y = block(d, c["hook"], fh, y + 50, (250, 244, 255) if night else PURPLE, maxw=920, gap=1.1, x=70)
    if c.get("sub"): block(d, c["sub"], font("Poppins-Bold.ttf", 50), y + 30, GOLD if night else GREEN, maxw=900, x=70)
    if not night: sprig(im, 930, 1640, 330, -105, 1.1)
    footer(ImageDraw.Draw(im), dark=night); return b, im

def v3_cta(c):
    night = c.get("rubrica") == "rituale"
    b = bg("night" if night else "light", seed=4); im = b.copy()
    if night: stars(ImageDraw.Draw(im), 9, 14, 420)
    else: sprig(im, 10, 600, 330, 52, 1.15); sprig(im, W - 20, 1650, 300, 112, 1.05)
    header(im, night); d = ImageDraw.Draw(im)
    cx, top = W // 2, 470
    paste_drop(im, cx, top, 74, 150, fill=LILAC); paste_drop(im, cx, top, 74, 150, outline=GOLD if night else PURPLE, width=5)
    d = ImageDraw.Draw(im)
    y = block(d, c["cta"], fit(d, c["cta"], "Poppins-Bold.ttf", 88, 880, 4), 800, (250, 244, 255) if night else PURPLE, maxw=880, gap=1.14)
    block(d, f"Ogni {GIORNI.get(c.get('rubrica'), 'giorno')}: {RUBRICHE.get(c.get('rubrica'), 'un consiglio pratico').lower()}", font("Poppins-Bold.ttf", 40), y + 60, GOLD if night else GREEN, maxw=860)
    footer(d, dark=night); return b, im

def v3_tip(t, i, n, kind="pink"):
    b = bg(kind, seed=10 + i); im = b.copy()
    top = 160; paste_drop(im, 230, top, 150, 270, fill=LILAC)
    d = ImageDraw.Draw(im); num = f"{i + 1:02d}"; fn = font("Poppins-Bold.ttf", 140)
    d.text((230 - d.textlength(num, font=fn) / 2 + 6, top + 270 - fn.size * 0.62), num, font=fn, fill=(255, 255, 255))
    pill(d, f"{i + 1}/{n}", W - 70, 80)
    y = top + 270 + 150 + 90
    y = block(d, t["title"], fit(d, t["title"], "Poppins-BoldItalic.ttf", 84, 860, 3), y, PURPLE, maxw=860, gap=1.15, x=110)
    block(d, t["body"], fit(d, t["body"], "Poppins-Regular.ttf", 58, 860, 7), y + 44, BODY, maxw=860, gap=1.45, x=110)
    sprig(im, W - 70, 1730, 270, 112, 1.0)
    lg = logo(60); im.paste(lg, (70, H - 160), lg)
    d = ImageDraw.Draw(im); d.text((144, H - 150), "@laviadellaromaterapia", font=font("Poppins-Bold.ttf", 36), fill=PURPLE)
    return b, im

def v3_moment(t, i, n):
    b = bg("pink", seed=20 + i); im = b.copy(); d = ImageDraw.Draw(im)
    pill(d, f"{i + 1}/{n}", W - 70, 80)
    cx, cy, r = W // 2, 600, 250
    glow(im, cx, cy, r + 90, r + 90, (255, 255, 255), alpha=150, blur=70)
    d = ImageDraw.Draw(im); d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=MOMENT_COLS[i % len(MOMENT_COLS)])
    paste_drop(im, cx, cy - 150, 95, 140, fill=(255, 255, 255), alpha=235)
    d = ImageDraw.Draw(im)
    if t.get("momento"):
        f = font("Poppins-Bold.ttf", 46); s = t["momento"].upper()
        d.text(((W - d.textlength(s, font=f)) / 2, cy + r + 60), s, font=f, fill=GREEN)
    y = block(d, t["title"], fit(d, t["title"], "Poppins-BoldItalic.ttf", 120, 900, 2), cy + r + 130, PURPLE, maxw=900)
    block(d, t["body"], fit(d, t["body"], "Poppins-Regular.ttf", 56, 860, 5), y + 30, BODY, maxw=860, gap=1.4)
    lg = logo(64); im.paste(lg, (70, H - 160), lg)
    d = ImageDraw.Draw(im); d.text((150, H - 150), "@laviadellaromaterapia", font=font("Poppins-Bold.ttf", 36), fill=PURPLE)
    return b, im

def v3_blend(bl):
    b = bg("cream", seed=21); im = b.copy(); header(im); d = ImageDraw.Draw(im)
    y = label(d, "IL BLEND DELLA SETTIMANA", 70, 300, bgc=TERRA, fs=32)
    y = block(d, bl["nome"], fit(d, bl["nome"], "Poppins-Bold.ttf", 96, 920, 2), y + 40, TERRA, maxw=920, gap=1.1, x=70)
    y = block(d, bl.get("quando", ""), font("Poppins-Bold.ttf", 46), y + 20, GREEN, maxw=920, x=70) + 70
    for k, o in enumerate(bl["oli"][:4]):
        d.rounded_rectangle([70, y, W - 70, y + 210], radius=40, fill=(255, 255, 255))
        d.text((120, y + 40), o["olio"], font=fit(d, o["olio"], "Poppins-Bold.ttf", 60, 560, 1), fill=PURPLE)
        g = int(o["gocce"]); d.text((120, y + 120), f"{g} gocc{'ia' if g == 1 else 'e'}", font=font("Poppins-Regular.ttf", 44), fill=BODY)
        for j in range(min(g, 6)): paste_drop(im, W - 130 - j * 62, y + 62, 22, 34, fill=DROP_COLS[k % len(DROP_COLS)])
        d = ImageDraw.Draw(im); y += 240
    if bl.get("note"): block(d, bl["note"], fit(d, bl["note"], "Poppins-Regular.ttf", 46, 920, 4), y + 30, BODY, maxw=920, gap=1.4, x=70)
    footer(d); return b, im

def v3_myth(m, i, n):
    b = Image.new("RGB", (W, H), OFF); ImageDraw.Draw(b).rectangle([0, 0, W, 980], fill=LILAC)
    b = Image.blend(b, bg("light", seed=30 + i), 0.25); im = b.copy()
    header(im); d = ImageDraw.Draw(im)
    label(d, "VERO O FALSO?", 70, 300, bgc=(255, 255, 255), fg=PURPLE, fs=34)
    if n > 1: pill(d, f"{i + 1}/{n}", W - 70, 80)
    claim = f"“{m['claim']}”"
    block(d, claim, fit(d, claim, "Poppins-BoldItalic.ttf", 96, 920, 5), 440, PURPLE, maxw=920, gap=1.12, x=70)
    v = m["verdetto"].upper(); f = font("Poppins-Bold.ttf", 140); tw = d.textlength(v, font=f)
    d.rounded_rectangle([(W - tw) / 2 - 50, 910, (W + tw) / 2 + 50, 1090], radius=60, fill=TERRA if v.startswith("FALS") else GREEN)
    d.text(((W - tw) / 2, 918), v, font=f, fill=(255, 255, 255))
    block(d, m["spiegazione"], fit(d, m["spiegazione"], "Poppins-Regular.ttf", 58, 900, 6), 1200, BODY, maxw=900, gap=1.45)
    footer(d); return b, im

def v3_ritual(rt):
    b = bg("night", seed=8); im = b.copy(); d = ImageDraw.Draw(im)
    stars(d, 8, 22, 640); moon(im, 800, 420, 160); header(im, True); d = ImageDraw.Draw(im)
    y = label(d, "IL RITUALE DI STAGIONE", 70, 700, bgc=GOLD, fg=DEEP, fs=32)
    y = block(d, rt["titolo"], fit(d, rt["titolo"], "Poppins-Bold.ttf", 100, 920, 2), y + 40, (250, 244, 255), maxw=920, gap=1.1, x=70)
    if rt.get("sub"): y = block(d, rt["sub"], font("Poppins-Bold.ttf", 46), y + 20, GOLD, maxw=920, x=70)
    y += 50; fp = font("Poppins-Regular.ttf", 48 if len(rt["passi"]) <= 3 else 42)
    for k, p in enumerate(rt["passi"][:5], 1):
        d.text((70, y), f"{k}", font=font("Poppins-Bold.ttf", 54), fill=GOLD)
        y = block(d, p, fp, y + 6, (236, 228, 248), maxw=860, gap=1.35, x=140) + 30
    footer(d, dark=True); return b, im

def v3_card(s):
    b = bg("light", seed=31); im = b.copy(); header(im); d = ImageDraw.Draw(im)
    y = label(d, "LA SCHEDA DELL'OLIO", 70, 290, bgc=GREEN, fs=32)
    y = block(d, s["olio"], fit(d, s["olio"], "Poppins-Bold.ttf", 130, 920, 2), y + 30, PURPLE, maxw=920, x=70)
    y = block(d, s.get("famiglia", ""), font("Poppins-Bold.ttf", 44), y + 6, GREEN, maxw=920, x=70) + 50
    secs = [("PROFUMO", s["profumo"]), ("SI ABBINA CON", s["abbinamenti"]), ("3 USI", " · ".join(s["usi"]))]
    if s.get("sostituti"): secs.append(("SE NON CE L'HAI", s["sostituti"]))
    fs, lines = (50, 4) if len(secs) == 3 else (44, 3)
    for t, body in secs:
        d.rounded_rectangle([70, y, W - 70, y + 60], radius=30, fill=(255, 255, 255))
        d.text((100, y + 8), t, font=font("Poppins-Bold.ttf", 36), fill=TERRA)
        y = block(d, body, fit(d, body, "Poppins-Regular.ttf", fs, 900, lines), y + 84, BODY, maxw=900, gap=1.34, x=90) + 34
    footer(d); return b, im

def v3_scenes(c):
    """sequenza di scene (sfondo, completa, durata, tipo sfondo) del reel per rubrica"""
    r = c.get("rubrica", "comesifa"); tips = c.get("tips", []); sc = []
    def add(pair, text, lo=3.2, hi=6.5, dark=False): sc.append(pair + (secs_for(text, lo, hi), dark))
    add(v3_cover(c), c["hook"] + " " + c.get("sub", ""), 3.0, 4.5, r == "rituale")
    if r == "momento":
        for i, t in enumerate(tips): add(v3_moment(t, i, len(tips)), t["title"] + " " + t["body"])
    elif r == "blend":
        bl = c["blend"]; add(v3_blend(bl), bl["nome"] + " " + bl.get("note", "") + " x" * 8, 5, 8)
        for i, t in enumerate(tips): add(v3_tip(t, i, len(tips)), t["title"] + " " + t["body"])
    elif r == "mito":
        ms = c["mito"]
        for i, m in enumerate(ms): add(v3_myth(m, i, len(ms)), m["claim"] + " " + m["spiegazione"], 4.5, 7.5)
    elif r == "rituale":
        rt = c["rituale"]; add(v3_ritual(rt), " ".join(rt["passi"]) + " " + rt["titolo"], 6, 9, True)
    elif r == "scheda":
        s = c["scheda"]; add(v3_card(s), s["profumo"] + " " + s["abbinamenti"] + " " + " ".join(s["usi"]) + " " + s.get("sostituti", ""), 6, 10)
        for i, t in enumerate(tips): add(v3_tip(t, i, len(tips)), t["title"] + " " + t["body"])
    else:
        for i, t in enumerate(tips): add(v3_tip(t, i, len(tips)), t["title"] + " " + t["body"])
    add(v3_cta(c), c["cta"], 3.6, 4.2, r == "rituale")
    return sc

def summary_tips(c):
    """punti per il riassunto Facebook, ricavati dalla rubrica se mancano i tips"""
    if c.get("tips"): return c["tips"]
    r = c.get("rubrica")
    if r == "blend": return [{"title": o["olio"], "body": f"{o['gocce']} gocce"} for o in c["blend"]["oli"]] + ([{"title": "Come usarlo", "body": c["blend"]["note"]}] if c["blend"].get("note") else [])
    if r == "mito": return [{"title": f"{m['verdetto']}: {m['claim']}", "body": m["spiegazione"]} for m in c["mito"]]
    if r == "rituale": return [{"title": f"Passo {k}", "body": p} for k, p in enumerate(c["rituale"]["passi"], 1)]
    if r == "scheda":
        s = c["scheda"]; return [{"title": "Profumo", "body": s["profumo"]}, {"title": "Si abbina con", "body": s["abbinamenti"]}, {"title": "Usi", "body": ", ".join(s["usi"])}] + ([{"title": "Se non ce l'hai", "body": s["sostituti"]}] if s.get("sostituti") else [])
    return []

# ----- movimento: gocce dietro al testo + zoom lento -----
def fg_layer(b, full):
    """la scena senza lo sfondo: alfa = dove la scena differisce dallo sfondo"""
    from PIL import ImageChops
    diff = ImageChops.difference(full.convert("RGB"), b.convert("RGB")).convert("L")
    mask = diff.point(lambda v: min(255, v * 22)).filter(ImageFilter.MaxFilter(3)).filter(ImageFilter.GaussianBlur(1.0))
    fg = full.convert("RGBA"); fg.putalpha(mask); return fg

def drops_layer(dark, seed=5):
    rnd = random.Random(seed); im = Image.new("RGBA", (W, H * 2), (0, 0, 0, 0))
    col = (214, 196, 240) if dark else (150, 112, 196); a = 70 if dark else 46
    for _ in range(11):
        cx, top, r = rnd.randint(60, W - 60), rnd.randint(0, H - 80), rnd.randint(14, 34)
        for off in (0, H): paste_drop(im, cx, top + off, r, int(r * 1.5), fill=col, alpha=a)
    return im

def render_motion(b, full, dur, out, dark=False, fade_in=True, tmp="."):
    bp, fp, dp = f"{out}.bg.png", f"{out}.fg.png", f"{out}.drops.png"
    b.convert("RGB").save(bp); fg_layer(b, full).save(fp); drops_layer(dark).save(dp)
    n = int(dur * FPS)
    fin = "fade=t=in:st=0:d=0.35:color=0xFBF8F6," if fade_in else ""
    fc = (f"[0:v][2:v]overlay=x=0:y='mod(t*70,{H})-{H}'[b];[b][1:v]overlay=0:0,format=yuv420p,"
          f"scale=1620:2880,zoompan=z='1+0.045*on/{n}':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=1:s={W}x{H}:fps={FPS},"
          f"trim=duration={dur:.2f},{fin}fade=t=out:st={dur - 0.35:.2f}:d=0.35:color=0xFBF8F6[v]")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-loop", "1", "-framerate", str(FPS), "-t", f"{dur:.2f}", "-i", bp,
                    "-loop", "1", "-framerate", str(FPS), "-t", f"{dur:.2f}", "-i", fp,
                    "-loop", "1", "-framerate", str(FPS), "-t", f"{dur:.2f}", "-i", dp,
                    "-filter_complex", fc, "-map", "[v]", "-r", str(FPS), "-c:v", "libx264", "-crf", "20", "-preset", "veryfast",
                    "-pix_fmt", "yuv420p", out], check=True)
    for p in (bp, fp, dp): os.remove(p)

def reel_v3(c, out, audio=None, frames=False):
    tmp = tempfile.mkdtemp(); sc = v3_scenes(c); files = []
    for k, (b, full, dur, dark) in enumerate(sc):
        mp4 = f"{tmp}/s{k}.mp4"; render_motion(b, full, dur, mp4, dark, fade_in=(k > 0)); files.append(mp4)
    lst = f"{tmp}/list.txt"; open(lst, "w").write("".join(f"file '{f}'\n" for f in files))
    silent = f"{tmp}/video.mp4"
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", silent], check=True)
    total = sum(s[2] for s in sc)
    if audio:
        af = f"afade=t=in:st=0:d=0.8,afade=t=out:st={total-2:.2f}:d=2,volume=0.85"
        cmd = ["ffmpeg", "-y", "-loglevel", "error", "-i", silent, "-stream_loop", "-1", "-i", audio, "-map", "0:v", "-map", "1:a",
               "-af", af, "-t", f"{total:.2f}", "-c:v", "copy", "-c:a", "aac", "-b:a", "160k", out]
    else:
        cmd = ["ffmpeg", "-y", "-loglevel", "error", "-i", silent, "-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo",
               "-map", "0:v", "-map", "1:a", "-c:v", "copy", "-c:a", "aac", "-shortest", out]
    subprocess.run(cmd, check=True)
    if frames:
        for k, s in enumerate(sc): s[1].save(out[:-4] + f"_frame{k}.png")
    print(out)

# ----- carosello del sabato (1080x1350) -----
def wc_cover(title, sub):
    w, h = W, CH; im = bg("night", w, h, seed=8); d = ImageDraw.Draw(im)
    stars(d, 4, 16, 480, w); moon(im, 830, 250, 130); header(im, True); d = ImageDraw.Draw(im)
    y = label(d, "DA SALVARE", 70, 520, bgc=GOLD, fg=DEEP, fs=30)
    y = block(d, title, fit(d, title, "Poppins-Bold.ttf", 92, 920, 3), y + 36, (250, 244, 255), maxw=920, gap=1.1, x=70)
    if sub: block(d, sub, font("Poppins-Bold.ttf", 42), y + 20, GOLD, maxw=920, x=70)
    arrow_label(d, "Scorri", w - 60, h - 110, color=(236, 228, 248)); return im

def wc_slide(i, n, title, body):
    w, h = W, CH; im = bg("lilac", w, h, seed=40 + i)
    paste_drop(im, 150, 110, 80, 120, fill=LILAC); d = ImageDraw.Draw(im)
    f = font("Poppins-Bold.ttf", 76); t = f"{i}"; d.text((150 - d.textlength(t, font=f) / 2, 160), t, font=f, fill=(255, 255, 255))
    pill(d, f"{i}/{n}", w - 70, 80)
    y = block(d, title, fit(d, title, "Poppins-BoldItalic.ttf", 78, 900, 3), 430, PURPLE, maxw=900, gap=1.15, x=90)
    block(d, body, fit(d, body, "Poppins-Regular.ttf", 50, 900, 8), y + 40, BODY, maxw=900, gap=1.45, x=90)
    sprig(im, w - 60, h - 120, 230, 112, 0.9); d = ImageDraw.Draw(im)
    d.text((90, h - 100), "@laviadellaromaterapia", font=font("Poppins-Bold.ttf", 34), fill=PURPLE); return im

def wc_end(cta):
    w, h = W, CH; im = bg("night", w, h, seed=9); d = ImageDraw.Draw(im); stars(d, 6, 14, 280, w)
    header(im, True); paste_drop(im, w // 2, 330, 74, 150, fill=LILAC); d = ImageDraw.Draw(im)
    y = block(d, cta, fit(d, cta, "Poppins-Bold.ttf", 80, 880, 4), 640, (250, 244, 255), maxw=880, gap=1.14)
    block(d, "Ogni sabato un nuovo rituale", font("Poppins-Bold.ttf", 40), y + 50, GOLD, maxw=860)
    f = font("Poppins-Bold.ttf", 38); t = "@laviadellaromaterapia"; d.text(((w - d.textlength(t, font=f)) / 2, h - 120), t, font=f, fill=(230, 220, 245))
    return im

def weekly_carousel(c, outdir):
    """copertina + una slide per passo (o consiglio) + chiusura; usa c['carosello'] se presente"""
    os.makedirs(outdir, exist_ok=True)
    cs = c.get("carosello") or {}
    title = cs.get("titolo") or (c.get("rituale") or {}).get("titolo") or c["hook"]
    sub = cs.get("sub") or (c.get("rituale") or {}).get("sub") or c.get("sub", "")
    slides = cs.get("slides") or [{"title": t["title"], "body": t["body"]} for t in summary_tips(c)]
    n = len(slides); ims = [wc_cover(title, sub)] + [wc_slide(i + 1, n, s["title"], s["body"]) for i, s in enumerate(slides)]
    ims.append(wc_end(cs.get("cta") or "Salva il post e prova il rituale questa sera"))
    paths = []
    for k, im in enumerate(ims):
        p = os.path.join(outdir, f"slide_{k + 1:02d}.jpg"); im.convert("RGB").save(p, "JPEG", quality=90); paths.append(p)
    print("\n".join(paths))

def main_v2():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if "--carousel" in sys.argv:
        return carousel(json.load(open(args[0])), args[1])
    c = json.load(open(args[0])); out = args[1]; audio = args[2] if len(args) > 2 else None
    tmp = tempfile.mkdtemp(); tips = c["tips"]
    scenes = [(scene_hook(c), secs_for(c["hook"] + " " + c.get("sub", ""), 3.0, 4.5))]
    scenes += [(scene_tip(t, i, len(tips), c.get("handle")), secs_for(t["title"] + " " + t["body"])) for i, t in enumerate(tips)]
    scenes += [(scene_cta(c), 3.8)]
    files = []
    for k, (im, dur) in enumerate(scenes):
        png = f"{tmp}/s{k}.png"; im.save(png); mp4 = f"{tmp}/s{k}.mp4"
        render(png, dur, mp4, fade_in=(k > 0)); files.append(mp4)
    lst = f"{tmp}/list.txt"; open(lst, "w").write("".join(f"file '{f}'\n" for f in files))
    silent = f"{tmp}/video.mp4"
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", silent], check=True)
    if audio:
        total = sum(d for _, d in scenes)
        af = f"afade=t=in:st=0:d=0.8,afade=t=out:st={total-2:.2f}:d=2,volume=0.85"
        cmd = ["ffmpeg", "-y", "-loglevel", "error", "-i", silent, "-stream_loop", "-1", "-i", audio, "-map", "0:v", "-map", "1:a",
               "-af", af, "-t", f"{total:.2f}", "-c:v", "copy", "-c:a", "aac", "-b:a", "160k", out]
    else:
        cmd = ["ffmpeg", "-y", "-loglevel", "error", "-i", silent, "-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo",
               "-map", "0:v", "-map", "1:a", "-c:v", "copy", "-c:a", "aac", "-shortest", out]
    subprocess.run(cmd, check=True)
    if "--frames" in sys.argv:
        for k, (im, _) in enumerate(scenes): im.save(out[:-4] + f"_frame{k}.png")
    print(out)


# =====================================================================
# TEMPLATE v4 (dall'8 novembre 2026): foto stock di sfondo + movimento Ken Burns
# Si attiva da solo se esiste la cartella stock/ (accanto a reel.py o in $STOCK_DIR).
# JSON v4 = JSON v3 + "foto"?: {"cover": "lavanda", "scene": "bottiglie", "cta": "candele"}
#   ogni valore e' una categoria di stock/catalogo.json oppure un nome file (es. "lavanda_4936400.jpg").
#   Se "foto" manca, le categorie vengono scelte dalla rubrica e dalle parole dell'hook.
# Rubrica serale "pillola" (reel delle 19:30): come comesifa, 1-3 tips, "serie": nome della serie mostrato in copertina.
# Forzare i vecchi template: aggiungere --v3 alla riga di comando.
# =====================================================================
import hashlib
RUBRICHE["pillola"] = "La pillola della sera"; GIORNI["pillola"] = "sera"
STOCK_DIR = os.environ.get("STOCK_DIR") or os.path.join(os.path.dirname(os.path.abspath(__file__)), "stock")
KEYWORDS = {"lavanda": "lavanda", "limone": "limone", "arancia": "arancio", "arancio": "arancio", "mandarino": "arancio",
            "bergamotto": "arancio", "agrum": "arancio", "eucalipto": "eucalipto", "menta": "erbe", "rosmarino": "rosmarino",
            "tea tree": "erbe", "cedro": "bottiglie", "salvia": "erbe", "timo": "erbe", "ylang": "candele", "geranio": "erbe", "cannella": "natale", "chiodi di garofano": "natale", "camomilla": "erbe", "incenso": "incenso", "diffusore": "diffusore", "candel": "candele",
            "sera": "candele", "notte": "luna", "luna": "luna", "sonno": "luna", "autunno": "autunno", "freddo": "tessuti",
            "inverno": "tessuti", "natale": "natale", "regal": "natale", "bagno": "bagno", "tisana": "te", "tè": "te",
            "casa": "casa", "pulizi": "casa", "fritto": "casa", "bucato": "tessuti", "armadio": "tessuti", "viaggio": "viaggio",
            "valigia": "viaggio", "auto": "viaggio", "kit": "bottiglie", "scade": "bottiglie", "gocce": "bottiglie"}
RUB_FOTO = {"momento": ("bottiglie", "bottiglie", "candele"), "comesifa": ("diffusore", "bottiglie", "diffusore"),
            "blend": ("bottiglie", "bottiglie", "candele"), "faidate": ("casa", "casa", "tessuti"),
            "mito": ("bottiglie", "bottiglie", "bottiglie"), "rituale": ("candele", "candele", "luna"),
            "scheda": ("erbe", "erbe", "bottiglie"), "pillola": ("bottiglie", "bottiglie", "candele")}

def stock_ok():
    return os.path.isdir(STOCK_DIR) and any(f.endswith(".jpg") for f in os.listdir(STOCK_DIR))

def stock_files(cat):
    fs = sorted(f for f in os.listdir(STOCK_DIR) if f.endswith(".jpg") and f.split("_")[0] == cat)
    return fs or sorted(f for f in os.listdir(STOCK_DIR) if f.startswith("bottiglie_"))

def pick_photo(spec, seed, avoid=()):
    if spec.endswith(".jpg") and os.path.exists(os.path.join(STOCK_DIR, spec)): return spec
    fs = [f for f in stock_files(spec) if f not in avoid] or stock_files(spec)
    return fs[int(hashlib.md5(seed.encode()).hexdigest(), 16) % len(fs)]

def photos_for(c):
    r = c.get("rubrica", "comesifa"); dflt = list(RUB_FOTO.get(r, RUB_FOTO["comesifa"]))
    txt = (c.get("hook", "") + " " + c.get("sub", "") + " " + json.dumps(c.get("scheda", {}), ensure_ascii=False)).lower()
    for k, cat in KEYWORDS.items():
        if k in txt: dflt[0] = cat; break
    f = c.get("foto") or {}
    spec = {"cover": f.get("cover", dflt[0]), "scene": f.get("scene", dflt[1]), "cta": f.get("cta", dflt[2])}
    seed = c.get("hook", "") + c.get("data", "")
    cov = pick_photo(spec["cover"], seed + "c"); sce = pick_photo(spec["scene"], seed + "s", (cov,))
    cta = pick_photo(spec["cta"], seed + "t", (cov, sce)); return cov, sce, cta

def photo(name, w=W, h=H):
    """ritaglio w x h; se la foto e' piu' alta del riquadro sceglie la fascia con piu' dettagli (il soggetto)"""
    im = Image.open(os.path.join(STOCK_DIR, name)).convert("RGB")
    s = max(w / im.width, h / im.height); im = im.resize((round(im.width * s), round(im.height * s)), Image.LANCZOS)
    x, y = (im.width - w) // 2, (im.height - h) // 2
    if im.height - h > 40:
        e = im.convert("L").resize((im.width // 8, im.height // 8)).filter(ImageFilter.FIND_EDGES)
        import numpy as _np; rows = _np.asarray(e, dtype=float).sum(axis=1).tolist()
        hh = h // 8; mid = (e.height - hh) / 2 or 1
        best = max(range(0, e.height - hh + 1), key=lambda r: sum(rows[r:r + hh]) * (1 - 0.45 * abs(r - mid) / mid))
        y = min(im.height - h, best * 8)
    return im.crop((x, y, x + w, y + h))

def shade(im, top=0.0, bottom=0.0, color=(28, 18, 40), start=0.35, flat=0.0):
    """sfumatura scura dall'alto e dal basso per leggere il testo bianco"""
    w, h = im.size; g = Image.new("L", (1, h))
    for y in range(h):
        t = y / h; a = flat
        if bottom: a = max(a, bottom * max(0.0, (t - start) / (1 - start)) ** 1.25)
        if top: a = max(a, top * max(0.0, 1 - t / 0.22))
        g.putpixel((0, y), int(255 * min(1, a)))
    over = Image.new("RGB", (w, h), color); return Image.composite(over, im, g.resize((w, h)))

def soft_bg(name, dark=False, w=W, h=H):
    """foto sfocata e schiarita (o scurita) come fondo delle schede piene di testo"""
    p = photo(name, w, h).filter(ImageFilter.GaussianBlur(28))
    if dark: return Image.blend(p, Image.new("RGB", (w, h), DEEP), 0.68)
    return Image.blend(p, Image.new("RGB", (w, h), OFF), 0.84)

WHITE = (255, 255, 255); SOFTW = (244, 236, 250)
def header_white(im):
    lg = logo(72); im.paste(lg, (70, 70), lg); d = ImageDraw.Draw(im)
    spaced(d, (160, 76), "LA VIA", serif(30, "Bold"), WHITE); spaced(d, (160, 112), "DELL’AROMATERAPIA", serif(17), SOFTW)

def shadow_text(im, fn):
    """disegna il testo con un'ombra morbida: fn(draw, color, dx, dy)"""
    sh = Image.new("RGBA", im.size, (0, 0, 0, 0)); fn(ImageDraw.Draw(sh), (0, 0, 0, 150), 0, 4)
    sh = sh.filter(ImageFilter.GaussianBlur(8)); im.paste(sh, (0, 0), sh); fn(ImageDraw.Draw(im), None, 0, 0)

def v4_cover(c, ph):
    im = shade(photo(ph), top=0.55, bottom=0.88, start=0.30); header_white(im); d = ImageDraw.Draw(im)
    fh = fit(d, c["hook"], "Poppins-Bold.ttf", 112, 940, 5); lines = wrap(d, c["hook"], fh, 940)
    fs = font("Poppins-Bold.ttf", 50); sl = wrap(d, c.get("sub", ""), fs, 920) if c.get("sub") else []
    hh = len(lines) * fh.size * 1.1 + (30 + len(sl) * 50 * 1.22 if sl else 0)
    y0 = int(H - 260 - hh); y = label(d, (c.get("serie") or RUBRICHE.get(c.get("rubrica"), "Il consiglio del giorno")).upper(), 70, y0 - 100,
                                      bgc=GOLD, fg=DEEP, fs=32)
    def draw(dd, col, dx, dy):
        yy = block(dd, c["hook"], fh, y0 + dy, col or WHITE, maxw=940, gap=1.1, x=70 + dx)
        if sl: block(dd, c["sub"], fs, yy + 30 + dy, col or (250, 222, 160), maxw=920, x=70 + dx)
    shadow_text(im, draw); d = ImageDraw.Draw(im)
    t = "@laviadellaromaterapia"; f = font("Poppins-Bold.ttf", 36); d.text(((W - d.textlength(t, font=f)) / 2, H - 130), t, font=f, fill=SOFTW)
    return im

def v4_tip(t, i, n, ph):
    """foto in alto, pannello crema in basso con numero e consiglio"""
    top = 860; im = Image.new("RGB", (W, H), OFF); im.paste(photo(ph, W, top + 80), (0, 0))
    im = shade(im, top=0.4); pan = Image.new("RGBA", (W, H), (0, 0, 0, 0)); pd = ImageDraw.Draw(pan)
    pd.rounded_rectangle([0, top, W, H + 80], radius=70, fill=OFF + (255,)); im.paste(pan, (0, 0), pan)
    header_white(im); d = ImageDraw.Draw(im); pill(d, f"{i + 1}/{n}", W - 70, 80)
    cx = 180; d.ellipse([cx - 90, top - 90, cx + 90, top + 90], fill=PURPLE, outline=OFF, width=10)
    num = f"{i + 1:02d}"; fn = font("Poppins-Bold.ttf", 82); d.text((cx - d.textlength(num, font=fn) / 2, top - 58), num, font=fn, fill=WHITE)
    y = top + 150
    if t.get("momento"):
        f = font("Poppins-Bold.ttf", 44); d.text((90, y), t["momento"].upper(), font=f, fill=GREEN); y += 80
    y = block(d, t["title"], fit(d, t["title"], "Poppins-BoldItalic.ttf", 100, 900, 3), y, PURPLE, maxw=900, gap=1.12, x=90)
    block(d, t["body"], fit(d, t["body"], "Poppins-Regular.ttf", 62, 900, 7), y + 40, BODY, maxw=900, gap=1.42, x=90)
    lg = logo(56); im.paste(lg, (90, H - 150), lg); d = ImageDraw.Draw(im)
    d.text((160, H - 142), "@laviadellaromaterapia", font=font("Poppins-Bold.ttf", 34), fill=PURPLE); return im

def v4_cta(c, ph):
    im = shade(photo(ph), top=0.5, flat=0.55, color=(30, 18, 46)); header_white(im); d = ImageDraw.Draw(im)
    cx, top = W // 2, 520; paste_drop(im, cx, top, 74, 150, fill=LILAC); paste_drop(im, cx, top, 74, 150, outline=GOLD, width=5)
    d = ImageDraw.Draw(im); fc = fit(d, c["cta"], "Poppins-Bold.ttf", 88, 880, 4)
    sub = ("Ogni sera alle 19:30 una nuova pillola" if c.get("rubrica") == "pillola" else
           f"Ogni {GIORNI.get(c.get('rubrica'), 'giorno')}: {RUBRICHE.get(c.get('rubrica'), 'un consiglio pratico').lower()}")
    def draw(dd, col, dx, dy):
        y = block(dd, c["cta"], fc, 860 + dy, col or WHITE, maxw=880, gap=1.14)
        block(dd, sub, font("Poppins-Bold.ttf", 40), y + 60 + dy, col or (250, 222, 160), maxw=860)
    shadow_text(im, draw); d = ImageDraw.Draw(im)
    t = "@laviadellaromaterapia"; f = font("Poppins-Bold.ttf", 38); d.text(((W - d.textlength(t, font=f)) / 2, H - 140), t, font=f, fill=SOFTW)
    return im

def on_photo(pair, ph, dark=False):
    """riusa una scheda v3 (blend, mito, rituale, scheda) sostituendo la texture con la foto sfocata"""
    b, full = pair; fg = fg_layer(b, full); nb = soft_bg(ph, dark); nb.paste(fg, (0, 0), fg); return nb

def render_kb(im, dur, out, fade_in=True, zoom_out=False, dark=False):
    """Ken Burns: zoom lento su tutta la scena (avanti o indietro)"""
    png = out + ".png"; im.convert("RGB").save(png); n = int(dur * FPS)
    z = f"1.06-0.06*on/{n}" if zoom_out else f"1+0.05*on/{n}"
    col = "0x1C1228" if dark else "0xFBF8F6"
    fin = f"fade=t=in:st=0:d=0.3:color={col}," if fade_in else ""
    vf = (f"scale=1620:2880,zoompan=z='{z}':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={n}:s={W}x{H}:fps={FPS},"
          f"format=yuv420p,trim=duration={dur:.2f},{fin}fade=t=out:st={dur - 0.3:.2f}:d=0.3:color={col}")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-loop", "1", "-framerate", str(FPS), "-t", f"{dur:.2f}", "-i", png,
                    "-vf", vf, "-r", str(FPS), "-c:v", "libx264", "-crf", "20", "-preset", "veryfast", "-pix_fmt", "yuv420p", out], check=True)
    os.remove(png)

def v4_scenes(c):
    r = c.get("rubrica", "comesifa"); tips = c.get("tips", []); cov, sce, cta = photos_for(c); sc = []
    extra = [f for f in stock_files(c.get("foto", {}).get("scene", RUB_FOTO.get(r, RUB_FOTO["comesifa"])[1])) if f not in (cov, cta)]
    used_tip = set()
    def tip_photo(i):
        for t in ((tips[i]["title"].lower(), tips[i].get("body", "").lower()) if i < len(tips) else ()):
          for k, cat in KEYWORDS.items():
            if k in t and cat in ("bottiglie", "lavanda", "limone", "arancio", "eucalipto", "erbe", "rosmarino", "incenso", "diffusore", "candele", "tessuti", "casa", "bagno", "te", "viaggio"):
                f = pick_photo(cat, c["hook"] + str(i), tuple(used_tip | {cov, cta})); used_tip.add(f); return f
        return _tip_photo(i)
    def _tip_photo(i): return extra[(i + int(hashlib.md5(c["hook"].encode()).hexdigest(), 16)) % len(extra)] if extra else sce
    def add(im, text, lo=3.2, hi=6.5, dark=False): sc.append((im, secs_for(text, lo, hi), dark))
    add(v4_cover(c, cov), c["hook"] + " " + c.get("sub", ""), 3.0, 4.5, True)
    def tipscenes():
        for i, t in enumerate(tips): add(v4_tip(t, i, len(tips), tip_photo(i)), t["title"] + " " + t["body"])
    if r == "blend":
        bl = c["blend"]; add(on_photo(v3_blend(bl), sce), bl["nome"] + " " + bl.get("note", "") + " x" * 8, 5, 8); tipscenes()
    elif r == "mito":
        for i, m in enumerate(c["mito"]): add(on_photo(v3_myth(m, i, len(c["mito"])), tip_photo(i)), m["claim"] + " " + m["spiegazione"], 4.5, 7.5)
    elif r == "rituale":
        rt = c["rituale"]; add(on_photo(v3_ritual(rt), sce, True), " ".join(rt["passi"]) + " " + rt["titolo"], 6, 9, True)
    elif r == "scheda":
        s = c["scheda"]; add(on_photo(v3_card(s), sce), s["profumo"] + " " + s["abbinamenti"] + " " + " ".join(s["usi"]) + " " + s.get("sostituti", ""), 6, 10); tipscenes()
    else: tipscenes()
    add(v4_cta(c, cta), c["cta"], 3.6, 4.2, True)
    return sc, (cov, sce, cta)

def reel_v4(c, out, audio=None, frames=False):
    tmp = tempfile.mkdtemp(); sc, used = v4_scenes(c); files = []
    for k, (im, dur, dark) in enumerate(sc):
        mp4 = f"{tmp}/s{k}.mp4"; render_kb(im, dur, mp4, fade_in=(k > 0), zoom_out=(k % 2 == 1), dark=dark); files.append(mp4)
    lst = f"{tmp}/list.txt"; open(lst, "w").write("".join(f"file '{f}'\n" for f in files))
    silent = f"{tmp}/video.mp4"
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", silent], check=True)
    total = sum(s[1] for s in sc)
    if audio:
        af = f"afade=t=in:st=0:d=0.8,afade=t=out:st={total-2:.2f}:d=2,volume=0.85"
        cmd = ["ffmpeg", "-y", "-loglevel", "error", "-i", silent, "-stream_loop", "-1", "-i", audio, "-map", "0:v", "-map", "1:a",
               "-af", af, "-t", f"{total:.2f}", "-c:v", "copy", "-c:a", "aac", "-b:a", "160k", out]
    else:
        cmd = ["ffmpeg", "-y", "-loglevel", "error", "-i", silent, "-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo",
               "-map", "0:v", "-map", "1:a", "-c:v", "copy", "-c:a", "aac", "-shortest", out]
    subprocess.run(cmd, check=True)
    if frames:
        for k, s in enumerate(sc): s[0].convert("RGB").save(out[:-4] + f"_frame{k}.png")
    print(out); print("FOTO_USATE:", ",".join(used))

def wc_cover_photo(title, sub, ph):
    w, h = W, CH; im = shade(photo(ph, w, h), top=0.55, bottom=0.9, start=0.25); header_white(im); d = ImageDraw.Draw(im)
    ft = fit(d, title, "Poppins-Bold.ttf", 92, 920, 3); lines = wrap(d, title, ft, 920)
    y0 = int(h - 230 - len(lines) * ft.size * 1.1 - (70 if sub else 0)); label(d, "DA SALVARE", 70, y0 - 100, bgc=GOLD, fg=DEEP, fs=30)
    def draw(dd, col, dx, dy):
        y = block(dd, title, ft, y0 + dy, col or WHITE, maxw=920, gap=1.1, x=70)
        if sub: block(dd, sub, font("Poppins-Bold.ttf", 42), y + 20 + dy, col or (250, 222, 160), maxw=920, x=70)
    shadow_text(im, draw); arrow_label(ImageDraw.Draw(im), "Scorri", w - 60, h - 100, color=WHITE); return im


# ----- v4.1: schede senza illustrazioni disegnate (solo foto + pannello) -----
def panel(ph, top, dark=False, h=H):
    """foto nella fascia alta, pannello pieno sotto con angoli arrotondati"""
    im = Image.new("RGB", (W, h), DEEP if dark else OFF); im.paste(photo(ph, W, top + 80), (0, 0))
    im = shade(im, top=0.45); lay = Image.new("RGBA", (W, h), (0, 0, 0, 0))
    ImageDraw.Draw(lay).rounded_rectangle([0, top, W, h + 80], radius=70, fill=(DEEP if dark else OFF) + (255,))
    im.paste(lay, (0, 0), lay); header_white(im); return im

def foot(im, dark=False, h=H):
    d = ImageDraw.Draw(im); f = font("Poppins-Bold.ttf", 34); t = "@laviadellaromaterapia"
    d.text(((W - d.textlength(t, font=f)) / 2, h - 120), t, font=f, fill=(222, 210, 240) if dark else PURPLE)

def v4_ritual(rt, ph):
    top = 640; im = panel(ph, top, dark=True); d = ImageDraw.Draw(im)
    y = label(d, "IL RITUALE DI STAGIONE", 70, top + 70, bgc=GOLD, fg=DEEP, fs=32)
    y = block(d, rt["titolo"], fit(d, rt["titolo"], "Poppins-Bold.ttf", 96, 940, 2), y + 36, (250, 244, 255), maxw=940, gap=1.1, x=70)
    if rt.get("sub"): y = block(d, rt["sub"], font("Poppins-Bold.ttf", 44), y + 16, GOLD, maxw=940, x=70)
    y += 44; fp = font("Poppins-Regular.ttf", 46 if len(rt["passi"]) <= 3 else 40)
    for k, p in enumerate(rt["passi"][:5], 1):
        d.text((70, y), f"{k}", font=font("Poppins-Bold.ttf", 52), fill=GOLD)
        y = block(d, p, fp, y + 6, (236, 228, 248), maxw=860, gap=1.33, x=140) + 28
    foot(im, True); return im

def v4_blend(bl, ph):
    top = 600; im = panel(ph, top); d = ImageDraw.Draw(im)
    y = label(d, "IL BLEND DELLA SETTIMANA", 70, top + 60, bgc=TERRA, fs=30)
    y = block(d, bl["nome"], fit(d, bl["nome"], "Poppins-Bold.ttf", 88, 940, 2), y + 30, TERRA, maxw=940, gap=1.1, x=70)
    y = block(d, bl.get("quando", ""), font("Poppins-Bold.ttf", 42), y + 10, GREEN, maxw=940, x=70) + 40
    for o in bl["oli"][:4]:
        d.rounded_rectangle([70, y, W - 70, y + 130], radius=36, fill=(255, 255, 255))
        d.text((110, y + 34), o["olio"], font=fit(d, o["olio"], "Poppins-Bold.ttf", 54, 600, 1), fill=PURPLE)
        g = int(o["gocce"]); t = f"{g} gocc{'ia' if g == 1 else 'e'}"; f = font("Poppins-Bold.ttf", 44)
        d.text((W - 110 - d.textlength(t, font=f), y + 40), t, font=f, fill=TERRA); y += 150
    if bl.get("note"): block(d, bl["note"], fit(d, bl["note"], "Poppins-Regular.ttf", 44, 940, 4), y + 20, BODY, maxw=940, gap=1.38, x=70)
    foot(im); return im

def v4_myth(m, i, n, ph):
    top = 700; im = panel(ph, top); d = ImageDraw.Draw(im)
    if n > 1: pill(d, f"{i + 1}/{n}", W - 70, 80)
    y = label(d, "VERO O FALSO?", 70, top + 70, bgc=PURPLE, fs=32); claim = f"“{m['claim']}”"
    y = block(d, claim, fit(d, claim, "Poppins-BoldItalic.ttf", 80, 940, 4), y + 34, PURPLE, maxw=940, gap=1.12, x=70)
    v = m["verdetto"].upper(); f = font("Poppins-Bold.ttf", 96); tw = d.textlength(v, font=f); y += 40
    d.rounded_rectangle([70, y, 70 + tw + 90, y + 140], radius=50, fill=TERRA if v.startswith("FALS") else GREEN)
    d.text((115, y + 10), v, font=f, fill=(255, 255, 255))
    block(d, m["spiegazione"], fit(d, m["spiegazione"], "Poppins-Regular.ttf", 52, 940, 6), y + 190, BODY, maxw=940, gap=1.42, x=70)
    foot(im); return im

def v4_card(s, ph):
    top = 560; im = panel(ph, top); d = ImageDraw.Draw(im)
    y = label(d, "LA SCHEDA DELL'OLIO", 70, top + 56, bgc=GREEN, fs=30)
    y = block(d, s["olio"], fit(d, s["olio"], "Poppins-Bold.ttf", 110, 940, 2), y + 20, PURPLE, maxw=940, x=70)
    y = block(d, s.get("famiglia", ""), font("Poppins-Bold.ttf", 40), y + 2, GREEN, maxw=940, x=70) + 36
    secs = [("PROFUMO", s["profumo"]), ("SI ABBINA CON", s["abbinamenti"]), ("3 USI", " · ".join(s["usi"]))]
    if s.get("sostituti"): secs.append(("SE NON CE L'HAI", s["sostituti"]))
    fs, lines = (46, 3) if len(secs) == 3 else (40, 3)
    for t, body in secs:
        d.text((70, y), t, font=font("Poppins-Bold.ttf", 34), fill=TERRA)
        y = block(d, body, fit(d, body, "Poppins-Regular.ttf", fs, 940, lines), y + 50, BODY, maxw=940, gap=1.3, x=70) + 26
    foot(im); return im

def v4_cta(c, ph):
    im = shade(photo(ph), top=0.5, flat=0.55, color=(30, 18, 46)); header_white(im)
    lg = logo(170); im.paste(lg, ((W - 170) // 2, 560), lg); d = ImageDraw.Draw(im)
    fc = fit(d, c["cta"], "Poppins-Bold.ttf", 88, 880, 4)
    sub = ("Ogni sera alle 19:30 una nuova pillola" if c.get("rubrica") == "pillola" else
           f"Ogni {GIORNI.get(c.get('rubrica'), 'giorno')}: {RUBRICHE.get(c.get('rubrica'), 'un consiglio pratico').lower()}")
    def draw(dd, col, dx, dy):
        y = block(dd, c["cta"], fc, 860 + dy, col or WHITE, maxw=880, gap=1.14)
        block(dd, sub, font("Poppins-Bold.ttf", 40), y + 60 + dy, col or (250, 222, 160), maxw=860)
    shadow_text(im, draw); d = ImageDraw.Draw(im)
    t = "@laviadellaromaterapia"; f = font("Poppins-Bold.ttf", 38); d.text(((W - d.textlength(t, font=f)) / 2, H - 140), t, font=f, fill=SOFTW)
    return im

def v4_scenes(c):
    r = c.get("rubrica", "comesifa"); tips = c.get("tips", []); cov, sce, cta = photos_for(c); sc = []
    extra = [f for f in stock_files(c.get("foto", {}).get("scene", RUB_FOTO.get(r, RUB_FOTO["comesifa"])[1])) if f not in (cov, cta)]
    used_tip = set()
    def _tip_photo(i): return extra[(i + int(hashlib.md5(c["hook"].encode()).hexdigest(), 16)) % len(extra)] if extra else sce
    def tip_photo(i):
        for t in ((tips[i]["title"].lower(), tips[i].get("body", "").lower()) if i < len(tips) else ()):
            for k, cat in KEYWORDS.items():
                if k in t and cat in ("bottiglie", "lavanda", "limone", "arancio", "eucalipto", "erbe", "rosmarino", "incenso", "diffusore", "candele", "tessuti", "casa", "bagno", "te", "viaggio"):
                    f = pick_photo(cat, c["hook"] + str(i), tuple(used_tip | {cov, cta})); used_tip.add(f); return f
        return _tip_photo(i)
    def add(im, text, lo=3.2, hi=6.5, dark=False): sc.append((im, secs_for(text, lo, hi), dark))
    add(v4_cover(c, cov), c["hook"] + " " + c.get("sub", ""), 3.0, 4.5, True)
    def tipscenes():
        for i, t in enumerate(tips): add(v4_tip(t, i, len(tips), tip_photo(i)), t["title"] + " " + t["body"])
    if r == "blend":
        bl = c["blend"]; add(v4_blend(bl, sce), bl["nome"] + " " + bl.get("note", "") + " x" * 8, 5, 8); tipscenes()
    elif r == "mito":
        for i, m in enumerate(c["mito"]): add(v4_myth(m, i, len(c["mito"]), _tip_photo(i)), m["claim"] + " " + m["spiegazione"], 4.5, 7.5)
    elif r == "rituale":
        rt = c["rituale"]; add(v4_ritual(rt, sce), " ".join(rt["passi"]) + " " + rt["titolo"], 6, 9, True)
    elif r == "scheda":
        s = c["scheda"]; ph = pick_photo(next((cat for k, cat in KEYWORDS.items() if k in s["olio"].lower()), sce), c["hook"] + "s", (cov,)) if any(k in s["olio"].lower() for k in KEYWORDS) else sce
        add(v4_card(s, ph), s["profumo"] + " " + s["abbinamenti"] + " " + " ".join(s["usi"]) + " " + s.get("sostituti", ""), 6, 10); tipscenes()
    else: tipscenes()
    add(v4_cta(c, cta), c["cta"], 3.6, 4.2, True)
    return sc, (cov, sce, cta)

# carosello del sabato senza disegni
def wc_slide_photo(i, n, title, body, ph):
    w, h = W, CH; top = 600; im = panel(ph, top, h=h); d = ImageDraw.Draw(im); pill(d, f"{i}/{n}", w - 70, 80)
    cx = 170; d.ellipse([cx - 80, top - 80, cx + 80, top + 80], fill=PURPLE, outline=OFF, width=10)
    t = f"{i}"; f = font("Poppins-Bold.ttf", 76); d.text((cx - d.textlength(t, font=f) / 2, top - 52), t, font=f, fill=WHITE)
    y = block(d, title, fit(d, title, "Poppins-BoldItalic.ttf", 78, 920, 2), top + 120, PURPLE, maxw=920, gap=1.12, x=80)
    block(d, body, fit(d, body, "Poppins-Regular.ttf", 54, 920, 5), y + 30, BODY, maxw=920, gap=1.42, x=80)
    d.text((80, h - 90), "@laviadellaromaterapia", font=font("Poppins-Bold.ttf", 32), fill=PURPLE); return im

def wc_end_photo(cta, ph):
    w, h = W, CH; im = shade(photo(ph, w, h), top=0.5, flat=0.58, color=(30, 18, 46)); header_white(im)
    lg = logo(150); im.paste(lg, ((w - 150) // 2, 330), lg); d = ImageDraw.Draw(im); fc = fit(d, cta, "Poppins-Bold.ttf", 80, 880, 4)
    def draw(dd, col, dx, dy):
        y = block(dd, cta, fc, 600 + dy, col or WHITE, maxw=880, gap=1.14)
        block(dd, "Ogni sabato un nuovo rituale", font("Poppins-Bold.ttf", 40), y + 50 + dy, col or (250, 222, 160), maxw=860)
    shadow_text(im, draw); d = ImageDraw.Draw(im); f = font("Poppins-Bold.ttf", 36); t = "@laviadellaromaterapia"
    d.text(((w - d.textlength(t, font=f)) / 2, h - 110), t, font=f, fill=SOFTW); return im

def weekly_carousel_v4(c, outdir):
    os.makedirs(outdir, exist_ok=True); cs = c.get("carosello") or {}
    title = cs.get("titolo") or (c.get("rituale") or {}).get("titolo") or c["hook"]
    sub = cs.get("sub") or (c.get("rituale") or {}).get("sub") or c.get("sub", "")
    slides = cs.get("slides") or [{"title": t["title"], "body": t["body"]} for t in summary_tips(c)]
    cov, sce, cta = photos_for(c); r = c.get("rubrica", "rituale")
    pool = [f for f in stock_files(c.get("foto", {}).get("scene", RUB_FOTO.get(r, RUB_FOTO["comesifa"])[1])) + stock_files("candele") + stock_files("tessuti") if f not in (cov, cta)]
    pool = list(dict.fromkeys(pool)); n = len(slides)
    def sp(i):
        for k, cat in KEYWORDS.items():
            if k in (slides[i]["title"] + " " + slides[i]["body"]).lower() and cat not in ("luna",): return pick_photo(cat, title + str(i), (cov, cta))
        return pool[(i + int(hashlib.md5(title.encode()).hexdigest(), 16)) % len(pool)]
    ims = [wc_cover_photo(title, sub, cov)] + [wc_slide_photo(i + 1, n, s["title"], s["body"], sp(i)) for i, s in enumerate(slides)]
    end = cta if not cta.startswith("luna_") else pick_photo("candele", title + "e", (cov,))
    ims.append(wc_end_photo(cs.get("cta") or "Salva il post e prova il rituale questa sera", end))
    paths = []
    for k, im in enumerate(ims):
        p = os.path.join(outdir, f"slide_{k + 1:02d}.jpg"); im.convert("RGB").save(p, "JPEG", quality=90); paths.append(p)
    print("\n".join(paths))


# ----- v4.2: zone sicure per Reels e TikTok -----
# In alto ~200 px coperti da barra/ricerca, a destra ~200 px dai pulsanti (mi piace, commenti, salva),
# in basso ~460 px da nome utente, didascalia e musica. Tutto il testo sta in x 70-880, y 210-1460;
# se una scheda e' troppo piena, i caratteri si riducono da soli finche' non ci sta.
SX0, SX1, SY0, SY1 = 70, 880, 210, 1460
SW = SX1 - SX0
_FS = 1.0
_font0 = font
def font(name, size): return _font0(name, max(12, int(size * _FS)))

def fitscene(fn, *a):
    global _FS
    for s in (1.0, 0.93, 0.86, 0.8, 0.74, 0.68, 0.62):
        _FS = s; im, y = fn(*a)
        if y <= SY1: break
    _FS = 1.0; return im

def header_white(im, y=SY0 + 6):
    lg = logo(64); im.paste(lg, (SX0, y), lg); d = ImageDraw.Draw(im)
    spaced(d, (SX0 + 80, y + 4), "LA VIA", serif(28, "Bold"), WHITE); spaced(d, (SX0 + 80, y + 38), "DELL’AROMATERAPIA", serif(16), SOFTW)

def v4_cover(c, ph):
    im = shade(photo(ph), top=0.6, bottom=0.9, start=0.28); header_white(im); d = ImageDraw.Draw(im)
    fh = fit(d, c["hook"], "Poppins-Bold.ttf", 104, SW, 5); lines = wrap(d, c["hook"], fh, SW)
    fs = font("Poppins-Bold.ttf", 46); sl = wrap(d, c.get("sub", ""), fs, SW) if c.get("sub") else []
    hh = len(lines) * int(fh.size * 1.1) + (26 + len(sl) * int(fs.size * 1.22) if sl else 0)
    y0 = SY1 - hh
    label(d, (c.get("serie") or RUBRICHE.get(c.get("rubrica"), "Il consiglio del giorno")).upper(), SX0, y0 - 96, bgc=GOLD, fg=DEEP, fs=30)
    def draw(dd, col, dx, dy):
        yy = block(dd, c["hook"], fh, y0 + dy, col or WHITE, maxw=SW, gap=1.1, x=SX0 + dx)
        if sl: block(dd, c["sub"], fs, yy + 26 + dy, col or (250, 222, 160), maxw=SW, x=SX0 + dx)
    shadow_text(im, draw); return im, SY1

def v4_tip(t, i, n, ph):
    top = 720; im = Image.new("RGB", (W, H), OFF); im.paste(photo(ph, W, top + 80), (0, 0))
    im = shade(im, top=0.45); lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(lay).rounded_rectangle([0, top, W, H + 80], radius=70, fill=OFF + (255,)); im.paste(lay, (0, 0), lay)
    header_white(im); d = ImageDraw.Draw(im); pill(d, f"{i + 1}/{n}", SX1, SY0 + 10)
    cx = 160; d.ellipse([cx - 84, top - 84, cx + 84, top + 84], fill=PURPLE, outline=OFF, width=10)
    num = f"{i + 1:02d}"; fn = font("Poppins-Bold.ttf", 76); d.text((cx - d.textlength(num, font=fn) / 2, top - 54), num, font=fn, fill=WHITE)
    y = top + 130
    if t.get("momento"):
        f = font("Poppins-Bold.ttf", 42); y = block(d, t["momento"].upper(), f, y, GREEN, maxw=SW, x=SX0 + 10) + 14
    y = block(d, t["title"], fit(d, t["title"], "Poppins-BoldItalic.ttf", 86, SW, 3), y, PURPLE, maxw=SW, gap=1.12, x=SX0 + 10)
    y = block(d, t["body"], fit(d, t["body"], "Poppins-Regular.ttf", 56, SW, 6), y + 34, BODY, maxw=SW, gap=1.42, x=SX0 + 10)
    return im, y

def v4_cta(c, ph):
    im = shade(photo(ph), top=0.5, flat=0.55, color=(30, 18, 46)); header_white(im)
    lg = logo(150); im.paste(lg, ((SX0 + SX1 - 150) // 2, 470), lg); d = ImageDraw.Draw(im)
    fc = fit(d, c["cta"], "Poppins-Bold.ttf", 84, SW, 4)
    sub = ("Ogni sera alle 19:30 una nuova pillola" if c.get("rubrica") == "pillola" else
           f"Ogni {GIORNI.get(c.get('rubrica'), 'giorno')}: {RUBRICHE.get(c.get('rubrica'), 'un consiglio pratico').lower()}")
    out = {}
    def draw(dd, col, dx, dy):
        y = block(dd, c["cta"], fc, 700 + dy, col or WHITE, maxw=SW, gap=1.14, width=SX0 + SX1)
        out["y"] = block(dd, sub, font("Poppins-Bold.ttf", 40), y + 50 + dy, col or (250, 222, 160), maxw=SW, width=SX0 + SX1)
    shadow_text(im, draw); return im, out["y"]

def v4_ritual(rt, ph):
    top = 600; im = panel(ph, top, dark=True); header_white(im); d = ImageDraw.Draw(im)
    y = label(d, "IL RITUALE DI STAGIONE", SX0, top + 60, bgc=GOLD, fg=DEEP, fs=30)
    y = block(d, rt["titolo"], fit(d, rt["titolo"], "Poppins-Bold.ttf", 90, SW, 2), y + 32, (250, 244, 255), maxw=SW, gap=1.1, x=SX0)
    if rt.get("sub"): y = block(d, rt["sub"], font("Poppins-Bold.ttf", 42), y + 12, GOLD, maxw=SW, x=SX0)
    y += 40; fp = font("Poppins-Regular.ttf", 46 if len(rt["passi"]) <= 3 else 40)
    for k, p in enumerate(rt["passi"][:5], 1):
        d.text((SX0, y), f"{k}", font=font("Poppins-Bold.ttf", 50), fill=GOLD)
        y = block(d, p, fp, y + 6, (236, 228, 248), maxw=SW - 70, gap=1.33, x=SX0 + 70) + 26
    return im, y

def v4_blend(bl, ph):
    top = 560; im = panel(ph, top); header_white(im); d = ImageDraw.Draw(im)
    y = label(d, "IL BLEND DELLA SETTIMANA", SX0, top + 56, bgc=TERRA, fs=28)
    y = block(d, bl["nome"], fit(d, bl["nome"], "Poppins-Bold.ttf", 84, SW, 2), y + 26, TERRA, maxw=SW, gap=1.1, x=SX0)
    y = block(d, bl.get("quando", ""), font("Poppins-Bold.ttf", 40), y + 8, GREEN, maxw=SW, x=SX0) + 34
    rh = int(118 * _FS)
    for o in bl["oli"][:4]:
        d.rounded_rectangle([SX0, y, SX1, y + rh], radius=34, fill=(255, 255, 255))
        g = int(o["gocce"]); t = f"{g} gocc{'ia' if g == 1 else 'e'}"; f = font("Poppins-Bold.ttf", 42); tw = d.textlength(t, font=f)
        d.text((SX0 + 36, y + rh * 0.26), o["olio"], font=fit(d, o["olio"], "Poppins-Bold.ttf", 50, SW - tw - 110, 1), fill=PURPLE)
        d.text((SX1 - 36 - tw, y + rh * 0.3), t, font=f, fill=TERRA); y += rh + 18
    if bl.get("note"): y = block(d, bl["note"], fit(d, bl["note"], "Poppins-Regular.ttf", 44, SW, 4), y + 18, BODY, maxw=SW, gap=1.38, x=SX0)
    return im, y

def v4_myth(m, i, n, ph):
    top = 640; im = panel(ph, top); header_white(im); d = ImageDraw.Draw(im)
    if n > 1: pill(d, f"{i + 1}/{n}", SX1, SY0 + 10)
    y = label(d, "VERO O FALSO?", SX0, top + 64, bgc=PURPLE, fs=30); claim = f"“{m['claim']}”"
    y = block(d, claim, fit(d, claim, "Poppins-BoldItalic.ttf", 76, SW, 4), y + 30, PURPLE, maxw=SW, gap=1.12, x=SX0)
    v = m["verdetto"].upper(); f = font("Poppins-Bold.ttf", 88); tw = d.textlength(v, font=f); y += 36; bh = int(f.size * 1.45)
    d.rounded_rectangle([SX0, y, SX0 + tw + 80, y + bh], radius=bh // 2, fill=TERRA if v.startswith("FALS") else GREEN)
    d.text((SX0 + 40, y + (bh - f.size) * 0.32), v, font=f, fill=(255, 255, 255))
    y = block(d, m["spiegazione"], fit(d, m["spiegazione"], "Poppins-Regular.ttf", 50, SW, 6), y + bh + 40, BODY, maxw=SW, gap=1.42, x=SX0)
    return im, y

def v4_card(s, ph):
    top = 500; im = panel(ph, top); header_white(im); d = ImageDraw.Draw(im)
    y = label(d, "LA SCHEDA DELL'OLIO", SX0, top + 52, bgc=GREEN, fs=28)
    y = block(d, s["olio"], fit(d, s["olio"], "Poppins-Bold.ttf", 104, SW, 2), y + 16, PURPLE, maxw=SW, x=SX0)
    y = block(d, s.get("famiglia", ""), font("Poppins-Bold.ttf", 38), y, GREEN, maxw=SW, x=SX0) + 30
    secs = [("PROFUMO", s["profumo"]), ("SI ABBINA CON", s["abbinamenti"]), ("3 USI", " · ".join(s["usi"]))]
    if s.get("sostituti"): secs.append(("SE NON CE L'HAI", s["sostituti"]))
    fs = 44 if len(secs) == 3 else 40
    for t, body in secs:
        d.text((SX0, y), t, font=font("Poppins-Bold.ttf", 32), fill=TERRA)
        y = block(d, body, fit(d, body, "Poppins-Regular.ttf", fs, SW, 3), y + int(46 * _FS), BODY, maxw=SW, gap=1.3, x=SX0) + 22
    return im, y

def v4_scenes(c):
    r = c.get("rubrica", "comesifa"); tips = c.get("tips", []); cov, sce, cta = photos_for(c); sc = []
    extra = [f for f in stock_files(c.get("foto", {}).get("scene", RUB_FOTO.get(r, RUB_FOTO["comesifa"])[1])) if f not in (cov, cta)]
    used_tip = set()
    def _tip_photo(i): return extra[(i + int(hashlib.md5(c["hook"].encode()).hexdigest(), 16)) % len(extra)] if extra else sce
    def tip_photo(i):
        for t in ((tips[i]["title"].lower(), tips[i].get("body", "").lower()) if i < len(tips) else ()):
            for k, cat in KEYWORDS.items():
                if k in t and cat in ("bottiglie", "lavanda", "limone", "arancio", "eucalipto", "erbe", "rosmarino", "incenso", "diffusore", "candele", "tessuti", "casa", "bagno", "te", "viaggio"):
                    f = pick_photo(cat, c["hook"] + str(i), tuple(used_tip | {cov, cta})); used_tip.add(f); return f
        return _tip_photo(i)
    def add(im, text, lo=3.2, hi=6.5, dark=False): sc.append((im, secs_for(text, lo, hi), dark))
    add(fitscene(v4_cover, c, cov), c["hook"] + " " + c.get("sub", ""), 3.0, 4.5, True)
    def tipscenes():
        for i, t in enumerate(tips): add(fitscene(v4_tip, t, i, len(tips), tip_photo(i)), t["title"] + " " + t["body"])
    if r == "blend":
        bl = c["blend"]; add(fitscene(v4_blend, bl, sce), bl["nome"] + " " + bl.get("note", "") + " x" * 8, 5, 8); tipscenes()
    elif r == "mito":
        for i, m in enumerate(c["mito"]): add(fitscene(v4_myth, m, i, len(c["mito"]), _tip_photo(i)), m["claim"] + " " + m["spiegazione"], 4.5, 7.5)
    elif r == "rituale":
        rt = c["rituale"]; add(fitscene(v4_ritual, rt, sce), " ".join(rt["passi"]) + " " + rt["titolo"], 6, 9, True)
    elif r == "scheda":
        s = c["scheda"]; ph = pick_photo(next((cat for k, cat in KEYWORDS.items() if k in s["olio"].lower()), sce), c["hook"] + "s", (cov,)) if any(k in s["olio"].lower() for k in KEYWORDS) else sce
        add(fitscene(v4_card, s, ph), s["profumo"] + " " + s["abbinamenti"] + " " + " ".join(s["usi"]) + " " + s.get("sostituti", ""), 6, 10); tipscenes()
    else: tipscenes()
    add(fitscene(v4_cta, c, cta), c["cta"], 3.6, 4.2, True)
    return sc, (cov, sce, cta)


# ----- v4.2: zoom liscio (sub-pixel, con accelerazione morbida) -----
# Lo zoompan di ffmpeg arrotonda il riquadro al pixel intero e il video "tremola":
# qui ogni fotogramma e' calcolato in Python con ritaglio a virgola mobile e interpolazione bicubica.
ZOOM_AMP = 0.035   # 3,5% in tutta la scena: movimento appena percepibile
def render_kb(im, dur, out, fade_in=True, zoom_out=False, dark=False):
    import math
    src = im.convert("RGB"); n = max(2, int(round(dur * FPS)))
    col = "0x1C1228" if dark else "0xFBF8F6"
    fin = f"fade=t=in:st=0:d=0.3:color={col}," if fade_in else ""
    vf = f"{fin}fade=t=out:st={dur - 0.3:.2f}:d=0.3:color={col},format=yuv420p"
    p = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                          "-r", str(FPS), "-i", "-", "-vf", vf, "-r", str(FPS), "-c:v", "libx264", "-crf", "20",
                          "-preset", "veryfast", "-pix_fmt", "yuv420p", out], stdin=subprocess.PIPE)
    for f in range(n):
        t = f / (n - 1); e = 0.5 - 0.5 * math.cos(math.pi * t)          # ease-in-out
        z = 1 + ZOOM_AMP * ((1 - e) if zoom_out else e)
        w, h = W / z, H / z; x0, y0 = (W - w) / 2, (H - h) / 2
        fr = src.transform((W, H), Image.EXTENT, (x0, y0, x0 + w, y0 + h), Image.BICUBIC)
        p.stdin.write(fr.tobytes())
    p.stdin.close(); p.wait()
    if p.returncode: raise RuntimeError("ffmpeg render_kb fallito")


# ----- v4.3 (audit del 7/11): primi 2 secondi piu' forti, tagli secchi, durata nei limiti, controllo del testo -----
# Copertina 1,8-2,2 s con zoom piu' deciso (7%) e testo che si muove dal fotogramma zero (il primo fotogramma resta
# leggibile: e' la copertina di Instagram). Niente dissolvenze tra le scene: tagli secchi, cosi' il reel puo' andare in loop.
# Durata totale: rubrica 20-30 s, pillola 12-18 s (oppure "durata": [min, max] nel JSON, usato nei test).
# Prima del render stampa CONTROLLO_TESTO: OK oppure gli avvisi (parole per schermata, hook lungo, parole vietate).
COVER_ZOOM = 0.07
POP = 0.05            # il testo della copertina parte al 105% e si assesta in 0,35 s
PAROLE_MAX = 25
HOOK_MAX = 7
VIETATE = ["salute", "curare", "guarisc", "guarire", "terapeutic", "terapia", "rimedio", "sintom", "malatt",
           "dolore", "mal di testa", "emicrania", "ansia", "insonnia", "depression", "infiamm", "antibatteric", "antivir",
           "immunitari", "disintossic", "detox", "medic", "farmac", "gravidanza", "incinta", "raffreddore", "tosse",
           "influenza", "digestion", "ingerire", "da bere", "per cucinare", "nei piatti", "puro sulla pelle", "bocchetta", "aspirapolvere",
           "ferro da stiro", "umidificatore", "stress"]
DURATE = {"pillola": (12, 18)}

def v4_cta(c, ph):
    im = shade(photo(ph), top=0.5, flat=0.55, color=(30, 18, 46)); header_white(im)
    lg = logo(150); im.paste(lg, ((SX0 + SX1 - 150) // 2, 470), lg); d = ImageDraw.Draw(im)
    fc = fit(d, c["cta"], "Poppins-Bold.ttf", 84, SW, 4)
    sub = c.get("cta_sub") or ("Ogni sera alle 19:30 una nuova pillola" if c.get("rubrica") == "pillola" else
           f"Ogni {GIORNI.get(c.get('rubrica'), 'giorno')}: {RUBRICHE.get(c.get('rubrica'), 'un consiglio pratico').lower()}")
    out = {}
    def draw(dd, col, dx, dy):
        y = block(dd, c["cta"], fc, 700 + dy, col or WHITE, maxw=SW, gap=1.14, width=SX0 + SX1)
        out["y"] = block(dd, sub, font("Poppins-Bold.ttf", 40), y + 50 + dy, col or (250, 222, 160), maxw=SW, width=SX0 + SX1)
    shadow_text(im, draw); return im, out["y"]

def _testi(c):
    """testo di ogni schermata, nello stesso ordine delle scene"""
    r = c.get("rubrica"); out = [("copertina", c["hook"] + " " + c.get("sub", ""))]
    tips = [("consiglio %d" % (i + 1), t["title"] + " " + t.get("body", "") + " " + t.get("momento", "")) for i, t in enumerate(c.get("tips", []))]
    if r == "blend":
        bl = c["blend"]; out.append(("blend", " ".join([bl["nome"], bl.get("quando", ""), bl.get("note", "")]))); out += tips
    elif r == "mito": out += [("vero o falso %d" % (i + 1), m["claim"] + " " + m["verdetto"] + " " + m["spiegazione"]) for i, m in enumerate(c["mito"])]
    elif r == "rituale": rt = c["rituale"]; out.append(("rituale", " ".join([rt["titolo"]] + rt["passi"])))
    elif r == "scheda":
        s = c["scheda"]; out.append(("scheda", " ".join([s["olio"], s["profumo"], s["abbinamenti"], s.get("sostituti", "")] + s["usi"]))); out += tips
    else: out += tips
    out.append(("chiusura", c["cta"] + " " + c.get("cta_sub", "")))
    return out

def controllo_testo(c):
    avvisi = []
    if len(c["hook"].split()) > HOOK_MAX: avvisi.append(f"hook di {len(c['hook'].split())} parole (max {HOOK_MAX})")
    for nome, t in _testi(c):
        n = len(t.split())
        if nome not in ("copertina", "chiusura") and n > PAROLE_MAX: avvisi.append(f"{nome}: {n} parole (max {PAROLE_MAX})")
    import re
    tutto = " ".join(t for _, t in _testi(c)).lower()
    for v in VIETATE:
        if re.search(r"\b" + re.escape(v.strip()), tutto): avvisi.append(f"parola da evitare: '{v.strip()}'")
    print("CONTROLLO_TESTO:", "OK" if not avvisi else " | ".join(avvisi))
    return avvisi

def _durate(c, sc):
    lo, hi = c.get("durata") or DURATE.get(c.get("rubrica"), (20, 30))
    durs = [s[1] for s in sc]; tot = sum(durs); fixed = durs[0]
    if tot > hi:
        k = (hi - fixed) / max(0.1, tot - fixed)
        durs = [durs[0]] + [max(2.4, d * k) for d in durs[1:]]
    if sum(durs) < lo: print("AVVISO_DURATA: %.1f s, sotto i %d s previsti: aggiungi un consiglio" % (sum(durs), lo))
    return durs

def _strato(a, b):
    """parti di a che non ci sono in b, come livello trasparente"""
    from PIL import ImageChops, ImageFilter
    m = ImageChops.difference(a.convert("RGB"), b.convert("RGB")).convert("L").point(lambda v: 255 if v > 4 else 0)
    m = m.filter(ImageFilter.MaxFilter(5)).filter(ImageFilter.GaussianBlur(0.8))
    lay = a.convert("RGBA"); lay.putalpha(m); return lay, m.getbbox()

def _pipe(out, dur):
    return subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                             "-r", str(FPS), "-i", "-", "-vf", "format=yuv420p", "-r", str(FPS), "-c:v", "libx264", "-crf", "20",
                             "-preset", "veryfast", "-pix_fmt", "yuv420p", "-t", f"{dur:.3f}", out], stdin=subprocess.PIPE)

def _zoom(src, z):
    w, h = W / z, H / z; x0, y0 = (W - w) / 2, (H - h) / 2
    return src.transform((W, H), Image.EXTENT, (x0, y0, x0 + w, y0 + h), Image.BICUBIC)

def render_cover43(bg, full, ph, dur, out):
    import math
    hdr = bg.copy(); header_white(hdr)
    head, _ = _strato(hdr, bg); txt, bb = _strato(full, hdr)
    cx, cy = ((bb[0] + bb[2]) / 2, (bb[1] + bb[3]) / 2) if bb else (W / 2, H / 2)
    n = max(2, int(round(dur * FPS))); p = _pipe(out, dur); src = bg.convert("RGB")
    for f in range(n):
        t = f / (n - 1); e = 1 - (1 - t) ** 2                       # parte veloce e rallenta: movimento subito
        fr = _zoom(src, 1 + COVER_ZOOM * e).convert("RGBA")
        fr.alpha_composite(head)
        tt = min(1.0, (f / FPS) / 0.35); s = 1 + POP * (1 - (0.5 - 0.5 * math.cos(math.pi * tt)))
        if s > 1.0005:
            w, h = W / s, H / s; x0, y0 = cx - cx / s, cy - cy / s
            lay = txt.transform((W, H), Image.EXTENT, (x0, y0, x0 + w, y0 + h), Image.BICUBIC)
        else: lay = txt
        fr.alpha_composite(lay); p.stdin.write(fr.convert("RGB").tobytes())
    p.stdin.close(); p.wait()
    if p.returncode: raise RuntimeError("ffmpeg copertina fallito")

def render_cut(im, dur, out, zoom_out=False):
    import math
    src = im.convert("RGB"); n = max(2, int(round(dur * FPS))); p = _pipe(out, dur)
    for f in range(n):
        t = f / (n - 1); e = 0.5 - 0.5 * math.cos(math.pi * t)
        p.stdin.write(_zoom(src, 1 + ZOOM_AMP * ((1 - e) if zoom_out else e)).tobytes())
    p.stdin.close(); p.wait()
    if p.returncode: raise RuntimeError("ffmpeg scena fallito")

def reel_v43(c, out, audio=None, frames=False):
    controllo_testo(c)
    tmp = tempfile.mkdtemp(); sc, used = v4_scenes(c); cov = used[0]
    sc[0] = (sc[0][0], secs_for(c["hook"] + " " + c.get("sub", ""), 1.8, 2.2), sc[0][2])
    durs = _durate(c, sc); files = []
    for k, ((im, _, dark), dur) in enumerate(zip(sc, durs)):
        mp4 = f"{tmp}/s{k}.mp4"
        if k == 0: render_cover43(shade(photo(cov), top=0.6, bottom=0.9, start=0.28), im, cov, dur, mp4)
        else: render_cut(im, dur, mp4, zoom_out=(k % 2 == 1))
        files.append(mp4)
    lst = f"{tmp}/list.txt"; open(lst, "w").write("".join(f"file '{f}'\n" for f in files))
    silent = f"{tmp}/video.mp4"
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", silent], check=True)
    total = sum(durs)
    if audio:
        af = f"afade=t=in:st=0:d=0.3,afade=t=out:st={total-1.2:.2f}:d=1.2,volume=0.85"
        cmd = ["ffmpeg", "-y", "-loglevel", "error", "-i", silent, "-stream_loop", "-1", "-i", audio, "-map", "0:v", "-map", "1:a",
               "-af", af, "-t", f"{total:.2f}", "-c:v", "copy", "-c:a", "aac", "-b:a", "160k", out]
    else:
        cmd = ["ffmpeg", "-y", "-loglevel", "error", "-i", silent, "-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo",
               "-map", "0:v", "-map", "1:a", "-c:v", "copy", "-c:a", "aac", "-shortest", out]
    subprocess.run(cmd, check=True)
    if frames:
        for k, s in enumerate(sc): s[0].convert("RGB").save(out[:-4] + f"_frame{k}.png")
    print(out); print("DURATA: %.1f s" % total); print("FOTO_USATE:", ",".join(used))


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    c = json.load(open(args[0])); v4 = stock_ok() and "--v3" not in sys.argv
    if "--weekly-carousel" in sys.argv:
        return (weekly_carousel_v4 if v4 else weekly_carousel)(c, args[1])
    if "--carousel" in sys.argv:
        if "rubrica" in c: c = dict(c, tips=summary_tips(c))
        return carousel(c, args[1])
    if "--controllo" in sys.argv:
        return controllo_testo(c)
    if "rubrica" in c:
        fn = reel_v43 if v4 else reel_v3
        return fn(c, args[1], args[2] if len(args) > 2 else None, "--frames" in sys.argv)
    return main_v2()

if __name__ == "__main__":
    main()
