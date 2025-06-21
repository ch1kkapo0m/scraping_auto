import asyncio
from app.db import create_pool  
from app.parser import parse_car_card 

async def main():
    pool = await create_pool()

    car_urls = [
        'https://auto.ria.com/uk/car_1',
        'https://auto.ria.com/uk/car_2',
    ]

    async with pool.acquire() as conn:
        for url in car_urls:
            car_data = await parse_car_card(url)
            
            await conn.execute("""
                INSERT INTO cars(url, title, price_usd, odometer, username, phone_number, image_url, images_count, car_number, car_vin, datetime_found)
                VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11)
                ON CONFLICT (url) DO UPDATE SET
                    title = EXCLUDED.title,
                    price_usd = EXCLUDED.price_usd,
                    odometer = EXCLUDED.odometer,
                    username = EXCLUDED.username,
                    phone_number = EXCLUDED.phone_number,
                    image_url = EXCLUDED.image_url,
                    images_count = EXCLUDED.images_count,
                    car_number = EXCLUDED.car_number,
                    car_vin = EXCLUDED.car_vin,
                    datetime_found = EXCLUDED.datetime_found

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

    await pool.close()

if __name__ == "__main__":
    asyncio.run(main())
