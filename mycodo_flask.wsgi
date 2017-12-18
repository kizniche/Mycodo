import sys

activate_this = '/var/www/mycodo/env_py3/bin/activate_this.py'
with open(activate_this) as file_:
    exec(file_.read(), dict(__file__=activate_this))

sys.path.append('/var/www/mycodo/mycodo')

from mycodo.start_flask_ui import app as application
