import logging
import os
import re
from typing import Dict, List

from src.views import read_xlsx_file

# Настройка логгера
logger = logging.getLogger("services")

os.makedirs("logs", exist_ok=True)
file_handler = logging.FileHandler("logs/services.log", encoding="utf-8")
file_formatter = logging.Formatter("%(asctime)s %(name)s %(levelname)s: %(message)s")
file_handler.setFormatter(file_formatter)
logger.addHandler(file_handler)
logger.setLevel(logging.INFO)


def find_number(data_call: List[Dict]) -> List[Dict]:
    """
    Поиск по телефонным номерам, принимает транзаакции в формате списка
    """
    try:
        pattern = re.compile(r"(\+?7\s?\d{3}\s\d{2,3}-\d{2}-\d{2})")
        new_list_number = []
        for number in data_call:
            logger.info("Получаем описание, преобразуем в строку для безопасности.")
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
