import asyncio
import aiohttp
import asyncpg
from bs4 import BeautifulSoup
from datetime import datetime

print("Старт парсера", flush=True)

phone_semaphore = asyncio.Semaphore(1)  

async def fetch_phone_number(session, car_id, data_hash, data_expires, retries=3):
    if not car_id or not data_hash or not data_expires:
        print("Недостатньо даних для отримання телефону.")
        return None

    phone_api_url = f'https://auto.ria.com/users/phones/{car_id}?hash={data_hash}&expires={data_expires}'
    print(f"[DEBUG] Запит телефону: {phone_api_url}")
    headers = {
        "User-Agent": "Mozilla/5.0",
        "Accept": "application/json, text/plain, */*",
    }

    async with phone_semaphore:  
        for attempt in range(retries):
            try:
                await asyncio.sleep(1) 
                async with session.get(phone_api_url, headers=headers, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        phones = data.get('phones', [])
                        if phones:
                            return phones[0].get('phoneFormatted')
                    else:
                        print(f"Не вдалось отримати телефон. Статус: {resp.status}")
            except aiohttp.ClientConnectionError as e:
                print(f"Помилка підключення при отриманні телефону: {e}, спроба {attempt+1}")
            except asyncio.TimeoutError:
                print(f"Таймаут при отриманні телефону, спроба {attempt+1}")
            except Exception as e:
                print(f"Інша помилка при отриманні телефону: {e}")
            await asyncio.sleep(1)  

    return None


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

    def parse_odometer(soup):
        div = soup.select_one('div.base-information.bold')
        if not div:
            return None

        number_span = div.select_one('span.size18')
        if not number_span:
            return None

        try:
            number = int(number_span.text.strip())
        except ValueError:
            return None

        text_after = div.get_text(strip=True)
        if 'тис.' in text_after:
            number *= 1000

        return number

    def parse_username(soup):
        a_tag = soup.select_one('h4.seller_info_name a')
        if a_tag:
            return a_tag.text.strip()
        a_tag2 = soup.select_one('div.seller_info_name a')
        if a_tag2:
            return a_tag2.text.strip()
        div_tag = soup.select_one('div.seller_info_name')
        if div_tag:
            return div_tag.text.strip()
        return None

    def parse_first_image_url(soup):
        img_tag = soup.select_one('picture img.outline.m-auto')
        if img_tag and img_tag.has_attr('src'):
            return img_tag['src']
        return None

    def get_images_count(soup):
        count_span = soup.select_one('span.count span.mhide')
        if count_span:
            text = count_span.text.strip() 
            digits = ''.join(filter(str.isdigit, text))
            if digits:
                return int(digits)
        return None

    def get_car_number(soup):
        span = soup.select_one('span.state-num.ua')
        if span:
            texts = [t for t in span.contents if isinstance(t, str)]
            if texts:
                car_number = texts[0].strip()
                return car_number

        return None

    def get_car_vin(soup):
        vin_span = soup.select_one('span.label-vin')
        if vin_span:
            vin_text = ''.join(vin_span.find_all(string=True, recursive=False)).strip()
            if vin_text:
                return vin_text
        vin_code_span = soup.select_one('span.vin-code')
        if vin_code_span:
            vin_text = vin_code_span.text.strip()
            if vin_text:
                return vin_text
        return None

    def get_car_id(soup):
        for li in soup.find_all('li', class_='item grey'):
            if li.text.strip().startswith('ID авто'):
                span = li.find('span', class_='bold')
                if span:
                    print(f"ID авто: {span.text.strip()}")
                    return span.text.strip()
        return None

    car_number = get_car_number(soup)
    car_id = get_car_id(soup)

    script_tag = soup.find('script', attrs={'data-hash': True, 'data-expires': True})
    if script_tag:
        data_hash = script_tag.get('data-hash')
        data_expires = script_tag.get('data-expires')
    else:
        script_tag = soup.find('script', lambda attr: attr and 'data-hash' in attr and 'data-expires' in attr)
        if script_tag:
            data_hash = script_tag.get('data-hash')
            data_expires = script_tag.get('data-expires')
        else:
            data_hash = None
            data_expires = None
    
    phone_number = await fetch_phone_number(session, car_id, data_hash, data_expires)
    phone_number = int('38' + phone_number.replace('(', '').replace(')', '').replace('-', '').replace(' ', '')) if phone_number else None

    title = safe_text('h1.head')
    price_usd = safe_int_from_text('strong')
    odometer = parse_odometer(soup)
    username = parse_username(soup)
    image_url = parse_first_image_url(soup)
    images_count = get_images_count(soup)
    car_vin = get_car_vin(soup)
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

async def extract_car_links(session, page):
    url = f"https://auto.ria.com/uk/search/?lang_id=4&page={page}&countpage=100&indexName=auto&custom=1&abroad=2"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36",
        "Accept": "text/html",
    }

    async with session.get(url, headers=headers) as response:
        html = await response.text()
        soup = BeautifulSoup(html, 'html.parser')
        all_links = soup.find_all('a', class_='address')

        car_links = []
        for a in all_links:
            href = a.get('href', '')
            if href.startswith('https://auto.ria.com/uk/auto_') and href.endswith('.html'):
                car_links.append(href)

        has_more = len(car_links) == 100
        return car_links, has_more

