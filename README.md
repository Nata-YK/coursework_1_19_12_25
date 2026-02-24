# Курсовая работа №1
## В модулях:
### views.py
* Функция read_xlsx_file(output_file) для считывания финансовых операций из Excel  принимает путь к Excel файлу в качестве аргумента,
где output_file - это Excel-файл.
* Функция cards_unique(dict_xlsx, date_now=None) анализирует транзакции за период с 1 числа месяца до указанной даты, 
если дата не указана, то фильтрации по датам не будет. По каждой карте: последние 4 цифры карты; общая сумма расходов; 
кешбэк (1 рубль на каждые 100 рублей), где dict_xlsx это словарь, а date_now - дата для формирования отчета.
* Функция get_top_transactions(dict_xlsx, date_now=None, limit=5), которая сортирует топ-N транзакций по сумме (по модулю).
### utils.py
* Функция print_hi() приветствия.
* функция saves_in_json(transactions, output_file) сохраняет в JSON-файл.
### course_api.py
* Функция get_currency_rates_cbr(date_report=None) создана для получения курсов валют от ЦБ РФ на указанную дату или последнюю доступную дату.
date_report: Дата в формате DD.MM.YYYY. Если None - используется текущая дата. Функция возвращает список словарей с курсами 
валют в формате {"currency": "USD", "rate": 73.21}.
* функция get_transaction_amount(dict_xlsx, date_report) создана для получения курсов валюткурсов валют для обработки транзакций.
dict_xlsx: Список словарей с данными транзакций. date_report: Дата отчета в формате DD.MM.YYYY. Если None - используется текущая дата.
Функция возвращает словарь с курсами валют в формате JSON.
* функция get_stock_prices_yahoo(symbols), которая принимает список транзакций и возвращает курсы валют, 
альтернативный способ через Yahoo Finance (без API ключа)
* функция get_stock_prices_alphavantage(symbols=None, date_past=None) создана для получение цен акций через Alpha Vantage API.
symbols: Список тикеров акций. По умолчанию: ["AAPL", "AMZN", "GOOGL", "MSFT", "TSLA", "ORCL"], date_past: Дата в формате DD.MM.YYYY или объект date.
Если None - используется последняя доступная дата. Функция возвращает словарь с ценами акций.
### services.py
* функция find_number(data_call), которая осуществляет поиск по телефонным номерам, принимает транзаакции в формате списка.
### reports.py
* функция-декоратор report_writer(filename=None):, декоратор для записи результатов функций-отчетов в файл, в скобках можно указать в формате *.txt
наименование файла, в который можно сохранить отчет, если файла с таким названием нет в данной папке / директории, то декоратор его создаст.
* функция spending_by_category(transactions, category, date=None) возвращает траты по заданной категории за последние три месяца,
если дата не указана, то фильтрации по датам не будет. Параметры функции: transactions - это датафрейм с транзакциями, category - это 
название категории для анализа, а date - опциональная дата (в формате 'YYYY-MM-DD'), если не передана, берется текущая дата.

