#
# nginx + gunicorn web server
# install gunicorn in the python3 virtualenv
# install nginx via apt-get
#
# install install/mycodoflask.conf: sudo cp install/mycodoflask.conf /etc/nginx/sites-enabled
# enable it: sudo service nginx restart
#
# install mycodoflask.service: sudo cp install/mycodoflask.service /etc/systemd/system
# enable it: sudo systemctl daemon-reload && sudo systemctl enable mycodoflask
#
# start and stop mycodoflask:
# sudo service mycodoflask start
# sudo service mycodoflask stop
#

from mycodo.start_flask_ui import app

if __name__ == "__main__":
    app.run()
