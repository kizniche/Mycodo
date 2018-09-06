# coding=utf-8

import logging
import sys
import timeit
from pprint import pformat

import os

sys.path.append(
    os.path.abspath(os.path.join(os.path.dirname(__file__), os.path.pardir) + '/../..'))

from mycodo.utils.inputs import parse_input_information

logging.basicConfig(
    format='%(asctime)s %(levelname)s: %(message)s',
    level='INFO')

logger = logging.getLogger("input_parser_start")

if __name__ == "__main__":
    logger.info("Starting parser")
    logger.info("")

    startup_timer = timeit.default_timer()

    dict_inputs = parse_input_information()

    logger.info("")

    run_time = timeit.default_timer() - startup_timer
    logger.info("Run time: {time:.3f} seconds".format(time=run_time))
    logger.info("")

    logger.info("Parsed Input Information:\n{}".format(pformat(dict_inputs)))
