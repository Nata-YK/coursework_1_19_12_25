import os
from typing import Dict, List

import requests
from dotenv import load_dotenv

load_dotenv()  # Загружаем переменные из окружения .env

API_KEY = os.getenv("API_KEY")


def get_transaction_amount(dict_xlsx: List[Dict]) -> List[Dict]:
    """Функция принимает список транзакций и возвращает курсы валют в формате [{currency:..., rate:...}]"""
    if not dict_xlsx:
        return []

    result = []

    try:
        # Собираем уникальные валюты
        currencies_needed = set()
        for transaction in dict_xlsx:
            if transaction.get("Статус") == "OK" and transaction.get("Валюта операции") in [
                "EUR",
                "USD",
                "CNY",
                "TRY",
            ]:
                currencies_needed.add(transaction.get("Валюта операции"))

        if not currencies_needed:
            return []

        # Запрос к API
        response = requests.get("https://www.cbr-xml-daily.ru/daily_json.js", timeout=5)
        response.raise_for_status()
        data = response.json()

        # Формируем ответ в нужном формате
        for currency_code in currencies_needed:
            if currency_code in data["Valute"]:
                currency_data = data["Valute"][currency_code]
                result.append({"currency": currency_code, "rate": currency_data["Value"]})

        return {"currency_rates": result}

    except Exception as e:
        print(f"Ошибка: {e}")
        return []


def get_stock_prices_yahoo(symbols: List[str] = None) -> List[Dict]:
    """Альтернативный способ через Yahoo Finance (без API ключа)"""
    if symbols is None:
        symbols = ["AAPL", "AMZN", "GOOGL", "MSFT", "TSLA"]

    result = []

    for symbol in symbols:
        try:
            # Yahoo Finance через быстрое API
            url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"
            headers = {"User-Agent": "Mozilla/5.0"}

            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            data = response.json()

            # Извлекаем цену
            if "chart" in data and "result" in data["chart"]:
                price = data["chart"]["result"][0]["meta"]["regularMarketPrice"]
                result.append({"stock": symbol, "price": round(price, 2)})
                # print(f"Цена {symbol}: {price}")

        except Exception as e:
            print(f"Ошибка получения цены акции {symbol}: {e}")

    return {"stock_prices": result}
