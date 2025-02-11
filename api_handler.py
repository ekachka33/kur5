import requests
from typing import List, Dict, Optional


class APIHandler:
    """
    Класс для работы с API hh.ru и получения данных о компаниях и вакансиях.
    """
    BASE_URL = "https://api.hh.ru"

    def __init__(self):
        """
        Инициализация списка компаний для поиска.
        """
        self.companies = [
            "Яндекс", "Сбербанк", "Тинькофф", "Mail.ru", "Газпром",
            "Роснефть", "Лукойл", "ВТБ", "Альфа-Банк", "Мегафон"
        ]

    def get_companies(self) -> List[Dict[str, str]]:
        """
        Получение информации о компаниях через API hh.ru.

        Returns:
            List[Dict[str, str]]: Список словарей с информацией о компаниях.
        """
        companies_data = []
        for company_name in self.companies:
            try:
                response = requests.get(f"{self.BASE_URL}/employers", params={
                    "text": company_name,
                    "only_with_vacancies": True,
                    "per_page": 1
                })
                response.raise_for_status()

                # Добавим отладочную печать
                print(f"Response for {company_name}: {response.json()}")

                items = response.json().get('items', [])
                if items:
                    companies_data.append(items[0])
                else:
                    print(f"Не найдены компании по запросу: {company_name}")
            except requests.RequestException as e:
                print(f"Ошибка при получении данных для {company_name}: {e}")
            except Exception as e:
                print(f"Неожиданная ошибка для {company_name}: {e}")

        # Добавим проверку на пустой список
        if not companies_data:
            raise ValueError("Не удалось получить данные ни об одной компании")

        return companies_data

    def get_vacancies(self, company_id: str) -> List[Dict[str, Optional[str]]]:
        """
        Получение вакансий для конкретной компании.

        Args:
            company_id (str): Идентификатор компании.

        Returns:
            List[Dict[str, Optional[str]]]: Список вакансий компании.
        """
        try:
            response = requests.get(f"{self.BASE_URL}/vacancies", params={
                "employer_id": company_id,
                "per_page": 100
            })
            response.raise_for_status()

            # Добавим отладочную печать
            print(f"Vacancies response for {company_id}: {response.json()}")

            vacancies = response.json().get('items', [])

            # Добавим проверку на пустой список вакансий
            if not vacancies:
                print(f"Для компании {company_id} не найдены вакансии")

            return vacancies
        except requests.RequestException as e:
            print(f"Ошибка при получении вакансий для компании {company_id}: {e}")
            return []