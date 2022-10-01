# -*- coding: utf-8 -*-
"""Generate markdown file of Input information to be inserted into the manual."""
import os
import sys

sys.path.append(os.path.abspath(os.path.join(__file__, "../../..")))

from collections import OrderedDict
from mycodo.config import INSTALL_DIRECTORY
from mycodo.scripts.generate_doc_output import generate_controller_doc
from mycodo.utils.inputs import parse_input_information

save_path = os.path.join(INSTALL_DIRECTORY, "docs/Supported-Inputs.md")

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

        if ('input_manufacturer' in input_data and
                input_data['input_manufacturer'] in ['Linux', 'Mycodo', 'Raspberry Pi', 'System']):

            if name_str in mycodo_info and 'dependencies_module' in mycodo_info[name_str]:
                # Multiple sets of dependencies, append library
                mycodo_info[name_str]['dependencies_module'].append(input_data['dependencies_module'])
            else:
                # Only one set of dependencies
                mycodo_info[name_str] = input_data
                if 'dependencies_module' in input_data:
                    mycodo_info[name_str]['dependencies_module'] = [input_data['dependencies_module']]  # turn into list
        else:
            if name_str in inputs_info and 'dependencies_module' in inputs_info[name_str]:
                # Multiple sets of dependencies, append library
                inputs_info[name_str]['dependencies_module'].append(input_data['dependencies_module'])
            else:
                # Only one set of dependencies
                inputs_info[name_str] = input_data
                if 'dependencies_module' in input_data:
                    inputs_info[name_str]['dependencies_module'] = [input_data['dependencies_module']]  # turn into list

    mycodo_info = dict(OrderedDict(sorted(mycodo_info.items(), key = lambda t: t[0])))
    inputs_info = dict(OrderedDict(sorted(inputs_info.items(), key = lambda t: t[0])))

    list_inputs = [
        (mycodo_info, "Built-In Inputs (System)"),
        (inputs_info, "Built-In Inputs (Devices)")
    ]

    with open(save_path, 'w') as out_file:
        for each_list in list_inputs:
            out_file.write("## {}\n\n".format(each_list[1]))

            for each_id, each_data in each_list[0].items():
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

                generate_controller_doc(out_file, each_data)
