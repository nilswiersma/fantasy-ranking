from tempfile import NamedTemporaryFile
from hltv.helpers import *
from pprint import pprint
import pandas as pd

def df_from_hltv_player_stats(data, fantasyId, leagueId):
  data_flat = []
  for team in data['moneyDraftData']['teams']:
    for player in team['players']:
      row = {}
      row['fantasyId'] = fantasyId
      row['leagueId'] = leagueId
      row['teamName'] = team['teamData']['name']
      row['teamRank'] = team['rank']
      row['playerCost'] = player['cost']
      row['playerName'] = player['playerData']['name']
      row['playerLevel'] = player['playerData'].get('playerLevel', 'BRONZE')
      row['playerRating'] = float(player['playerData']['stats']['rating'])
      row['playerCtRating'] = float(player['playerData']['stats']['ctRating'])
      row['playerTRating'] = float(player['playerData']['stats']['tRating'])
      row['playerAwpKillsPerRound'] = float(player['playerData']['stats']['awpKillsPerRound'])
      row['playerHs'] = float(player['playerData']['stats']['hsPercentage'].replace('%', '')) / 100
      row['playerEntryFragsPerRound'] = float(player['playerData']['stats']['entryFragsPerRound'].replace('%', '')) / 100
      row['playerCluthesPerRound'] = float(player['playerData']['stats']['cluthesPerRound'].replace('%', '')) / 100
      row['playerSupportRounds'] = float(player['playerData']['stats']['supportRounds'].replace('%', '')) / 100
      row['playerMultiKillRounds'] = float(player['playerData']['stats']['multiKillRounds'].replace('%', '')) / 100
      row['playerDpr'] = player['playerData']['stats']['dpr']
      row['playerId'] = player['playerData']['fantasyPlayerId']['playerId']

      data_flat.append(row)
  df = pd.DataFrame(data_flat)
  df.set_index(['fantasyId', 'playerId'], inplace=True)
  return df

def create_player_stats_table(con, df):
  con.execute(pd.io.sql.get_schema(df.reset_index(), 'player_stats', ['fantasyId', 'playerId']))

db_name = '/tmp/tmpqmieabas.sqlite' # NamedTemporaryFile(suffix='.sqlite', delete=False).name
print(db_name)
# with sqlite3.connect(f'file:{db_name}?mode=ro', uri=True) as con:
with sqlite3.connect(db_name) as con:
  df_events = pd.read_sql_query("""SELECT * FROM season_events WHERE seasonName = "Spring season 2024" """, con)
  for fantasyId in df_events.fantasyId:
    leagueId, data = get_hltv_league_stats(fantasyId)
    df = df_from_hltv_player_stats(data, fantasyId, leagueId)

# with sqlite3.connect(db_name) as con:
#   create_player_stats_table(con, df)

with sqlite3.connect(db_name) as con:
  df_update_in_sqlite_table(con, df, 'player_stats')