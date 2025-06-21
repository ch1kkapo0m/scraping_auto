import asyncio
import aiohttp
import asyncpg
from bs4 import BeautifulSoup
from datetime import datetime


async def parse_car_card(session, url: str) -> dict:
    async with session.get(url) as response:
        html = await response.text()

    soup = BeautifulSoup(html, 'html.parser')

    def safe_text(selector):
        el = soup.select_one(selector)
        return el.text.strip() if el else None

    def safe_int_from_text(selector, factor=1):
        txt = safe_text(selector)
        if not txt:
            return None
        digits = ''.join(filter(str.isdigit, txt))
        if not digits:
            return None
        return int(digits) * factor

    title = safe_text('h1.headline') or safe_text('.ticket-title a.address span.blue.bold')
    price_usd = safe_int_from_text('.price-ticket .bold.size22.green[data-currency="USD"]')
    odometer = safe_int_from_text('.definition-data .js-race', factor=1000)  # "350 тис. км" -> 350000
    username = safe_text('.seller-info .username') or safe_text('.base_information .label-vin span')
    phone_raw = safe_text('.phone-number')
    phone_number = int(''.join(filter(str.isdigit, phone_raw))) if phone_raw else None
    image_url = soup.select_one('.gallery img')['src'] if soup.select_one('.gallery img') else None
    images_count = len(soup.select('.gallery img'))
    car_number = safe_text('.car-number')
    car_vin = safe_text('.label-vin span')  # наприклад
    datetime_found = datetime.now()

    return {
        'url': url,
        'title': title,
        'price_usd': price_usd,
        'odometer': odometer,
        'username': username,
        'phone_number': phone_number,
        'image_url': image_url,
        'images_count': images_count,
        'car_number': car_number,
        'car_vin': car_vin,
        'datetime_found': datetime_found,
    }


async def extract_car_links(session, url):
    async with session.get(url) as response:
        html = await response.text()

    soup = BeautifulSoup(html, 'html.parser')
    # Витягуємо всі <a class="address" href="...">
    all_links = soup.find_all('a', class_='address')

    car_links = []
    for a in all_links:
        href = a.get('href', '')
        if href.startswith('https://auto.ria.com/uk/auto_') and href.endswith('.html'):
            car_links.append(href)

    # Знайдемо посилання на наступну сторінку
    next_page_tag = soup.select_one('a.next:not(.disabled)')  # Потрібно уточнити селектор для кнопки "Наступна"
    next_page = next_page_tag['href'] if next_page_tag else None

    return car_links, next_page


async def save_to_db(pool, car_data):
    async with pool.acquire() as conn:
        await conn.execute("""
            INSERT INTO cars(
                url, title, price_usd, odometer, username, phone_number, 
                image_url, images_count, car_number, car_vin, datetime_found
            ) VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11)
            ON CONFLICT (url) DO NOTHING
        """,
        car_data['url'],
        car_data['title'],
        car_data['price_usd'],
        car_data['odometer'],
        car_data['username'],
        car_data['phone_number'],
        car_data['image_url'],
        car_data['images_count'],
        car_data['car_number'],
        car_data['car_vin'],
        car_data['datetime_found']
        )


async def main(start_url):
    pool = await asyncpg.create_pool(
        user='postgres',
        password='your_password',
        database='your_dbname',
        host='localhost',
        port=5432
    )

    async with aiohttp.ClientSession() as session:
        url = start_url

        semaphore = asyncio.Semaphore(10)  # ліміт одночасних запитів

        while url:
            print(f"Обробляємо сторінку списку: {url}")
            car_links, url = await extract_car_links(session, url)
            print(f"Знайдено {len(car_links)} авто")

            async def parse_and_save(link):
                async with semaphore:
                    try:
                        data = await parse_car_card(session, link)
                        await save_to_db(pool, data)
                        print(f"Збережено: {link}")
                    except Exception as e:
                        print(f"Помилка при обробці {link}: {e}")

            tasks = [asyncio.create_task(parse_and_save(link)) for link in car_links]
            await asyncio.gather(*tasks)

    await pool.close()


if __name__ == '__main__':
    asyncio.run(main('https://auto.ria.com/uk/used'))
