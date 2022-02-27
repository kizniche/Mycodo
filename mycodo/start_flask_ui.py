# coding=utf-8
"""Starts the mycodo flask UI."""
import argparse
import sys
import os

sys.path.append(
    os.path.abspath(os.path.join(os.path.dirname(__file__), os.path.pardir)))

from mycodo.config import ENABLE_FLASK_PROFILER
from mycodo.mycodo_flask.app import create_app

app = create_app()  # required by the wsgi config and main()

# Flask profiler
if ENABLE_FLASK_PROFILER:
    import flask_profiler
    flask_profiler.init_app(app)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Mycodo Flask HTTP server.")

    options = parser.add_argument_group('Options')
    options.add_argument('-d', '--debug', action='store_true',
                         help="Run Flask with debug=True (Default: False)")
    options.add_argument('-s', '--ssl', action='store_true',
                         help="Run Flask without SSL (Default: Enabled)")

    args = parser.parse_args()

    debug = args.debug

    if args.ssl:
        app.run(host='0.0.0.0', port=80, debug=debug)
    else:
        # Locate the SSL certificates for forced-HTTPS
        file_path = os.path.abspath(__file__)
        dir_path = os.path.dirname(file_path)
        cert = os.path.join(dir_path, "mycodo_flask/ssl_certs/server.crt")
        privkey = os.path.join(dir_path, "mycodo_flask/ssl_certs/server.key")
        context = (cert, privkey)
        app.run(host='0.0.0.0', port=443, ssl_context=context, debug=debug)
