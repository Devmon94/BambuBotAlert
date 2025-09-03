from colorama import Fore, Style, init
from dotenv import load_dotenv
from create_tables import CreateTables
from email.mime.text import MIMEText
from playwright.sync_api import sync_playwright
from queries_db import QueriesDB

import argparse
import json
import os
import requests
import smtplib
import sys

CHANNEL_FILE = "alert_channel.json"

URLS = {"https://eu.store.bambulab.com/es/products/p1s?id=596563853858123782&skr=yes&gad_campaignid=20576991998": "Combo",
        "https://eu.store.bambulab.com/es/products/p1s?id=596563853866512385&skr=yes&gad_campaignid=20576991998": "",
        "https://eu.store.bambulab.com/es/products/p1s?id=596563853866512390&skr=yes&gad_campaignid=20576991998": "AM2 Pro Combo"}


def load_config():
    if not os.path.exists(CHANNEL_FILE):
        config = {
            "by_mail": True,
            "by_telegram": True
        }
        
        save_config(config)
        return config
    
    else:
        with open(CHANNEL_FILE, "r") as f:
            config = json.load(f)
        
        return config


def save_config(config):
    with open(CHANNEL_FILE, "w") as f:
        json.dump(config, f, indent=4)


def clean_price(price):
    price_str = price.replace("€", "").replace("EUR", "").strip()

    if "," in price_str:
        price_str = price_str.replace(".", "")
        price_str = price_str.replace(",", ".")

    last_price = float(price_str)
    return last_price


def send_mail_alert(subject, body, to_email):
    smtp_server = SMTP
    smtp_port = PORT
    sender_email = SENDER_MAIL
    sender_password = SENDER_PWD 

    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = sender_email
    msg["To"] = to_email

    with smtplib.SMTP(smtp_server, smtp_port) as server:
        server.starttls()
        server.login(sender_email, sender_password)
        server.send_message(msg)


def send_telegram_alert(body):
    bot_token = TOKEN
    chat_id = ID

    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {"chat_id": chat_id, "text": body}

    requests.post(url, data=payload)


def retrieve_prices():
    with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True)
            db = QueriesDB()

            for url, variant in URLS.items():
                page = browser.new_page()
                page.goto(url)

                title = page.locator("h1.ProductMeta__Title").text_content().strip()
                title = (title + " " + variant)

                db.insert_bambu_product(title)

                discount_price = None
                normal_price = None

                prices = page.locator("div.ProductMeta__PriceList span.ProductMeta__Price")
                for i in range(prices.count()):
                    cls = prices.nth(i).get_attribute("class")
                    text = clean_price(prices.nth(i).text_content().strip())

                    if "--highlight" in cls:
                        discount_price = text

                    elif "--subdued" in cls:
                        normal_price = text

                # si no hay oferta el precio por defecto aparece en --highlight, entonces igualamos el discount al normal
                if discount_price and not normal_price:
                    normal_price = discount_price

                product_id = db.select_bambu_product_id(title)
                print(f"{Fore.LIGHTBLUE_EX}Product ID:{Style.RESET_ALL} {Fore.LIGHTCYAN_EX}{product_id}{Style.RESET_ALL}")
                
                last_prices_data = db.select_bambu_prices(product_id)
                last_normal_price, last_discount_price = last_prices_data if last_prices_data else (None, None)
                print(f"{Fore.LIGHTYELLOW_EX}last_normal_price:{Style.RESET_ALL} {Fore.LIGHTRED_EX}{last_normal_price}{Style.RESET_ALL} | {Fore.LIGHTYELLOW_EX}last_discount_price:{Style.RESET_ALL} {Fore.LIGHTGREEN_EX}{last_discount_price}{Style.RESET_ALL}")

                # SI NO HAY DATOS EN LA BBDD
                if not last_normal_price:
                    db.insert_bambu_prices(product_id, normal_price, discount_price)

                    # SOLO SE ENVIA EN CASO DE OFERTA
                    if discount_price < normal_price:
                        text = f"{title} ha bajado de {normal_price} a {discount_price}"

                        if config.get("by_mail", False):
                            send_mail_alert(
                                subject=f"BOT BAMBU: {title} - Nueva OFERTA!",
                                body=text,
                                to_email=EMAIL_DEST
                            )
                        
                        if config.get("by_telegram", False):
                            send_telegram_alert(text)

                else:
                    # BAJA EL PRECIO NORMAL 
                    if normal_price < last_normal_price:
                        db.insert_bambu_prices(product_id, normal_price, discount_price)
                        text = f"{title} ha bajado su precio normal de {normal_price} a {last_normal_price}"

                        if config.get("by_mail", False):  
                            send_mail_alert(
                                subject=f"BOT BAMBU: {title} - Ha bajado SU PRECIO OFICIAL!",
                                body=text,
                                to_email=EMAIL_DEST
                            )      

                        if config.get("by_telegram", False):
                            send_telegram_alert(text)

                    # DESCUENTO DE AHORA < DESCUENTO ANTERIOR - BAJA MAS DE OFERTA
                    if discount_price < last_discount_price:
                        db.insert_bambu_prices(product_id, normal_price, discount_price)
                        text = f"{title} ha bajado AUN MAS de OFERTA, de {last_discount_price} a {discount_price}"

                        if config.get("by_mail", False):
                            send_mail_alert(
                                subject=f"BOT BAMBU: {title} - Ha bajado MAS de OFERTA!",
                                body=text,
                                to_email=EMAIL_DEST
                            )

                        if config.get("by_telegram", False):
                            send_telegram_alert(text)
                        
                    # DESCUENTO DE AHORA > DESCUENTO ANTERIOR pero DESCUENTO DE AHORA < PRECIO NORMAL - SIGUE EN OFERTA PERO MAS CARA
                    elif discount_price > last_discount_price and discount_price < normal_price:
                        db.insert_bambu_prices(product_id, normal_price, discount_price)
                        text = f"{title} sigue de OFERTA pero ha SUBIDO SU PRECIO de {last_discount_price} a {discount_price}"

                        if config.get("by_mail", False):
                            send_mail_alert(
                                subject=f"BOT BAMBU: {title} - Ha SUBIDO con respecto a la ULTIMA REBAJA pero SIGUE de OFERTA!",
                                body=text,
                                to_email=EMAIL_DEST
                            )
                        
                        if config.get("by_telegram", False):
                            send_telegram_alert(text)

                    # DESCUENTO DE AHORA >= PRECIO NORMAL - VUELVE A SU PRECIO ORIGINAL
                    elif discount_price >= normal_price:
                        db.insert_bambu_prices(product_id, normal_price, discount_price)
                        text = f"{title} ha vuelto al precio de {normal_price}"

                        if config.get("by_mail", False):
                            send_mail_alert(
                                subject=f"BOT BAMBU: {title} - Oferta finalizada!",
                                body=text,
                                to_email=EMAIL_DEST
                            )

                        if config.get("by_telegram", False):
                            send_telegram_alert(text)
                