## Kод для функции read_xlsx_file
```
def read_xlsx_file(output_file: str) -> Any:
    try:
        if not output_file:
            logger.warning(f"Передан пустой путь к файлу: {output_file}")
            print("Не найдено ни одной транзакции, подходящей под вашиm условия фильтрации")
            return []
            # Проверка существования файла
        elif not os.path.exists(output_file):
            logger.warning(f"Файл не найден: {output_file}")
            return f"Файл не найден: {output_file}"
        elif output_file:
            logger.info(f"Файл-xlsx: {output_file} читаю")
            data_file_xlsx_read = pd.read_excel(output_file, engine="openpyxl")
            data_file_xlsx_read_not_none = data_file_xlsx_read.where(
                pd.notna(data_file_xlsx_read), None
            )  # Проверка пустых ячеек на Nan, где пустые ячейки
            # могут интерпретироваться (тип float).
            result_dict = data_file_xlsx_read_not_none.to_dict(orient="records")
            return result_dict
    except FileNotFoundError:
        logger.error(f"Ошибка: файл {output_file} не найден по пути")
        return f"Ошибка: файл {output_file} не найден по пути"
    except PermissionError:
        logger.error(f"Ошибка: к файлу {output_file} нет прав с доступом")
        return f"Ошибка: к файлу {output_file} нет прав с доступом"
    except Exception as ex:
        logger.error(f"Ошибка: Файл {output_file} {ex}.")
        return f"Ошибка: Файл {output_file} {ex}."
```
## Kод для функции cards_unique(dict_xlsx, date_now=None)
```
def cards_unique(dict_xlsx, date_now=None):
    if not dict_xlsx:
        print("Нет транзакций для отображения статистики")
        return {"cards": []}
        # Если дата не указана, анализируем весь файл
    if not date_now:
        start_date = None
        end_date = None
    else:
        # Парсим указанную дату
        end_date = datetime.strptime(date_now, "%d.%m.%Y")
        # Начало периода - 1 число того же месяца
        start_date = datetime(end_date.year, end_date.month, 1)

    # Создаем словарь для агрегации данных по картам
    cards_dict = {}

    for key in dict_xlsx:
        # Пропускаем транзакции без даты
        if not key.get("Дата операции"):
            continue

        try:
            # Парсим дату транзакции
            transaction_date_str = key.get("Дата операции", "").split()[0]
            transaction_date = datetime.strptime(transaction_date_str, "%d.%m.%Y")
        except (ValueError, AttributeError, IndexError):
            continue

        # Если указан период, фильтруем по датам
        if start_date and end_date:
            if transaction_date < start_date or transaction_date > end_date:
                continue

        cards_number = key.get("Номер карты")
        # Пропускаем пустые номера карт
        if not cards_number:
            continue
        # Получаем сумму операции
        amount = key.get("Сумма платежа", 0)
        status_ok = key.get("Статус")
        # Пропускаем не-OK транзакции
        if status_ok != "OK":
            continue

        # Если сумма отрицательная (расход)
        if amount < 0:
            amount_for_cashback = abs(amount)

            # Рассчитываем cashback (1 рубль на каждые 100 рублей)
            cashback = (amount_for_cashback // 100) * 1  # 1 рубль за каждые 100 рублей

            # Извлекаем последние 4 цифры карты
            card_str = str(cards_number)
            if '*' in card_str:
                last_digits = card_str.split('*')[-1]
            else:
                # Берем последние 4 символа, если их меньше - дополняем
                last_digits = card_str[-4:] if len(card_str) >= 4 else card_str.zfill(4)[-4:]

            # Используем последние 4 цифры как ключ, а не полный номер карты
            if last_digits not in cards_dict:
                cards_dict[last_digits] = {
                    "last_digits": last_digits,
                    "total_spent": 0,
                    "cashback": 0
                }

            # Суммируем потраченное
            cards_dict[last_digits]["total_spent"] += abs(amount)
            cards_dict[last_digits]["cashback"] += cashback

        # Преобразуем в нужный формат
    result_cards = []
    for card_data in cards_dict.values():
        result_cards.append({
            "last_digits": card_data["last_digits"],
            "total_spent": round(card_data["total_spent"], 2),
            "cashback": round(card_data["cashback"], 2)
        })

    return {"cards": result_cards}
```
## Kод для функции get_top_transactions(dict_xlsx, date_now=None, limit=5)
```
def get_top_transactions(dict_xlsx, date_now=None, limit=5):
    if not dict_xlsx:
        print("Нет транзакций для отображения статистики")
        return {"top_transactions": []}

    # Определяем период
    if date_now:
        end_date = datetime.strptime(date_now, "%d.%m.%Y")
        start_date = datetime(end_date.year, end_date.month, 1)
    else:
        start_date = end_date = None

    # Фильтруем транзакции
    filtered = []
    for trans in dict_xlsx:
        # Проверяем статус и сумму
        if trans.get("Статус") != "OK" or trans.get("Сумма платежа", 0) >= 0:
            continue

        # Проверяем дату, если указан период
        if start_date and end_date:
            try:
                trans_date_str = trans.get("Дата операции", "").split()[0]
                trans_date = datetime.strptime(trans_date_str, "%d.%m.%Y")
                if not (start_date <= trans_date <= end_date):
                    continue
            except:
                continue

        filtered.append(trans)

    # Сортируем и выбираем топ
    sorted_trans = sorted(filtered, key=lambda x: abs(x["Сумма платежа"]), reverse=True)

    # Формируем результат
    top = []
    for trans in sorted_trans[:limit]:
        top.append({
            "date": trans.get("Дата операции", ""),
            "amount": abs(trans.get("Сумма платежа", 0)),
            "category": trans.get("Категория", ""),
            "description": trans.get("Описание", "")
        })

    return {"top_transactions": top}
```
## Kод для функции print_hi()
```
def print_hi()-> str:
    """
    Функция приветствия
    """
    name_client = input()
    hour_now = datetime.datetime.now()
    hour = hour_now.hour
    minute = hour_now.minute
    total_minutes = hour * 60 + minute
    if 5*60 <= hour < 12*60:
        str_val = "Доброе утро"
    elif 12*60 < hour < 18*60:
        str_val = "Добрый день"
    elif 18*60 < hour < 21*60:
        str_val = "Добрый вечер"
    else:
        str_val = "Доброй ночи"

    result = {"greeting": f"{str_val}, {name_client}!"}
    return result
```
## Kод для функции saves_in_json(transactions, output_file)
```
def saves_in_json(transactions, output_file):
    try:
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(transactions, f, ensure_ascii=False, indent=4)
            print(f"{transactions}. Результат сохранен в {output_file}")
    except Exception as e:
        print(f"Ошибка при сохранении файла: {e}")

        return transactions
```
## Код для функции get_currency_rates_cbr(date_report=None)
```
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
```
## Kод для функции get_transaction_amount(dict_xlsx, date_report)
```
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

```
## Код для функции get_stock_prices_yahoo(symbols)
```
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
```
## Код get_stock_prices_alphavantage(symbols=None, date_past=None)
```
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
```
## Код для функции-декоратора find_number(data_call)
```
def find_number(data_call: List[Dict]) -> List[Dict]:
    """
    Поиск по телефонным номерам, принимает транзаакции в формате списка
    """
    try:
        pattern = re.compile(r"(\+?7\s?\d{3}\s\d{2,3}-\d{2}-\d{2})")
        new_list_number = []
        for number in data_call:
            logger.info("Получаем описание, преобразуем в строку для безопасности")
            description = str(number.get("Описание", ""))
            logger.info("Ищем номер в любой части строки")
            if pattern.search(description):
                new_list_number.append(description)
            result = {f"Найдено {len(new_list_number)} номер(ов)": new_list_number}
        return result
    except FileNotFoundError:
        logger.error(f"Ошибка: файл {data_call} не найден по пути")
        return f"Ошибка: файл {data_call} не найден по пути"
    except PermissionError:
        logger.error(f"Ошибка: к файлу {data_call} нет прав с доступом")
        return f"Ошибка: к файлу {data_call} нет прав с доступом"
    except Exception as ex:
        logger.error(f"Ошибка: Файл {data_call} {ex}.")
        return f"Ошибка: Файл {data_call} {ex}."

```
## Код для функции report_writer(filename)
```
def report_writer(filename: Optional[str] = None):
    """
    Декоратор для записи результатов функций-отчетов в файл

    Args:
        filename: Имя файла для записи. Если None - генерируется автоматически.
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            # Выполняем исходную функцию
            result = func(*args, **kwargs)

            # Определяем имя файла
            if filename:
                logger.info("Имя файла для сохранения отчета - указано")
                file_path = filename
            else:
                # Генерируем имя файла по умолчанию
                logger.info("Имя файла для записи. Если None - генерируется автоматически")
                timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                func_name = func.__name__
                file_path = f"report_{func_name}_{timestamp}.txt"

            # Записываем результат в файл
            try:
                with open(file_path, "w", encoding="utf-8") as f:
                    if isinstance(result, pd.DataFrame):
                        logger.info("Файла является DataFrame выводим в виде таблицы")
                        # Для DataFrame записываем в виде таблицы
                        f.write(result.to_string())
                    elif isinstance(result, (list, tuple, dict)):
                        logger.info("Файла является листом или кортежем или словарем, преобразуем в JSON")
                        # Для структур данных - красивое представление
                        import json

                        f.write(json.dumps(result, indent=2, ensure_ascii=False))
                    else:
                        logger.info("Для остальных форматов файлов, выводим в виде строки")
                        # Для всего остального - строковое представление
                        f.write(str(result))

                print(f"Отчет сохранен в файл: {file_path}")
            except Exception as e:
                logger.error(f"Ошибка: Файл {file_path} {e}.")
                print(f"Ошибка при записи в файл {file_path}: {e}")

            return result

        return wrapper

    # Если декоратор вызван без скобок (без параметров)
    if callable(filename):
        logger.info("Декоратор вызван без параметров")
        func = filename
        filename = None
        return decorator(func)

    return decorator
```
## Код для функции spending_by_category(transactions, category, date= None)
```
def spending_by_category(transactions: pd.DataFrame, category: str, date: Optional[str] = None) -> pd.DataFrame:
    """
    Возвращает траты по заданной категории за последние три месяца

    Args:
        transactions: Датафрейм с транзакциями
        category: Название категории для анализа
        date: Опциональная дата (в формате 'YYYY-MM-DD').
               Если не передана, берется текущая дата.

    Returns:
        pd.DataFrame с тратами по категории за последние 3 месяца
    """
    # Преобразуем дату
    if date is None:
        target_date = datetime.date.today()
    else:
        target_date = datetime.datetime.strptime(date, "%d.%m.%Y").date()

    # Вычисляем дату 3 месяца назад
    three_months_ago = target_date - datetime.timedelta(days=90)

    # Преобразуем даты в датафрейме к формату datetime
    # Предполагаем, что столбец с датой называется 'Дата операции'
    transactions["Дата операции"] = pd.to_datetime(transactions["Дата операции"], format="%d.%m.%Y %H:%M:%S")

    # Фильтруем по дате (последние 3 месяца)
    filtered_df = transactions[
        (transactions["Дата операции"].dt.date >= three_months_ago)
        & (transactions["Дата операции"].dt.date <= target_date)
    ]

    # Фильтруем по категории
    # Предполагаем, что столбец с категорией называется 'Категория'
    category_column = None
    possible_category_columns = ["Категория"]

    for col in possible_category_columns:
        if col in filtered_df.columns:
            category_column = col
            break

    if category_column is None:
        # Если не нашли столбец с категорией, ищем столбец, содержащий категории
        for col in filtered_df.columns:
            if any(
                isinstance(val, str) and val.lower().find("категория") != -1
                for val in filtered_df[col].dropna().head(5)
            ):
                category_column = col
                break

    if category_column is None:
        raise ValueError("Не найден столбец с категориями в датафрейме")

    # Фильтруем по указанной категории
    result_df = filtered_df[filtered_df[category_column] == category].copy()

    # Если результат пустой, возвращаем пустой датафрейм
    if result_df.empty:
        return pd.DataFrame()

    # Сортируем по дате (от новых к старым)
    result_df = result_df.sort_values("Дата операции", ascending=False)

    # Сортируем по столбецу 'Сумма платежа'
    amount_column = None
    possible_amount_columns = ["Сумма платежа"]

    for col in possible_amount_columns:
        if col in result_df.columns:
            amount_column = col
            break

    if amount_column is None:
        raise ValueError("Не найден столбец с суммами платежей")

    # Преобразуем суммы к числовому типу (убираем RUB и другие символы)
    result_df[amount_column] = (
        result_df[amount_column].astype(str).str.replace("RUB", "").str.replace(" ", "").astype(float)
    )

    # Добавляем столбец с месяцем для группировки
    result_df["Месяц"] = result_df["Дата операции"].dt.to_period("M")

    return result_df
```

