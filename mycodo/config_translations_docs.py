# -*- coding: utf-8 -*-
#
#  config_translations_docs.py - Mycodo Docs phrases for translation
#

from flask_babel import lazy_gettext


TRANSLATIONS = {
    "index.md": {
        'Mycodo Environmental Monitoring and Regulation System': lazy_gettext('Mycodo Environmental Monitoring and Regulation System'),
        'text_1_1': lazy_gettext('Mycodo is open source software designed to run on the [Raspberry Pi](https://en.wikipedia.org/wiki/Raspberry_Pi) and other single-board computers (SBCs). It couples inputs and outputs in interesting ways to sense and manipulate the environment.'),

        'Information': lazy_gettext('Information'),
        'text_2_1': lazy_gettext('See the [README](https://github.com/kizniche/Mycodo#uses) for features, projects using Mycodo, screenshots, and other information.'),

        'Prerequisites': lazy_gettext('Prerequisites'),
        'text_3_1': lazy_gettext('Single-board computer (Recommended: [Raspberry Pi](https://www.raspberrypi.org/), any version: Zero, 1, 2, 3, or 4)'),
        'text_3_2': lazy_gettext('Debian-based operating system'),
        'text_3_3': lazy_gettext('An active internet connection'),

        'Install': lazy_gettext('Install'),
        'text_4_1': lazy_gettext('Once booted and logged in, run the following command to initiate the Mycodo install:'),
        'text_4_2': lazy_gettext("After installation, open a web browser to the SBC's IP address and you will be prompted to create an Admin user and login."),

        'Support': lazy_gettext('Support'),
        "text_5_1": lazy_gettext("Discussion Forum"),
        "text_5_2": lazy_gettext("Frequently Asked Questions"),

        'Donate': lazy_gettext('Donate'),
        'text_6_1': lazy_gettext("Become a Sponsor"),
        'text_6_2': lazy_gettext("Other Methods")
    },

    "About.md": {
        "text_1_1": lazy_gettext("Mycodo is an open-source environmental monitoring and regulation system that was built to run on single-board computers, specifically the [Raspberry Pi](https://en.wikipedia.org/wiki/Raspberry_Pi)."),
        "text_1_2": lazy_gettext("Originally developed for cultivating edible mushrooms, Mycodo has grown to do much more. The system consists of two parts, a backend (daemon) and a frontend (web server). The backend performs tasks such as acquiring measurements from sensors and devices and coordinating a diverse set of responses to those measurements, including the ability to modulate outputs (switch relays, generate PWM signals, operate pumps, switch wireless outlets, publish/subscribe to MQTT, among others), regulate environmental conditions with PID control, schedule timers, capture photos and stream video, trigger actions when measurements meet certain conditions, and more. The frontend hosts a web interface that enables viewing and configuration from any browser-enabled device."),
        "text_1_3": lazy_gettext("There are a number of different uses for Mycodo. Some users simply store sensor measurements to monitor conditions remotely, others regulate the environmental conditions of a physical space, while others capture motion-activated or time-lapse photography, among other uses."),
        "text_1_4": lazy_gettext("Input controllers acquire measurements and store them in the InfluxDB time series database. Measurements typically come from sensors, but may also be configured to use the return value of Linux Bash or Python commands, or math equations, making this a very dynamic system for acquiring and generating data."),
        "text_1_5": lazy_gettext("Output controllers produce changes to the general input/output (GPIO) pins or may be configured to execute Linux Bash or Python commands, enabling a variety of potential uses. There are a few different types of outputs: simple switching of GPIO pins (HIGH/LOW), generating pulse-width modulated (PWM) signals, controlling peristaltic pumps, MQTT publishing, and more."),
        "text_1_6": lazy_gettext("When Inputs and Outputs are combined, Function controllers may be used to create feedback loops that uses the Output device to modulate an environmental condition the Input measures. Certain Inputs may be coupled with certain Outputs to create a variety of different control and regulation applications. Beyond simple regulation, Methods may be used to create a changing setpoint over time, enabling such things as thermal cyclers, reflow ovens, environmental simulation for terrariums, food and beverage fermentation or curing, and cooking food ([sous-vide](https://en.wikipedia.org/wiki/Sous-vide)), to name a few."),
        "text_1_7": lazy_gettext('Triggers can be set to activate events based on specific dates and times, according to durations of time, or the sunrise/sunset at a specific latitude and longitude.'),
        "text_1_8": lazy_gettext("Mycodo has been translated to several languages. By default, the language of the browser will determine which language is used, but may be overridden in the General Settings, on the `[Gear Icon] -> Configure -> General` page. If you find an issue and would like to correct a translation or would like to add another language, this can be done at [https://translate.kylegabriel.com](https://translate.kylegabriel.com/engage/mycodo/).")
    },

    "Data-Viewing.md": {
        "Live Measurements": lazy_gettext("Live Measurements"),
        "text_1_1": lazy_gettext("The `Live Measurements` page is the first page a user sees after logging in to Mycodo. It will display the current measurements being acquired from Input and Function controllers. If there is nothing displayed on the `Live` page, ensure an Input or Function controller is both configured correctly and activated. Data will be automatically updated on the page from the measurement database."),

        "Asynchronous Graphs": lazy_gettext("Asynchronous Graphs"),
        "Page": lazy_gettext("Page"),
        "Data": lazy_gettext("Data"),
        "text_2_1": lazy_gettext("A graphical data display that is useful for viewing data sets spanning relatively long periods of time (weeks/months/years), which could be very data- and processor-intensive to view as a Synchronous Graph. Select a time frame and data will be loaded from that time span, if it exists. The first view will be of the entire selected data set. For every view/zoom, 700 data points will be loaded. If there are more than 700 data points recorded for the time span selected, 700 points will be created from an averaging of the points in that time span. This enables much less data to be used to navigate a large data set. For instance, 4 months of data may be 10 megabytes if all of it were downloaded. However, when viewing a 4 month span, it's not possible to see every data point of that 10 megabytes, and aggregating of points is inevitable. With asynchronous loading of data, you only download what you see. So, instead of downloading 10 megabytes every graph load, only ~50kb will be downloaded until a new zoom level is selected, at which time only another ~50kb is downloaded."),
        "text_2_2": lazy_gettext("Graphs require measurements, therefore at least one Input/Output/Function/etc. needs to be added and activated in order to display data."),

        "Dashboard": lazy_gettext("Dashboard"),
        "text_3_1": lazy_gettext("The dashboard can be used for both viewing data and manipulating the system, thanks to the numerous dashboard widgets available. Multiple dashboards can be created as well as locked to prevent changing the arrangement."),

        "Widgets": lazy_gettext("Widgets"),
        "text_4_1": lazy_gettext("Widgets are elements on the Dashboard that have a number of uses, such as viewing data (charts, indicators, gauges, etc.) or interacting with the system (manipulate outputs, change PWM duty cycle, querying or modifying a database, etc.). Widgets can be easily rearranged and resized by dragging and dropping. For a full list of supported Widgets, see [Supported Widgets](Supported-Widgets.md)."),

        "Custom Widgets": lazy_gettext("Custom Widgets"),
        "text_5_1": lazy_gettext("There is a Custom Widget import system in Mycodo that allows user-created Widgets to be used in the Mycodo system. Custom Widgets can be uploaded on the `[Gear Icon] -> Configure -> Custom Widgets` page. After import, they will be available to use on the `Setup -> Widget` page."),
        "text_5_2": lazy_gettext("If you develop a working module, please consider [creating a new GitHub issue](https://github.com/kizniche/Mycodo/issues/new?assignees=&labels=&template=feature-request.md&title=New%20Module) or pull request, and it may be included in the built-in set."),
        "text_5_3": lazy_gettext("Open any of the built-in Widget modules located in the directory [Mycodo/mycodo/widgets](https://github.com/kizniche/Mycodo/tree/master/mycodo/widgets/) for examples of the proper formatting. There are also example Custom Widgets in the directory [Mycodo/mycodo/widgets/examples](https://github.com/kizniche/Mycodo/tree/master/mycodo/widgets/examples)."),
        "text_5_4": lazy_gettext("Creating a custom widget module often requires specific placement and execution of Javascript. Several variables were created in each module to address this, and follow the following brief structure of the dashboard page that would be generated with multiple widgets being displayed.")
    }
}