def print_historical():
    try:
        db = QueriesDB()
        rows = db.select_bambu_historical_prices()

        if not rows:
            print("There is no data.")
        else:
            for row in rows:
                print(f"""{Fore.CYAN}[{row['inserted_on']}]{Style.RESET_ALL} {Fore.LIGHTCYAN_EX}{row['name']}{Style.RESET_ALL}                 
                        {Fore.LIGHTYELLOW_EX}  - Precio normal:{Style.RESET_ALL} {Fore.LIGHTRED_EX}{row['normal_price']} €{Style.RESET_ALL}, 
                        {Fore.LIGHTYELLOW_EX}  - Precio oferta:{Style.RESET_ALL} {Fore.LIGHTGREEN_EX}{row['discount_price']} €{Style.RESET_ALL}""")
    
    except Exception as e:
        print(f"Se ha producido un error: {Fore.RED}{e}{Style.RESET_ALL}")


if __name__ == "__main__":
    config = load_config()

    parser = argparse.ArgumentParser(description="Bot BAMBU")
    subparsers = parser.add_subparsers(dest="command")

    subparsers.add_parser("history", help="Muestra el historico de precios")
    subparsers.add_parser("bymail", help="Envia las alertas solo por mail")
    subparsers.add_parser("bytelegram", help="Envia las alertas solo por telegram")

    args = parser.parse_args()
    
    if args.command == "history":
        print_historical()
        sys.exit(0)

    if args.command == "bymail":
        config["by_mail"] = not config["by_mail"]
        save_config(config)
        print(f"{Fore.RED}Alertas por correo {'activadas' if config['by_mail'] else 'desactivadas'}{Style.RESET_ALL}")
        sys.exit(0)

    elif args.command == "bytelegram":
        config["by_telegram"] = not config["by_telegram"]
        save_config(config)
        print(f"{Fore.RED}Alertas por Telegram {'activadas' if config['by_telegram'] else 'desactivadas'}{Style.RESET_ALL}")
        sys.exit(0)

    print(f"{Fore.LIGHTMAGENTA_EX} -- Starting Bot Alert --{Style.RESET_ALL}")
    print(f"{Fore.LIGHTYELLOW_EX}Checking DDBB and tables{Style.RESET_ALL}")
    CreateTables()

    print(f"{Fore.LIGHTYELLOW_EX}Loading .env file for SMTP...{Style.RESET_ALL}")
    load_dotenv()
    EMAIL_DEST = os.getenv("EMAIL_DEST")
    SMTP = os.getenv("SMTP")
    PORT = os.getenv("PORT")
    SENDER_MAIL = os.getenv("SENDER_MAIL")
    SENDER_PWD = os.getenv("SENDER_PWD")

    TOKEN = os.getenv("TOKEN")
    ID = os.getenv("ID")

    print(f"{Fore.LIGHTYELLOW_EX}Connecting to website...{Style.RESET_ALL}")
    retrieve_prices()

    print(f"{Fore.LIGHTMAGENTA_EX} -- Ending Bot Alert --{Style.RESET_ALL}")