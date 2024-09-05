DB = 'data/points.sqlite'

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

data = get_data()