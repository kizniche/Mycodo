# -*- coding: utf-8 -*-
"""Generate markdown file of Function information to be inserted into the manual."""
import sys
import os

sys.path.append(os.path.abspath(os.path.join(__file__, "../../..")))

from collections import OrderedDict

from mycodo.config import INSTALL_DIRECTORY
from mycodo.scripts.generate_doc_output import generate_controller_doc
from mycodo.utils.functions import parse_function_information

save_path = os.path.join(INSTALL_DIRECTORY, "docs/Supported-Functions.md")

functions_info = OrderedDict()
mycodo_info = OrderedDict()


def repeat_to_length(s, wanted):
    return (s * (wanted//len(s) + 1))[:wanted]


if __name__ == "__main__":
    for function_id, function_data in parse_function_information(exclude_custom=True).items():
        name_str = ""
        if 'function_name' in function_data and function_data['function_name']:
            name_str += ": {}".format(function_data['function_name'])
        if 'function_library' in function_data and function_data['function_library']:
            name_str += ": {}".format(function_data['function_library'])

        if name_str in functions_info and 'dependencies_module' in functions_info[name_str]:
            # Multiple sets of dependencies, append library
            functions_info[name_str]['dependencies_module'].append(function_data['dependencies_module'])
        else:
            # Only one set of dependencies
            functions_info[name_str] = function_data
            if 'dependencies_module' in function_data:
                functions_info[name_str]['dependencies_module'] = [function_data['dependencies_module']]  # turn into list

    mycodo_info = dict(OrderedDict(sorted(mycodo_info.items(), key = lambda t: t[0])))
    functions_info = dict(OrderedDict(sorted(functions_info.items(), key = lambda t: t[0])))

    list_functions = [
        (functions_info, "Built-In Functions")
    ]

    with open(save_path, 'w') as out_file:
        for each_list in list_functions:
            out_file.write("## {}\n\n".format(each_list[1]))

            for each_id, each_data in each_list[0].items():
                if 'function_name' in each_data and each_data['function_name']:
                    name_str = "{}".format(each_data['function_name'])

                out_file.write("### {}\n\n".format(name_str))

                if 'function_library' in each_data and each_data['function_library']:
                    out_file.write("- Libraries: {}\n".format(each_data['function_library']))

                generate_controller_doc(out_file, each_data)
