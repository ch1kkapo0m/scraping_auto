from apscheduler.schedulers.blocking import BlockingScheduler
from datetime import datetime

sched = BlockingScheduler()

@sched.scheduled_job('interval', minutes=1)
def test_job():
    print(f"[{datetime.now()}] Скрипт працює 🚗")

if __name__ == "__main__":
    sched.start()
