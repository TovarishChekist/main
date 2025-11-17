# -*- coding: utf-8 -*-
"""
Модуль валидации данных
Проверка корректности введенных пользователем данных
"""

import re
from typing import Tuple


class Validators:
    """Класс для валидации пользовательских данных"""

    @staticmethod
    def validate_age(age_text: str) -> Tuple[bool, str]:
        """
        Валидация возраста
        :param age_text: Текст с возрастом
        :return: (валидность, сообщение об ошибке)
        """
        try:
            age = int(age_text.strip())
            if 10 <= age <= 25:
                return True, ""
            else:
                return False, "Возраст должен быть от 10 до 25 лет"
        except ValueError:
            return False, "Возраст должен быть числом"

    @staticmethod
    def validate_class(class_text: str) -> Tuple[bool, str]:
        """
        Валидация класса
        :param class_text: Текст с классом
        :return: (валидность, сообщение об ошибке)
        """
        # Паттерн: число (5-11) и опционально буква
        pattern = r'^([5-9]|1[01])\s*[А-Я]?$'
        if re.match(pattern, class_text.strip(), re.IGNORECASE):
            return True, ""
        return False, "Класс должен быть в формате: 9А, 11Б и т.д."

    @staticmethod
    def validate_username(username: str) -> Tuple[bool, str]:
        """
        Валидация никнейма Telegram
        :param username: Никнейм
        :return: (валидность, сообщение об ошибке)
        """
        # Паттерн для Telegram username: начинается с @, затем буквы, цифры, подчеркивания
        pattern = r'^@[a-zA-Z0-9_]{5,32}$'
        if re.match(pattern, username.strip()):
            return True, ""
        return False, "Никнейм должен начинаться с @ и содержать только латинские буквы, цифры и подчеркивания (5-32 символа)"

    @staticmethod
    def validate_text_length(text: str, min_length: int = 10, max_length: int = 1000) -> Tuple[bool, str]:
        """
        Валидация длины текста
        :param text: Текст для проверки
        :param min_length: Минимальная длина
        :param max_length: Максимальная длина
        :return: (валидность, сообщение об ошибке)
        """
        text_len = len(text.strip())
        if text_len < min_length:
            return False, f"Текст слишком короткий (минимум {min_length} символов)"
        if text_len > max_length:
            return False, f"Текст слишком длинный (максимум {max_length} символов)"
        return True, ""

    @staticmethod
    def validate_fio(fio: str) -> Tuple[bool, str]:
        """
        Валидация ФИО
        :param fio: Фамилия Имя Отчество
        :return: (валидность, сообщение об ошибке)
        """
        # Проверяем, что есть хотя бы 2 слова (Фамилия Имя)
        words = fio.strip().split()
        if len(words) < 2:
            return False, "ФИО должно содержать минимум Фамилию и Имя"

        # Проверяем, что каждое слово начинается с заглавной буквы и содержит только буквы
        for word in words:
            if not word[0].isupper() or not word.replace('-', '').isalpha():
                return False, "ФИО должно быть в формате: Иванов Иван Иванович (каждое слово с заглавной буквы)"

        return True, ""

    @staticmethod
    def validate_school(school: str) -> Tuple[bool, str]:
        """
        Валидация названия школы
        :param school: Название школы
        :return: (валидность, сообщение об ошибке)
        """
        school = school.strip()
        if len(school) < 5:
            return False, "Название школы слишком короткое"
        if len(school) > 200:
            return False, "Название школы слишком длинное"
        return True, ""

    @staticmethod
    def validate_contacts(contacts: str) -> Tuple[bool, str]:
        """
        Валидация контактов
        :param contacts: Контактная информация
        :return: (валидность, сообщение об ошибке)
        """
        contacts = contacts.strip()
        if len(contacts) < 5:
            return False, "Контактная информация слишком короткая"
        if len(contacts) > 500:
            return False, "Контактная информация слишком длинная"
        return True, ""


# Создаем экземпляр для удобного использования
validators = Validators()
