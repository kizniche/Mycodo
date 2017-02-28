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
# Start the flask app in debug mode with the command:
# sudo python ./Mycodo/mycodo/start_flask_ui.py -d
#
# Navigate to a few pages, then stop the flask app (ctrl+c)
#
# Use the log file created from flask with this program:
# ./Mycodo/mycodo/scripts/profile_analyzer -f ./Mycodo/profile-2017-02-27_18:15:26/profile.log
#
# Use the -n flag to show full request names instead shortened versions
#

import argparse
import datetime
import logging
import os.path

logging.basicConfig(format='%(asctime)s %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)


def analyze(args):
    dt_start = datetime.datetime.now()
    parsed_data = {}
    for index, line in enumerate(open(args.filename, 'r')):
        if line.startswith('PATH: '):
            request = line.split()[1]
            if request.startswith("'") and request.endswith("'"):
                request = request[1:-1]
        if line.find('primitive calls) in') > -1:
            time_ms = float(line.split()[7])
            if request not in parsed_data:
                parsed_data[request] = [time_ms]
            else:
                parsed_data[request].append(time_ms)
            logger.info(
                "Found request '{request}' with a render time of {sec} "
                "seconds".format(request=request,
                                 sec=float(line.split()[7])))
    logger.info("Parsing completed in {msec:.2f} ms. Begin analysis for each request.".format(
        msec=(datetime.datetime.now()-dt_start).total_seconds() * 1000))
    logger.info("")
    dt_timer = datetime.datetime.now()

    logger.info("Analyzed Profile Data (times in seconds). avg and median exclude the 1st time.")
    logger.info("")
    logger.info("Request                   Quantity      1st      avg   median")
    for page, times in parsed_data.items():
        stats = False
        if len(times) == 1:
            times_avg = 0.0
        elif len(times) == 2:
            times_avg = times[1]

        if len(times) > 2:
            stats = True
            # remove first time (first load is slow and throws off calculations)
            times_except_first = times[1:]

            # average
            times_avg = sum(times_except_first) / float(len(times_except_first))

            # median
            half = len(times) // 2
            if len(times) % 2 == 1:
                times_median = times[half]
            else:
                low = float(times[half - 1])
                high = float(times[half])
                times_median = low + (high - low) / 2

        if len(page) > 19:
            if args.full_name:
                logger.info("{pg}".format(pg=page))
                logger.info("{pg:26} {nr:7} {fms:8.3f} {av:8.3f} {med:8.3f}".format(
                    pg='', nr=len(times), fms=times[0], av=times_avg, med=times_median))
            else:
                logger.info("{pg:26} {nr:7} {fms:8.3f} {av:8.3f} {med:8.3f}".format(
                    pg=page[:26], nr=len(times), fms=times[0], av=times_avg, med=times_median))
        else:
            logger.info("{pg:26} {nr:7} {fms:8.3f} {av:8.3f} {med:8.3f}".format(
                pg=page, nr=len(times), fms=times[0], av=times_avg, med=times_median))

    now = datetime.datetime.now()
    logger.info("")
    logger.info(
        "Analysis completed in {msec:.2f} ms, "
        "total run time: {tot:.2f} ms".format(
            msec=(now - dt_timer).total_seconds() * 1000,
            tot=(now - dt_start).total_seconds() * 1000))


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
