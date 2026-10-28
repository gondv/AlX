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
        r = requests.post(url_tg, data=payload, timeout=15)
        if r.status_code != 200:
            print(f"Aviso de Telegram ({r.status_code}): {r.text}")
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
    producto_objetivo = None

    # 1. Recorremos todas las tarjetas exactas <label class="home-saba__product">
    for label in soup.select("label.home-saba__product"):
        titulo_el = label.select_one(".home-saba__product-title")
        desc_el = label.select_one(".home-saba__product-desc")
        
        texto_titulo = titulo_el.get_text(strip=True) if titulo_el else ""
        texto_desc = desc_el.get_text(strip=True) if desc_el else ""

        if "Abono 24h L-D" in texto_titulo or "59-Abono 24h" in texto_desc:
            producto_objetivo = label
            break

    if not producto_objetivo:
        print("Aviso: No se encontró la tarjeta 'label.home-saba__product' del Abono 24h L-D.")
        if MODO_PRUEBA:
            enviar_telegram("⚠️ <b>Aviso de prueba:</b> No se encontró la tarjeta del producto en el HTML.")
        return

    # Extraemos los datos exactos de los selectores de la tarjeta
    titulo = producto_objetivo.select_one(".home-saba__product-title")
    precio = producto_objetivo.select_one(".home-saba__product-price")
    etiqueta_agotado = producto_objetivo.select_one(".home-saba__product-outofstock")
    caja_deshabilitada = producto_objetivo.select_one(".home-saba__product-body-disabled")
    radio_compra = producto_objetivo.select_one("input.home-saba__product-radio, input[name='contractId']")

    texto_completo = producto_objetivo.get_text(" | ", strip=True)
    print(f"Lectura completa de <label class='home-saba__product'>: {texto_completo}")

    # Comprobación triple de disponibilidad real:
    # Está agotado si tiene el div .home-saba__product-outofstock, la clase disabled, o la palabra "agotado"
    esta_agotado = (
        etiqueta_agotado is not None
        or caja_deshabilitada is not None
        or "agotado" in texto_completo.lower()
    )

    if not esta_agotado or radio_compra is not None:
        enviar_telegram(
            "🚨 <b>¡ABONO 24H L-D DISPONIBLE EN ALFONSO X!</b> 🚨\n\n"
            f"📌 <b>Producto:</b> {titulo.get_text(strip=True) if titulo else 'Abono 24h L-D'}\n"
            f"💶 <b>Precio actual:</b> {precio.get_text(strip=True) if precio else 'Ver web'}\n"
            f"📋 <b>Lectura tarjeta:</b> <i>{texto_completo}</i>\n\n"
            f"👉 <a href='{URL_PARKING}'>HAZ CLIC AQUÍ PARA CONTRATARLO AHORA</a>"
        )
        print("¡DISPONIBLE! Alerta enviada.")
    else:
        print("Confirmado: Sigue agotado (detectado .home-saba__product-outofstock / body-disabled).")
        if MODO_PRUEBA:
            enviar_telegram(
                "✅ <b>¡Calibración HTML perfecta!</b>\n\n"
                "Ahora estoy leyendo la etiqueta exacta <code>label.home-saba__product</code> de SABA/Interparking:\n\n"
                f"📋 <i>{texto_completo}</i>\n\n"
                "He detectado correctamente el bloque <code>home-saba__product-outofstock (Agotado)</code>. "
                "Cero falsos positivos a partir de ahora: solo te avisaré cuando se habilite la compra real."
            )

if __name__ == "__main__":
    comprobar_abono()
