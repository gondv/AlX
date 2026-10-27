import os
import time
import random
import requests
from bs4 import BeautifulSoup

URL_PARKING = "https://p-web.interparking.es/Home/Products?carParkId=6259&contractTypeId=1"
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")
MODO_PRUEBA = os.environ.get("MODO_PRUEBA", "false").lower() == "true"

def enviar_telegram(mensaje):
    url_tg = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": mensaje,
        "parse_mode": "HTML",
        "disable_web_page_preview": False
    }
    r = requests.post(url_tg, data=payload, timeout=10)
    r.raise_for_status()

def comprobar_abono():
    # Pausa aleatoria (2 a 12 seg) para simular comportamiento humano
    if not MODO_PRUEBA:
        time.sleep(random.uniform(2, 12))

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "es-ES,es;q=0.9,en;q=0.8",
        "Referer": "https://www.interparking.es/"
    }

    response = requests.get(URL_PARKING, headers=headers, timeout=20)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")
    encontrado = False
    agotado = True

    # Buscamos específicamente el bloque de Multientrada 30 días
    for texto in soup.find_all(string=lambda t: t and "Multientrada 30" in t):
        encontrado = True
        # Subimos al contenedor de la tarjeta del producto
        bloque = texto.find_parent("div", class_=lambda c: c and any(k in c.lower() for k in ["product", "card", "item", "box"]))
        if not bloque:
            bloque = texto.parent.parent.parent

        contenido_tarjeta = bloque.get_text(" ", strip=True)
        print(f"Estado leído en la web: {contenido_tarjeta}")

        if "Agotado" not in contenido_tarjeta and "agotado" not in contenido_tarjeta.lower():
            agotado = False
        break

    if not encontrado:
        print("Aviso: No se encontró el texto 'Multientrada 30' en la página.")
        return

    if not agotado:
        enviar_telegram(
            "🚨 <b>¡ABONO DISPONIBLE EN ALFONSO X!</b> 🚨\n\n"
            "El abono <b>Multientrada 30 días (124,55€)</b> ya NO aparece como Agotado.\n\n"
            f"👉 <a href='{URL_PARKING}'>HAZ CLIC AQUÍ PARA COMPRARLO AHORA</a>"
        )
        print("¡DISPONIBLE! Alerta enviada a Telegram.")
    else:
        print("Sigue agotado. Sin novedades.")
        if MODO_PRUEBA:
            enviar_telegram(
                "✅ <b>¡Tu vigilante del Parking Alfonso X funciona perfectamente!</b>\n\n"
                "He entrado en la web de Interparking y he comprobado que el abono "
                "<i>Multientrada 30 días (124,55€)</i> sigue <b>Agotado</b> ahora mismo.\n\n"
                "A partir de este momento vigilaré en silencio 24/7 y solo volveré a escribirte "
                "en el instante en que quede una plaza libre. 🚗💨"
            )

if __name__ == "__main__":
    comprobar_abono()
