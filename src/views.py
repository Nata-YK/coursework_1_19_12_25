import logging
import os
from typing import Any
from datetime import datetime, timedelta
import calendar
import pandas as pd

# Настройка логгера
logger = logging.getLogger("views")

os.makedirs("logs", exist_ok=True)
file_handler = logging.FileHandler("logs/views.log", encoding="utf-8")
file_formatter = logging.Formatter("%(asctime)s %(name)s %(levelname)s: %(message)s")
file_handler.setFormatter(file_formatter)
logger.addHandler(file_handler)
logger.setLevel(logging.INFO)


def read_xlsx_file(output_file: str) -> Any:
    """
    Функция  для считывания финансовых операций из Excel  принимает путь к Excel файлу в качестве аргумента.
    """
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


def cards_unique(dict_xlsx, date_now=None):
    """
    Функция анализирует транзакции за период с 1 числа месяца до указанной даты, если дата не указана то весь файл
    По каждой карте: последние 4 цифры карты; общая сумма расходов; кешбэк (1 рубль на каждые 100 рублей).
    """
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
            if "*" in card_str:
                last_digits = card_str.split("*")[-1]
            else:
                # Берем последние 4 символа, если их меньше - дополняем
                last_digits = card_str[-4:] if len(card_str) >= 4 else card_str.zfill(4)[-4:]

            # Используем последние 4 цифры как ключ, а не полный номер карты
            if last_digits not in cards_dict:
                cards_dict[last_digits] = {"last_digits": last_digits, "total_spent": 0, "cashback": 0}

            # Суммируем потраченное
            cards_dict[last_digits]["total_spent"] += abs(amount)
            cards_dict[last_digits]["cashback"] += cashback

        # Преобразуем в нужный формат
    result_cards = []
    for card_data in cards_dict.values():
        result_cards.append(
            {
                "last_digits": card_data["last_digits"],
                "total_spent": round(card_data["total_spent"], 2),
                "cashback": round(card_data["cashback"], 2),
            }
        )

    return {"cards": result_cards}


def get_top_transactions(dict_xlsx, date_now=None, limit=5):
    """Получить топ-N транзакций по сумме (по модулю)"""
    if not dict_xlsx:
        print("Нет транзакций для отображения статистики")
        return {"top_transactions": []}

    # Определяем период
    if not date_now:
        start_date = None
        end_date = None
    else:
        end_date = datetime.strptime(date_now, "%d.%m.%Y")
        start_date = datetime(end_date.year, end_date.month, 1)

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
        top.append(
            {
                "date": trans.get("Дата операции", ""),
                "amount": abs(trans.get("Сумма платежа", 0)),
                "category": trans.get("Категория", ""),
                "description": trans.get("Описание", ""),
            }
        )

    return {"top_transactions": top}
