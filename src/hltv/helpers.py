import pandas as pd
import requests
import json
import sqlite3
import re
import random
import time
import os

from flask import escape

try:
    import colorlog as logging
    logger = logging.getLogger(__name__)
except ImportError:
    import logging
    logger = logging.getLogger(__name__)

# nils: 1355207
# eric: 1223636


# https://www.hltv.org/fantasy/474/user/1710937/overview/gameredirect

HLTV_FANTASY_OVERVIEW = 'https://www.hltv.org/fantasy/json'
HLTV_FANTASY_EVENT_OVERVIEW = 'https://www.hltv.org/fantasy/{}/overview/json'
HLTV_FANTASY_SINGLE_TEAM = 'https://www.hltv.org/fantasy/{}/league/{}/overview/{}/json'
HLTV_FANTASY_SINGLE_TEAM_RE = r'https://www.hltv.org/fantasy/(\d+)/league/(\d+)/team/(\d+)/*'
HLTV_FANTASY_LEAGUE_STATS = 'https://www.hltv.org/fantasy/{}/leagues/{}/join/json'
HLTV_FANTASY_USER_SEASON_STATS = 'https://www.hltv.org/fantasy/user/{}/overview/json'
# https://www.hltv.org/fantasy/462/league/173894/overview/4150537/draft/462/triggerrates/json
HLTV_FANTASY_ROLE_BOOSTER_STATS = 'https://www.hltv.org/fantasy/{}/league/{}/overview/{}/draft/{}/triggerrates/json'
HLTV_FANTASY_LEAGUE_TEAM_REDIRECT = 'https://www.hltv.org/fantasy/{}/user/{}/overview/redirect/json'

STATS_ID_RE = r'<a href=\"/events/(\d+)/([a-zA-Z0-9-]*)\".*?</a>'

DB = './data/pointsv2.sqlite'
DB_TEMPLATE = None #'./flaskr/templates/points.sqlite'

# HEADER = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.85 Safari/537.36 Edg/90.0.818.46'}

HEADER = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.85 Safari/537.36 Edg/90.0.818.46',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate',
        'DNT': '1',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'same-origin',
    }

def random_sleep():
    x = random.randint(1,1500)/1000
    logger.info(f'Random sleep {x}s')
    time.sleep(x)

def safe_get(url, *args, **kwargs):
    random_sleep()
    resp = requests.get(url, headers=HEADER)
    assert resp.status_code == 200, f'{resp.status_code=}, {resp.url=}'
    return resp

def get_fantasy_teams_current_season(user_id):
    logger.debug(f'{HLTV_FANTASY_USER_SEASON_STATS.format(user_id)=}')
    random_sleep()
    resp = requests.get(HLTV_FANTASY_USER_SEASON_STATS.format(user_id), headers=HEADER)
    if resp.status_code == 200:
        return resp.json()
    else:
        raise Exception(f'{resp.status_code=} {resp.text=}')

def get_league_stats(event_id, league_id):
    # https://www.hltv.org/fantasy/475/user/1223636/overview/redirect/json
    resp = safe_get(HLTV_FANTASY_EVENT_OVERVIEW.format(event_id))
    league_id = resp.json()['hltvLeagueId']['id']
    resp = safe_get(HLTV_FANTASY_LEAGUE_STATS.format(event_id, league_id))
    return resp.json()

def get_hltv_league_stats(event_id):
    data = get_stats_event_id(event_id)
    publicLeagueId = data['topMenuData']['publicLeagueId']['id']
    data = get_league_stats(event_id, publicLeagueId)
    return publicLeagueId, data

def get_stats_event_id(event_id):
    logger.debug(f'{HLTV_FANTASY_EVENT_OVERVIEW.format(event_id)=}')
    random_sleep()
    print(HLTV_FANTASY_EVENT_OVERVIEW.format(event_id))
    resp = requests.get(HLTV_FANTASY_EVENT_OVERVIEW.format(event_id), headers=HEADER)
    if resp.status_code == 200:
        return resp.json()
    else:
        raise Exception(f'{resp.status_code=} {resp.text=}')