async def get_existing_urls(pool, urls):
    if not urls:
        return set()
    async with pool.acquire() as conn:
        rows = await conn.fetch("SELECT url FROM cars WHERE url = ANY($1)", urls)
        return set(row['url'] for row in rows)

async def save_to_db(pool, car_data):
    phone_number = car_data.get('phone_number')
    if phone_number is not None:
        try:
            if isinstance(phone_number, str):
                phone_number = int(phone_number)
        except Exception:
            phone_number = None  

    async with pool.acquire() as conn:
        try:
            await conn.execute("""
                INSERT INTO cars(
                    url, title, price_usd, odometer, username, phone_number, 
                    image_url, images_count, car_number, car_vin, datetime_found
                ) VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11)
                ON CONFLICT (url) DO NOTHING
            """,
            car_data.get('url'),
            car_data.get('title'),
            car_data.get('price_usd'),
            car_data.get('odometer'),
            car_data.get('username'),
            phone_number,
            car_data.get('image_url'),
            car_data.get('images_count'),
            car_data.get('car_number'),
            car_data.get('car_vin'),
            car_data.get('datetime_found')
            )
        except Exception as e:
            print(f"Помилка при збереженні в БД: {e}")


async def main():
    pool = await asyncpg.create_pool(
        user='postgres',
        password='postgres',
        database='autoria',
        host='db',
        port=5432
    )

    import ssl
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE

    async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=ssl_context)) as session:
        page = 0
        semaphore = asyncio.Semaphore(10)

        while True:
            print(f"Обробляємо сторінку: {page}")
            car_links, has_more = await extract_car_links(session, page)

            if not car_links:
                print(f"Сторінка {page}: більше немає авто, зупинка.")
                break

            existing_urls = await get_existing_urls(pool, car_links)
            new_links = [link for link in car_links if link not in existing_urls]

            print(f"Сторінка {page}: знайдено {len(car_links)} авто, нових до парсингу: {len(new_links)}")

            if not new_links:
                print(f"На сторінці {page} всі авто вже є в БД, переходимо далі.")

            async def parse_and_save(link):
                async with semaphore:
                    try:
                        data = await parse_car_card(session, link)
                        await save_to_db(pool, data)
                        print(f"Збережено: {link}")
                    except Exception as e:
                        print(f"Помилка при обробці {link}: {e}")

            max_workers = 30
            semaphore = asyncio.Semaphore(max_workers)
            tasks = [asyncio.create_task(parse_and_save(link)) for link in new_links]
            await asyncio.gather(*tasks)

            if not has_more:
                print("Усі сторінки оброблено.")
                break

            page += 1

    await pool.close()



if __name__ == '__main__':
        asyncio.run(main())

