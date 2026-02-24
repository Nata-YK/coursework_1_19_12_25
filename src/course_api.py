import os
import time

from datetime import datetime, date
from typing import List, Dict, Optional, Union

import requests
from dotenv import load_dotenv

load_dotenv()  # Загружаем переменные из окружения .env

API_KEY = os.getenv("API_KEY")


def get_currency_rates_cbr(date_report: str = None) -> List[Dict]:
    """
    Получение курсов валют от ЦБ РФ на указанную дату или последний доступный.

    Args:
        date_report: Дата в формате DD.MM.YYYY. Если None - используется текущая дата.

    Returns:
        Список словарей с курсами валют в формате {"currency": "USD", "rate": 73.21}
    """
    result = []
    currencies_needed = ["USD", "EUR", "CNY", "TRY"]

    try:
        if date_report:
            # Преобразуем дату из DD.MM.YYYY в формат для ЦБ РФ
            try:
                date_obj = datetime.strptime(date_report, "%d.%m.%Y")
                date_for_api = date_obj.strftime("%d/%m/%Y")
            except ValueError:
                print(f"Неверный формат даты: {date_report}. Используется текущая дата.")
                date_for_api = None
        else:
            date_for_api = None

        # Если дата указана, пробуем получить данные на эту дату
        if date_for_api:
            try:
                url = f"https://www.cbr.ru/scripts/XML_daily.asp?date_req={date_for_api}"
                response = requests.get(url, timeout=10)

                if response.status_code == 200:
                    # Парсим XML ответ
                    import xml.etree.ElementTree as ET
                    root = ET.fromstring(response.content)

                    for valute in root.findall('Valute'):
                        char_code = valute.find('CharCode').text
                        if char_code in currencies_needed:
                            value = float(valute.find('Value').text.replace(',', '.'))
                            nominal = int(valute.find('Nominal').text)
                            rate = round(value / nominal, 4)

                            result.append({
                                "currency": char_code,
                                "rate": rate
                            })
            except Exception:
                # Если ошибка, переходим к получению последних данных
                pass

        # Если на указанную дату данных нет или не все валюты найдены,
        # используем последние доступные данные
        if not result or len(result) < len(currencies_needed):
            # Используем текущие курсы с daily_json.js (последние доступные)
            try:
                response = requests.get("https://www.cbr-xml-daily.ru/daily_json.js", timeout=5)
                response.raise_for_status()
                data = response.json()

                # Собираем недостающие курсы
                found_currencies = {item["currency"] for item in result}

                for currency_code in currencies_needed:
                    if currency_code not in found_currencies and currency_code in data["Valute"]:
                        currency_data = data["Valute"][currency_code]
                        result.append({
                            "currency": currency_code,
                            "rate": round(currency_data["Value"], 4)
                        })
            except Exception:
                # Если API не доступен, возвращаем пустой список
                return []

    except Exception as e:
        print(f"Ошибка получения курсов валют: {e}")
        return []

    # Сортируем валюты в алфавитном порядке для удобства
    result.sort(key=lambda x: x["currency"])
    return result


def get_transaction_amount(dict_xlsx: List[Dict], date_report: str = None) -> Dict:
    """
    Получение курсов валют для обработки транзакций.

    Args:
        dict_xlsx: Список словарей с данными транзакций.
        date_report: Дата отчета в формате DD.MM.YYYY.
                    Если None - используется текущая дата.

    Returns:
        Словарь с курсами валют в формате JSON:
        {
            "currency_rates": [
                {"currency": "USD", "rate": 73.21},
                {"currency": "EUR", "rate": 87.08}
            ]
        }
    """
    try:
        # Собираем уникальные валюты из транзакций со статусом OK
        currencies_needed = set()
        for transaction in dict_xlsx:
            if transaction.get("Статус") == "OK" and transaction.get("Валюта операции") in [
                "EUR", "USD", "CNY", "TRY"
            ]:
                currencies_needed.add(transaction.get("Валюта операции"))

        if not currencies_needed:
            # Возвращаем пустой JSON если нет транзакций с нужными валютами
            return {"currency_rates": []}

        # Получаем курсы валют на указанную дату
        currency_rates = get_currency_rates_cbr(date_report)

        # Фильтруем только нужные валюты (из транзакций)
        filtered_rates = [rate for rate in currency_rates if rate["currency"] in currencies_needed]

        # Сортируем по алфавиту
        filtered_rates.sort(key=lambda x: x["currency"])

        return {
            "currency_rates": filtered_rates
        }

    except Exception as e:
        print(f"Ошибка в get_transaction_amount: {e}")
        # Возвращаем пустой JSON в случае ошибки
        return {"currency_rates": []}


def get_stock_prices_yahoo(symbols: List[str] = None) -> List[Dict]:
    """Альтернативный способ через Yahoo Finance (без API ключа)"""
    if symbols is None:
        symbols = ["AAPL", "AMZN", "GOOGL", "MSFT", "TSLA", "ORCL"]

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

