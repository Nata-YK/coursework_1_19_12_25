import json
import datetime


def print_hi() -> str:
    """
    Функция приветствия
    """
    name_client = input()
    hour_now = datetime.datetime.now()
    hour = hour_now.hour
    minute = hour_now.minute
    total_minutes = hour * 60 + minute
    if 5 * 60 <= total_minutes <= 12 * 60:
        str_val = "Доброе утро"
    elif 12 * 60 <= total_minutes <= 18 * 60:
        str_val = "Добрый день"
    elif 18 * 60 <= total_minutes <= 21 * 60:
        str_val = "Добрый вечер"
    else:
        str_val = "Доброй ночи"

    result = {"greeting": f"{str_val}, {name_client}!"}
    return result


def saves_in_json(transactions, output_file):
    """Функция сохраняет в JSON-файл."""
    try:
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(transactions, f, ensure_ascii=False, indent=4)
            print(f"{transactions}. Результат сохранен в {output_file}")
    except Exception as e:
        print(f"Ошибка при сохранении файла: {e}")

        return transactions
