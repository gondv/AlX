import os
import time
import random
import requests
from bs4 import BeautifulSoup

# URL exacta de Abonos Mensuales (contractTypeId=2) en Alfonso X (6259)
URL_PARKING = "https://p-web.interparking.es/Home/Products?carParkId=6259&contractTypeId=2"

TELEGRAM_TOKEN = (os.environ.get("TELEGRAM_TOKEN") or "").strip()
TELEGRAM_CHAT_ID = (os.environ.get("TELEGRAM_CHAT_ID") or "").strip()
MODO_PRUEBA = (os.environ.get("MODO_PRUEBA") or "false").strip().lower() == "true"

def enviar_telegram(mensaje):
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        print("Error: Faltan TELEGRAM_TOKEN o TELEGRAM_CHAT_ID en los Secrets de GitHub.")
        return

    url_tg = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": mensaje,
        "parse_mode": "HTML",
        "disable_web_page_preview": False
    }
    try:
        r = requests.post(url_tg, data=payload, timeout=15)
        if r.status_code != 200:
            print(f"Aviso de Telegram ({r.status_code}): {r.text}")
        else:
            print("Mensaje enviado a Telegram correctamente.")
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
        print(f"No se pudo cargar la web de Interparking en este intento: {e}")
        return

    soup = BeautifulSoup(response.text, "html.parser")
    encontrado = False
    agotado = True
    contenido_tarjeta = ""

    # Busca únicamente por el nombre del abono, sin importar qué precio tenga ahora o en el futuro
    for texto in soup.find_all(string=lambda t: t and ("Abono 24h L-D" in t or "59-Abono 24h" in t)):
        encontrado = True
        bloque = texto.find_parent("div", class_=lambda c: c and any(k in c.lower() for k in ["product", "card", "item", "box"]))
        if not bloque:
            bloque = texto.parent.parent.parent

        contenido_tarjeta = bloque.get_text(" ", strip=True)
        print(f"Estado leído en la web: {contenido_tarjeta}")

        if "agotado" not in contenido_tarjeta.lower():
            agotado = False
        break

    if not encontrado:
        print("Aviso: No se encontró el texto 'Abono 24h L-D' en la página.")
        if MODO_PRUEBA:
            enviar_telegram(
                "⚠️ <b>Aviso de prueba:</b> He conectado con la web, pero no he encontrado el texto 'Abono 24h L-D'. "
                f"Revisa el enlace: {URL_PARKING}"
            )
        return

    if not agotado:
        enviar_telegram(
            "🚨 <b>¡ABONO 24H L-D DISPONIBLE EN ALFONSO X!</b> 🚨\n\n"
            "El <b>Abono 24h L-D ALFONSO X</b> ya NO aparece como Agotado.\n"
            f"📋 <i>Info detectada: {contenido_tarjeta}</i>\n\n"
            f"👉 <a href='{URL_PARKING}'>HAZ CLIC AQUÍ PARA CONTRATARLO AHORA</a>"
        )
        print("¡DISPONIBLE! Alerta enviada a Telegram.")
    else:
        print("Sigue agotado. Sin novedades.")
        if MODO_PRUEBA:
            enviar_telegram(
                "✅ <b>¡Vigilante actualizado al Abono 24h L-D!</b>\n\n"
                "He comprobado la web de Interparking (sin depender del precio) y he leído esto en vivo:\n"
                f"📌 <i>{contenido_tarjeta}</i>\n\n"
                "Me quedo vigilando 24/7 cada 5 minutos. ¡Te avisaré en cuanto desaparezca la palabra Agotado! 🚗💨"
            )

if __name__ == "__main__":
    comprobar_abono()
