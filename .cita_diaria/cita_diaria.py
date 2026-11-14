import requests
from PIL import Image, ImageDraw, ImageFont
from datetime import datetime
from html import unescape
import sys
import os
import subprocess
import re

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

PLANTILLA675 = os.path.join(BASE_DIR, "plantilla.jpg")
PLANTILLA720 = os.path.join(BASE_DIR, "plantilla1.jpg")
PLANTILLA787 = os.path.join(BASE_DIR, "plantilla3.jpg")
FUENTE = os.path.join(BASE_DIR, "Adelle_Reg.otf")

cita_manual = None
imagen_manual = None
fecha_manual = None
idioma = "es"
solo_imagen = False

# -----------------------------
# Argumentos
# -----------------------------

for arg in sys.argv[1:]:
    if arg.startswith("cita="):
        cita_manual = arg[5:]
    elif arg.startswith("imagen="):
        imagen_manual = arg[7:]
    elif arg.startswith("fecha="):
        fecha_manual = arg[6:]
    elif arg.startswith("idioma="):
        idioma = arg[7:]
    elif arg == "imagen":
        solo_imagen = True

# -----------------------------
# Variables base
# -----------------------------
cita = cita_manual if cita_manual else None
img_path = "imagen.jpg"

# -----------------------------
# Fecha
# -----------------------------
if fecha_manual:
    fecha = fecha_manual.lower()
else:
    fecha = datetime.now().strftime("%B-%d-%Y").lower()    
