import os
from dotenv import load_dotenv
from api_handler import APIHandler
from db_manager import DBManager


def load_db_config():
    """
    Загрузка конфигурации базы данных из переменных окружения.

    Returns:
        dict: Словарь с параметрами подключения к базе данных.
    """
    load_dotenv()
    return {
        'dbname': os.getenv('DB_NAME'),
        'user': os.getenv('DB_USER'),
        'password': os.getenv('DB_PASSWORD'),
        'host': os.getenv('DB_HOST'),
        'port': os.getenv('DB_PORT')
    }


def user_interaction(db_manager: DBManager) -> None:
    """
    Функция взаимодействия с пользователем.

    Args:
        db_manager (DBManager): Экземпляр класса управления базой данных.
    """
    while True:
        print("\nВыберите действие:")
        print("1. Получить список компаний и количество вакансий")
        print("2. Получить список всех вакансий")
        print("3. Получить среднюю зарплату")
        print("4. Получить вакансии с зарплатой выше средней")
        print("5. Найти вакансии по ключевому слову")
        print("0. Выйти")

        choice = input("Введите номер действия: ")

        try:
            if choice == '1':
                print("\nСписок компаний и количество вакансий:")
                for company, count in db_manager.get_companies_and_vacancies_count():
                    print(f"{company}: {count} вакансий")

            elif choice == '2':
                print("\nСписок всех вакансий:")
                for company, name, salary_from, salary_to, url in db_manager.get_all_vacancies():
                    print(f"Компания: {company}, Вакансия: {name}, Зарплата: {salary_from}-{salary_to}, Ссылка: {url}")

            elif choice == '3':
                avg_salary = db_manager.get_avg_salary()
                print(f"\nСредняя зарплата: {avg_salary if avg_salary else 'Нет данных'}")

            elif choice == '4':
                print("\nВакансии с зарплатой выше средней:")
                for name, salary_from, salary_to, url in db_manager.get_vacancies_with_higher_salary():
                    print(f"Вакансия: {name}, Зарплата: {salary_from}-{salary_to}, Ссылка: {url}")

            elif choice == '5':
                keyword = input("Введите ключевое слово: ")
                print(f"\nВакансии по ключевому слову '{keyword}':")
                for name, salary_from, salary_to, url in db_manager.get_vacancies_with_keyword(keyword):
                    print(f"Вакансия: {name}, Зарплата: {salary_from}-{salary_to}, Ссылка: {url}")

            elif choice == '0':
                break
            else:
                print("Неверный выбор. Попробуйте снова.")
        except Exception as e:
            print(f"Произошла ошибка: {e}")


def main():
    """
    Основная функция для загрузки данных и взаимодействия с пользователем.
    """
    db_manager = None
    try:
        # Загрузка параметров базы данных
        db_params = load_db_config()

        # Создание экземпляров классов
        api_handler = APIHandler()
        db_manager = DBManager(db_params)

        # Получение и загрузка данных о компаниях
        companies = api_handler.get_companies()
        print(f"Получено компаний: {len(companies)}")

        for company in companies:
            print(f"Обработка компании: {company}")
            
            # Проверка наличия обязательных ключей
            if 'id' not in company or 'name' not in company:
                print(f"Пропуск некорректной компании: {company}")
                continue

            db_manager.insert_company(company)

            vacancies = api_handler.get_vacancies(company['id'])
            print(f"Получено вакансий для {company['name']}: {len(vacancies)}")

            for vacancy in vacancies:
                # Проверка наличия обязательных ключей в вакансии
                if not all(key in vacancy for key in ['id', 'name', 'alternate_url']):
                    print(f"Пропуск некорректной вакансии: {vacancy}")
                    continue
                
                db_manager.insert_vacancy(vacancy, company['id'])

        # Запуск взаимодействия с пользователем
        user_interaction(db_manager)

    except Exception as e:
        print(f"Произошла ошибка в main: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # Безопасное закрытие соединения с базой данных
        if db_manager is not None:
            try:
                db_manager.close()
            except Exception as close_error:
                print(f"Ошибка при закрытии соединения: {close_error}")


if __name__ == "__main__":
    main()