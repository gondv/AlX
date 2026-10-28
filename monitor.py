import os
import time
import random
import requests
from bs4 import BeautifulSoup

URL_PARKING = "https://p-web.interparking.es/Home/Products?carParkId=6259&contractTypeId=2"

TELEGRAM_TOKEN = (os.environ.get("TELEGRAM_TOKEN") or "").strip()
TELEGRAM_CHAT_ID = (os.environ.get("TELEGRAM_CHAT_ID") or "").strip()
MODO_PRUEBA = (os.environ.get("MODO_PRUEBA") or "false").strip().lower() == "true"

def enviar_telegram(mensaje):
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        print("Error: Faltan credenciales de Telegram.")
        return
    url_tg = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": mensaje,
        "parse_mode": "HTML",
        "disable_web_page_preview": False
    }
    try:
        requests.post(url_tg, data=payload, timeout=15)
    except Exception as e:
        print(f"Error al conectar con Telegram: {e}")

def comprobar_abono():
    if not MODO_PRUEBA:
        time.sleep(random.uniform(2, 12))

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "es-ES,es;q=0.9,en;q=0.8",
        "Referer": "https://www.interparking.es/"
    }

    try:
        response = requests.get(URL_PARKING, headers=headers, timeout=25)
        response.raise_for_status()
    except Exception as e:
        print(f"Error de conexión web: {e}")
        return

    soup = BeautifulSoup(response.text, "html.parser")
    encontrado = False
    agotado = True
    contenido_tarjeta = ""

    # Buscar el texto del abono
    for texto in soup.find_all(string=lambda t: t and ("Abono 24h L-D" in t or "59-Abono 24h" in t)):
        # Táctica del ancla: Subimos por el árbol HTML hasta atrapar el contenedor que tiene el precio (€)
        padre = texto.parent
        while padre and padre.name != 'body':
            texto_padre = padre.get_text(" ", strip=True)
            # Si el contenedor ya incluye el símbolo del euro, hemos capturado la tarjeta entera
            if "€" in texto_padre:
                contenido_tarjeta = texto_padre
                encontrado = True
                break
            padre = padre.parent
        
        if encontrado:
            break

    if not encontrado:
        print("Aviso: No se encontró el abono o su precio en la página.")
        return

    print(f"Estado leído en la web ampliado: {contenido_tarjeta}")

    # Ahora sí, comprobamos si dice agotado en toda la tarjeta (Título + Precio + Botón)
    if "agotado" not in contenido_tarjeta.lower():
        agotado = False

    if not agotado:
        enviar_telegram(
            "🚨 <b>¡ABONO 24H L-D DISPONIBLE EN ALFONSO X!</b> 🚨\n\n"
            "El <b>Abono 24h L-D ALFONSO X</b> ya NO aparece como Agotado.\n"
            f"📋 <i>Info detectada: {contenido_tarjeta}</i>\n\n"
            f"👉 <a href='{URL_PARKING}'>HAZ CLIC AQUÍ PARA CONTRATARLO</a>"
        )
    else:
        print("Sigue agotado. Sin novedades.")

if __name__ == "__main__":
    comprobar_abono()
