from apscheduler.schedulers.blocking import BlockingScheduler
from datetime import datetime
import subprocess
from pytz import timezone
import os

sched = BlockingScheduler(timezone=timezone('Europe/Kyiv'))

PARSER_HOUR = 12
PARSER_MINUTE = 00
DUMP_HOUR = 12
DUMP_MINUTE = 00

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
        "-h", "db",
        "-U", "postgres",
        "-d", "autoria",
        "-f", dump_file
    ], env={**os.environ, "PGPASSWORD": "postgres"})
    if result.returncode == 0:
        print(f"Дамп збережено: {dump_file}")
    else:
        print(f"Помилка дампу! Код: {result.returncode}")

if __name__ == "__main__":
    sched.start()
