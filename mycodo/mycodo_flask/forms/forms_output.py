# -*- coding: utf-8 -*-
#
# forms_output.py - Output Flask Forms
#

from flask_babel import lazy_gettext
from flask_wtf import FlaskForm
from wtforms import BooleanField
from wtforms import HiddenField
from wtforms import IntegerField
from wtforms import SelectField
from wtforms import StringField
from wtforms import SubmitField
from wtforms import widgets
from wtforms.validators import DataRequired
from wtforms.widgets import NumberInput

from mycodo.config_translations import TRANSLATIONS
from mycodo.mycodo_flask.utils.utils_general import generate_form_output_list
from mycodo.utils.outputs import parse_output_information
from mycodo.utils.utils import sort_tuple


class OutputAdd(FlaskForm):
    choices_outputs = []
    dict_outputs = parse_output_information()
    list_outputs_sorted = generate_form_output_list(dict_outputs)
    for each_output in list_outputs_sorted:
        value = '{inp},'.format(inp=each_output)
        name = '{name}'.format(name=dict_outputs[each_output]['output_name'])

        if 'output_library' in dict_outputs[each_output]:
            name += ' ({lib})'.format(lib=dict_outputs[each_output]['output_library'])

        if 'interfaces' in dict_outputs[each_output] and dict_outputs[each_output]['interfaces']:
            for each_interface in dict_outputs[each_output]['interfaces']:
                tmp_value = '{val}{int}'.format(val=value, int=each_interface)
                tmp_name = '{name} [{int}]'.format(name=name, int=each_interface)
                choices_outputs.append((tmp_value, tmp_name))
        else:
            choices_outputs.append((value, name))

    choices_outputs = sort_tuple(choices_outputs)

    output_type = SelectField(
        choices=choices_outputs,
        validators=[DataRequired()]
    )
    output_add = SubmitField(TRANSLATIONS['add']['title'])


class OutputMod(FlaskForm):
    output_id = StringField('Output ID', widget=widgets.HiddenInput())
    output_pin = HiddenField('Output Pin')
    name = StringField(TRANSLATIONS['name']['title'], validators=[DataRequired()])
    log_level_debug = BooleanField(TRANSLATIONS['log_level_debug']['title'])
    location = StringField(lazy_gettext('Location'))
    ftdi_location = StringField(TRANSLATIONS['ftdi_location']['title'])
    uart_location = StringField(TRANSLATIONS['uart_location']['title'])
    baud_rate = IntegerField(TRANSLATIONS['baud_rate']['title'])
    gpio_location = IntegerField(TRANSLATIONS['gpio_location']['title'], widget=NumberInput())
    i2c_location = StringField(TRANSLATIONS['i2c_location']['title'])
    i2c_bus = IntegerField(TRANSLATIONS['i2c_bus']['title'])
    output_mod = SubmitField(TRANSLATIONS['save']['title'])
    output_delete = SubmitField(TRANSLATIONS['delete']['title'])
    on_submit = SubmitField(lazy_gettext('Turn On'))
