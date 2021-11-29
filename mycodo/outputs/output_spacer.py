# coding=utf-8
from flask_babel import lazy_gettext

OUTPUT_INFORMATION = {
    'output_name_unique': 'output_spacer',
    'output_name': lazy_gettext('Spacer'),
    'measurements_dict': {},
    'channels_dict': {},
    'output_types': [],
    'no_run': True,

    'message': 'A spacer to organize Outputs.',

    'options_enabled': [],
    'options_disabled': [],

    'interfaces': ['MYCODO'],

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
