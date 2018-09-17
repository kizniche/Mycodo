#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# profile_analyzer.py
#
# This script analyzes the log output from the flask profiler
#
# To enable the profiler, open Mycodo/mycodo/mycodo_flask/app.py
# and uncomment the following line in create_app():
# app = setup_profiler(app)
#
# Stop nginx (we need the flask app to use port 443)
# sudo service nginx stop
#
# Start the flask app in debug mode with the command:
# sudo ~/Mycodo/env/bin/python ~/Mycodo/mycodo/start_flask_ui.py -d
#
# Navigate to a few pages, then stop the flask app (ctrl+c)
#
# Use the log file created from flask with this program:
# ~/Mycodo/env/bin/python ~/Mycodo/mycodo/scripts/profile_analyzer.py -f ~/Mycodo/profile-2017-02-27_18:15:26/profile.log
#
# Use the -n flag to show full request names instead shortened versions
#

import argparse
import datetime
import logging
import os
import re

logging.basicConfig(format='%(asctime)s %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)


def analyze(args):
    dt_start = datetime.datetime.now()
    parsed_data = {}

    for line in open(args.filename, 'r'):
        if line.startswith('PATH: '):
            request = re.findall(r"'(.*?)'", line, re.DOTALL)[0]
        if line.find('primitive calls) in') > -1:
            time_ms = float(line.split()[7])
            if request not in parsed_data:
                parsed_data[request] = [time_ms]
            else:
                parsed_data[request].append(time_ms)
            logger.info(
                "Found '{request}', {sec} sec".format(
                    request=request, sec=float(line.split()[7])))

    logger.info("Parsing completed in {msec:.2f} ms. Begin analysis for each request.".format(
        msec=(datetime.datetime.now()-dt_start).total_seconds() * 1000))
    dt_timer = datetime.datetime.now()

    analyzed_data = []
    for page, times in parsed_data.items():
        avg = None
        median = None
        if len(times) == 1:
            avg = times[0]
            median = times[0]
        elif len(times) > 1:
            # remove first time (first load is slow and throws off calculations)
            times_except_first = times[1:]
            # average
            avg = sum(times_except_first) / float(len(times_except_first))
            # median
            half = len(times) // 2
            if len(times) % 2 == 1:
                median = times[half]
            else:
                low = float(times[half - 1])
                high = float(times[half])
                median = low + (high - low) / 2
        # page, count, 1st, avg, median
        analyzed_data.append([page, len(times), times[0], avg, median])

    # Sort by average load time (find the slowest pages)
    analyzed_data.sort(key=lambda x: x[3])
    now = datetime.datetime.now()

    logger.info(
        "Analysis completed in {msec:.2f} ms".format(
            msec=(now - dt_timer).total_seconds() * 1000))
    logger.info("")
    logger.info("Analyzed Profile Data (times in seconds). avg and median exclude the 1st time.")
    logger.info("")
    if args.full_name:
        logger.info("Request                                                               Quantity      1st      avg   median")
    else:
        logger.info("Request                            Quantity      1st      avg   median")

    for each_line in analyzed_data:
        str_avg = ''
        str_median = ''
        if each_line[3]:
            str_avg = '{:8.3f}'.format(each_line[3])
        if each_line[4]:
            str_median = '{:8.3f}'.format(each_line[4])

        if args.full_name:
            logger.info("{pg}".format(pg=each_line[0]))
            logger.info("{pg:70} {nr:7} {fms:8.3f} {av:8} {med:8}".format(
                pg='', nr=each_line[1], fms=each_line[2], av=str_avg, med=str_median))
        else:
            logger.info("{pg:35} {nr:7} {fms:8.3f} {av:8} {med:8}".format(
                pg=each_line[0][:35], nr=each_line[1], fms= each_line[2], av=str_avg, med=str_median))


def extant_file(x):
    """
    'Type' for argparse - checks that file exists but does not open.
    """
    if not os.path.exists(x):
        raise argparse.ArgumentError("{0} does not exist".format(x))
    return x


def menu():
    parser = argparse.ArgumentParser(description="Analyze profile log file")
    parser.add_argument("-f", dest="filename", required=True,
                        help="Input file to analyze", metavar="FILE",
                        type=extant_file)
    parser.add_argument('-n', dest="full_name", action='store_true',
                        help='display full route names. (Default: cut to 26)')
    args = parser.parse_args()
    analyze(args)


if __name__ == "__main__":
    menu()
