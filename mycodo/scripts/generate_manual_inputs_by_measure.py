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

                out_file.write("### {}\n\n".format(name_str))

                if 'input_manufacturer' in each_data and each_data['input_manufacturer']:
                    out_file.write("- Manufacturer: {}\n".format(each_data['input_manufacturer']))

                if 'measurements_name' in each_data and each_data['measurements_name']:
                    out_file.write("- Measurements: {}\n".format(each_data['measurements_name']))

                if 'interfaces' in each_data and each_data['interfaces']:
                    list_interfaces = []
                    for each_type in each_data['interfaces']:
                        if each_type == 'I2C':
                            list_interfaces.append("I<sup>2</sup>C")
                        elif each_type == 'MYCODO':
                            list_interfaces.append("Mycodo")
                        elif each_type == '1WIRE':
                            list_interfaces.append("1-Wire")
                        elif each_type == 'HTTP':
                            list_interfaces.append("HTTP")
                        elif each_type == 'FTDI':
                            list_interfaces.append("FTDI")
                        elif each_type == 'UART':
                            list_interfaces.append("UART")
                        elif each_type == 'GPIO':
                            list_interfaces.append("GPIO")
                        elif each_type == 'PYTHON':
                            list_interfaces.append("Python")
                        elif each_type == 'SHELL':
                            list_interfaces.append("Shell")
                        else:
                            list_interfaces.append(each_type)
                    out_file.write("- Interfaces: {}\n".format(", ".join(list_interfaces)))

                if 'input_library' in each_data and each_data['input_library']:
                    out_file.write("- Libraries: {}\n".format(each_data['input_library']))

                if 'dependencies_module' in each_data and each_data['dependencies_module']:
                    out_file.write("- Dependencies: ")
                    for i, each_dep_set in enumerate(each_data['dependencies_module']):
                        if len(each_data['dependencies_module']) > 1:
                            out_file.write("Input Variant {}: ".format(i + 1))
                        for i_d, each_dep in enumerate(each_dep_set):
                            if each_dep[0] == "apt":
                                out_file.write("[{0}](https://packages.debian.org/buster/{0})".format(each_dep[2]))
                            elif each_dep[0] == "pip-pypi":
                                if 'git+' in each_dep[2]:
                                    url = re.search('git\+(.*).git', each_dep[2])
                                    out_file.write("[{name}]({url})".format(name=each_dep[1], url=url.group(1)))
                                elif "==" in each_dep[2]:
                                    out_file.write("[{0}](https://pypi.org/project/{0})".format(each_dep[2].split("==")[0]))
                                else:
                                    out_file.write("[{0}](https://pypi.org/project/{0})".format(each_dep[2]))
                            elif each_dep[0] == "pip-git":
                                url = re.search('git://(.*).git', each_dep[2])
                                out_file.write("[{name}](https://{url})".format(name=each_dep[1], url=url.group(1)))
                            else:
                                out_file.write(each_dep[2])

                            if i_d + 1 < len(each_dep_set):
                                out_file.write(", ")

                        if i + 1 < len(each_data['dependencies_module']):
                            out_file.write("; ")
                        else:
                            out_file.write("\n")

                if 'url_manufacturer' in each_data and each_data['url_manufacturer']:
                    out_file.write("- Manufacturer URL")
                    if len(each_data['url_manufacturer']) == 1:
                        out_file.write(": ")
                    else:
                        out_file.write("s: ")
                    for i, each_url in enumerate(each_data['url_manufacturer']):
                        if len(each_data['url_manufacturer']) == 1:
                            out_file.write("[Link]({})".format(each_url))
                        else:
                            out_file.write("[Link {num}]({url})".format(num=i + 1, url=each_url))
                        if i + 1 < len(each_data['url_manufacturer']):
                            out_file.write(", ")
                        else:
                            out_file.write("\n")

                if 'url_datasheet' in each_data and each_data['url_datasheet']:
                    out_file.write("- Datasheet URL")
                    if len(each_data['url_datasheet']) == 1:
                        out_file.write(": ")
                    else:
                        out_file.write("s: ")
                    for i, each_url in enumerate(each_data['url_datasheet']):
                        if len(each_data['url_datasheet']) == 1:
                            out_file.write("[Link]({})".format(each_url))
                        else:
                            out_file.write("[Link {num}]({url})".format(num=i + 1, url=each_url))
                        if i + 1 < len(each_data['url_datasheet']):
                            out_file.write(", ")
                        else:
                            out_file.write("\n")

                if 'url_product_purchase' in each_data and each_data['url_product_purchase']:
                    out_file.write("- Product URL")
                    if len(each_data['url_product_purchase']) == 1:
                        out_file.write(": ")
                    else:
                        out_file.write("s: ")
                    for i, each_url in enumerate(each_data['url_product_purchase']):
                        if len(each_data['url_product_purchase']) == 1:
                            out_file.write("[Link]({})".format(each_url))
                        else:
                            out_file.write("[Link {num}]({url})".format(num=i + 1, url=each_url))
                        if i + 1 < len(each_data['url_product_purchase']):
                            out_file.write(", ")
                        else:
                            out_file.write("\n")

                if 'url_additional' in each_data and each_data['url_additional']:
                    if len(each_data['url_additional']) == 1:
                        out_file.write("- Additional URL: ")
                    else:
                        out_file.write("- Additional URL(s): ")
                    for i, each_url in enumerate(each_data['url_additional']):
                        if len(each_data['url_additional']) == 1:
                            out_file.write("[Link]({})".format(each_url))
                        else:
                            out_file.write("[Link {num}]({url})".format(num=i + 1, url=each_url))
                        if i + 1 < len(each_data['url_additional']):
                            out_file.write(", ")
                        else:
                            out_file.write("\n")

                if 'message' in each_data and each_data['message']:
                    out_file.write("\n{}\n".format(each_data['message']))

                out_file.write("\n")
