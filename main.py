import os
import hltv.background_update

hltv.background_update.setup_scheduler()
os.system("waitress-serve --call 'flaskr:create_app'")