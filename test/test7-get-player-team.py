from hltv.helpers import HLTV_FANTASY_LEAGUE_TEAM_REDIRECT, get_event_team_id, get_single_team, get_team_params, HEADER, safe_get
from flask import escape
import requests


fantasy_id = 474
user_id = 1355207

resp = safe_get(HLTV_FANTASY_LEAGUE_TEAM_REDIRECT.format(escape(fantasy_id), escape(user_id)))
team_url = resp.json()['url']

if team_url == f'/fantasy/{fantasy_id}/overview':
    # no team listed yet
    return {}
else:
    resp = safe_get(f'https://www.hltv.org{escape(team_url.replace("team", "overview"))}/json')
    return reps.json()