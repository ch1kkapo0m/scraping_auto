# Scraping Auto Project

Цей проект автоматично парсить оголошення з auto.ria.com, зберігає дані у PostgreSQL та запускає парсер і дамп БД за розкладом через APScheduler.

---

## Як швидко запустити проект

### 1. Клонувати репозиторій
```sh
git clone https://github.com/ch1kkapo0m/scraping_auto.git
cd scraping_auto
```

### 2. Створити файл .env
- Скопіюйте файл `.env.example` у `.env`:
```sh
cp .env.example .env
```
- Відредагуйте `.env` за потреби (час запуску, дані БД, стартова сторінка).

### 3. Встановити Docker та Docker Compose
- [Docker Desktop для Windows/Mac](https://www.docker.com/products/docker-desktop/)
- Для Linux: встановіть docker та docker-compose через пакетний менеджер

## Запустіть Docker - без запуску Docker проект не запуститься!

### 4. Запустити проект через Docker Compose
```sh
docker compose up --build -d
```
- Піднімається база PostgreSQL та контейнер з парсером і scheduler.

### 5. Створити таблиці у БД (один раз)
```sh
docker compose exec app python app/create_tables.py
```

### 6. Перевірити БД через pgAdmin (опціонально)
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

### 8. Автоматичний запуск парсера і дампу
- Парсер і дамп БД автоматично запускаються у час, вказаний у `.env` (SCRAPE_TIME, DUMP_TIME).
- Scheduler запускається автоматично як основний процес контейнера app (див. Dockerfile).
- Якщо scheduler не стартує автоматично, запустіть вручну:
```sh
docker compose exec app python app/scheduler.py
```
- Дампи БД зберігаються у папці `dumps/` (автоматично створюється, не потрапляє у git).

---

## Структура проекту
- `app/scraper/parser.py` — основний парсер
- `app/scheduler.py` — запуск парсера і дампу за розкладом
- `app/create_tables.py` — створення таблиць у БД
- `app/models.py` — структура даних
- `docker-compose.yml` — налаштування сервісів
- `requirements.txt` — залежності Python
- `dumps/` — автоматичні дампи БД (ігнорується git)
- `.env.example` — приклад налаштувань (обов'язково створіть свій `.env`!)

---

## Важливі моменти
- Парсер не парсить оголошення, які вже є у БД.
- Для отримання телефону використовується car_id (ID авто).
- VIN-код та username парсяться з різних варіантів розмітки.
- Час запуску парсера і дампу змінюється у `.env` (SCRAPE_TIME, DUMP_TIME).
- Для дампу потрібен pg_dump (вже встановлюється у контейнері автоматично).
- dumps/ створюється автоматично, дампи не потрапляють у git.

---

## Контакти
З усіх питань — звертайтесь до автора репозиторію (t.me/mbvee).
