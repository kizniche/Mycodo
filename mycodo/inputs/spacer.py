# coding=utf-8
from flask_babel import lazy_gettext

INPUT_INFORMATION = {
    'input_name_unique': 'input_spacer',
    'input_manufacturer': 'Mycodo',
    'input_name': lazy_gettext('Spacer'),
    'measurements_dict': {},

    'message': 'A spacer to organize Inputs.',

    'options_enabled': [],
    'options_disabled': [],

    'interfaces': ['MYCODO']
}
