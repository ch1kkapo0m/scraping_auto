from apscheduler.schedulers.blocking import BlockingScheduler
from datetime import datetime
import subprocess
from pytz import timezone
import os
from dotenv import load_dotenv

load_dotenv()

sched = BlockingScheduler(timezone=timezone('Europe/Kyiv'))

SCRAPE_TIME = os.getenv('SCRAPE_TIME', '12:00')
DUMP_TIME = os.getenv('DUMP_TIME', '12:00')

PARSER_HOUR, PARSER_MINUTE = map(int, SCRAPE_TIME.split(':'))
DUMP_HOUR, DUMP_MINUTE = map(int, DUMP_TIME.split(':'))

@sched.scheduled_job('cron', hour=PARSER_HOUR, minute=PARSER_MINUTE)
def run_parser():
    print(f"[{datetime.now()}] Запуск парсера")
    subprocess.run(["python", "app/scraper/parser.py"])

@sched.scheduled_job('cron', hour=DUMP_HOUR, minute=DUMP_MINUTE)
def dump_db():
    print(f"[{datetime.now()}] Дамп бази даних...")
    dumps_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'dumps')
    os.makedirs(dumps_dir, exist_ok=True)
    dump_file = os.path.join(dumps_dir, f"dump_{datetime.now().strftime('%Y%m%d_%H%M%S')}.sql")
    result = subprocess.run([
        "pg_dump",
        "-h", os.getenv('DB_HOST', 'db'),
        "-U", os.getenv('DB_USER', 'postgres'),
        "-d", os.getenv('DB_NAME', 'autoria'),
        "-f", dump_file
    ], env={**os.environ, "PGPASSWORD": os.getenv('DB_PASSWORD', 'postgres')})
    if result.returncode == 0:
        print(f"Дамп збережено: {dump_file}")
    else:
        print(f"Помилка дампу! Код: {result.returncode}")

if __name__ == "__main__":
    sched.start()
