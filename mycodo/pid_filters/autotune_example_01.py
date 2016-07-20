#!/usr/bin/python
# coding=utf-8
#
# PID filter test
# Simulate PID controller and calucluate new Kp, Ki, and Kd each period

from autotune import PID_Filter_simple1

class Filter_Values(object):
    pass

variables = Filter_Values()
variables.setpoint = 30
variables.Kp = 1.0
variables.Ki = 0.1
variables.Kd = 0.01
variables.error = 10

# Initialize PID filter class with variables
pid_filter = PID_Filter_simple1(variables)

# Loop to simulate PID controller
for _ in range(20):
    # Calculate new new Kp, Ki, Kd, and output of them (sum of parts)
    temp_Kp, temp_Ki, temp_Kd, output = pid_filter.autotune_simple(
        variables.Kp, variables.Ki, variables.Kd, variables.error)

    # Print 
    print("Values in/out:  Kp: {:.2f}/{:.2f}, Ki: {:.2f}/{:.2f}, "
          "Kd: {:.2f}/{:.2f}, setpoint: {:.2f}, error: {:.2f}, "
          "output: {:.2f}".format(
            variables.Kp, temp_Kp,
            variables.Ki, temp_Ki,
            variables.Kd, temp_Kd,
            variables.setpoint, variables.error, output))

    variables.Kp = temp_Kp
    variables.Ki = temp_Ki
    variables.Kd = temp_Kd

    # How much to change the error each loop to simulate change
    variables.error *= 0.6
