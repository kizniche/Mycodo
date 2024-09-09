# -*- coding: utf-8 -*-
#
#  config_translations.py - Mycodo phrases for translation
#

from flask_babel import lazy_gettext


TRANSLATIONS = {
    # Words
    'actions': {
        'title': lazy_gettext('Actions')},
    'add': {
        'title': lazy_gettext('Add')},
    'activate': {
        'title': lazy_gettext('Activate')},
    'alert': {
        'title': lazy_gettext('Alert')},
    'average': {
        'title': lazy_gettext('Average')},
    'bt_adapter': {
        'title': lazy_gettext('Bluetooth Adapter (hci[X])')},
    'bt_location': {
        'title': lazy_gettext('Bluetooth MAC (XX:XX:XX:XX:XX:XX)')},
    'bus': {
        'title': lazy_gettext('Bus')},
    'calibration': {
        'title': lazy_gettext('Calibration')},
    'calculate': {
        'title': lazy_gettext('Calculate')},
    'camera': {
        'title': lazy_gettext('Camera')},
    'cancel': {
        'title': lazy_gettext('Cancel')},
    'clear': {
        'title': lazy_gettext('Clear')},
    'commands': {
        'title': lazy_gettext('Commands')},
    'completed': {
        'title': lazy_gettext('Completed')},
    'conditional': {
        'title': lazy_gettext('Conditional')},
    'controller': {
        'title': lazy_gettext('Controller')},
    'create': {
        'title': lazy_gettext('Create')},
    'custom': {
        'title': lazy_gettext('Custom')},
    'dashboard': {
        'title': lazy_gettext('Dashboard')},
    'data': {
        'title': lazy_gettext('Data')},
    'deactivate': {
        'title': lazy_gettext('Deactivate')},
    'default': {
        'title': lazy_gettext('Default')},
    'delete': {
        'title': lazy_gettext('Delete')},
    'device': {
        'title': lazy_gettext('Device')},
    'diagnostic': {
        'title': lazy_gettext('Diagnostic')},
    'display': {
        'title': lazy_gettext('Display')},
    'down': {
        'title': lazy_gettext('Down')},
    'duplicate': {
        'title': lazy_gettext('Duplicate')},
    'duration': {
        'title': lazy_gettext('Duration')},
    'edge': {
        'title': lazy_gettext('Edge')},
    'edit': {
        'title': lazy_gettext('Edit')},
    'email': {
        'title': lazy_gettext('E-Mail')},
    'energy_usage': {
        'title': lazy_gettext('Energy Usage')},
    'error': {
        'title': lazy_gettext('Error')},
    'export': {
        'title': lazy_gettext('Export')},
    'fail': {
        'title': lazy_gettext('Fail')},
    'function': {
        'title': lazy_gettext('Function')},
    'general': {
        'title': lazy_gettext('General')},
    'hold': {
        'title': lazy_gettext('Hold')},
    'i2c_bus': {
        'title': lazy_gettext('I2C Bus')},
    'i2c_location': {
        'title': lazy_gettext('I2C Address')},
    'indicator': {
        'title': lazy_gettext('Indicator')},
    'invert': {
        'title': lazy_gettext('Invert')},
    'import': {
        'title': lazy_gettext('Import')},
    'input': {
        'title': lazy_gettext('Input')},
    'invalid': {
        'title': lazy_gettext('Invalid')},
    'last': {
        'title': lazy_gettext('Last')},
    'lcd': {
        'title': lazy_gettext('LCD')},
    'line': {
        'title': lazy_gettext('Line')},
    'lock': {
        'title': lazy_gettext('Lock')},
    'login': {
        'title': lazy_gettext('Login')},
    'math': {
        'title': lazy_gettext('Math')},
    'measurement': {
        'title': lazy_gettext('Measurement')},
    'method': {
        'title': lazy_gettext('Method')},
    'modify': {
        'title': lazy_gettext('Modify')},
    'multiple': {
        'title': lazy_gettext('Multiple')},
    'none_available': {
        'title': lazy_gettext('None Available')},
    'note': {
        'title': lazy_gettext('Note')},
    'off': {
        'title': lazy_gettext('Off')},
    'on': {
        'title': lazy_gettext('On')},
    'output': {
        'title': lazy_gettext('Output')},
    'past': {
        'title': lazy_gettext('Past')},
    'password': {
        'title': lazy_gettext('Password')},
    'pause': {
        'title': lazy_gettext('Pause')},
    'pid': {
        'title': lazy_gettext('PID')},
    'pin': {
        'title': lazy_gettext('Pin')},
    'publish': {
        'title': lazy_gettext('Publish')},
    'pwm': {
        'title': lazy_gettext('PWM')},
    'ramp': {
        'title': lazy_gettext('Ramp')},
    'rename': {
        'title': lazy_gettext('Rename')},
    'reorder': {
        'title': lazy_gettext('Reorder')},
    'reset': {
        'title': lazy_gettext('Reset')},
    'resume': {
        'title': lazy_gettext('Resume')},
    'save': {
        'title': lazy_gettext('Save')},
    'save_order': {
        'title': lazy_gettext('Save Order')},
    'scale': {
        'title': lazy_gettext('Scale')},
    'scale_from_min': {
        'title': lazy_gettext('Unscaled Unit Min')},
    'scale_from_max': {
        'title': lazy_gettext('Unscaled Unit Max')},
    'scale_to_min': {
        'title': lazy_gettext('Rescaled Unit Min')},
    'scale_to_max': {
        'title': lazy_gettext('Rescaled Unit Max')},
    'select_one': {
        'title': lazy_gettext('Select One')},
    'sensitivity': {
        'title': lazy_gettext('Sensitivity')},
    'setpoint': {
        'title': lazy_gettext('Setpoint')},
    'settings': {
        'title': lazy_gettext('Settings')},
    'single': {
        'title': lazy_gettext('Single')},
    'stops': {
        'title': lazy_gettext('Stops')},
    'success': {
        'title': lazy_gettext('Success')},
    'sum': {
        'title': lazy_gettext('Sum')},
    'system': {
        'title': lazy_gettext('System')},
    'tag': {
        'title': lazy_gettext('Tag')},
    'text': {
        'title': lazy_gettext('Text')},
    'theme': {
        'title': lazy_gettext('Theme')},
    'timelapse': {
        'title': lazy_gettext('Time-lapse')},
    'timer': {
        'title': lazy_gettext('Timer')},
    'trigger': {
        'title': lazy_gettext('Trigger')},
    'unlock': {
        'title': lazy_gettext('Unlock')},
    'up': {
        'title': lazy_gettext('Up')},
    'user': {
        'title': lazy_gettext('User')},
    'value': {
        'title': lazy_gettext('Value')},
    'voltage': {
        'title': lazy_gettext('Voltage')},
    'volume': {
        'title': lazy_gettext('Volume')},
    'widget': {
        'title': lazy_gettext('Widget')},

    # Phrases
    '1wire_id': {
        'title': lazy_gettext('1-Wire Device ID'),
        'phrase': None},
    'adc_gain': {
        'title': lazy_gettext('Gain'),
        'phrase': None},
    'adc_resolution': {
        'title': lazy_gettext('Resolution'),
        'phrase': None},
    'adc_sample_speed': {
        'title': lazy_gettext('Sample Speed'),
        'phrase': None},
    'baud_rate': {
        'title': lazy_gettext('Baud Rate'),
        'phrase': lazy_gettext('The UART baud rate')},
    'cmd_command': {
        'title': lazy_gettext('Command'),
        'phrase': lazy_gettext('The command to be executed')},
    'convert_unit': {
        'title': None,
        'phrase': lazy_gettext('Select the unit of the measurement to be stored in the database')},
    'convert_to_measurement_unit': {
        'title': lazy_gettext('Convert to Unit'),
        'phrase': lazy_gettext('Convert the measurement to a different unit')},
    'copy_to_clipboard': {
        'title': None,
        'phrase': lazy_gettext('click to copy to the clipboard')},
    'deadline': {
        'title': "{} ({})".format(lazy_gettext('Deadline'), lazy_gettext('Seconds')),
        'phrase': lazy_gettext('Time to wait until failure')},
    'duty_cycle': {
        'title': lazy_gettext('Duty Cycle'),
        'phrase': lazy_gettext('Duty cycle for the PWM (percent, 0.0 - 100.0)')},
    'flow_rate': {
        'title': "{} ({})".format(lazy_gettext('Desired Flow Rate'), lazy_gettext('ml/min')),
        'phrase': None},
    'font_em_name': {
        'title': lazy_gettext('Name Font Size (em)'),
        'phrase': lazy_gettext('The font size of the Name text')},
    'force_command': {
        'title': lazy_gettext('Force Command'),
        'phrase': lazy_gettext('Always send the command if instructed, regardless of the current state')},
    'ftdi_location': {
        'title': lazy_gettext('FTDI Device'),
        'phrase': lazy_gettext('The FTDI device connected to the input/output/etc.')},
    'gpio_location': {
        'title': "{}: {}".format(lazy_gettext('Pin'), lazy_gettext('GPIO')),
        'phrase': lazy_gettext('GPIO (using BCM numbering)')},
    'flow_rate_method': {
        'title': lazy_gettext('Flow Rate Method'),
        'phrase': lazy_gettext('The flow rate to use when pumping a volume')},
    'host': {
        'title': lazy_gettext('Host'),
        'phrase': lazy_gettext('Host or IP address')},
    'interface': {
        'title': lazy_gettext('Interface'),
        'phrase': lazy_gettext('The interface used to communicate')},
    'linux_command_user': {
        'title': lazy_gettext('User'),
        'phrase': lazy_gettext('The user to execute the command')},
    'log_level_debug': {
        'title': lazy_gettext('Log Level: Debug'),
        'phrase': lazy_gettext('Show debug lines in the Daemon Log')},
    'max_age': {
        'title': "{} ({})".format(lazy_gettext('Max Age'), lazy_gettext('Seconds')),
        'phrase': lazy_gettext('The maximum allowable measurement age')},
    'measurement_units': {
        'title': lazy_gettext('Unit Measurement'),
        'phrase': lazy_gettext('Select a unit for the stored value')},
    'measurements_enabled': {
        'title': lazy_gettext('Measurements Enabled'),
        'phrase': lazy_gettext('The measurements to record')},
    'message_include_code': {
        'title': lazy_gettext('Message Includes Code'),
        'phrase': lazy_gettext('Include the code in the message variable')},
    'name': {
        'title': lazy_gettext('Name'),
        'phrase': lazy_gettext('A name to distinguish this from others')},
    'off_command': {
        'title': lazy_gettext('Off Command'),
        'phrase': lazy_gettext('Command to execute when the output is instructed to turn off')},
    'on_command': {
        'title': lazy_gettext('On Command'),
        'phrase': lazy_gettext('Command to execute when the output is instructed to turn on')},
    'on_state': {
        'title': lazy_gettext('On State'),
        'phrase': lazy_gettext('What state triggers the output to turn on? High or Low?')},
    'output_amount_duration': {
        'title': lazy_gettext('Duration'),
        'phrase': "{}: {}".format(lazy_gettext('Send to output controller'), lazy_gettext('Duration'))},
    'output_amount_value': {
        'title': lazy_gettext('Value'),
        'phrase': "{}: {}".format(lazy_gettext('Send to output controller'), lazy_gettext('Value'))},
    'output_amount_voltage': {
        'title': lazy_gettext('Voltage'),
        'phrase': "{}: {}".format(lazy_gettext('Send to output controller'), lazy_gettext('Voltage'))},
    'output_amount_volume': {
        'title': lazy_gettext('Volume'),
        'phrase': "{}: {}".format(lazy_gettext('Send to output controller'), lazy_gettext('Volume'))},
    'period': {
        'title': "{} ({})".format(lazy_gettext('Period'), lazy_gettext('Seconds')),
        'phrase': lazy_gettext('The duration between measurements or actions')},
    'pin_clock': {
        'title': "{}: {}".format(lazy_gettext('Pin'), lazy_gettext('Clock')),
        'phrase': "{}: {}: {}".format(lazy_gettext('GPIO (using BCM numbering)'), lazy_gettext('Pin'), lazy_gettext('Clock'))},
    'pin_cs': {
        'title': "{}: {}".format(lazy_gettext('Pin'), lazy_gettext('Cable Select')),
        'phrase': "{}: {}: {}".format(lazy_gettext('GPIO (using BCM numbering)'), lazy_gettext('Pin'), lazy_gettext('Cable Select'))},
    'pin_miso': {
        'title': "{}: {}".format(lazy_gettext('Pin'), lazy_gettext('MISO')),
        'phrase': "{}: {}: {}".format(lazy_gettext('GPIO (using BCM numbering)'), lazy_gettext('Pin'), lazy_gettext('MISO'))},
    'pin_mosi': {
        'title': "{}: {}".format(lazy_gettext('Pin'), lazy_gettext('MOSI')),
        'phrase': "{}: {}: {}".format(lazy_gettext('GPIO (using BCM numbering)'), lazy_gettext('Pin'), lazy_gettext('MOSI'))},
    'port': {
        'title': lazy_gettext('Port'),
        'phrase': lazy_gettext('Host port number')},
    'pre_output_duration': {
        'title': "{} ({})".format(lazy_gettext('Pre Out Duration'), lazy_gettext('Seconds')),
        'phrase': lazy_gettext(
            'If a Pre Output is selected, set the duration to turn '
            'the Pre Output on for before every measurement is acquired.')},
    'pre_output_during_measure': {
        'title': lazy_gettext('Pre During Measure'),
        'phrase': lazy_gettext('Check to turn the output off after (opposed to before) the measurement is complete')},
    'pre_output_id': {
        'title': lazy_gettext('Pre Output'),
        'phrase': lazy_gettext('Turn the selected output on before taking every measurement')},
    'pwm_command': {
        'title': lazy_gettext('PWM Command'),
        'phrase': lazy_gettext('Command to execute to set the PWM duty cycle (%)')},
    'pwm_hertz': {
        'title': "{} ({})".format(lazy_gettext('Frequency'), lazy_gettext('Hertz')),
        'phrase': lazy_gettext('The Hertz to output the PWM signal (0 - 70,000)')},
    'pwm_library': {
        'title': lazy_gettext('Library'),
        'phrase': lazy_gettext('Which method to produce the PWM signal (hardware pins can produce higher frequencies)')},
    'ref_ohm': {
        'title': lazy_gettext('Reference Resistance'),
        'phrase': "{} ({})".format(lazy_gettext('Reference Resistance'), lazy_gettext('Ohm'))},
    'refresh_duration': {
        'title': "{} ({})".format(lazy_gettext('Refresh'), lazy_gettext('Seconds')),
        'phrase': lazy_gettext('Duration to wait between acquiring new measurements')},
    'resolution': {
        'title': lazy_gettext('Resolution'),
        'phrase': lazy_gettext('Measurement resolution')},
    'resolution_2': {
        'title': lazy_gettext('Resolution'),
        'phrase': lazy_gettext('Measurement resolution')},
    'rpm_pulses_per_rev': {
        'title': lazy_gettext('Pulses Per Rev'),
        'phrase': lazy_gettext('The number of pulses per revolution to calculate revolutions per minute (RPM)')},
    'sample_time': {
        'title': lazy_gettext('Sample Time'),
        'phrase': lazy_gettext('The duration of time to sample')},
    'select_measurement_unit': {
        'title': lazy_gettext('Measurement Unit'),
        'phrase': lazy_gettext('Select the measurement and unit to store this measurement in the database')},
    'setpoint_tracking_type': {
        'title': lazy_gettext('Setpoint Tracking Type'),
        'phrase': lazy_gettext('Select the type of setpoint tracking')},
    'sht_voltage': {
        'title': lazy_gettext('Voltage'),
        'phrase': lazy_gettext('The input voltage to the sensor')},
    'shutdown_value': {
        'title': lazy_gettext('Shutdown Value'),
        'phrase': lazy_gettext('The output value to set when Mycodo shuts down')},
    'start_offset': {
        'title': "{} ({})".format(lazy_gettext('Start Offset'), lazy_gettext('Seconds')),
        'phrase': lazy_gettext('The duration to wait before the first operation')},
    'startup_value': {
        'title': lazy_gettext('Startup Value'),
        'phrase': lazy_gettext('The output value to set when Mycodo starts up')},
    'state_shutdown': {
        'title': lazy_gettext('Shutdown State'),
        'phrase': lazy_gettext('When Mycodo shuts down, set the output state')},
    'state_startup': {
        'title': lazy_gettext('Startup State'),
        'phrase': lazy_gettext('When Mycodo starts, set the output state')},
    'switch_edge': {
        'title': lazy_gettext('Edge'),
        'phrase': lazy_gettext('Edge detection: low to high (rising), high to low (falling), or both')},
    'switch_bouncetime': {
        'title': "{} ({})".format(lazy_gettext('Bounce Time'), lazy_gettext('Milliseconds')),
        'phrase': lazy_gettext('The amount of time to bounce the input signal')},
    'switch_reset_period': {
        'title': "{} ({})".format(lazy_gettext('Reset Period'), lazy_gettext('Seconds')),
        'phrase': lazy_gettext('Wait a period of time after the first edge detection to begin detecting again')},
    'thermocouple_type': {
        'title': lazy_gettext('RTD Probe Type'),
        'phrase': lazy_gettext('The type of thermocouple connected')},
    'times_check': {
        'title': lazy_gettext('Times to Check'),
        'phrase': lazy_gettext('Number of times to check')},
    'trigger_functions_at_start': {
        'title': lazy_gettext('Trigger at Startup'),
        'phrase': lazy_gettext('Whether or not to trigger Functions when Mycodo starts')},
    'uart_location': {
        'title': lazy_gettext('UART Device'),
        'phrase': lazy_gettext('The UART device location (e.g. /dev/ttyUSB1)')},
    'unique_id': {
        'title': lazy_gettext('Unique ID'),
        'phrase': lazy_gettext('A unique ID to distinguish this from others')},
    'use_pylint': {
        'title': lazy_gettext('Analyze Python with Pylint'),
        'phrase': lazy_gettext('Analyze the Python code with pylint and return the output')},
    'weighting': {
        'title': lazy_gettext('Weighting'),
        'phrase': lazy_gettext(
            'The weighting of the previous measurement on the current measurement. '
            'Range: 0.0 - 1.0. Used for smoothing measurements. 0.0 means no weighting.')},

    # PID
    'raise_always_min_pwm': {
        'title': "{} ({})".format(lazy_gettext('Always Min'), lazy_gettext('Raise')),
        'phrase': lazy_gettext('Never allow duty cycle to go below Min.')},
    'lower_always_min_pwm': {
        'title': "{} ({})".format(lazy_gettext('Always Min'), lazy_gettext('Lower')),
        'phrase': lazy_gettext('Never allow duty cycle to go below Min.')},

    # '': {
    #     'title': lazy_gettext(''),
    #     'phrase': lazy_gettext('')},
}
