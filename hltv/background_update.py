from apscheduler.schedulers.background import BackgroundScheduler
from .helpers import *
import atexit
import datetime

REFRESH_INTERVAL = 10 * 60

def update_overview():
    print('[DEBUG] updating overview on timer')
    # Do live first to make sure to grab the last points update before it goes to finished
    refresh_live_events()
    refresh_overview()

def setup_scheduler():
    scheduler = BackgroundScheduler()
    print(f'[DEBUG] adding refresh on a {REFRESH_INTERVAL} seconds scheduler')
    scheduler.add_job(func=update_overview)
    scheduler.add_job(func=update_overview, trigger="interval", seconds=REFRESH_INTERVAL)
    atexit.register(lambda: scheduler.shutdown())
    scheduler.start()
    print(f'scheduler started?')

if __name__ == '__main__':
    setup_scheduler()