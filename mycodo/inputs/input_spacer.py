# coding=utf-8
from flask_babel import lazy_gettext

INPUT_INFORMATION = {
    'input_name_unique': 'input_spacer',
    'input_manufacturer': 'Mycodo',
    'input_name': 'Spacer',
    'measurements_dict': {},

    'message': 'A spacer to organize Inputs.',

    'custom_options': [
        {
            'id': 'color',
            'type': 'text',
            'default_value': '#000000',
            'required': True,
            'name': lazy_gettext('Color'),
            'phrase': 'The color of the name text'
        }
    ]
}
