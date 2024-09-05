from hltv.helpers import *
from pprint import pprint
from tempfile import NamedTemporaryFile

import pandas as pd
import sqlite3

try:
    import colorlog as logging
    logger = logging.getLogger(__name__)
except ImportError:
    import logging
    logger = logging.getLogger(__name__)



if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    db_name = '/tmp/tmpqm_6840j.sqlite' #'/tmp/tmpqmieabas.sqlite' # NamedTemporaryFile(suffix='.sqlite', delete=False).name
    logger.critical(f'{db_name=}')

    update_user_teams_current_season(db_name, 1223636)
    update_user_teams_current_season(db_name, 1355207)

    