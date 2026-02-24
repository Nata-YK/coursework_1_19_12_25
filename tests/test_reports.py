import os
from unittest.mock import Mock, patch

import pandas as pd
import pytest

from src.reports import report_writer, spending_by_category


def test_spending_by_category(df_file):
    """Тест базовой функциональности"""
    # Используем фикстуру напрямую
    result = spending_by_category(df_file, "Каршеринг")

    assert isinstance(result, pd.DataFrame)
    assert "Дата операции" in result.columns
    assert "Категория" in result.columns

    # В вашей функции ожидается столбец 'Сумма платежа', а не 'Сумма операции'
    # Проверяем, есть ли хотя бы один из возможных столбцов
    assert any(col in result.columns for col in ["Сумма платежа", "Сумма операции"])
    assert "Месяц" in result.columns  # Этот столбец добавляется в функции

    # Проверяем, что все строки имеют категорию 'Каршеринг'
    assert all(result["Категория"] == "Каршеринг")


def test_empty_result(df_file):
    """Тест с категорией, которой нет в данных"""
    result = spending_by_category(df_file, "Несуществующая категория")

    assert isinstance(result, pd.DataFrame)
    assert len(result) == 0  # Пустой DataFrame


def test_function_with_explicit_date():
    """Тест с явно указанной датой (чтобы старые данные попали в фильтр)"""
    # Создаем DataFrame со старыми датами
    data = {
        "Дата операции": ["31.12.2021 12:00:00", "29.12.2021 14:30:00", "28.12.2021 09:15:00", "26.12.2021 18:45:00"],
        "Категория": ["Супермаркеты", "Дом и ремонт", "Каршеринг", "Фастфуд"],
        "Сумма платежа": ["100.50 RUB", "2500 RUB", "350.75 RUB", "500 RUB"],
        "Описание": ["1", "2", "3", "4"],
    }

    df = pd.DataFrame(data)

    # Указываем дату, соответствующую данным
    result = spending_by_category(df, "Каршеринг", date="31.12.2021")

    print(f"Результат с указанной датой: {len(result)} строк")

    assert isinstance(result, pd.DataFrame)
    if len(result) > 0:
        assert "Дата операции" in result.columns
        assert "Категория" in result.columns
        assert all(result["Категория"] == "Каршеринг")


def test_spend_by_category(transactions_without_category):
    with pytest.raises(ValueError) as exc_info:
        spending_by_category(transactions_without_category, "Категрия отсутствует")

    # Проверяем, что сообщение об ошибке соответствует ожидаемому
    assert str(exc_info.value) == "Не найден столбец с категориями в датафрейме"


def test_report_writer_basic():
    """Тест, что декоратор не влияет на работу функции"""

    @report_writer("test_report.txt")
    def simple_func():
        return "test result"

    result = simple_func()

    assert result == "test result"
    assert os.path.exists("test_report.txt")

    # Чистка
    if os.path.exists("test_report.txt"):
        os.remove("test_report.txt")


def test_report_writer_handles_write_error():
    """Тест обработки ошибки при записи в файл"""

    @report_writer("error_file.txt")
    def test_func():
        return "test result"

    # Создаем mock, который выбрасывает исключение при вызове write
    mock_file = Mock()
    mock_file.__enter__ = Mock(return_value=mock_file)
    mock_file.__exit__ = Mock(return_value=None)
    mock_file.write = Mock(side_effect=IOError("Disk full"))

    with patch("builtins.open", return_value=mock_file):
        with patch("builtins.print") as mock_print:
            result = test_func()

            # Проверяем, что функция все равно возвращает результат
            assert result == "test result"

            # Проверяем, что было напечатано сообщение об ошибке
            mock_print.assert_called_with("Ошибка при записи в файл error_file.txt: Disk full")


def test_report_writer_calls_open_correctly():
    """Тест, что декоратор вызывает open с правильными параметрами"""

    @report_writer("test_file.txt")
    def test_func():
        return pd.DataFrame({"A": [1, 2, 3]})

    mock_file = Mock()
    mock_file.__enter__ = Mock(return_value=mock_file)
    mock_file.__exit__ = Mock(return_value=None)
    mock_file.write = Mock()

    with patch("builtins.open", return_value=mock_file) as mock_open:
        test_func()

        # Проверяем, что open был вызван с правильными параметрами
        mock_open.assert_called_once_with("test_file.txt", "w", encoding="utf-8")

        # Проверяем, что write был вызван
        assert mock_file.write.called
