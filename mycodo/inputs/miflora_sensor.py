# coding=utf-8
import logging

from .base_input import AbstractInput
from .sensorutils import convert_units


class MifloraSensor(AbstractInput):
    """
    A sensor support class that measures the Miflora's electrical
    conductivity, moisture, temperature, and light.

    """

    def __init__(self, input_dev, testing=False):
        super(MifloraSensor, self).__init__()
        self.logger = logging.getLogger("mycodo.inputs.miflora")
        self._battery = None
        self._electrical_conductivity = None
        self._lux = None
        self._moisture = None
        self._temperature = None

        if not testing:
            from miflora.miflora_poller import MiFloraPoller
            from btlewrap import BluepyBackend
            self.logger = logging.getLogger(
                "mycodo.inputs.miflora_{id}".format(id=input_dev.id))
            self.location = input_dev.location
            self.bt_adapter = input_dev.bt_adapter
            self.convert_to_unit = input_dev.convert_to_unit
            self.poller = MiFloraPoller(self.location, BluepyBackend, adapter=self.bt_adapter)

    def __repr__(self):
        """  Representation of object """
        return "<{cls}(battery={bat})(electrical_conductivity={ec})(lux={lux})(moisture={moist})(temperature={temp})>".format(
            cls=type(self).__name__,
            bat="{0}".format(self._battery),
            ec="{0}".format(self._electrical_conductivity),
            lux="{0}".format(self._lux),
            moist="{0}".format(self._moisture),
            temp="{0:.2f}".format(self._temperature))

    def __str__(self):
        """ Return measurement information """
        return "Battery: {bat}, Electrical Conductitivty: {ec}. Light: {lux}, Moisture: {moist}, Temperature: {temp}".format(
            bat="{0}".format(self._battery),
            ec="{0}".format(self._electrical_conductivity),
            lux="{0}".format(self._lux),
            moist="{0}".format(self._moisture),
            temp="{0:.2f}".format(self._temperature))

    def __iter__(self):  # must return an iterator
        """ MifloraSensor iterates through live measurement readings """
        return self

    def next(self):
        """ Get next measurement reading """
        if self.read():  # raised an error
            raise StopIteration  # required
        return dict(battery=float('{0}'.format(self._battery)),
                    electrical_conductivity=float('{0}'.format(self._electrical_conductivity)),
                    lux=float('{0}'.format(self._lux)),
                    moisture=float('{0}'.format(self._moisture)),
                    temperature=float('{0:.2f}'.format(self._temperature)))

    @property
    def battery(self):
        """ Miflora battery measurement """
        if self._battery is None:  # update if needed
            self.read()
        return self._battery

    @property
    def electrical_conductivity(self):
        """ Miflora electrical conductivity measurement """
        if self._electrical_conductivity is None:  # update if needed
            self.read()
        return self._electrical_conductivity
    
    @property
    def lux(self):
        """ Miflora light measurement """
        if self._lux is None:  # update if needed
            self.read()
        return self._lux

    @property
    def moisture(self):
        """ Miflora moisture measurement """
        if self._moisture is None:  # update if needed
            self.read()
        return self._moisture

    @property
    def temperature(self):
        """ Miflora temperature in Celsius """
        if self._temperature is None:  # update if needed
            self.read()
        return self._temperature

    def get_measurement(self):
        """ Gets the light, moisture, and temperature """
        from miflora.miflora_poller import MI_CONDUCTIVITY
        from miflora.miflora_poller import MI_MOISTURE
        from miflora.miflora_poller import MI_LIGHT
        from miflora.miflora_poller import MI_TEMPERATURE
        from miflora.miflora_poller import MI_BATTERY

        self._electrical_conductivity = None
        self._lux = None
        self._moisture = None
        self._temperature = None

        battery = self.poller.parameter_value(MI_BATTERY)
        electrical_conductivity = self.poller.parameter_value(MI_CONDUCTIVITY)
        lux = self.poller.parameter_value(MI_LIGHT)
        moisture = self.poller.parameter_value(MI_MOISTURE)
        temperature = self.poller.parameter_value(MI_TEMPERATURE)
        temperature = convert_units(
            'temperature', 'celsius', self.convert_to_unit,
            temperature)
        return battery, electrical_conductivity, lux, moisture, temperature

    def read(self):
        """
        Takes a reading from the AM2315 and updates the self.dew_point,
        self._humidity, and self._temperature values

        :returns: None on success or 1 on error
        """
        try:
            (self._battery,
             self._electrical_conductivity,
             self._lux,
             self._moisture,
             self._temperature) = self.get_measurement()
            if self._electrical_conductivity is not None:
                return  # success - no errors
        except Exception as e:
            self.logger.exception(
                "{cls} raised an exception when taking a reading: "
                "{err}".format(cls=type(self).__name__, err=e))
        return 1
