OLD_DB = 'data/points.sqlite'

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
    logging.basicConfig(level=logging.INFO)
    db_name = '/tmp/tmpqm_6840j.sqlite'
    logger.critical(f'{db_name=}')

    with sqlite3.connect(OLD_DB) as con:
        df_events = pd.read_sql_query('''select * from events''', con)
    with sqlite3.connect(db_name) as con:
        df_season_events = pd.read_sql_query('''select * from season_events''', con)
        df_season_events.set_index('fantasyId', inplace=True)

    df_events.rename(columns={'id': 'fantasyId', 'season': 'seasonName'}, inplace=True)
    df_events.set_index('fantasyId', inplace=True)

    df_filter = df_events.index.drop(df_season_events.index, errors='ignore')
    df_season_events = pd.concat([df_events.loc[df_filter], df_season_events])

    df_update_in_sqlite_table(db_name, df_season_events, 'season_events')

    with sqlite3.connect(OLD_DB) as con:
        df_points = pd.read_sql_query('''select * from points''', con)
    with sqlite3.connect(db_name) as con:
        df_fantasy_teams = pd.read_sql_query('''select * from fantasy_teams''', con)
        df_fantasy_teams.set_index(['fantasyId', 'userId'], inplace=True)

    df_points.rename(columns={
        'event_id': 'fantasyId',
        'team_id': 'teamId',
        'player': 'userId',
        'score': 'teamTeamPoints',
        'percent': 'teamPlacementPercent',
        'season_points': 'teamSeasonPoints',
    }, inplace=True)
    df_points.drop(columns='league_id', inplace=True)
    df_points.replace('nils', 1355207, inplace=True)
    df_points.replace('eric', 1223636, inplace=True)
    df_points.set_index(['fantasyId', 'userId'], inplace=True)


    df_filter = df_points.index.drop(df_fantasy_teams.index, errors='ignore')
    dft = pd.concat([df_points.loc[df_filter], df_fantasy_teams], verify_integrity=True)

    df_update_in_sqlite_table(db_name, dft, 'fantasy_teams')

    
