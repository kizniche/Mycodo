description: Documentation (Wiki) for Mycodo, an environmental monitoring and regulation system.

## Mycodo Environmental Monitoring and Regulation System

Mycodo is open source software for the Raspberry Pi that couples inputs and outputs in interesting ways to sense and manipulate the environment.

### Features

*   **[Inputs](https://github.com/kizniche/Mycodo/blob/master/mycodo-manual.rst#input)** that record measurements from sensors, GPIO pin states, analog-to-digital converters, etc. (or create your own [Custom Inputs](#custom-inputs)).
*   **[Outputs](https://github.com/kizniche/Mycodo/blob/master/mycodo-manual.rst#output)** that perform actions such as switching GPIO pins high/low, generating PWM signals, executing shell scripts and Python code, etc. (or create your own [Custom Outputs](#custom-outputs)).
*   **[Functions](https://github.com/kizniche/Mycodo/blob/master/mycodo-manual.rst#functions)** that perform tasks, such as coupling Inputs and Outputs in interesting ways, such as [PID controllers](https://github.com/kizniche/Mycodo/blob/master/mycodo-manual.rst#pid-controller), [Conditional Controllers](https://github.com/kizniche/Mycodo/blob/master/mycodo-manual.rst#conditional), [Trigger Controllers](https://github.com/kizniche/Mycodo/blob/master/mycodo-manual.rst#trigger), to name a few (or create your own [Custom Controllers](https://github.com/kizniche/Mycodo/blob/master/mycodo-manual.rst#custom-controllers)).
*   **[Web Interface](https://github.com/kizniche/Mycodo/blob/master/mycodo-manual.rst#web-interface)** for securely accessing Mycodo using a web browser on your local network or anywhere in the world with an internet connection, to view and configure the system, which includes several light and dark themes to suit your style.
*   **[Dashboards](https://github.com/kizniche/Mycodo/blob/master/mycodo-manual.rst#dashboard)** that display configurable widgets, including interactive live and historical graphs, gauges, output state indicators, text measurements, among others.
*   **[Alert Notifications](https://github.com/kizniche/Mycodo/blob/master/mycodo-manual.rst#alerts)** to send emails when measurements reach or exceed user-specified thresholds, important for knowing immediately when issues arise.
*   **[Setpoint Tracking](https://github.com/kizniche/Mycodo/blob/master/mycodo-manual.rst#methods)** for changing a PID controller setpoint over time, for use with things like terrariums, reflow ovens, thermal cyclers, sous-vide cooking, and more.
*   **[Notes](https://github.com/kizniche/Mycodo/blob/master/mycodo-manual.rst#notes)** to record events, alerts, and other important points in time, which can be overlaid on graphs to visualize events with your measurement data.
*   **[Cameras](https://github.com/kizniche/Mycodo/blob/master/mycodo-manual.rst#camera)** for remote live streaming, image capture, and time-lapse photography.
*   **[Energy Usage Measurement](https://github.com/kizniche/Mycodo/blob/master/mycodo-manual.rst#energy-usage)** for calculating and tracking power consumption and cost over time.
*   **[Upgrade System](https://github.com/kizniche/Mycodo/blob/master/mycodo-manual.rst#upgrading)** to easily upgrade the Mycodo system to the latest release to get the newest features or restore to a previously-backed up version.
*   **[Translations](https://github.com/kizniche/Mycodo/blob/master/mycodo-manual.rst#translations)** that enable the web interface to be presented in different [Languages](https://github.com/kizniche/Mycodo#features).


### Uses

See the [README](https://github.com/kizniche/Mycodo#uses) for more information.

### Prerequisites

*   [Raspberry Pi](https://www.raspberrypi.org/) single-board computer (any version: Zero, 1, 2, 3, or 4)
*   [Raspbian OS](https://www.raspberrypi.org/downloads/raspbian/) flashed to a micro SD card
*   An active internet connection

### Install

Once you have the Raspberry Pi booted into Raspbian with an internet connection, run the following command in a terminal to initiate the Mycodo install:

```bash
curl -L https://kizniche.github.io/Mycodo/install | bash
```

If the install is successful, open a web browser to the Raspberry Pi's IP address and you will be greeted with a screen to create an Admin user and password.

```
https://127.0.0.1/
```

### Support

*   [Mycodo on GitHub](https://github.com/kizniche/Mycodo)
*   [Mycodo Manual](https://github.com/kizniche/Mycodo/blob/master/mycodo-manual.rst)
*   [Mycodo API](https://kizniche.github.io/Mycodo/mycodo-api.html)
*   [Mycodo Support](https://play.google.com/store/apps/details?id=com.mycodo.mycododocs) (Android App)