def get_current_fantasy_overview():
    logger.debug(f'{HLTV_FANTASY_OVERVIEW=}')
    random_sleep()
    resp = requests.get(HLTV_FANTASY_OVERVIEW, headers=HEADER)
    if resp.status_code == 200:
        return resp.json()
    else:
        raise Exception(f'{resp.status_code=} {resp.text=}')

def get_single_team(fantasy_id, user_id):
    resp = safe_get(HLTV_FANTASY_LEAGUE_TEAM_REDIRECT.format(escape(fantasy_id), escape(user_id)))
    team_url = resp.json()['url']
    logger.info(f'{team_url=}')
    logger.info(f'https://www.hltv.org{escape(team_url.replace("team", "overview"))}/json')
    if team_url == f'/fantasy/{fantasy_id}/overview':
        # no team listed yet
        return {}
    else:
        resp = safe_get(f'https://www.hltv.org{escape(team_url.replace("team", "overview"))}/json')
        return resp.json()

def get_role_booster_stats(event_id, league_id, team_id):
    logger.debug(f'{HLTV_FANTASY_ROLE_BOOSTER_STATS.format(event_id, league_id, team_id, event_id)=}')
    random_sleep()
    resp = requests.get(HLTV_FANTASY_ROLE_BOOSTER_STATS.format(event_id, league_id, team_id, event_id), headers=HEADER)
    if resp.status_code == 200:
        return resp.json()
    else:
        raise Exception(f'{resp.status_code=} {resp.text=}')
    
def overview_to_db(overview):
    events = {}
    season = overview['seasonName']
    for month in overview['monthlyEvents']:
        for event in month['events']:
            id_ = event['fantasyId']['id']
            name = event['name']
            state = event['state']['type'].split('.')[-1]
            events[id_] = (name, season, state)
    
    with sqlite3.connect(DB) as con:
        cur = con.cursor()
        ids_db = [x[0] for x in cur.execute("select id from events").fetchall()]
        logger.debug(f'{ids_db=}')
        
        # Insert new rows for new events
        events_insert = []
        logger.debug(f'{[id_ for id_ in events.keys() if id_ not in ids_db]}')
        for id_ in [id_ for id_ in events.keys() if id_ not in ids_db]:
            events_insert.append((id_,) + events[id_])
        cur.executemany("""insert into events values(?, ?, ?, ?)""", events_insert)
        
        # Update rows for existing events
        events_update = []
        for id_ in [id_ for id_ in events.keys() if id_ in ids_db]:
            events_update.append(events[id_] + (id_,))
        logger.debug(f'{events_update=}')
        cur.executemany("""update events set name=?, season=?, state=? where id=?""", events_update)
        
        con.commit()
    
    return events

def team_to_db(team, event_id, player):
    score = None
    percent = None
    season_points = None
    
    if team['keyNumbers']['totalPoints']:
        score = int(team['keyNumbers']['totalPoints'])
    if team['seasonTierData']:
        if team['seasonTierData']['usersTopPercentageFormatted']:
            percent = int(team['seasonTierData']['usersTopPercentageFormatted'].replace('%', ''))
        for tieridx in range(1,12):
            tier = team['seasonTierData'][f'tier{tieridx}']
            if tier['fromPercent'] >= percent:
                break
            season_points = int(tier['seasonPoints'])
    
    with sqlite3.connect(DB) as con:
        cur = con.cursor()
        logger.debug(f'{(score, percent, season_points, event_id, player)}')
        cur.execute("""update points set score=?, percent=?, season_points=? where event_id=? and player=?""", 
                        (score, percent, season_points, event_id, player))
        con.commit()

    return (score, percent, season_points)

def get_data():
    ret = {}
    with sqlite3.connect(DB) as con:
        df_season_events = pd.read_sql_query('''select * from season_events''', con)
        df_fantasy_teams = pd.read_sql_query('''select * from fantasy_teams''', con)
        df_totals = pd.read_sql_query('''select seasonName,userId,sum(teamSeasonPoints) from fantasy_teams join season_events on fantasy_teams.fantasyId = season_events.fantasyId group by seasonName,userId''', con)

    df = df_season_events.set_index(['seasonName', 'fantasyId'])
    ret['events'] = {level: df.xs(level).to_dict('index') for level in df.index.levels[0]}
    df = df_fantasy_teams.set_index(['fantasyId', 'userId']).fillna(0)
    ret['points'] = {level: df.xs(level).to_dict('index') for level in df.index.levels[0]}
    df = df_totals.set_index(['seasonName', 'userId']).squeeze()
    ret['totals'] = {level: df.xs(level).to_dict() for level in df.index.levels[0]}
    return ret

