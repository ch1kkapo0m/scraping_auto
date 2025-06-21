# Scraping Auto Project

Цей проект автоматично парсить оголошення з auto.ria.com, зберігає дані у PostgreSQL та запускає парсер і дамп БД за розкладом через APScheduler.

## Як розгорнути проект на іншому комп'ютері

### 1. Клонування репозиторію
```sh
git clone <your-repo-url>
cd scraping_auto
```

### 2. Переконайтесь, що встановлено Docker та Docker Compose
- [Docker Desktop для Windows/Mac](https://www.docker.com/products/docker-desktop/)
- Для Linux: встановіть docker та docker-compose через пакетний менеджер

### 3. Налаштуйте .env (опціонально)
Створіть файл `.env` (або переконайтесь, що він є) з такими змінними:
```
POSTGRES_DB=autoria
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
```

### 4. Запуск через Docker Compose
```sh
docker compose up --build -d
```
- Піднімається база PostgreSQL та контейнер з парсером і scheduler.

### 5. Ініціалізація таблиць (один раз)
```sh
docker compose exec app python app/create_tables.py
```

### 6. Перевірка підключення до БД через pgAdmin (опціонально)
- Host: localhost
- Port: 5432
- User: postgres
- Password: postgres
- Database: autoria

### 7. Ручний запуск парсера (опціонально)
```sh
docker compose exec app python app/scraper/parser.py
```
- Парсер збере всі нові оголошення та збереже їх у БД.

### 8. Автоматичний запуск парсера і дампу за розкладом
- Парсер і дамп БД автоматично запускаються у час, вказаний у `app/scheduler.py` (за замовчуванням 12:00 або як ви вкажете).
- Scheduler запускається автоматично як основний процес контейнера app (див. Dockerfile).
- Якщо scheduler не стартує автоматично, запустіть вручну:
```sh
docker compose exec app python app/scheduler.py
```
- Дампи БД зберігаються у папці `dumps/` (автоматично створюється, не потрапляє у git).

## Структура проекту
- `app/scraper/parser.py` — основний парсер
- `app/scheduler.py` — запуск парсера і дампу за розкладом
- `app/create_tables.py` — створення таблиць у БД
- `app/models.py` — структура даних
- `docker-compose.yml` — налаштування сервісів
- `requirements.txt` — залежності Python
- `dumps/` — автоматичні дампи БД (ігнорується git)

## Важливі моменти
- Парсер не парсить оголошення, які вже є у БД.
- Для отримання телефону використовується car_id (ID авто).
- VIN-код та username парсяться з різних варіантів розмітки.
- Якщо потрібно змінити час запуску — редагуйте `app/scheduler.py` (змінні PARSER_HOUR, PARSER_MINUTE, DUMP_HOUR, DUMP_MINUTE).
- Для дампу потрібен pg_dump (вже встановлюється у контейнері автоматично).

## Контакти
З усіх питань — звертайтесь до автора репозиторію (t.me/mbvee).
