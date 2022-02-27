# coding=utf-8
import math

# From
# https://github.com/hirschmann/pid-autotune


class Kettle(object):
    """
    A simulated brewing kettle.

    Args:
        diameter (float): Kettle diameter in centimeters.
        volume (float): Content volume in liters.
        temp (float): Initial content temperature in degree celsius.
        density (float): Content density.
    """
    # specific heat capacity of water: c = 4.182 kJ / kg * K
    SPECIFIC_HEAT_CAP_WATER = 4.182

    # thermal conductivity of steel: lambda = 15 W / m * K
    THERMAL_CONDUCTIVITY_STEEL = 15

    def __init__(self, diameter, volume, temp, density=1):
        self._mass = volume * density
        self._temp = temp
        radius = diameter / 2

        # height in cm
        height = (volume * 1000) / (math.pi * math.pow(radius, 2))

        # surface in m^2
        self._surface = (2 * math.pi * math.pow(radius, 2) + 2 * math.pi * radius * height) / 10000

    @property
    def temperature(self):
        """Get the content's temperature."""
        return self._temp

    def heat(self, power, duration, efficiency=0.98):
        """
        Heat the kettle's content.

        Args:
            power (float): The power in kW.
            duration (float): The duration in seconds.
            efficiency (float): The efficiency as number between 0 and 1.
        """
        self._temp += self._get_delta_t(power * efficiency, duration)
        return self._temp

    def cool(self, duration, ambient_temp, heat_loss_factor=1):
        """
        Make the content lose heat.

        Args:
            duration (float): The duration in seconds.
            ambient_temp (float): The ambient temperature in degree celsius.
            heat_loss_factor (float): Increase or decrease the heat loss by a
            specified factor.
        """
        # Q = k_w * A * (T_kettle - T_ambient)
        # P = Q / t
        power = ((Kettle.THERMAL_CONDUCTIVITY_STEEL * self._surface
                 * (self._temp - ambient_temp)) / duration)

        # W to kW
        power /= 1000
        self._temp -= self._get_delta_t(power, duration) * heat_loss_factor
        return self._temp

    def _get_delta_t(self, power, duration):
        # P = Q / t
        # Q = c * m * delta T
        # => delta(T) = (P * t) / (c * m)
        return (power * duration) / (Kettle.SPECIFIC_HEAT_CAP_WATER * self._mass)
