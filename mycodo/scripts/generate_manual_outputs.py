# -*- coding: utf-8 -*-
"""Generate markdown file of Output information to be inserted into the manual."""
import sys
import os

sys.path.append(os.path.abspath(os.path.join(__file__, "../../..")))

from collections import OrderedDict

from mycodo.config import INSTALL_DIRECTORY
from mycodo.scripts.generate_doc_output import generate_controller_doc
from mycodo.utils.outputs import parse_output_information

save_path = os.path.join(INSTALL_DIRECTORY, "docs/Supported-Outputs.md")

outputs_info = OrderedDict()
mycodo_info = OrderedDict()


def repeat_to_length(s, wanted):
    return (s * (wanted//len(s) + 1))[:wanted]


if __name__ == "__main__":
    for output_id, output_data in parse_output_information(exclude_custom=True).items():
        name_str = ""
        if 'output_name' in output_data and output_data['output_name']:
            name_str += "{}".format(output_data['output_name'])
        if 'output_manufacturer' in output_data and output_data['output_manufacturer']:
            name_str += ": {}".format(output_data['output_manufacturer'])
        if 'measurements_name' in output_data and output_data['measurements_name']:
            name_str += ": {}".format(output_data['measurements_name'])
        if 'output_library' in output_data and output_data['output_library']:
            name_str += ": {}".format(output_data['output_library'])

        if ('output_manufacturer' in output_data and
                output_data['output_manufacturer'] in ['Linux', 'Mycodo', 'Raspberry Pi', 'System']):

            if name_str in mycodo_info and 'dependencies_module' in mycodo_info[name_str]:
                # Multiple sets of dependencies, append library
                mycodo_info[name_str]['dependencies_module'].append(output_data['dependencies_module'])
            else:
                # Only one set of dependencies
                mycodo_info[name_str] = output_data
                if 'dependencies_module' in output_data:
                    mycodo_info[name_str]['dependencies_module'] = [output_data['dependencies_module']]  # turn into list
        else:
            if name_str in outputs_info and 'dependencies_module' in outputs_info[name_str]:
                # Multiple sets of dependencies, append library
                outputs_info[name_str]['dependencies_module'].append(output_data['dependencies_module'])
            else:
                # Only one set of dependencies
                outputs_info[name_str] = output_data
                if 'dependencies_module' in output_data:
                    outputs_info[name_str]['dependencies_module'] = [output_data['dependencies_module']]  # turn into list

    mycodo_info = dict(OrderedDict(sorted(mycodo_info.items(), key = lambda t: t[0])))
    outputs_info = dict(OrderedDict(sorted(outputs_info.items(), key = lambda t: t[0])))

    list_outputs = [
        (mycodo_info, "Built-In Outputs (System)"),
        (outputs_info, "Built-In Outputs (Devices)")
    ]

    with open(save_path, 'w') as out_file:
        for each_list in list_outputs:
            out_file.write("## {}\n\n".format(each_list[1]))

            for each_id, each_data in each_list[0].items():
                if 'output_name' in each_data and each_data['output_name']:
                    out_file.write("### {}\n\n".format(each_data['output_name']))
                else:
                    out_file.write("### {}\n\n".format(each_id))

                if 'output_manufacturer' in each_data and each_data['output_manufacturer']:
                    out_file.write("- Manufacturer: {}\n".format(each_data['output_manufacturer']))

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

                if 'output_types' in each_data and each_data['output_types']:
                    list_output_types = []
                    for each_type in each_data['output_types']:
                        if each_type == 'on_off':
                            list_output_types.append("On/Off")
                        elif each_type == 'volume':
                            list_output_types.append("Volume")
                        elif each_type == 'pwm':
                            list_output_types.append("PWM")
                        elif each_type == 'value':
                            list_output_types.append("Value")
                    out_file.write("- Output Types: {}\n".format(", ".join(list_output_types)))

                if 'output_library' in each_data and each_data['output_library']:
                    out_file.write("- Libraries: {}\n".format(each_data['output_library']))

                generate_controller_doc(out_file, each_data)
