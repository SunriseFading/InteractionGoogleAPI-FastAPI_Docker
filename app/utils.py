import os
import requests
import gspread
from bs4 import BeautifulSoup as bs


TELEGRAM_TOKEN = os.environ.get('TELEGRAM_TOKEN')
TELEGRAM_USER_ID = os.environ.get('TELEGRAM_USER_ID')
GOOGLE_SHEET_URL = os.environ.get('GOOGLE_SHEET_URL')


def get_google_sheet() -> list[list]:
    gc = gspread.service_account('key.json')
    sheet = gc.open_by_key(GOOGLE_SHEET_URL).sheet1
    return sheet.get_all_values()


def get_usd_rate() -> float:
    url = "https://www.cbr.ru/scripts/XML_daily.asp"
    try:
        request = requests.get(url)
    except Exception:
        print('Request error get_usd_rate()')
    soup = bs(request.content, 'xml')
    usd_rate = soup.find(ID='R01235').Value.string
    return float(usd_rate.replace(',', '.'))


def send_message_to_telegram(order: str) -> bool:
    text = f"Заказ №{order} не доставлен"
    try:
        response = requests.get(
            url=f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
            params={"chat_id": TELEGRAM_USER_ID, "text": text},
            headers={"Content-Type": "application/octet-stream"}
        )
        if response.status_code == 200:
            return True
    except requests.exceptions.RequestException as e:
        print('HTTP Request failed [send_message_to_telegram]', e)
        return False
