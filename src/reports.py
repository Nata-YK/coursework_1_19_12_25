import datetime
import functools
import logging
import os
from typing import Any, Callable, Optional

import pandas as pd

# Настройка логгера
logger = logging.getLogger("reports")

os.makedirs("logs", exist_ok=True)
file_handler = logging.FileHandler("logs/reports.log", encoding="utf-8")
file_formatter = logging.Formatter("%(asctime)s %(name)s %(levelname)s: %(message)s")
file_handler.setFormatter(file_formatter)
logger.addHandler(file_handler)
logger.setLevel(logging.INFO)


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


@report_writer("file_report.txt")
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