# -----------------------------
# Scraping Isha (imagen + cita)
# -----------------------------
def extraer_cita(html):
    try:
        # 1️⃣ CAPA MAESTRA: Buscar en el bloque de datos puros de la plataforma (Next.js)
        match_next = re.search(r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', html, re.DOTALL)
        if match_next:
            json_puro = match_next.group(1)
            canditatos = re.findall(r'"(?:text|body|quote_text|description|content)":\s*"([^"]+)"', json_puro)

            canditatos = re.findall(
                r'"(?:text|body|quote_text|description|content)":\s*"([^"]+)"',
                json_puro
            )
            

            for texto in canditatos:
                texto_limpio = texto.strip()
            
                if re.match(r'https?://', texto_limpio):
                    continue
            
                if len(texto_limpio) < 20:
                    continue
            
                # Decodificar entidades HTML: &#x27; -> ', &amp; -> &, etc.
                texto_limpio = unescape(texto_limpio)
            
                # Corrección UTF-8 / Unicode
                try:
                    # Primero decodificamos escapes tipo \u00fa
                    texto_limpio = texto_limpio.encode('utf-8').decode('unicode-escape')
            
                    # Si quedó mal codificado en bytes latinos (mojibake), repararlo
                    try:
                        texto_limpio = texto_limpio.encode('latin-1').decode('utf-8')
                    except Exception:
                        pass
            
                except Exception:
                    try:
                        texto_limpio = texto_limpio.encode('latin-1').decode('utf-8')
                    except Exception:
                        pass
            
                # Volver a procesar entidades HTML por si aparecieron después
                texto_limpio = unescape(texto_limpio)
            
                texto_limpio = texto_limpio.replace("Sadhguru Quotes - ", "")
            
                return texto_limpio

        # 2️⃣ CAPA DE EMERGENCIA
        propiedades_json = re.findall(r'"(?:text|body|quote_text)"\s*:\s*"([^"]+)"', html)
        for texto in propiedades_json:
            texto_limpio = texto.strip()
            texto_limpio = unescape(texto_limpio)
            if (len(texto_limpio) > 80 
                and "Subscribe" not in texto_limpio 
                and "{" not in texto_limpio
                and "Home/" not in texto_limpio
                and not texto_limpio.endswith(" s")):
                try:
                    texto_limpio = texto_limpio.encode('utf-8').decode('unicode-escape').encode('latin-1').decode('utf-8')
                except Exception:
                    try:
                        texto_limpio = texto_limpio.encode('latin-1').decode('utf-8')
                    except Exception:
                        pass
                texto_limpio = texto_limpio.replace("Sadhguru Quotes - ", "")
                return texto_limpio

        # 3️⃣ FALLBACK
        match = re.search(r'<meta name="description" content="([^"]+)"', html)
        if match:
            texto = unescape(match.group(1))
            texto = texto.replace(" - Sadhguru", "").strip()
            texto = re.sub(r'\.\.\.$', '', texto).strip()
            texto = texto.replace("Sadhguru Quotes - ", "")
            return texto

        return None

    except Exception as e:
        return None

def descargar_datos_isha(fecha):
    try:
        url = f"https://isha.sadhguru.org/{idioma}/wisdom/quotes/date/{fecha}"

        resp = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
        
        resp.encoding = "utf-8"
        html = resp.text


#        imagenes = [
#            img for img in imagenes
#            if not any(x in img.lower() for x in (
#                "logo",
#                "favicon",
#                "icon",
#                "apple-touch",
#                "twitter",
#                "facebook",
#                "linkedin"
#            ))
#        ]
        
        # imagen

        imagenes = re.findall(
            r'https://static\.sadhguru\.org[^"\']+\.(?:jpg|jpeg|png|webp)',
            html
        )
        
        img_url = None
        
        # Buscar una imagen que contenga la fecha en el nombre
        for img in imagenes:
            if fecha in img:
                img_url = img
                break
        
        # Si no existe, usar la última imagen encontrada
        if not img_url and imagenes:
            img_url = imagenes[-1]

        # cita
        cita = extraer_cita(html)

        return img_url, cita

    except:
        return None, None


# -----------------------------
# Obtener imagen + cita
# -----------------------------
if imagen_manual:
    os.system(f'cp "{imagen_manual}" {img_path}')
    print("🖼️ Usando imagen manual")

else:
    print("🔎 Intentando obtener imagen y cita desde Isha...")

    # Fecha
    if fecha_manual:
        fecha = fecha_manual.lower()
    else:
        fecha = datetime.now().strftime("%B-%d-%Y").lower()

    print("📅 Fecha usada:", fecha)

    # Obtener datos
    img_url, cita_auto = descargar_datos_isha(fecha)

    if not img_url:
        print("\n❌ No hay imagen automática.")
        print("https://webapp.sadhguru.org/start-your-day-with-sadhguru/")
        exit()

    # descargar imagen
    with open(img_path, "wb") as f:
        f.write(requests.get(img_url).content)

    print("🌐 URL:", img_url)
    
    if solo_imagen:
        nombre = os.path.expanduser(f"~/Descargas/{fecha}.jpg")
        os.replace(img_path, nombre)
        print("📁", nombre)
        sys.exit(0)

    # usar cita automática si no hay manual
    if not cita and cita_auto:
        cita = cita_auto
        print("📝 Cita obtenida automáticamente")

        
# -----------------------------
# Validación cita
# -----------------------------
if not cita:
    print("❌ No se pudo obtener la cita automáticamente.")
    print('Usa: cita-diaria cita="Tu texto aquí"')
    exit()

# -----------------------------
# Imagen base
# -----------------------------
top = Image.open(img_path).convert("RGB")

w, h = top.size
ratio = 1080 / w
nuevo_h = int(h * ratio)
top = top.resize((1080, nuevo_h))

# -----------------------------
# Plantilla
# -----------------------------
if nuevo_h >= 780:
    top = top.crop((0, 0, 1080, 787))
    plantilla = Image.open(PLANTILLA787).convert("RGB")
    Y = 902
elif nuevo_h >= 720:
    top = top.crop((0, 0, 1080, 720))
    plantilla = Image.open(PLANTILLA720).convert("RGB")
    Y = 812
else:
    top = top.crop((0, 0, 1080, 675))
    plantilla = Image.open(PLANTILLA675).convert("RGB")
    Y = 797

plantilla.paste(top, (0, 0))
draw = ImageDraw.Draw(plantilla)

# -----------------------------
# Texto
# -----------------------------
ANCHO = 762
size = 48

while size > 38:
    font = ImageFont.truetype(FUENTE, size)
    words = cita.split()
    lines = []
    line = ""

    for w_ in words:
        test = line + " " + w_ if line else w_
        if font.getlength(test) < ANCHO * 1.03:
            line = test
        else:
            lines.append(line)
            line = w_

    lines.append(line)
    altura = len(lines) * (size + 12)

    if altura < 250:
        break

    size -= 2

line_spacing = int(size * 0.28)

def draw_text_tracking(draw, x, y, text, font, fill, tracking=2):
    for char in text:
        draw.text((x, y), char, font=font, fill=fill)
        x += font.getlength(char) + tracking

# -----------------------------
# Dibujar texto
# -----------------------------
y = Y
extra_total = 2

for line in lines:
    base_width = sum(font.getlength(c) for c in line)

    tracking = extra_total / (len(line) - 1) if len(line) > 1 else 0

    w_line = base_width + extra_total
    x = (1080 - w_line) // 2

    draw_text_tracking(draw, x, y, line, font, "#111111", tracking)

    y += size + line_spacing

# -----------------------------
# Guardar
# -----------------------------
titulo = " ".join(cita.split()[:4])
titulo = re.sub(r'[\\/*?:"<>|]', "", titulo)

base = os.path.expanduser("~/Descargas")
os.makedirs(base, exist_ok=True)

jpg_name = os.path.join(base, f"{titulo}.jpg")
plantilla.save(jpg_name, "JPEG", quality=100, subsampling=0)
txt_name = os.path.join(base, f"{titulo}.txt")

plantilla.save(jpg_name)

with open(txt_name, "w", encoding="utf-8") as f:
    f.write(cita.strip() + "\n\nSadhguru\n")

os.remove(img_path)

# -----------------------------
# Output
# -----------------------------
print("📝", cita)
print("📁", jpg_name)
print("📄", txt_name)
print("📅 Fecha usada:", fecha)

# Android
if "ANDROID_ARGUMENT" in os.environ:
    subprocess.run([
        "am", "start",
        "-a", "android.intent.action.VIEW",
        "-d", f"file://{txt_name}",
        "-t", "text/plain"
    ])
