Supported Functions are listed below.

## Built-In Functions

### Average (Last, Multiple)


This function acquires the last measurement of those that are selected, averages them, then stores the resulting value as the selected measurement and unit.

### Average (Past, Single)


This function acquires the past measurements (within Max Age) for the selected measurement, averages them, then stores the resulting value as the selected measurement and unit.

### Bang-Bang Hysteretic


A simple bang-bang control for controlling one output from one input. Select an input, an output, enter a setpoint and a hysteresis, and select a direction. The output will turn on when the input is below setpoint-hysteresis and turn off when the input is above setpoint+hysteresis. This is the behavior when Raise is selected, such as when heating. Lower direction has the opposite behavior - it will try to turn the output on in order to drive the input lower.

### Difference


This function acquires 2 measurements, calculates the difference, and stores the resulting value as the selected measurement and unit.

### Equation (Multi-Measure)


This function acquires two measurements and uses them within a user-set equation and stores the resulting value as the selected measurement and unit.

### Equation (Single-Measure)


This function acquires a measurement and uses it within a user-set equation and stores the resulting value as the selected measurement and unit.

### Humidity (Wet/Dry-Bulb)


This function calculates the humidity based on wet and dry bulb temperature measurements.

### PID Autotune


This function will attempt to perform a PID controller autotune. That is, an output will be powered and the response measured from a sensor several times to calculate the P, I, and D gains. Updates about the operation will be sent to the Daemon log. If the autotune successfully completes, a summary will be sent to the Daemon log as well. Currently, only raising a Measurement is supported, but lowering should be possible with some modification to the function controller code. It is recommended to create a graph on a dashboard with the Measurement and Output to monitor that the Output is successfully raising the Measurement beyond the Setpoint. Note: Autotune is an experimental feature, it is not well-developed, and it has a high likelihood of failing to generate PID gains. Do not rely on it for accurately tuning your PID controller.

### Redundancy


This function stores the first available measurement. This is useful if you have multiple sensors that you want to serve as backups in case one stops working, you can set them up in the order of importance. This function will check if a measurement exits, starting with the first measurement. If it doesn't, the next is checked, until a measurement is found. Once a measurement is found, it is stored in the database with the user-set measurement and unit. The output of this function can be used as an input throughout Mycodo. If you need more than 3 measurements to be checked, you can string multiple Redundancy Functions by creating a second Function and setting the first Function's output as the second Function's input.

### Statistics (Last, Multiple)


This function acquires multiple measurements, calculates statistics, and stores the resulting values as the selected unit.

### Statistics (Past, Single)


This function acquires multiple values from a single measurement, calculates statistics, and stores the resulting values as the selected unit.

### Sum (Last, Multiple)


This function acquires the last measurement of those that are selected, sums them, then stores the resulting value as the selected measurement and unit.

### Sum (Past, Single)


This function acquires the past measurements (within Max Age) for the selected measurement, sums them, then stores the resulting value as the selected measurement and unit.

### Vapor Pressure Deficit


This function calculates the vapor pressure deficit based on leaf temperature and humidity.

### Verification


This function acquires 2 measurements, calculates the difference, and if the difference is not larger than the set threshold, the Measurement A value is stored. This enables verifying one sensor's measurement with another sensor's measurement. Only when they are both in agreement is a measurement stored. This stored measurement can be used in functions such as Conditional Statements that will notify the user if no measurement is avilable to indicate there may be an issue with a sensor.

