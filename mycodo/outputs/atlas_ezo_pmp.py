# coding=utf-8
#
# atlas_ezo_pmp.py - Output for Atlas Scientific EZO Pump
#
import datetime
from flask_babel import lazy_gettext
from mycodo.outputs.base_output import AbstractOutput
from mycodo.utils.influx import add_measurements_influxdb
from mycodo.utils.database import db_retrieve_table_daemon
from mycodo.databases.models import DeviceMeasurements
from mycodo.utils.influx import read_last_influxdb

# Measurements
measurements_dict = {
    0: {
        'measurement': 'volume',
        'unit': 'ml'
    },
    1: {
        'measurement': 'duration_time',
        'unit': 'minute'
    }
}

# Output information
OUTPUT_INFORMATION = {
    'output_name_unique': 'atlas_ezo_pmp',
    'output_name': lazy_gettext('Atlas Scientific Pump'),
    'measurements_dict': measurements_dict,

    'on_state_internally_handled': False,
    'output_types': ['volume'],

    'message': 'Information about this output.',

    'dependencies_module': [],
    'interfaces': ['I2C', 'UART', 'FTDI'],
}


class OutputModule(AbstractOutput):
    """
    An output support class that operates an output
    """
    def __init__(self, output, testing=False):
        super(OutputModule, self).__init__(output, testing=testing, name=__name__)

        if not testing:
            self.output_unique_id = output.unique_id
            self.output_interface = output.interface
            self.output_location = output.location
            self.output_i2c_bus = output.i2c_bus
            self.output_baud_rate = output.baud_rate
            self.output_mode = output.output_mode
            self.output_flow_rate = output.flow_rate

    def output_switch(self, state, amount=None, duty_cycle=None):
        volume_ml = amount
        if state == 'on' and volume_ml > 0:
            if self.output_mode == 'fastest_flow_rate':
                minutes_to_run = volume_ml * 105
                write_cmd = 'D,{ml:.2f}'.format(ml=volume_ml)
            elif self.output_mode == 'specify_flow_rate':
                # Calculate command, given flow rate
                minutes_to_run = volume_ml / self.output_flow_rate
                write_cmd = 'D,{ml:.2f},{min:.2f}'.format(
                    ml=volume_ml, min=minutes_to_run)
            else:
                msg = "Invalid output_mode: '{}'".format(
                    self.output_mode)
                self.logger.error(msg)
                return 1, msg

            self.logger.debug("EZO-PMP command: {}".format(write_cmd))
            self.atlas_command.write(write_cmd)

            msg = 'pump turned on'

            measurement_dict = {
                0: {
                    'measurement': 'volume',
                    'unit': 'ml',
                    'value': volume_ml
                },
                1: {
                    'measurement': 'time',
                    'unit': 'minute',
                    'value': minutes_to_run
                }
            }
            add_measurements_influxdb(
                self.output_unique_id, measurement_dict)

        elif state == 'off' or volume_ml <= 0:
            write_cmd = 'X'
            self.logger.debug("EZO-PMP command: {}".format(write_cmd))
            self.atlas_command.write(write_cmd)
            measurement_dict = {
                0: {
                    'measurement': 'volume',
                    'unit': 'ml',
                    'value': 0
                },
                1: {
                    'measurement': 'time',
                    'unit': 'minute',
                    'value': 0
                }
            }
            add_measurements_influxdb(
                self.output_unique_id, measurement_dict)

        else:
            msg = "Invalid parameters: " \
                  "State: {state}, " \
                  "Volume: {vol}, " \
                  "Flow Rate: {fr}".format(
                state=state,
                vol=volume_ml,
                fr=self.output_flow_rate)
            self.logger.error(msg)
            return 1, msg

    def is_on(self):
        device_measurements = db_retrieve_table_daemon(
            DeviceMeasurements).filter(
            DeviceMeasurements.device_id == self.output_unique_id)
        for each_dev_meas in device_measurements:
            if each_dev_meas.unit == 'minute':
                last_measurement = read_last_influxdb(
                    self.output_unique_id,
                    each_dev_meas.unit,
                    each_dev_meas.channel,
                    measure=each_dev_meas.measurement, )
                if last_measurement:
                    datetime_ts = datetime.datetime.strptime(
                        last_measurement[0][:-7], '%Y-%m-%dT%H:%M:%S.%f')
                    minutes_on = last_measurement[1]
                    ts_pmp_off = datetime_ts + datetime.timedelta(minutes=minutes_on)
                    now = datetime.datetime.utcnow()
                    is_on = bool(now < ts_pmp_off)
                    if is_on:
                        return True

    def is_setup(self):
        if self.atlas_command:
            return True
        return False

    def setup_output(self):
        if self.output_interface == 'FTDI':
            from mycodo.devices.atlas_scientific_ftdi import AtlasScientificFTDI
            self.atlas_command = AtlasScientificFTDI(
                self.output_location)
        elif self.output_interface == 'I2C':
            from mycodo.devices.atlas_scientific_i2c import AtlasScientificI2C
            self.atlas_command = AtlasScientificI2C(
                i2c_address=int(str(self.output_location), 16),
                i2c_bus=self.output_i2c_bus)
        elif self.output_interface == 'UART':
            from mycodo.devices.atlas_scientific_uart import AtlasScientificUART
            self.atlas_command = AtlasScientificUART(
                self.output_location,
                baudrate=self.output_baud_rate)
