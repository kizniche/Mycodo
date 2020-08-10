description: Documentation for Mycodo, an open source environmental monitoring and regulation system.

## Mycodo Environmental Monitoring and Regulation System

Mycodo is open source software for the [Raspberry Pi](https://en.wikipedia.org/wiki/Raspberry_Pi) that couples inputs and outputs in interesting ways to sense and manipulate the environment.

### Features

*   **[Inputs](Inputs.md)** that record measurements from sensors, GPIO pin states, analog-to-digital converters, and more (or create your own [Custom Inputs](Inputs.md#custom-inputs)).
*   **[Outputs](Outputs.md)** that perform actions such as switching GPIO pins high/low, generating PWM signals, executing shell scripts and Python code, and more (or create your own [Custom Outputs](Outputs.md#custom-outputs)).
*   **[Functions](Functions.md)** that perform tasks, such as coupling Inputs and Outputs in interesting ways, such as [PID controllers](Functions.md#pid-controller), [Conditional Controllers](Functions.md#conditional), [Trigger Controllers](Functions.md#trigger), to name a few (or create your own [Custom Functions](Functions.md#custom-functions)).
*   **[Web Interface](About.md#web-interface)** for securely accessing Mycodo using a web browser on your local network or anywhere in the world with an internet connection, to view and configure the system, which includes several light and dark themes to suit your style.
*   **[Dashboards](Data-Viewing.md#dashboard)** that display configurable widgets, including interactive live and historical graphs, gauges, output state indicators, measurements, among others (or create your own [Custom Widgets](Data-Viewing.md#custom-widgets))
*   **[Alert Notifications](Alerts.md)** to send emails when measurements reach or exceed user-specified thresholds, important for knowing immediately when issues arise.
*   **[Setpoint Tracking](Methods.md)** for changing a PID controller setpoint over time, for use with things like terrariums, reflow ovens, thermal cyclers, sous-vide cooking, and more.
*   **[Notes](Notes.md)** to record events, alerts, and other important points in time, which can be overlaid on graphs to visualize events with your measurement data.
*   **[Cameras](Camera.md)** for remote live streaming, image capture, and time-lapse photography.
*   **[Energy Usage Measurement](Energy-Usage.md)** for calculating and tracking power consumption and cost over time.
*   **[Upgrade System](Upgrade-Backup-Restore.md#upgrading)** to easily upgrade the Mycodo system to the latest release to get the newest features or restore to a previously-backed up version.
*   **[Translations](Translations.md)** that enable the web interface to be presented in different [Languages](https://github.com/kizniche/Mycodo#features).


### Uses

See the [README](https://github.com/kizniche/Mycodo#uses) for more information.

### Prerequisites

*   [Raspberry Pi](https://www.raspberrypi.org/) single-board computer (any version: Zero, 1, 2, 3, or 4)
*   [Raspberry Pi Operating System](https://www.raspberrypi.org/downloads/raspbian/) flashed to a micro SD card
*   An active internet connection

### Install

Once you have the Raspberry Pi booted into the Raspberry Pi OS with an internet connection, run the following command in a terminal to initiate the Mycodo install:

```bash
curl -L https://kizniche.github.io/Mycodo/install | bash
```

If the install is successful, open a web browser to the Raspberry Pi's IP address and you will be greeted with a screen to create an Admin user and password.

```
https://127.0.0.1
```

### Support

*   [Mycodo on GitHub](https://github.com/kizniche/Mycodo)
*   [Mycodo Manual](https://kizniche.github.io/Mycodo)
*   [Mycodo API](https://kizniche.github.io/Mycodo/mycodo-api.html)
*   [Mycodo Support](https://play.google.com/store/apps/details?id=com.mycodo.mycododocs) (Android App)
