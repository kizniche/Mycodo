# coding=utf-8
import importlib.util
import logging

import os

logger = logging.getLogger("mycodo.modules")

if logging.getLevelName(logging.getLogger().getEffectiveLevel()) == 'INFO':
    logger.setLevel(logging.INFO)


def load_module_from_file(path_file, module_type):
    module_name = "mycodo.{}.{}".format(
        module_type, os.path.basename(path_file).split('.')[0])
    spec = importlib.util.spec_from_file_location(module_name, path_file)
    module_custom = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module_custom)
    return module_custom
