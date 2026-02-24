import os
from typing import Dict
from unittest.mock import Mock, patch

import pandas as pd

from src.views import read_xlsx_file, cards_unique, get_top_transactions


@patch("pandas.read_excel")
@patch("os.path.exists")  # Мокаем и os.path.exists!
def test_read_xlsx_file(mock_exists: Mock, mock_read_excel: Mock, transactions: Dict) -> None:
    # Говорим, что файл "существует"
    mock_exists.return_value = True

    # Мокаем pandas.read_excel
    mock_read_excel.return_value = pd.DataFrame(transactions)

    result = read_xlsx_file("path_to_file.xlsx")
    assert result == transactions


def test_read_xlsx_file_not_file() -> None:
    file1_path = os.path.join("data", "operations.xlsx111.xlsx")
    assert read_xlsx_file(file1_path) == f"Файл не найден: {file1_path}"


def test_read_xlsx_file_empty() -> None:
    file1_path = os.path.join("")
    assert read_xlsx_file(file1_path) == []


def test_cards_emply(dict_for_test_empty):
    """Тест на пустые данные"""
    result = cards_unique([])
    assert result == {"cards": []}


def test_analyze_with_date_filter(sample_transactions):
    """Тест анализа с фильтром по дате, проверка количества карт"""
    result = cards_unique(sample_transactions, "27.12.2021")

    assert "cards" in result
    assert len(result["cards"]) == 2

    # Находим карты
    card_7197 = next((c for c in result["cards"] if c["last_digits"] == "7197"), None)
    card_5091 = next((c for c in result["cards"] if c["last_digits"] == "5091"), None)

    assert card_7197 is not None
    assert card_7197["total_spent"] == 2040.0  # 1500 + 320 + 220
    assert card_7197["cashback"] == 20.0  # 15 + 3 +2

    assert card_5091 is not None
    assert card_5091["total_spent"] == 450.0
    assert card_5091["cashback"] == 4.0


def test_analyze_without_date_filter(sample_transactions):
    """Тест анализа без фильтра по дате"""
    result = cards_unique(sample_transactions)

    assert len(result["cards"]) == 2
    card_7197 = next((c for c in result["cards"] if c["last_digits"] == "7197"), None)

    assert card_7197["total_spent"] == 2040.0
    assert card_7197["cashback"] == 20.0


def test_empty_data(dict_for_test_empty):
    """Тест с пустыми данными"""
    result = get_top_transactions([])
    assert result == {"top_transactions": []}


def test_with_date_filter(sample_transactions):
    """Тест с фильтром по дате"""
    result = get_top_transactions(sample_transactions, "27.12.2021")

    # Должно быть 3 транзакции (в период 01.12-27.12)
    assert len(result["top_transactions"]) == 4

    # Проверяем сортировку по убыванию суммы
    amounts = [t["amount"] for t in result["top_transactions"]]
    assert amounts == [1500.0, 450.0, 320.0, 220.0]

    # Проверяем первую (самую крупную) транзакцию
    first = result["top_transactions"][0]
    assert first["amount"] == 1500.0
    assert first["category"] == "Супермаркеты"
    assert first["description"] == "Магнит"


def test_without_date_filter(sample_transactions):
    """Тест без фильтра по дате"""
    result = get_top_transactions(sample_transactions)

    # Должно быть 5 транзакций (по умолчанию limit=5)
    assert len(result["top_transactions"]) == 5

    # Проверяем, что все транзакции со статусом OK и отрицательной суммой
    amounts = [t["amount"] for t in result["top_transactions"]]
    assert amounts == [1500.0, 450.0, 320.0, 300.0, 220.0]


def test_custom_limit(sample_transactions):
    """Тест с пользовательским лимитом"""
    result = get_top_transactions(sample_transactions, limit=2)
    assert len(result["top_transactions"]) == 2

    # Проверяем только 2 самые крупные транзакции
    amounts = [t["amount"] for t in result["top_transactions"]]
    assert amounts == [1500.0, 450.0]
