# coding=utf-8
from flask_babel import lazy_gettext

OUTPUT_INFORMATION = {
    'output_name_unique': 'output_spacer',
    'output_name': lazy_gettext('Spacer'),
    'output_library': '',
    'measurements_dict': {},
    'channels_dict': {},
    'output_types': [],
    'no_run': True,

    'message': 'A spacer to organize Outputs.',

    'options_enabled': [],
    'options_disabled': [],

    'interfaces': ['MYCODO']
}
