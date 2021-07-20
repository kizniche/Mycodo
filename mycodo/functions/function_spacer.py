# coding=utf-8
from flask_babel import lazy_gettext

FUNCTION_INFORMATION = {
    'function_name_unique': 'function_spacer',
    'function_name': 'Spacer',
    'measurements_dict': {},

    'message': 'A spacer to organize Functions.',

    'options_enabled': [],
    'options_disabled': [
        'measurements_select',
        'measurements_configure'
    ],

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
