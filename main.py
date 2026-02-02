import os

import pandas as pd

from src.course_api import get_transaction_amount, get_stock_prices_alphavantage, get_stock_prices_yahoo
from src.reports import spending_by_category
from src.services import find_number
from src.utils import print_hi, saves_in_json
from src.views import read_xlsx_file, cards_unique, get_top_transactions

folder = "data"
file_xlsx = "operations.xlsx"
file_path_xlsx = os.path.join(folder, file_xlsx)
abs_path_xlsx = os.path.abspath(file_path_xlsx)


def cards():
    print("Представьтесь, как Вас зовут")
    hi = print_hi()
    dict_xlsx = read_xlsx_file(abs_path_xlsx)
    print("Введи дату отчета в формате ДД.ММ.ГГГГ или оставьте поле пустым, чтобы не было фильтрации по датам")
    data_report = input()
    dict_cards = cards_unique(dict_xlsx, data_report)
    top_transactions = get_top_transactions(dict_xlsx, data_report)
    get_course = get_transaction_amount(dict_xlsx, data_report)
    get_stock = get_stock_prices_alphavantage(), get_stock_prices_yahoo()
    return hi, dict_cards, top_transactions, get_course, get_stock


def services():
    dict_xlsx = read_xlsx_file(abs_path_xlsx)
    numbers_json = find_number(dict_xlsx)
    return numbers_json


def record_json():
    record_file = cards()
    result_services = services()
    record_json = saves_in_json([record_file, result_services], "user_settings.json")
    return record_json


def record_txt(category, data_for_category=None):
    if not os.path.exists(abs_path_xlsx):
        print(f"Файл не найден: {abs_path_xlsx}")
        print("Текущая рабочая директория:", os.getcwd())
        exit()

    try:
        # Пробуем разные движки для чтения Excel
        try:
            file_json = pd.read_excel(abs_path_xlsx, engine="openpyxl")
        except:
            # Если openpyxl не работает, пробуем xlrd
            file_json = pd.read_excel(abs_path_xlsx, engine="xlrd")

        # 2. Вызываем декорированную функцию
        file_report = spending_by_category(file_json, category, data_for_category)

        # 3. Печатаем результат для проверки
        print(f"Траты по категории '{category}':")

    except FileNotFoundError:
        print(f"Файл не найден. Проверьте путь к файлу {abs_path_xlsx}")
    except Exception as e:
        print(f"Произошла ошибка: {e}")
    return file_report


if __name__ == "__main__":
    # формирование JSON-файла
    print(record_json())
    # формирование TXT-файла - отчет по категориям
    print(record_txt("Такси", "30.12.2021"))
    # data_report = '13.10.2020'
    # dict_xlsx = read_xlsx_file(abs_path_xlsx)
    # #print(get_top_transactions(dict_xlsx, data_report))
    # symbols = ["MSFT", "TSLA"]
    # print(get_transaction_amount(symbols))