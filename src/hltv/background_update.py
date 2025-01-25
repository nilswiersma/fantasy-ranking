from apscheduler.schedulers.background import BackgroundScheduler
from hltv.helpers import *
import atexit
import datetime

try:
    import colorlog as logging
    logger = logging.getLogger(__name__)
except ImportError:
    import logging
    logger = logging.getLogger(__name__)

REFRESH_INTERVAL = 10 * 60

def update_overview():
    logger.info('updating overview on timer')
    # # Do live first to make sure to grab the last points update before it goes to finished
    # refresh_live_events()
    # refresh_overview()

    data = get_current_fantasy_overview()
    df = df_from_htlv_current_fantasy_events(data)
    df_update_in_sqlite_table(DB, df, 'season_events')

    update_user_teams_current_season(DB, 1223636)
    update_user_teams_current_season(DB, 1355207)



def setup_scheduler():
    scheduler = BackgroundScheduler()
    logger.info(f'adding refresh on a {REFRESH_INTERVAL} seconds scheduler')
    scheduler.add_job(func=update_overview)
    scheduler.add_job(func=update_overview, trigger="interval", seconds=REFRESH_INTERVAL)
    atexit.register(lambda: scheduler.shutdown())
    scheduler.start()
    logger.info(f'scheduler started?')

if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    setup_scheduler()
    logger.critical('staying alive until enter')
    input()