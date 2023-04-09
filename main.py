import os
import hltv.background_update
from hltv.helpers import DB, DB_TEMPLATE

if not os.path.exists(DB):
    print(f'[DEBUG] {os.getcwd()=}')
    print('[DEBUG] creating db by copying base db')
    import shutil
    shutil.copy(DB_TEMPLATE, DB)

hltv.background_update.setup_scheduler()
os.system("waitress-serve --call 'flaskr:create_app'")