def get_team_params(event_id, player):
    with sqlite3.connect(DB) as con:
        cur = con.cursor()
        data = cur.execute('''select fantasyId, userId, teamId from fantasy_teams where fantasyId=? and userId=?''', (event_id, player)).fetchone()
        return data

def add_team(player, link):
    m = re.match(HLTV_FANTASY_SINGLE_TEAM_RE, link)
    assert m, 'invalid link'
    event_id, league_id, team_id = m.groups()

    with sqlite3.connect(DB) as con:
        cur = con.cursor()
        x = cur.execute('''select * from events where id=?''', (event_id,)).fetchall()
        assert x, 'invalid event'

        x = cur.execute('''select * from points where event_id=? and player=?''', (event_id, player)).fetchall()
        assert x == [], 'team already inserted'

        cur.execute('''insert into points values(?, ?, ?, ?, null, null, null)''', (event_id, league_id, team_id, player))

        con.commit()
    
    # Make sure to do this once, if state != LiveEvent this gets skipped later
    team_data = get_single_team(event_id, league_id, team_id)
    team_to_db(team_data, event_id, player)

def refresh_overview():
    overview = get_current_fantasy_overview()
    # stats_id = get_stats_ids(overview)
    overview_to_db(overview)

def refresh_live_events():
    logger.debug(f'{DB=}')
    with sqlite3.connect(DB) as con:
        cur = con.cursor()
        teams = cur.execute('''select event_id, league_id, team_id, player from points where event_id in (select id from events where state=="LiveEvent")''').fetchall()
    
    logger.debug(f'{teams=}')
    for team in teams:
        team_data = get_single_team(team[0], team[1], team[2])
        team_to_db(team_data, team[0], team[3])


# def collect_numbers_from_draft_events():
#     with sqlite3.connect(DB) as con:
#         cur = con.cursor()
#         teams = cur.execute('''select event_id, league_id, team_id, player from points where event_id in (select id from events where state=="DraftEvent")''').fetchall()
#     for team in teams:
#         data = get_single_team(team[0], team[1], team[2])
#         team_data = json.loads(data.text)
#         team_to_db(team_data, team[0], team[3])
#         x = random.randint(1,3000)/1000
#         logger.debug(f'Random sleep {x}s')
#         time.sleep(x)


def create_season_events_table(db_name, df):
    with sqlite3.connect(db_name) as con:
        try:
            con.execute(pd.io.sql.get_schema(df.reset_index(), 'season_events', ['fantasyId']))
        except sqlite3.OperationalError as e:
            if str(e) == """table "fantasy_teams" already exists""":
                pass
            else:
                raise e

def create_fantasy_teams_table(db_name, df):
    with sqlite3.connect(db_name) as con:
        try:
            con.execute(pd.io.sql.get_schema(df.reset_index(), 'fantasy_teams', ['fantasyId', 'userId']))
        except sqlite3.OperationalError as e:
            if str(e) == """table "fantasy_teams" already exists""":
                pass
            else:
                raise e
           
def df_update_in_sqlite_table(db_name, df, table):
    with sqlite3.connect(db_name) as con:
        # Instead of manually doing a UPDATE, just replace all data in the table 

        # Collect existing data
        df_meta = pd.read_sql_query(f'PRAGMA table_info("{table}")', con)
        df_existing = pd.read_sql_query(f'SELECT * FROM {table}', con).set_index(list(df_meta[df_meta.pk != 0].name.values))
        df_new = df.reset_index().set_index(list(df_meta[df_meta.pk != 0].name.values))

        # Drop those that are in the new data
        df_existing_filter = df_existing.index.drop(df_new.index, errors='ignore')
        df_insert = pd.concat([df_existing.loc[df_existing_filter], df_new])

        # Reinsert data
        con.execute(f'DELETE FROM {table}')
        df_insert.reset_index().to_sql(table, con, if_exists='append', index=False)


