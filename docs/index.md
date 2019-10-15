---
layout: default
---

Mycodo is open source software for the Raspberry Pi that couples inputs and outputs in interesting ways to sense and manipulate the environment.

## Features

*   **[Inputs](https://github.com/kizniche/Mycodo/blob/master/mycodo-manual.rst#data)** such as sensors, GPIO pin states, analog-to-digital converters, custom user created single-file input modules
*   **[Outputs](https://github.com/kizniche/Mycodo/blob/master/mycodo-manual.rst#output)** such as switching GPIO High/Low, pulse-width-modulation, LCD display, Python code, Linux commands
*   **[Dashboard](https://github.com/kizniche/Mycodo/blob/master/mycodo-manual.rst#dashboard)** with configurable widgets, such as interactive graphs, gauges, output state indicators, text measurements
*   **[Proportional Integral Derivative (PID) controllers](https://github.com/kizniche/Mycodo/blob/master/mycodo-manual.rst#pid-controller)** for environmental condition regulation
*   **[Setpoint Tracking](https://github.com/kizniche/Mycodo/blob/master/mycodo-manual.rst#methods)** for changing environmental conditions over time (reptile terrarium, reflow oven, thermal cycler, sous-vide, etc.)
*   **[Conditional Statements](https://github.com/kizniche/Mycodo/blob/master/mycodo-manual.rst#conditional)** for reacting to input measurements, manipulating outputs, and executing actions
*   **[Timers](https://github.com/kizniche/Mycodo/blob/master/mycodo-manual.rst#trigger)** (daily, duration, sunrise/sunset, etc.) to trigger actions at periodic intervals
*   **[Notifications](https://github.com/kizniche/Mycodo/blob/master/mycodo-manual.rst#alert-settings)** to alert via email when measurements reach or exceed user-specified thresholds
*   **[Notes](https://github.com/kizniche/Mycodo/blob/master/mycodo-manual.rst#notes)** to keep track of events, alerts, and other important points in time
*   **[Camera Feed](https://github.com/kizniche/Mycodo/blob/master/mycodo-manual.rst#camera)** for remote live stream, image capture, or time-lapse photography 
*   **[Energy Usage Statistics](https://github.com/kizniche/Mycodo/blob/master/mycodo-manual.rst#energy-usage)** to calculate and track power consumption and cost over time

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

*   [Mycodo on GitHub](https://github.com/kizniche/Mycodo)
*   [Mycodo Manual](https://github.com/kizniche/Mycodo/blob/master/mycodo-manual.rst)
*   [Mycodo Support](https://play.google.com/store/apps/details?id=com.mycodo.mycododocs) (Android App)

## Screenshots

![Mycodo 5.7.2 Dashboard](http://kylegabriel.com/screenshots/screenshot_mycodo_dashbaord_v5.7.2.png)

---

![Mycodo 3.6.0 Dashboard](http://kylegabriel.com/screenshots/screenshot_mycodo_dashboard_v3.6.0.png)

---

![Mycodo 5.2.0 Dashboard](http://kylegabriel.com/screenshots/screenshot_mycodo_dashboard_v5.2.0.png)

---

![Mycodo 5.5.0 Data Page](http://kylegabriel.com/screenshots/screenshot_mycodo_data_v5.5.0.png)

---

![Live Page](http://kylegabriel.com/projects/wp-content/uploads/sites/3/2017/03/screenshot-192.168.0.7-2017-03-01-18-17-14-live.png)
