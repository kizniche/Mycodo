# -*- coding: utf-8 -*-
"""Generate markdown Output to be inserted into the manual"""
import sys
import os

sys.path.append(os.path.abspath(os.path.join(__file__, "../../..")))

import re

from mycodo.config_translations import TRANSLATIONS


def generate_controller_doc(out_file, each_data):
    if 'dependencies_module' in each_data and each_data['dependencies_module']:
        out_file.write("- Dependencies: ")
        for i, each_dep_set in enumerate(each_data['dependencies_module']):
            if len(each_data['dependencies_module']) > 1:
                out_file.write("Output Variant {}: ".format(i + 1))
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

    if 'options_enabled' in each_data or 'custom_options' in each_data:
        out_file.write("\n#### Options\n")

    if 'options_enabled' in each_data and 'i2c_location' in each_data['options_enabled']:
        out_file.write("\n##### I<sup>2</sup>C Address\n")
        out_file.write("\n- Type: Text")
        out_file.write("\n- Description: {}\n".format(TRANSLATIONS['i2c_location']['phrase']))
        out_file.write("\n##### I<sup>2</sup>C Bus\n")
        out_file.write("\n- Type: Integer")
        out_file.write("\n- Description: {}\n".format(TRANSLATIONS['i2c_bus']['phrase']))

    if 'options_enabled' in each_data and 'bt_location' in each_data['options_enabled']:
        out_file.write("\n##### {}\n".format(TRANSLATIONS['bt_location']['title']))
        out_file.write("\n- Type: Text")
        out_file.write("\n- Description: {}\n".format(TRANSLATIONS['bt_location']['phrase']))
        out_file.write("\n##### {}\n".format(TRANSLATIONS['bt_adapter']['title']))
        out_file.write("\n- Type: Integer")
        out_file.write("\n- Description: {}\n".format(TRANSLATIONS['bt_adapter']['phrase']))

    if 'options_enabled' in each_data and 'ftdi_location' in each_data['options_enabled']:
        out_file.write("\n##### {}\n".format(TRANSLATIONS['ftdi_location']['title']))
        out_file.write("\n- Type: Text")
        out_file.write("\n- Description: {}\n".format(TRANSLATIONS['ftdi_location']['phrase']))

    if 'options_enabled' in each_data and 'uart_location' in each_data['options_enabled']:
        out_file.write("\n##### {}\n".format(TRANSLATIONS['uart_location']['title']))
        out_file.write("\n- Type: Text")
        out_file.write("\n- Description: {}\n".format(TRANSLATIONS['uart_location']['phrase']))

    if 'options_enabled' in each_data and 'baud_rate' in each_data['options_enabled']:
        out_file.write("\n##### {}\n".format(TRANSLATIONS['baud_rate']['title']))
        out_file.write("\n- Type: Integer")
        out_file.write("\n- Description: {}\n".format(TRANSLATIONS['baud_rate']['phrase']))

    if 'options_enabled' in each_data and 'pin_cs' in each_data['options_enabled']:
        out_file.write("\n##### {}\n".format(TRANSLATIONS['pin_cs']['title']))
        out_file.write("\n- Type: Integer")
        out_file.write("\n- Description: {}\n".format(TRANSLATIONS['pin_cs']['phrase']))

    if 'options_enabled' in each_data and 'measurements_select' in each_data['options_enabled']:
        out_file.write("\n##### {}\n".format(TRANSLATIONS['measurements_enabled']['title']))
        out_file.write("\n- Type: Multi-Select")
        out_file.write("\n- Description: {}\n".format(TRANSLATIONS['measurements_enabled']['phrase']))

    if 'options_enabled' in each_data and 'period' in each_data['options_enabled']:
        out_file.write("\n##### {}\n".format(TRANSLATIONS['period']['title']))
        out_file.write("\n- Type: Decimal")
        out_file.write("\n- Description: {}\n".format(TRANSLATIONS['period']['phrase']))

    if 'options_enabled' in each_data and 'start_offset' in each_data['options_enabled']:
        out_file.write("\n##### {}\n".format(TRANSLATIONS['start_offset']['title']))
        out_file.write("\n- Type: Integer")
        out_file.write("\n- Description: {}\n".format(TRANSLATIONS['start_offset']['phrase']))

    if 'options_enabled' in each_data and 'pre_output' in each_data['options_enabled']:
        out_file.write("\n##### {}\n".format(TRANSLATIONS['pre_output_id']['title']))
        out_file.write("\n- Type: Select")
        out_file.write("\n- Description: {}\n".format(TRANSLATIONS['pre_output_id']['phrase']))
        out_file.write("\n##### {}\n".format(TRANSLATIONS['pre_output_duration']['title']))
        out_file.write("\n- Type: Decimal")
        out_file.write("\n- Description: {}\n".format(TRANSLATIONS['pre_output_duration']['phrase']))
        out_file.write("\n##### {}\n".format(TRANSLATIONS['pre_output_during_measure']['title']))
        out_file.write("\n- Type: Boolean")
        out_file.write("\n- Description: {}\n".format(TRANSLATIONS['pre_output_during_measure']['phrase']))

    option_headings = [
        ('custom_options', ""),
        ('custom_channel_options', "Channel Options"),
        ('custom_actions', "Actions"),
    ]

    for each_opt, each_head in option_headings:
        if each_opt in each_data:
            if each_opt != 'custom_options':
                out_file.write("\n#### {}\n".format(each_head))

            for each_option in each_data[each_opt]:
                if each_option['type'] == 'new_line':
                    pass

                elif each_option['type'] == 'message':
                    out_file.write("\n##### {}\n".format(each_option['default_value']))

                elif each_option['type'] == 'button':
                    out_file.write("\n##### {}\n".format(each_option['name']))
                    out_file.write("\n- Type: Button")

                else:
                    out_file.write("\n##### {}\n".format(each_option['name']))
                    if each_option['type'] == 'integer':
                        out_file.write("\n- Type: Integer")
                    elif each_option['type'] == 'text':
                        out_file.write("\n- Type: Text")
                    elif each_option['type'] == 'float':
                        out_file.write("\n- Type: Decimal")
                    elif each_option['type'] == 'select_measurement':
                        out_file.write("\n- Type: Select Measurement")
                        if 'options_select' in each_option and each_option['options_select']:
                            out_file.write("\n- Selections: ")
                            for i, each_sel in enumerate(each_option['options_select']):
                                out_file.write(each_sel)
                                if i < len(each_option['options_select']):
                                    out_file.write(", ")
                    elif each_option['type'] == 'select':
                        out_file.write("\n- Type: Select")
                    elif each_option['type'] == 'bool':
                        out_file.write("\n- Type: Boolean")

                    if 'default_value' in each_option and each_option['default_value']:
                        if each_option['type'] in ['integer', 'text', 'float', 'bool']:
                            out_file.write("\n- Default Value: {}".format(each_option['default_value']))
                        elif each_option['type'] == 'select':
                            select_options = "\n- Options: \["
                            select_default = None
                            if 'default_value' in each_option and each_option['default_value']:
                                select_default = each_option['default_value']
                            for i, each_option_sel in enumerate(each_option['options_select']):
                                if select_default and select_default == each_option_sel[0]:
                                    select_options += "**{}**".format(each_option_sel[1])
                                else:
                                    select_options += each_option_sel[1]
                                if i < len(each_option['options_select']) - 1:
                                    select_options += " | "
                            select_options += "\] (Default in **bold**)"
                            out_file.write(select_options)

                    out_file.write("\n- Description: {}\n".format(each_option['phrase']))

    out_file.write("\n")
