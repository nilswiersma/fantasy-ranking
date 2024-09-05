from tempfile import NamedTemporaryFile
from hltv.helpers import *
from pprint import pprint
import sqlite3
import pandas as pd

try:
    import colorlog as logging
    logger = logging.getLogger(__name__)
except ImportError:
    import logging
    logger = logging.getLogger(__name__)

if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    data = get_current_fantasy_overview()
    df = df_from_htlv_current_fantasy_events(data)

    db_name = NamedTemporaryFile(suffix='.sqlite', delete=False).name
    logger.critical(f'{db_name=}')

    create_season_events_table(db_name, df)
    df_update_in_sqlite_table(db_name, df, 'season_events')
