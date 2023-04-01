from flask import Flask, render_template, request, send_file
from flask import current_app, g
from hltv.helpers import *

import os

def create_app():
    if not os.path.exists(DB):
        print('[DEBUG] creating db by copying base db')
        import shutil
        shutil.copy(f'./data/{DB}', DB)

    app = Flask(__name__, instance_relative_config=True)
    
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    @app.route("/", methods=('GET', 'POST'))
    def hello_world():
        if request.method == 'POST':
            app.logger.info(f'{request.form=}')
            key = next(iter(request.form.keys()))

            if key == 'refresh':
                # refresh_live_events()
                # refresh_overview()
                pass
            else:
                if key == 'nils_hltvlink':
                    player = 'nils'
                elif key == 'eric_hltvlink':
                    player = 'eric'
                else:
                    raise Exception()
                
                value = request.form[key]

                add_team(player, value)

        data = get_data()
        app.logger.info(f'{data=}')
        return render_template('template.html', data=data, can_refresh=False)

    @app.route("/grab_db", methods=('GET',))
    def grab_db():
        with sqlite3.connect(DB) as _:
            return send_file(DB, as_attachment=True)

    return app

# if __name__ == '__main__':
#     create_app()