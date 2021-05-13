# -*- coding: utf-8 -*-
"""Generate markdown file of Input information to be inserted into the manual"""
import os
import re
import sys

sys.path.append(os.path.abspath(os.path.join(__file__, "../../..")))

from collections import OrderedDict
from mycodo.utils.system_pi import add_custom_measurements
from mycodo.utils.system_pi import add_custom_units
from mycodo.config import INSTALL_DIRECTORY
from mycodo.utils.inputs import parse_input_information
from mycodo.databases.models import Measurement
from mycodo.databases.models import Unit
from mycodo.config import SQL_DATABASE_MYCODO
from mycodo.databases.utils import session_scope

MYCODO_DB_PATH = 'sqlite:///' + SQL_DATABASE_MYCODO

save_path = os.path.join(INSTALL_DIRECTORY, "docs/Supported-Inputs-By-Measurement.md")

inputs_info = OrderedDict()
mycodo_info = OrderedDict()


def repeat_to_length(s, wanted):
    return (s * (wanted//len(s) + 1))[:wanted]


if __name__ == "__main__":
    for input_id, input_data in parse_input_information(exclude_custom=True).items():
        name_str = ""
        if 'input_manufacturer' in input_data and input_data['input_manufacturer']:
            name_str += "{}".format(input_data['input_manufacturer'])
        if 'input_name' in input_data and input_data['input_name']:
            name_str += ": {}".format(input_data['input_name'])
        if 'measurements_name' in input_data and input_data['measurements_name']:
            name_str += ": {}".format(input_data['measurements_name'])
        if 'input_library' in input_data and input_data['input_library']:
            name_str += ": {}".format(input_data['input_library'])

        if name_str in inputs_info and 'dependencies_module' in inputs_info[name_str]:
            # Multiple sets of dependencies, append library
            inputs_info[name_str]['dependencies_module'].append(input_data['dependencies_module'])
        else:
            # Only one set of dependencies
            inputs_info[name_str] = input_data
            if 'dependencies_module' in input_data:
                inputs_info[name_str]['dependencies_module'] = [input_data['dependencies_module']]  # turn into list

    inputs_info = dict(OrderedDict(sorted(inputs_info.items(), key = lambda t: t[0])))

    with session_scope(MYCODO_DB_PATH) as new_session:
        dict_measurements = add_custom_measurements(new_session.query(Measurement).all())
        dict_units = add_custom_units(new_session.query(Unit).all())

    dict_inputs = {}
    for name, data in inputs_info.items():
        if 'measurements_dict' not in data:
            continue

        for channel, measure in data['measurements_dict'].items():
            if measure["measurement"]:
                if measure["measurement"] not in dict_inputs:
                    dict_inputs[measure["measurement"]] = {}
                dict_inputs[measure["measurement"]][name] = data

    dict_inputs = dict(OrderedDict(sorted(dict_inputs.items(), key=lambda t: t[0])))

    with open(save_path, 'w') as out_file:
        # Table of contents
        out_file.write("Measurements\n\n")
        for measure, data in dict_inputs.items():
            out_file.write(" - [{}](#{})\n".format(
                dict_measurements[measure]["name"],
                dict_measurements[measure]["name"]
                    .replace(" ", "-")
                    .replace("(", "")
                    .replace(")", "").lower()))
        out_file.write("\n")

        for measure, data in dict_inputs.items():
            out_file.write("## {}\n\n".format(dict_measurements[measure]["name"]))

            for each_name, each_data in data.items():
                name_str = ""
                if 'input_manufacturer' in each_data and each_data['input_manufacturer']:
                    name_str += "{}".format(each_data['input_manufacturer'])
                if 'input_name' in each_data and each_data['input_name']:
                    name_str += ": {}".format(each_data['input_name'])

                link_str = name_str.lower()
                link_str = link_str.replace(" ", "-").replace("(", "-").replace(")", "-").replace(":", "-").replace(",", "-").replace("/", "-")
                link_str = link_str.replace("--", "-").replace("--", "-").strip("-")

                out_file.write("### [{}](/Mycodo/Supported-Inputs/#{})\n".format(name_str, link_str))

                out_file.write("\n")
