## Built-In Widgets

### Activate/Deactivate Controller


Activate/Deactivate a Controller (Inputs and Functions). For manipulating a PID Controller, use the PID Controller Widget.

### Camera


Displays a camera image or stream.

### Function Status


Displays the status of a Function (if supported).

### Gauge (Angular) [Highcharts]

- Libraries: Highcharts
- Dependencies: highstock-9.1.2.js, highcharts-more-9.1.2.js

Displays an angular gauge. Be sure to set the Maximum option to the last Stop High value for the gauge to display properly.

### Gauge (Solid) [Highcharts]

- Libraries: Highcharts
- Dependencies: highstock-9.1.2.js, highcharts-more-9.1.2.js, solid-gauge-9.1.2.js

Displays a solid gauge. Be sure to set the Maximum option to the last Stop value for the gauge to display properly.

### Graph (Synchronous) [Highstock]

- Libraries: Highstock
- Dependencies: highstock-9.1.2.js, highcharts-more-9.1.2.js, data-9.1.2.js, exporting-9.1.2.js, export-data-9.1.2.js, offline-exporting-9.1.2.js

Displays a synchronous graph (all data is downloaded for the selected period on the x-axis).

### Indicator


Displays a red or green circular image based on a measurement value. Useful for showing if an Output is on or off.

### Measurement (1 Value)


Displays a measurement value and timestamp.

### Measurement (2 Values)


Displays two measurement values and timestamps.

### Output (PWM Slider)


Displays and allows control of a PWM output using a slider.

### Output Control (Channel)


Displays and allows control of an output channel. All output options and measurements for the selected channel will be displayed. E.g. pumps will have seconds on and volume as measurements, and can be turned on for a duration (Seconds) or amount (Volume). If NO DATA or TOO OLD is displayed, the Max Age is not sufficiently long enough to find a current measurement.

### PID Controller


Displays and allows control of a PID Controller.

### Python Code


Executes Python code and displays the output within the widget.

### Spacer


A simple widget to use as a spacer, which includes the ability to set text in its contents.

