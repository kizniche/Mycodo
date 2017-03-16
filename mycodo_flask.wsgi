import sys

activate_this = '/var/www/mycodo/env/bin/activate_this.py'
execfile(activate_this, dict(__file__=activate_this))

sys.path.append('/var/www/mycodo/mycodo')

from mycodo.start_flask_ui import app as application
