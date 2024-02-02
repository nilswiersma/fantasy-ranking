import requests
import json
import sqlite3
import re
import random
import time
import os

HLTV_FANTASY_OVERVIEW = 'https://www.hltv.org/fantasy/json'
HLTV_FANTASY_SINGLE_TEAM = 'https://www.hltv.org/fantasy/{}/league/{}/overview/{}/json'
HLTV_FANTASY_SINGLE_TEAM_RE = r'https://www.hltv.org/fantasy/(\d+)/league/(\d+)/team/(\d+)/*'
HLTV_FANTASY_LEAGUE_STATS = 'https://www.hltv.org/fantasy/{}/leagues/{}/join/json'
HLTV_FANTASY_USER_SEASON_STATS = 'https://www.hltv.org/fantasy/user/{}/overview/json'

DB = './data/points.sqlite'
DB_TEMPLATE = './flaskr/templates/points.sqlite'

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

def get_teams_current_season(user_id):
    resp = requests.get(HLTV_FANTASY_USER_SEASON_STATS.format(user_id), headers=HEADER)
    if resp.status_code == 200:
        return json.loads(resp.text)
    else:
        raise Exception(f'{resp.status_code=} {resp.text=}')

def get_league_stats(event_id, league_id):
    print(f'[DEBUG] {HLTV_FANTASY_LEAGUE_STATS.format(event_id, league_id)=}')
    resp = requests.get(HLTV_FANTASY_LEAGUE_STATS.format(event_id, league_id), headers=HEADER)
    # TODO log it to .jsoncache with a timestamp
    if resp.status_code == 200:
        return json.loads(resp.text)
    else:
        raise Exception(f'{resp.status_code=} {resp.text=}')
    # with open('flaskr/.jsoncache/stats-test.json', 'r') as f:
    #     return json.load(f)


def get_current_fantasy_overview():
    ret = requests.get(HLTV_FANTASY_OVERVIEW, headers=HEADER)
    assert ret.status_code == 200, f'ERROR fetching fantasy overview, {ret.status_code=}'
    # TODO log it to .jsoncache with a timestamp
    # TODO log stats for live events somewhere, need to log in first for that
    return ret

def get_single_team(event_id, league_id, team_id):
    url = HLTV_FANTASY_SINGLE_TEAM.format(event_id, league_id, team_id)
    ret = requests.get(url, headers=HEADER)
    assert ret.status_code == 200, f'ERROR fetching team'
    # TODO log it somewhere?
    return ret

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
        print(f'[DEBUG] {ids_db=}')
        
        # Insert new rows for new events
        events_insert = []
        print(f'[DEBUG] {[id_ for id_ in events.keys() if id_ not in ids_db]}')
        for id_ in [id_ for id_ in events.keys() if id_ not in ids_db]:
            events_insert.append((id_,) + events[id_])
        cur.executemany("""insert into events values(?, ?, ?, ?)""", events_insert)
        
        # Update rows for existing events
        events_update = []
        for id_ in [id_ for id_ in events.keys() if id_ in ids_db]:
            events_update.append(events[id_] + (id_,))
        print(f'[DEBUG] {events_update=}')
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
        print(f'[DEBUG] {(score, percent, season_points, event_id, player)}')
        cur.execute("""update points set score=?, percent=?, season_points=? where event_id=? and player=?""", 
                        (score, percent, season_points, event_id, player))
        con.commit()

    return (score, percent, season_points)

def get_data():
    with sqlite3.connect(DB) as con:
        cur = con.cursor()
        seasons = cur.execute('''select distinct season from events''').fetchall()
        ret = {}

        for season in seasons:
            season = season[0]
            ret[season] = {}
            events = cur.execute('''select * from events where season=? order by id desc''', (season,)).fetchall()

            ret[season]['totals'] = []
            for player in ['nils', 'eric']:
                total = cur.execute('''select sum(season_points) from points where player=? and event_id in (select id from events where season=?)''', (player, season)).fetchone()
                print(f'[DEBUG] {total=}')
                ret[season]['totals'].append(total[0])

            ret[season]['events'] = {}
            for event in events:
                event_id = event[0]
                event_name = event[1]
                state = event[3]
                key = (event_id, event_name, state)
                ret[season]['events'][key] = []

                for player in ['nils', 'eric']:
                    data = cur.execute('''select * from points where event_id=? and player=?''', (event_id, player)).fetchone()
                    ret[season]['events'][key].append(data)
            
        return ret

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
    data = get_single_team(event_id, league_id, team_id)
    team_data = json.loads(data.text)
    team_to_db(team_data, event_id, player)

def refresh_overview():
    overview = json.loads(get_current_fantasy_overview().text)
    overview_to_db(overview)

def refresh_live_events():
    print(f'[DEBUG] {DB=}')
    with sqlite3.connect(DB) as con:
        cur = con.cursor()
        teams = cur.execute('''select event_id, league_id, team_id, player from points where event_id in (select id from events where state=="LiveEvent")''').fetchall()
    
    print(f'[DEBUG] {teams=}')
    for team in teams:
        data = get_single_team(team[0], team[1], team[2])
        team_data = json.loads(data.text)
        team_to_db(team_data, team[0], team[3])
        x = random.randint(1,3000)/1000
        print(f'[DEBUG] Random sleep {x}s')
        time.sleep(x)

# def collect_numbers_from_draft_events():
#     with sqlite3.connect(DB) as con:
#         cur = con.cursor()
#         teams = cur.execute('''select event_id, league_id, team_id, player from points where event_id in (select id from events where state=="DraftEvent")''').fetchall()
#     for team in teams:
#         data = get_single_team(team[0], team[1], team[2])
#         team_data = json.loads(data.text)
#         team_to_db(team_data, team[0], team[3])
#         x = random.randint(1,3000)/1000
#         print(f'[DEBUG] Random sleep {x}s')
#         time.sleep(x)