def get_stock_prices_alphavantage(
        symbols: Optional[List[str]] = None,
        date_past: Optional[Union[str, date]] = None
) -> Dict:
    """
    Получение цен акций через Alpha Vantage API.

    Args:
        symbols: Список тикеров акций. По умолчанию: ["AAPL", "AMZN", "GOOGL", "MSFT", "TSLA", "ORCL"]
        date_past: Дата в формате DD.MM.YYYY или объект date.
                   Если None - используется последняя доступная дата.

    Returns:
        Словарь с ценами акций в формате:
        {
            "stock_prices": [
                {"stock": "AAPL", "price": 150.12},
                {"stock": "AMZN", "price": 3173.18},
                ...
            ]
        }
    """
    if symbols is None:
        symbols = ["AAPL", "AMZN", "GOOGL", "MSFT", "TSLA", "ORCL"]

    result = []
    # Преобразуем дату если указана
    target_date_str = None
    if date_past:
        if isinstance(date_past, str):
            try:
                date_obj = datetime.strptime(date_past, "%d.%m.%Y")
                target_date_str = date_obj.strftime("%Y-%m-%d")
            except ValueError:
                print(f"Неверный формат даты: {date_past}. Используется последняя доступная дата.")
        elif isinstance(date_past, date):
            date_obj = datetime.combine(date_past, datetime.min.time())
            target_date_str = date_obj.strftime("%Y-%m-%d")

    print(f"Получение цен {len(symbols)} акций через Alpha Vantage...")

    for i, symbol in enumerate(symbols):
        try:
            # Запрос к Alpha Vantage API
            url = "https://www.alphavantage.co/query"
            params = {
                "function": "TIME_SERIES_DAILY",
                "symbol": symbol,
                "outputsize": "compact",
                "datatype": "json",
                "apikey": API_KEY
            }

            print(f"  [{i + 1}/{len(symbols)}] Запрашиваю {symbol}...")
            response = requests.get(url, params=params, timeout=15)
            response.raise_for_status()
            data = response.json()

            # Обработка ответа
            if "Time Series (Daily)" in data:
                time_series = data["Time Series (Daily)"]

                if not time_series:
                    print(f"    Нет данных для {symbol}")
                    continue

                # Сортируем даты по убыванию (от новых к старым)
                available_dates = sorted(time_series.keys(), reverse=True)

                if target_date_str:
                    # Ищем данные на конкретную дату
                    if target_date_str in time_series:
                        price_data = time_series[target_date_str]
                        price = float(price_data["4. close"])
                        date_used = target_date_str
                    else:
                        # Ищем ближайшую предыдущую дату
                        found_date = None
                        for d in available_dates:
                            if d <= target_date_str:
                                found_date = d
                                break

                        if found_date:
                            price_data = time_series[found_date]
                            price = float(price_data["4. close"])
                            date_used = found_date
                            print(f"    Для {symbol} на {target_date_str} данные не найдены, используется {found_date}")
                        else:
                            # Используем самую последнюю доступную дату
                            last_date = available_dates[0]
                            price_data = time_series[last_date]
                            price = float(price_data["4. close"])
                            date_used = last_date
                            print(
                                f"    Для {symbol} на {target_date_str} и более ранние данные не найдены, используется {last_date}")
                else:
                    # Используем последнюю доступную дату
                    last_date = available_dates[0]
                    price_data = time_series[last_date]
                    price = float(price_data["4. close"])
                    date_used = last_date
                    print(f"    {symbol}: {price:.2f} (на {last_date})")

                result.append({
                    "stock": symbol,
                    "price": round(price, 2),
                    "date": date_used  # Добавляем дату для информации
                })

            elif "Note" in data:
                # Достигнут лимит API
                print(f"    Достигнут лимит Alpha Vantage API: {data['Note']}")
                print(f"    Получено {len(result)} цен из {len(symbols)}. Прерываю запросы...")
                break

            elif "Error Message" in data:
                print(f"    Ошибка для {symbol}: {data['Error Message']}")
            else:
                print(f"    Неожиданный ответ для {symbol}")

            # Соблюдаем лимит API (бесплатный тариф: 5 запросов в минуту)
            if i < len(symbols) - 1:
                time.sleep(12)  # 12 секунд между запросами = 5 запросов в минуту

        except requests.exceptions.Timeout:
            print(f"    Таймаут при запросе {symbol}")
        except requests.exceptions.RequestException as e:
            print(f"    Ошибка сети для {symbol}: {e}")
        except Exception as e:
            print(f"    Неожиданная ошибка для {symbol}: {e}")

    # Удаляем поле date из результата для соответствия формату
    final_result = []
    for item in result:
        final_result.append({
            "stock": item["stock"],
            "price": item["price"]
        })

    return {"stock_prices": final_result}
