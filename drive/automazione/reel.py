#!/usr/bin/env python3
"""La via dell'aromaterapia - generatore di contenuti.
Reel 1080x1920:      python3 reel.py contenuti.json out.mp4 [audio.mp3] [--frames]
Immagini 1080x1350:  python3 reel.py contenuti.json --carousel cartella_output
   (slide_01.jpg ... slide_NN.jpg + riassunto.jpg per Facebook)
JSON: {"hook", "sub", "tips": [{"title", "body"}], "cta", "cta_post"?, "handle"}
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
    d.text((80, 70), "Il consiglio del giorno", font=font("Poppins-Bold.ttf", 34), fill=(108, 84, 168))
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

def main():
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

if __name__ == "__main__":
    main()