### Пример выходных данных для проверки 
1) Функция read_xlsx_file(output_file):
'Номер карты': '*7197', 'Статус': 'OK', 'Сумма операции': -25.0, 'Валюта операции': 'RUB', 'Сумма платежа': -25.0, 'Валюта платежа': 'RUB', 'Кэшбэк': nan, 'Категория': 'Дом и ремонт', 'MCC': 5200.0, 'Описание': 'OOO Nadezhda', 'Бонусы (включая кэшбэк)': 0, 'Округление на инвесткопилку': 0, 'Сумма операции с округлением': 25.0}, {'Дата операции': '17.07.2019 15:01:15', 'Дата платежа': '19.07.2019', 
'Номер карты': '*7197', 'Статус': 'OK', 'Сумма операции': -27.0, 'Валюта операции': 'RUB', 'Сумма платежа': -27.0, 'Валюта платежа': 'RUB', 'Кэшбэк': nan, 'Категория': 'Дом и ремонт', 'MCC': 5200.0, 'Описание': 'OOO Nadezhda', 'Бонусы (включая кэшбэк)': 0, 'Округление на инвесткопилку': 0, 'Сумма операции с округлением': 27.0}, {'Дата операции': '16.07.2019 16:30:10', 'Дата платежа': '18.07.2019', 
2) Функция cards_unique(dict_xlsx, date_now=None):
{'cards': [{'last_digits': '7197', 'total_spent': 8301.2, 'cashback': 62.0}, {'last_digits': '4556', 'total_spent': 1061.0, 'cashback': 9.0}]}
3) get_top_transactions(dict_xlsx, date_now=None, limit=5)
{'top_transactions': [{'date': '04.10.2020 14:07:24', 'amount': 5376.02, 'category': 'ЖКХ', 'description': 'ЖКУ Квартира'}, {'date': '03.10.2020 15:04:23', 'amount': 5000.0, 'category': 'Переводы', 'description': 'Людмила Щ.'}, {'date': '13.10.2020 09:19:58', 'amount': 1653.82, 'category': 'ЖКХ', 'description': 'ЖКУ Дом'}, {'date': '09.10.2020 16:14:34', 'amount': 1235.0, 'category': 'Супермаркеты', 'description': 'WILDBERRIES'}, {'date': '05.10.2020 13:24:42', 'amount': 1199.0, 'category': 'Дом и ремонт', 'description': 'DNS'}]}
4) Функция print_hi():
{'greeting': 'Добрый вечер, Natalya!'}
5) saves_in_json(transactions, output_file):
[({'greeting': 'Добрый вечер, Natalya!'}, {'cards': [{'last_digits': '7197', 'total_spent': 21093.84, 'cashback': 177.0}, {'last_digits': '4556', 'total_spent': 500.0, 'cashback': 4.0}]}, {'top_transactions': [{'date': '23.07.2018 17:20:19', 'amount': 65718.61, 'category': 'Переводы', 'description': 'Перевод Кредитная карта. ТП 10.2 RUR'}, {'date': '21.07.2018 15:22:04', 'amount': 5600.0, 'category': 'Переводы', 'description': 'Дарья Ч.'}, {'date': '05.07.2018 14:01:14', 'amount': 4293.22, 'category': 'Другое', 'description': 'ГУП ВЦКП ЖХ'}, {'date': '23.07.2018 13:39:38', 'amount': 4200.0, 'category': 'Переводы', 'description': 'Перевод Кредитная карта. ТП 10.2 RUR'}, {'date': '20.07.2018 16:30:28', 'amount': 4000.0, 'category': 'Переводы', 'description': 'Дарья Ч.'}]}, {'currency_rates': [{'currency': 'EUR', 'rate': 91.247}, {'currency': 'USD', 'rate': 77.0223}, {'currency': 'CNY', 'rate': 11.0538}, {'currency': 'TRY', 'rate': 17.7551}]}, {'stock_prices': [{'stock': 'AAPL', 'price': 264.55}, {'stock': 'AMZN', 'price': 244.68}, {'stock': 'GOOGL', 'price': 341.86}, {'stock': 'MSFT', 'price': 425.75}, {'stock': 'TSLA', 'price': 419.33}]}), {'Найдено 31 номер(ов)': ['Тинькофф Мобайл +7 995 555-55-55', 'Тинькофф Мобайл +7 995 555-55-55', 'Я МТС +7 921 11-22-33', 'Я МТС +7 921 11-22-33', 'Я МТС +7 921 11-22-33', 'МТС Mobile +7 981 333-44-55', 'МТС Mobile +7 981 333-33-33', 'МегаФон +7 921 333-33-33', 'МТС Mobile +7 921 111-22-33', 'Я МТС +7 921 11-22-33', 'МТС +7 981 666-66-66', 'МТС Mobile +7 921 111-22-33', 'МТС Mobile +7 981 888-88-88', 'МТС +7 981 976-14-20', 'МТС +7 981 976-14-20', 'МТС +7 981 976-14-20', 'Я МТС +7 921 111-22-33', 'МТС Mobile +7 985 111-11-11', 'МТС Mobile +7 921 999-99-99', 'Я МТС +7 921 11-22-33', 'МТС +7 911 198-78-58', 'МТС +7 981 555-55-55', 'МТС +7 981 976-14-20', 'Teletie Бизнес +7 966 000-00-00', 'МТС +7 911 000-09-09', 'МТС +7 911 882-65-08', 'Билайн +7 962 717-08-52', 'Билайн +7 962 717-08-52', 'МТС +7 981 127-94-00', 'МТС +7 911 695-42-03', 'Я МТС +7 921 11-22-33']}]. Результат сохранен в user_settings.json
6) get_currency_rates_cbr(date_report=None):
7) get_transaction_amount(dict_xlsx, date_report):
8) get_stock_prices_yahoo(symbols):
9) find_number(data_call):
{'Найдено 31 номер(ов)': ['Тинькофф Мобайл +7 995 555-55-55', 'Тинькофф Мобайл +7 995 555-55-55', 'Я МТС +7 921 11-22-33', 'Я МТС +7 921 11-22-33', 'Я МТС +7 921 11-22-33', 'МТС Mobile +7 981 333-44-55', 'МТС Mobile +7 981 333-33-33', 'МегаФон +7 921 333-33-33', 'МТС Mobile +7 921 111-22-33', 'Я МТС +7 921 11-22-33', 'МТС +7 981 666-66-66', 'МТС Mobile +7 921 111-22-33', 'МТС Mobile +7 981 888-88-88', 'МТС +7 981 976-14-20', 'МТС +7 981 976-14-20', 'МТС +7 981 976-14-20', 'Я МТС +7 921 111-22-33', 'МТС Mobile +7 985 111-11-11', 'МТС Mobile +7 921 999-99-99', 'Я МТС +7 921 11-22-33', 'МТС +7 911 198-78-58', 'МТС +7 981 555-55-55', 'МТС +7 981 976-14-20', 'Teletie Бизнес +7 966 000-00-00', 'МТС +7 911 000-09-09', 'МТС +7 911 882-65-08', 'Билайн +7 962 717-08-52', 'Билайн +7 962 717-08-52', 'МТС +7 981 127-94-00', 'МТС +7 911 695-42-03', 'Я МТС +7 921 11-22-33']}
10)

## Тесты
1) К функциям read_xlsx_file(output_file) и cards_unique(dict_xlsx, date_now=None) тесты написаны в модуле test_masks.py, функциональный код покрыт тестами на 84%.