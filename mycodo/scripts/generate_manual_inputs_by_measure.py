# -*- coding: utf-8 -*-
"""Generate markdown file of Input information to be inserted into the manual."""
import sys
from collections import OrderedDict

import os

sys.path.append(os.path.abspath(os.path.join(__file__, "../../..")))

from mycodo.config import INSTALL_DIRECTORY
from mycodo.utils.inputs import parse_input_information
from mycodo.utils.system_pi import add_custom_measurements
from mycodo.utils.system_pi import add_custom_units


def repeat_to_length(s, wanted):
    return (s * (wanted//len(s) + 1))[:wanted]


def safe_link(link):
    link = link.lower()
    for rep in [" ", "(", ")", ":", ",", "/", "--", ]:
        link = link.replace(rep, "-")
    link = link.replace(".", "")
    link = link.strip("-")
    return link


if __name__ == "__main__":
    inputs_info = OrderedDict()
    mycodo_info = OrderedDict()

    save_path = os.path.join(INSTALL_DIRECTORY, "docs/Supported-Inputs-By-Measurement.md")

    for input_id, input_data in parse_input_information(exclude_custom=True).items():
        name_str = ""
        if 'input_manufacturer' in input_data and input_data['input_manufacturer']:
            name_str += f"{input_data['input_manufacturer']}"
        if 'input_name' in input_data and input_data['input_name']:
            name_str += f": {input_data['input_name']}"
        if 'measurements_name' in input_data and input_data['measurements_name']:
            name_str += f": {input_data['measurements_name']}"
        if 'input_library' in input_data and input_data['input_library']:
            name_str += f": {input_data['input_library']}"

        if name_str in inputs_info and 'dependencies_module' in inputs_info[name_str]:
            # Multiple sets of dependencies, append library
            inputs_info[name_str]['dependencies_module'].append(input_data['dependencies_module'])
        else:
            # Only one set of dependencies
            inputs_info[name_str] = input_data
            if 'dependencies_module' in input_data:
                inputs_info[name_str]['dependencies_module'] = [input_data['dependencies_module']]  # turn into list

    inputs_info = dict(OrderedDict(sorted(inputs_info.items(), key = lambda t: t[0])))

    dict_measurements = add_custom_measurements([])
    dict_units = add_custom_units([])

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
            out_file.write(f" - [{dict_measurements[measure]['name']}](#{safe_link(dict_measurements[measure]['name'])})\n")
        out_file.write("\n")

        for measure, data in dict_inputs.items():
            out_file.write(f"## {dict_measurements[measure]['name']}\n\n")

            # Determine if there are multiple of the same name
            dict_names = {}
            for each_name, each_data in data.items():
                name_str = ""
                if 'input_manufacturer' in each_data and each_data['input_manufacturer']:
                    name_str += "{}".format(each_data['input_manufacturer'])
                if 'input_name' in each_data and each_data['input_name']:
                    name_str += ": {}".format(each_data['input_name'])
                if name_str not in dict_names:
                    dict_names[name_str] = 1
                else:
                    dict_names[name_str] += 1

            for each_name, each_data in data.items():
                name_str = ""
                if 'input_manufacturer' in each_data and each_data['input_manufacturer']:
                    name_str += "{}".format(each_data['input_manufacturer'])
                if 'input_name' in each_data and each_data['input_name']:
                    name_str += ": {}".format(each_data['input_name'])
                if name_str in dict_names and dict_names[name_str] > 1:
                    if 'input_library' in each_data and each_data['input_library']:
                        name_str += " ({})".format(each_data['input_library'])

                out_file.write(f"### [{name_str}](/Mycodo/Supported-Inputs/#{safe_link(name_str)})\n")

                out_file.write("\n")
