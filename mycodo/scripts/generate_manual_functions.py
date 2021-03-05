# -*- coding: utf-8 -*-
"""Generate markdown file of Function information to be inserted into the manual"""

import sys

import os

sys.path.append(os.path.abspath(os.path.join(__file__, "../../..")))

import re
from collections import OrderedDict

from mycodo.config import INSTALL_DIRECTORY
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
        out_file.write("Supported Functions are listed below.\n\n")
        for each_list in list_functions:
            out_file.write("## {}\n\n".format(each_list[1]))

            for each_id, each_data in each_list[0].items():
                if 'function_name' in each_data and each_data['function_name']:
                    name_str = "{}".format(each_data['function_name'])

                out_file.write("### {}\n\n".format(name_str))

                if 'function_library' in each_data and each_data['function_library']:
                    out_file.write("- Libraries: {}\n".format(each_data['function_library']))

                if 'dependencies_module' in each_data and each_data['dependencies_module']:
                    out_file.write("- Dependencies: ")
                    for i, each_dep_set in enumerate(each_data['dependencies_module']):
                        if len(each_data['dependencies_module']) > 1:
                            out_file.write("Function Variant {}: ".format(i + 1))
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
