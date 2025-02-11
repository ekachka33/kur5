import psycopg2
from typing import List, Tuple
from configparser import ConfigParser
import os


class DBManager:
    """
    Класс для управления базой данных PostgreSQL.
    """

    def __init__(self, db_params: dict):
        """
        Инициализация подключения к базе данных.

        Args:
            db_params (dict): Параметры подключения к базе данных.
        """
        self.connection = psycopg2.connect(**db_params)
        self.connection.autocommit = True
        self.cursor = self.connection.cursor()
        self.create_tables()

    def create_tables(self) -> None:
        """
        Создание таблиц companies и vacancies.
        """
        with self.connection:
            with self.connection.cursor() as cursor:
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS companies (
                        id INT PRIMARY KEY,
                        name VARCHAR(255) UNIQUE NOT NULL,
                        url TEXT
                    );
                """)
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS vacancies (
                        id INT PRIMARY KEY,
                        company_id INT REFERENCES companies(id),
                        name VARCHAR(255),
                        salary_from INT,
                        salary_to INT,
                        currency VARCHAR(10),
                        url TEXT
                    );
                """)

    def insert_company(self, company: dict) -> None:
        """
        Вставка информации о компании.

        Args:
            company (dict): Словарь с информацией о компании.
        """
        with self.connection:
            with self.connection.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO companies (id, name, url) 
                    VALUES (%s, %s, %s) 
                    ON CONFLICT (id) DO NOTHING
                """, (company['id'], company['name'], company['alternate_url']))

    def insert_vacancy(self, vacancy: dict, company_id: int) -> None:
        """
        Вставка информации о вакансии с учетом возможных отсутствующих данных.
        """
        # Проверка наличия обязательных полей
        required_keys = ['id', 'name', 'alternate_url']
        if not all(key in vacancy for key in required_keys):
            return

        # Безопасная обработка зарплаты
        salary = vacancy.get('salary') or {}
        salary_from = salary.get('from') or 0
        salary_to = salary.get('to') or 0
        currency = salary.get('currency') or 'RUR'

        try:
            with self.connection:
                with self.connection.cursor() as cursor:
                    cursor.execute("""
                        INSERT INTO vacancies 
                        (id, company_id, name, salary_from, salary_to, currency, url) 
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (id) DO NOTHING
                    """, (
                        vacancy['id'],
                        company_id,
                        vacancy['name'],
                        salary_from,
                        salary_to,
                        currency,
                        vacancy['alternate_url']
                    ))
        except Exception as e:
            print(f"Ошибка при добавлении вакансии: {e}")
            print(f"Проблемная вакансия: {vacancy}")

    def get_companies_and_vacancies_count(self) -> List[Tuple[str, int]]:
        """
        Получение списка компаний и количества их вакансий.

        Returns:
            List[Tuple[str, int]]: Список кортежей (название компании, количество вакансий).
        """
        with self.connection:
            with self.connection.cursor() as cursor:
                cursor.execute("""
                    SELECT c.name, COUNT(v.id) 
                    FROM companies c 
                    LEFT JOIN vacancies v ON c.id = v.company_id 
                    GROUP BY c.name
                """)
                return cursor.fetchall()

    def get_all_vacancies(self) -> List[Tuple]:
        """
        Получение всех вакансий с информацией о компании.

        Returns:
            List[Tuple]: Список вакансий с названием компании, вакансии, зарплатой и ссылкой.
        """
        with self.connection:
            with self.connection.cursor() as cursor:
                cursor.execute("""
                    SELECT c.name, v.name, v.salary_from, v.salary_to, v.url 
                    FROM vacancies v 
                    JOIN companies c ON v.company_id = c.id
                """)
                return cursor.fetchall()

    def get_avg_salary(self) -> float:
        """
        Получение средней зарплаты по вакансиям.

        Returns:
            float: Средняя зарплата.
        """
        with self.connection:
            with self.connection.cursor() as cursor:
                cursor.execute("""
                    SELECT AVG((salary_from + salary_to) / 2) 
                    FROM vacancies 
                    WHERE salary_from IS NOT NULL AND salary_to IS NOT NULL
                """)
                return cursor.fetchone()[0]

    def get_vacancies_with_higher_salary(self) -> List[Tuple]:
        """
        Получение вакансий с зарплатой выше средней.

        Returns:
            List[Tuple]: Список вакансий с зарплатой выше средней.
        """
        avg_salary = self.get_avg_salary()
        with self.connection:
            with self.connection.cursor() as cursor:
                cursor.execute("""
                    SELECT name, salary_from, salary_to, url 
                    FROM vacancies 
                    WHERE ((salary_from + salary_to) / 2) > %s
                """, (avg_salary,))
                return cursor.fetchall()

    def get_vacancies_with_keyword(self, keyword: str) -> List[Tuple]:
        """
        Получение вакансий с определенным ключевым словом.

        Args:
            keyword (str): Ключевое слово для поиска.

        Returns:
            List[Tuple]: Список вакансий, содержащих ключевое слово.
        """
        with self.connection:
            with self.connection.cursor() as cursor:
                cursor.execute("""
                    SELECT name, salary_from, salary_to, url 
                    FROM vacancies 
                    WHERE name ILIKE %s
                """, (f'%{keyword}%',))
                return cursor.fetchall()

    def close(self) -> None:
        """Закрытие соединения с базой данных."""
        self.cursor.close()
        self.connection.close()