def df_from_htlv_current_fantasy_events(data):
    seasonName = data['seasonName']
    data_flat = []
    for month in data['monthlyEvents']:
        for event in month['events']:
            row = {}
            row['seasonName'] = seasonName
            row['fantasyId'] = event['fantasyId']['id']
            row['name'] = event['name']
            row['state'] = event['state']['type'].split('.')[-1]
            data_flat.append(row)
    df = pd.DataFrame(data_flat)
    df.set_index(['fantasyId'], inplace=True)
    return df


    
def df_from_hltv_season_stats(data, userId):
    def extract_row(game):
        row = {}
        row['fantasyId'] = game['gameId']['id']
        row['teamId'] = game['teamId']['id']
        row['userId'] = userId
        row['teamPlacement'] = game['placement']
        row['teamPlacementPercent'] = int(game['topPercentage'].replace('%', ''))
        row['teamSeasonPoints'] = game['points']
        row['teamTeamPoints'] = game['pointsSummaryData']['teamPointsSummary']['points']
        row['teamTeamPercentage'] = int(game['pointsSummaryData']['teamPointsSummary']['formattedPercentage'].replace('%', ''))
        row['teamRolePoints'] = game['pointsSummaryData']['rolePointsSummary']['points']
        row['teamRolePercentage'] = int(game['pointsSummaryData']['rolePointsSummary']['formattedPercentage'].replace('%', ''))
        row['teamBoostPoints'] = game['pointsSummaryData']['boostPointsSummary']['points']
        row['teamBoostPercentage'] = int(game['pointsSummaryData']['boostPointsSummary']['formattedPercentage'].replace('%', ''))
        row['teamPlayerPoints'] = game['pointsSummaryData']['playerPointsSummary']['points']
        row['teamPlayerPercentage'] = int(game['pointsSummaryData']['playerPointsSummary']['formattedPercentage'].replace('%', ''))
        return row
    
    data_flat = []

    for game in data['frontpageData']['seasonLeaderboardData']['previousGames']:
        row = extract_row(game)
        data_flat.append(row)
    
    for game in data['frontpageData']['seasonLeaderboardData']['liveGames']:
        row = extract_row(game)
        data_flat.append(row)

    df = pd.DataFrame(data_flat)
    df.set_index(['fantasyId', 'userId'], inplace=True)
    return df


def get_draft_events(db_name):
    with sqlite3.connect(db_name) as con:
        cur = con.cursor()
        query = '''select fantasyId from season_events where state = "DraftEvent"'''
        fantasyIds = cur.execute(query).fetchall()
        return fantasyIds

def get_event_team_id(fantasy_id, user_id):
    logger.info(f'{HLTV_FANTASY_LEAGUE_TEAM_REDIRECT.format(fantasy_id, user_id)=}')
    random_sleep()
    resp = requests.get(HLTV_FANTASY_LEAGUE_TEAM_REDIRECT.format(fantasy_id, user_id), headers=HEADER)
    if resp.status_code == 200:
        team_url = resp.json()['url']
        logger.info(f'{team_url=}')
        try:
            return int(team_url.split('/')[-1])
        except ValueError:
            logger.debug('no team registered yet')
            return None
    else:
        raise Exception(f'{resp.status_code=} {resp.text=}')
    return None

def update_user_teams_current_season(db_name, user_id):
    user_teams = get_fantasy_teams_current_season(user_id)
    df = df_from_hltv_season_stats(user_teams, user_id)
            
    create_fantasy_teams_table(db_name, df)
    fantasy_ids = get_draft_events(db_name)
    
    for fantasy_id in fantasy_ids:
        fantasy_id = fantasy_id[0]
        team_id = get_event_team_id(fantasy_id, user_id)

        if team_id != None:
            df.loc[(fantasy_id, user_id), :] = [team_id] + [None] * (df.iloc[0].shape[0]-1)

    df_update_in_sqlite_table(db_name, df, 'fantasy_teams')