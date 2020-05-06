# coding=utf-8
#
# pid_controller_default.py - Default PID controller for Mycodo


class PIDControl(object):
    """
    The default proportional-integral-derivative (PID) controller used by Mycodo
    """

    def __init__(self, logger, setpoint, kp, ki, kd, direction, band,
                 integrator_min=-500, integrator_max=500):
        self.logger = logger

        self.setpoint = setpoint
        self.Kp = kp
        self.Ki = ki
        self.Kd = kd
        self.integrator_min = integrator_min
        self.integrator_max = integrator_max
        self.direction = direction
        self.band = band

        self.setpoint_band = None
        self.control_variable = 0.0
        self.derivator = 0.0
        self.integrator = 0.0
        self.error = 0.0
        self.P_value = None
        self.I_value = None
        self.D_value = None
        self.first_start = True

        # Hysteresis options
        self.allow_raising = False
        self.allow_lowering = False

    def update_pid_output(self, current_value):
        """
        Calculate PID output value from reference input and feedback

        :return: Manipulated, or control, variable. This is the PID output.
        :rtype: float

        :param current_value: The input, or process, variable (the actual
            measured condition by the input)
        :type current_value: float
        """
        # Determine if hysteresis is enabled and if the PID should be applied
        setpoint = self.check_hysteresis(current_value)

        if setpoint != self.setpoint:
            self.setpoint_band = setpoint
        else:
            self.setpoint_band = None

        if setpoint is None:
            # Prevent PID variables form being manipulated and
            # restrict PID from operating.
            return 0

        self.error = setpoint - current_value

        # Calculate P-value
        self.P_value = self.Kp * self.error

        # Calculate I-value
        self.integrator += self.error

        # First method for managing integrator
        if self.integrator > self.integrator_max:
            self.integrator = self.integrator_max
        elif self.integrator < self.integrator_min:
            self.integrator = self.integrator_min

        # Second method for regulating integrator
        # if self.period is not None:
        #     if self.integrator * self.Ki > self.period:
        #         self.integrator = self.period / self.Ki
        #     elif self.integrator * self.Ki < -self.period:
        #         self.integrator = -self.period / self.Ki

        self.I_value = self.integrator * self.Ki

        # Prevent large initial D-value
        if self.first_start:
            self.derivator = self.error
            self.first_start = False

        # Calculate D-value
        self.D_value = self.Kd * (self.error - self.derivator)
        self.derivator = self.error

        # Produce output form P, I, and D values
        pid_value = self.P_value + self.I_value + self.D_value

        self.logger.debug(
            "PID: Input: {inp}, "
            "Output: P: {p}, I: {i}, D: {d}, Out: {o}".format(
                inp=current_value, p=self.P_value, i=self.I_value, d=self.D_value, o=pid_value))

        self.control_variable = pid_value

    def check_hysteresis(self, measure):
        """
        Determine if hysteresis is enabled and if the PID should be applied

        :return: float if the setpoint if the PID should be applied, None to
            restrict the PID
        :rtype: float or None

        :param measure: The PID input (or process) variable
        :type measure: float
        """
        if self.band == 0:
            # If band is disabled, return setpoint
            self.setpoint_band = None
            return self.setpoint

        band_min = self.setpoint - self.band
        band_max = self.setpoint + self.band

        if self.direction == 'raise':
            if (measure < band_min or
                    (band_min < measure < band_max and self.allow_raising)):
                self.allow_raising = True
                setpoint = band_max  # New setpoint
                return setpoint  # Apply the PID
            elif measure > band_max:
                self.allow_raising = False
            return None  # Restrict the PID

        elif self.direction == 'lower':
            if (measure > band_max or
                    (band_min < measure < band_max and self.allow_lowering)):
                self.allow_lowering = True
                setpoint = band_min  # New setpoint
                return setpoint  # Apply the PID
            elif measure < band_min:
                self.allow_lowering = False
            return None  # Restrict the PID

        elif self.direction == 'both':
            if measure < band_min:
                setpoint = band_min  # New setpoint
                if not self.allow_raising:
                    # Reset integrator and derivator upon direction switch
                    self.integrator = 0.0
                    self.derivator = 0.0
                    self.allow_raising = True
                    self.allow_lowering = False
            elif measure > band_max:
                setpoint = band_max  # New setpoint
                if not self.allow_lowering:
                    # Reset integrator and derivator upon direction switch
                    self.integrator = 0.0
                    self.derivator = 0.0
                    self.allow_raising = False
                    self.allow_lowering = True
            else:
                return None  # Restrict the PID
            return setpoint  # Apply the PID
