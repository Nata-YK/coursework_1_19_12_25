# Курсовая работа №1
## В модулях:
### views.py
* Функция read_xlsx_file(output_file) для считывания финансовых операций из Excel  принимает путь к Excel файлу в качестве аргумента,
где output_file - это Excel-файл.
* Функция cards_unique(dict_xlsx, date_now=None) анализирует транзакции за период с 1 числа месяца до указанной даты, 
если дата не указана, то фильтрации по датам не будет. По каждой карте: последние 4 цифры карты; общая сумма расходов; 
кешбэк (1 рубль на каждые 100 рублей), где dict_xlsx это словарь, а date_now - дата для формирования отчета.
### utils.py
* Функция print_hi() приветствия.
ранее написанные функции get_mask_card_number и get_mask_account.
* функция saves_in_json(transactions, output_file) сохраняет в JSON-файл.
### course_api.py
* функция get_transaction_amount(dict_xlsx), которая принимает список транзакций и возвращает курсы валют в формате [{currency:..., rate:...}];
* функция get_stock_prices_yahoo(symbols), которая принимает список транзакций и возвращает курсы валют, 
альтернативный способ через Yahoo Finance (без API ключа)
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
## Kод для функции get_transaction_amount(dict_xlsx)
```
def get_transaction_amount(dict_xlsx: List[Dict]) -> List[Dict]:
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
1) Функция read_xlsx_file(output_file)
2) Функция cards_unique(dict_xlsx, date_now=None)

## Тесты
1) К функциям read_xlsx_file(output_file) и cards_unique(dict_xlsx, date_now=None) тесты написаны в модуле test_masks.py, функциональный код покрыт тестами на 84%.