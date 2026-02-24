import os

from src.services import find_number


def test_find_number(transactions, result) -> None:
    assert find_number(transactions) == result


def test_find_number_not_file() -> None:
    file1_path = os.path.join("data", "operations.xlsx111.xlsx")
    assert find_number(file1_path) == f"Ошибка: Файл {file1_path} 'str' object has no attribute 'get'."


def test_find_number_empty(dict_for_test_empty) -> None:
    file1_path_empty = os.path.join("data", "")
    assert find_number(file1_path_empty) == f"Ошибка: Файл {file1_path_empty} 'str' object has no attribute 'get'."
