---
layout: default
---

Mycodo is open source software for the Raspberry Pi that couples input and output devices in interesting ways to sense and manipulate the environment.

## Features

*   **Inputs** such as sensors, GPIO pin states, analog-to-digital converters, custom user created single-file input modules
*   **Outputs** such as switching GPIO High/Low, pulse-width-modulation, LCD display, Python code, Linux commands
*   **Dashboard** with configurable widgets, such as interactive graphs, gauges, output state indicators, text measurements
*   **Proportional Integral Derivative (PID) controllers** for environmental condition regulation
*   **Setpoint Tracking** for changing environmental conditions over time (reptile terrarium, reflow oven, thermal cycler, sous-vide, etc.)
*   **Conditional Statements** for reacting to input measurements, manipulating outputs, and executing actions
*   **Timers** (daily, duration, sunrise/sunset, etc.) to trigger actions at periodic intervals
*   **Notifications** to alert via email when measurements reach or exceed user-specified thresholds
*   **Energy Usage Statistics** to calculate and track power consumption and cost over time
*   **Notes** to keep track of events, alerts, and other important points in time
*   **Camera Feed** for remote live stream, image capture, or time-lapse photography 

## Screenshots

![Mycodo Dashboard](http://kylegabriel.com/projects/wp-content/uploads/sites/3/2016/05/Mycodo-3.6.0-tango-Graph-2016-05-21-11-15-26.png)

## Get Mycodo

### Prerequisites

*   [Raspberry Pi](https://www.raspberrypi.org/) single-board computer (any version: Zero, 1, 2, 3, or 4)
*   [Raspbian OS](https://www.raspberrypi.org/downloads/raspbian/) flashed to a micro SD card
*   An active internet connection

### Install

Once you have the Raspberry Pi booted into Raspbian with an internet connection, run the following command in a terminal to install Mycodo:

```bash
curl -L https://raw.githubusercontent.com/kizniche/Mycodo/master/install/install | bash
```

If the install is successful, open a web browser to the Raspberry Pi's IP address and you will be greeted with a screen to create an Admin user and password.

```
https://127.0.0.1/
```

## Support

*   [Mycodo Manual](https://github.com/kizniche/Mycodo/blob/master/mycodo-manual.rst)
*   [Mycodo Support](https://play.google.com/store/apps/details?id=com.mycodo.mycododocs) (Android App)
