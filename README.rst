Mycodo
======

Environmental Regulation System

Latest version: 8.16.0

Mycodo is open source software for the Raspberry Pi that couples inputs and outputs in interesting ways to sense and manipulate the environment.

|Build Status| |Codacy Badge| |Translation Badge| |DOI|

.. contents:: Table of Contents
   :depth: 1

Quick Install
-------------

Prerequisites: Debian-based Linux operating system (apt).

Recommended: Single board computer (SBC) with General-Purpose Input-Output (GPIO) pins.

Install Command:

.. code:: bash

    curl -L https://kizniche.github.io/Mycodo/install | bash


See the `Install Mycodo <#install-mycodo>`__ section for more details.

Support
-------

Documentation
~~~~~~~~~~~~~

`Mycodo Manual <https://kizniche.github.io/Mycodo>`__

`Mycodo API <https://kizniche.github.io/Mycodo/mycodo-api.html>`__ (Version: v1)

`Mycodo Wiki <https://github.com/kizniche/Mycodo/wiki>`__

`Mycodo Custom Module Repository <https://github.com/kizniche/Mycodo-custom>`__

Discussion
~~~~~~~~~~

`Mycodo Issues (Bug Reports/Feature Requests) <https://github.com/kizniche/Mycodo/issues>`__

`Mycodo Forum <https://forum.radicaldiy.com>`__

`Mycodo Discord <https://discord.gg/kmDNky4ZHZ>`__

Bug in the Mycodo Software
~~~~~~~~~~~~~~~~~~~~~~~~~~

If you believe there is a bug in the Mycodo software, first search through the github `Issues <https://github.com/kizniche/Mycodo/issues>`__ and see if your issue has already recently been discussed or resolved. If your issue is novel or significantly more recent than a similar one, you should create a `New Issue <https://github.com/kizniche/Mycodo/issues/new>`__. When creating a new issue, make sure to read all information in the issue template and follow the instructions. Replace the template text with the information being requested (e.g. "step 1" under "Steps to Reproduce the issue" should be replaced with the actual steps to reproduce the issue). The more information you provide, the easier it is to reproduce and diagnose the issue. If the issue is not able to reproduced because not enough information is provided, it may delay or prevent solving the issue.

Donate
------

I have always made Mycodo free and I don't intend on changing that. However, if you find Mycodo useful and would like to support its continued development, please consider becoming a sponsor at `github.com/sponsors/kizniche <https://github.com/sponsors/kizniche>`__ or donate at `kylegabriel.com/donate <https://kylegabriel.com/donate>`__.

Features
--------

-  `Inputs <https://kizniche.github.io/Mycodo/Inputs/>`__ that record measurements from sensors, GPIO pin states, analog-to-digital converters, and more (or create your own `Custom Inputs <https://kizniche.github.io/Mycodo/Inputs/#custom-inputs>`__). See all `Supported Inputs <https://kizniche.github.io/Mycodo/Supported-Inputs-By-Measurement/>`__.
-  `Outputs <https://kizniche.github.io/Mycodo/Outputs/>`__ that perform actions such as switching GPIO pins high/low, generating PWM signals, executing shell scripts and Python code, and more (or create your own `Custom Outputs <https://kizniche.github.io/Mycodo/Outputs/#custom-outputs>`__). See all `Supported Outputs <https://kizniche.github.io/Mycodo/Supported-Outputs/>`__.
-  `Functions <https://kizniche.github.io/Mycodo/Functions/>`__ that perform tasks, such as coupling Inputs and Outputs in interesting ways, such as `PID <https://kizniche.github.io/Mycodo/Functions/#pid-controller>`__, `Conditional <https://kizniche.github.io/Mycodo/Functions/#conditional>`__, `Trigger <https://kizniche.github.io/Mycodo/Functions/#trigger>`__, to name a few (or create your own `Custom Functions <https://kizniche.github.io/Mycodo/Functions/#custom-functions>`__). See all `Supported Functions <https://kizniche.github.io/Mycodo/Supported-Functions/>`__.
-  `Web Interface <https://kizniche.github.io/Mycodo/About/#web-interface>`__ for securely accessing Mycodo using a web browser on your local network or anywhere in the world with an internet connection, to view and configure the system, which includes several light and dark themes.
-  `Dashboards <https://kizniche.github.io/Mycodo/Data-Viewing/#dashboard>`__ that display configurable widgets, including interactive live and historical graphs, gauges, output state indicators, measurements, and more (or create your own `Custom Widgets <https://kizniche.github.io/Mycodo/Widgets/#custom-widgets>`__). See all `Supported Widgets <https://kizniche.github.io/Mycodo/Supported-Widgets/>`__.
-  `Alert Notifications <https://kizniche.github.io/Mycodo/Alerts/>`__ to send emails when measurements reach or exceed user-specified thresholds, important for knowing immediately when issues arise.
-  `Setpoint Tracking <https://kizniche.github.io/Mycodo/Methods/>`__ for changing a PID controller setpoint over time, for use with things like terrariums, reflow ovens, thermal cyclers, sous-vide cooking, and more.
-  `Notes <https://kizniche.github.io/Mycodo/Notes/>`__ to record events, alerts, and other important points in time, which can be overlaid on graphs to visualize events with your measurement data.
-  `Cameras <https://kizniche.github.io/Mycodo/Camera/>`__ for remote live streaming, image capture, and time-lapse photography.
-  `Energy Usage Measurement <https://kizniche.github.io/Mycodo/Energy-Usage/>`__ for calculating and tracking power consumption and cost over time.
-  `Upgrade System <https://kizniche.github.io/Mycodo/Upgrade-Backup-Restore/>`__ to easily upgrade the Mycodo system to the latest release to get the newest features or restore to a previously-backed up version.
-  `Translations <https://kizniche.github.io/Mycodo/Translations/>`__ that enable the web interface to be presented in different `Languages <https://github.com/kizniche/Mycodo#features>`__.

.. image:: https://kylegabriel.com/projects/wp-content/uploads/sites/3/2020/06/Screenshot_2020-04-25-hydra-Default-Dashboard-Mycodo-8-4-0-dashboard_2.png
   :target: https://kylegabriel.com/projects/wp-content/uploads/sites/3/2020/06/Screenshot_2020-04-25-hydra-Default-Dashboard-Mycodo-8-4-0-dashboard_2.png

Figure: `Automated Hydroponic System Build <https://kylegabriel.com/projects/2020/06/automated-hydroponic-system-build.html>`__

--------------

Uses
----

Originally developed to cultivate edible mushrooms, Mycodo has evolved to do much more. Here are a few things that have been done with Mycodo:

Projects by Kyle Gabriel (core developer)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

-  `Mushroom Cultivation Automation <https://kylegabriel.com/projects/2021/09/mushroom-cultivation-automation.html>`__ (`Archive <https://archive.is/HUtdp>`__)
-  `Hydroponic System Automation <https://kylegabriel.com/projects/2020/06/automated-hydroponic-system-build.html>`__ (`Archive <http://archive.is/mB2zc>`__)
-  `Mushroom cultivation <https://kylegabriel.com/projects/2015/04/mushroom-cultivation-revisited.html>`__ (`Archive <http://archive.is/J92Xa>`__)
-  `Ground-based plant cultivation <https://www.youtube.com/watch?v=QNCx_VE7D-8>`__
-  `Maintaining honey bee apiary homeostasis <https://kylegabriel.com/projects/2015/12/environmentally-controlled-apiary.html>`__ (`Archive <http://archive.is/RLo6n>`__)
-  `Maintaining humidity in an underground artificial bat cave <https://kylegabriel.com/projects/2015/10/artificial-bat-cave.html>`__ (`Archive <http://archive.is/QIJ5G>`__)
-  `Remote radiation monitoring and mapping <https://kylegabriel.com/projects/2019/08/remote-radiation-monitoring.html>`__ (`Archive <http://archive.is/PF44Z>`__)
-  `Cooking sous-vide <https://hackaday.io/project/11997-mycodo-environmental-regulation-system/log/45733-sous-vide-pid-tuning-and-the-unexpected-electrical-fire>`__ (`Archive <http://archive.is/Mx52U>`__)
-  `Maintaining a light schedule and regulating humidity <https://fieldstation.kennesaw.edu/summer-days-2020.php#2020_07_16_gabriel_chestnut>`__, ramping from 90 % to 50 % over a 4 week period to acclimatize micropropagated American chestnut plantlets from laboratory to ambient outdoor conditions (`Archive <http://archive.is/Jp60P>`__)

Featured Projects
~~~~~~~~~~~~~~~~~

.. image:: https://kylegabriel.com/projects/wp-content/uploads/sites/3/2021/09/MushroomCultivation_512x288.jpg
   :target: https://www.youtube.com/watch?v=z41Wy5ZF4O8

.. image:: https://kylegabriel.com/projects/wp-content/uploads/sites/3/2020/07/VID_PROJ_HYDRO_512x288.jpg
   :target: https://www.youtube.com/watch?v=nyqykZK2Ev4

Projects by Others
~~~~~~~~~~~~~~~~~~

-  Maintaining aquatic systems (e.g. fish, hydroponic, aquaponic)
-  Maintaining terrarium, herpetarium, and vivarium environments
-  Incubating young animals and eggs
-  Aging cheese
-  Dry-aging, curing, and smoking meat (`Link 1 <http://www.charcuterie-worst.nl/forum/index.php/topic,425.0.html>`__ (`Archive <http://archive.is/NHKqp>`__), `Link 2 <https://www.floriske.nl/wordpress/2019/06/meat-curing-cabinet/>`__ (`Archive <https://archive.ph/57ouJ>`__))
-  Fermenting beer, food, and tobacco
-  Controlling reflow ovens
-  Culturing microorganisms
-  `Treating agricultural waste water <https://projects.sare.org/project-reports/gne17-158/>`__ (`Archive <http://archive.is/enJQs>`__, `Publication <https://pubs.acs.org/doi/pdf/10.1021/acsestwater.0c00234>`__)
-  ...and more

`Let me know <https://kylegabriel.com/contact/>`__ how you use Mycodo and I may include it on this list.

Screenshots
-----------

Visit the `Screenshots <https://github.com/kizniche/Mycodo/wiki/Screenshots>`__ page of the Wiki.

Install Mycodo
--------------

Prerequisites
~~~~~~~~~~~~~

Required:

-  Debian-based operating system
-  An active internet connection

Recommended:

-  `Raspberry Pi <https://www.raspberrypi.org>`__ single-board computer: 3, 4, or 5 (Zero, 1, and 2 are no longer recommended)
-  `Raspberry Pi Operating System <https://www.raspberrypi.com/software/>`__ flashed to a micro SD card or SSD

Mycodo has been tested to work with Raspberry Pi OS 12 (Bookworm release), Lite and Desktop, 32-bit and 64-bit.

Install Command
~~~~~~~~~~~~~~~

Once you have the Raspberry Pi booted, log in and run the following command in a terminal to initiate the Mycodo install to /opt/Mycodo:

.. code:: bash

    curl -L https://kizniche.github.io/Mycodo/install | bash


Install Notes
~~~~~~~~~~~~~

Make sure the install script finishes without errors. A log of the output will be created at ``/opt/Mycodo/install/setup.log``.

If the install is successful, the web user interface should be accessible by navigating a web browser to ``https://127.0.0.1/``, replacing ``127.0.0.1`` with the IP address of the computer you installed on. Upon your first visit, you will be prompted to create an admin user before being redirected to the login page. Once logged in, check that the time is correct at the top left of the page. Incorrect time can cause a number of issues with measurement storage and retrieval in a time-series database. Also ensure the host name and version number at the top left of the page is green, indicating the daemon is running. If it's red, it indicates the daemon is inactive or unresponsive. Last, ensure any java-blocking plugins of your browser are disabled for all parts of the web interface to function properly.

If you receive an error during the install that you believe is preventing your system from operating, please `create an issue <https://github.com/kizniche/Mycodo/issues>`__ with the install log attached. If you would first like to attempt to diagnose the issue yourself, see `Diagnosing Issues <#diagnosing-issues>`__.

A minimal set of anonymous usage statistics are collected to help improve development. No identifying information is saved from the information that is collected and it is only used to improve Mycodo. No one other than the development team will have access to this information and it will never be sold. The data collected is mainly what and how many features are used, and other similar information. The data that's collected can be viewed from the 'View collected statistics' link in the ``Settings -> General`` page. There is an opt out option on the General Settings page if you want to turn this functionality off.

Measurement Database
~~~~~~~~~~~~~~~~~~~~

Mycodo currently supports InfluxDB as the time-series database used to store measurements. Both versions 1.x (for 32-bit systems) and 2.x (for 64-bit systems) are supported. During the install, you will be prompted to install 1.x, 2.x, or none (if you wish to set up your own, either locally or remotely). The settings for the database can be reconfigured after install.

Docker
~~~~~~

Docker support is experimental, but if you want to try it, read the docker `README.md <https://github.com/kizniche/Mycodo/blob/master/docker/README.md>`__. There is also a `Docker Issue (#637) <https://github.com/kizniche/Mycodo/issues/637>`__ on github for those that wish to help with development.

REST API
--------

The latest API documentation can be found here: `API Information <https://kizniche.github.io/Mycodo/API/>`__ and `API Endpoint Documentation <https://kizniche.github.io/Mycodo/mycodo-api.html>`__.

About PID Control
-----------------

A `proportional–integral–derivative (PID) controller <https://en.wikipedia.org/wiki/PID_controller>`__ is a control loop feedback mechanism used throughout industry for controlling systems. It efficiently brings a measurable condition, such as temperature, to a desired state (setpoint). A well-tuned PID controller can raise to a setpoint quickly, have minimal overshoot, and maintain the setpoint with little oscillation.

.. figure:: docs/images/PID-Animation.gif
   :alt: PID Animation


|Mycodo|

The top graph visualizes the regulation of temperature. The red line is the desired temperature (setpoint) that has been configured to change over the course of each day. The blue line is the actual recorded temperature. The green vertical bars represent how long a heater has been activated for every 20-second period. This regulation was achieved with minimal tuning, and already displays a very minimal deviation from the setpoint (±0.5° Celsius). Further tuning would reduce this variability further.

See the `PID Controller <https://kizniche.github.io/Mycodo/Functions/#pid-controller>`__ and `PID Tuning <https://kizniche.github.io/Mycodo/Functions/#pid-tuning>`__ sections of the manual for more information.

Supported Inputs and Outputs
----------------------------

All supported Inputs, Outputs, and other devices can be found under the `Supported Devices <https://kizniche.github.io/Mycodo/Supported-Inputs-By-Measurement/>`__ section of the manual.

Custom Inputs, Outputs, Functions, Actions, and Widgets
-------------------------------------------------------

Mycodo supports importing custom Input, Output, Function, Action, and Widget modules. you can find more information about each in the manual under `Custom Inputs <https://kizniche.github.io/Mycodo/Inputs/#custom-inputs>`__, `Custom Outputs <https://kizniche.github.io/Mycodo/Outputs/#custom-outputs>`__, `Custom Functions <https://kizniche.github.io/Mycodo/Functions/#custom-functions>`__, `Custom Actions <https://kizniche.github.io/Mycodo/Functions/#custom-actions>`__, and `Custom Widgets <https://kizniche.github.io/Mycodo/Data-Viewing/#custom-widgets>`__.

If you would like to add to the list of supported Inputs, Outputs, Functions, Actions, and Widgets, submit a pull request with the module you created or start a `New Issue <https://github.com/kizniche/Mycodo/issues/new?assignees=&labels=&template=feature-request.md&title=>`__.

Additionally, I have another github repository devoted to custom modules that do not necessarily fit with the built-in set and are not included by default with Mycodo, but can be imported. These can be found at `kizniche/Mycodo-custom <https://github.com/kizniche/Mycodo-custom>`__.

Links
-----

Thanks for using and supporting Mycodo, however depending where you found this documentation, you may not have the latest version or it may have been altered, if not obtained through an official distribution site. You should be able to find the latest version on github.

https://github.com/kizniche/Mycodo

https://KyleGabriel.com

https://RadicalDIY.com

License
-------

See `License.txt <https://github.com/kizniche/Mycodo/blob/master/LICENSE.txt>`__

Mycodo is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.

Mycodo is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the `GNU General Public License <http://www.gnu.org/licenses/gpl-3.0.en.html>`__ for more details.

A full copy of the GNU General Public License can be found at http://www.gnu.org/licenses/gpl-3.0.en.html

This software includes third party open source software components. Please see individual files for license information, if applicable.

Languages
---------

Mycodo has been translated to several languages. Weblate is now used so anyone can contribute to translations. However, due to an increasing number of new languages being added and not translated, only languages that are at least 50% complete will be included in Mycodo as a translation option.

|Translation Table|

-  Native: `English <https://kizniche.github.io/Mycodo/>`__
-  `Dutch <https://kizniche.github.io/Mycodo/index.nl/>`__,
   `German <https://kizniche.github.io/Mycodo/index.de/>`__,
   `French <https://kizniche.github.io/Mycodo/index.fr/>`__,
   `Indonesian <https://kizniche.github.io/Mycodo/index.id/>`__,
   `Italian <https://kizniche.github.io/Mycodo/index.it/>`__,
   `Norwegian <https://kizniche.github.io/Mycodo/index.nn/>`__,
   `Polish <https://kizniche.github.io/Mycodo/index.pl/>`__,
   `Portuguese <https://kizniche.github.io/Mycodo/index.pt/>`__,
   `Russian <https://kizniche.github.io/Mycodo/index.ru/>`__,
   `Serbian <https://kizniche.github.io/Mycodo/index.sr/>`__,
   `Spanish <https://kizniche.github.io/Mycodo/index.es/>`__,
   `Swedish <https://kizniche.github.io/Mycodo/index.sv/>`__,
   `Turkish <https://kizniche.github.io/Mycodo/index.tr/>`__,
   `Chinese <https://kizniche.github.io/Mycodo/index.zh/>`__.

The install script will prompt you to select a language. This will be the set language when you first open the web user interface. You may change this at a later time on the settings page at ``[Gear Icon] -> Configure -> General -> Language``.

If you would like to contribute to the translations, you can do so at `http://translate.kylegabriel.com <https://translate.kylegabriel.com/engage/mycodo/>`__. Please read `How To Contribute to Language Translations in Mycodo <https://forum.radicaldiy.com/t/how-to-contribute-to-language-translations-in-mycodo/1162/2>`__ for more information.

Thanks
------

Mycodo is made possible, in part, by the many fine open source libraries, below.

-  `Alembic <https://alembic.sqlalchemy.org>`__
-  `Argparse <https://pypi.org/project/argparse>`__
-  `Bcrypt <https://pypi.org/project/bcrypt>`__
-  `Bootstrap <https://getbootstrap.com>`__
-  `Daemonize <https://pypi.org/project/daemonize>`__
-  `Date Range Picker <https://github.com/dangrossman/daterangepicker>`__
-  `Distro <https://pypi.org/project/distro>`__
-  `Email_Validator <https://pypi.org/project/email_validator>`__
-  `Filelock <https://pypi.org/project/filelock>`__
-  `Flask <https://pypi.org/project/flask>`__
-  `Flask_Accept <https://pypi.org/project/flask_accept>`__
-  `Flask_Babel <https://pypi.org/project/flask_babel>`__
-  `Flask_Compress <https://pypi.org/project/flask_compress>`__
-  `Flask_Limiter <https://pypi.org/project/flask_limiter>`__
-  `Flask_Login <https://pypi.org/project/flask_login>`__
-  `Flask_Marshmallow <https://pypi.org/project/flask_marshmallow>`__
-  `Flask_Profiler <https://github.com/muatik/flask-profiler>`__
-  `Flask_RESTX <https://pypi.org/project/flask_restx>`__
-  `Flask_Session <https://pypi.org/project/flask_session>`__
-  `Flask_SQLAlchemy <https://pypi.org/project/flask_sqlalchemy>`__
-  `Flask_Talisman <https://pypi.org/project/flask_talisman>`__
-  `Flask_WTF <https://pypi.org/project/flask_wtf>`__
-  `FontAwesome <https://fontawesome.com>`__
-  `Geocoder <https://pypi.org/project/geocoder>`__
-  `gridstack.js <https://github.com/gridstack/gridstack.js>`__
-  `Gunicorn <https://gunicorn.org>`__
-  `Highcharts <https://www.highcharts.com>`__
-  `importlib_metadata <https://github.com/python/importlib_metadata>`__
-  `InfluxDB <https://github.com/influxdata/influxdb>`__
-  `influxdb <https://github.com/influxdata/influxdb-python>`__
-  `influxdb_client <https://github.com/influxdata/influxdb-client-python>`__
-  `jQuery <https://jquery.com>`__
-  `Marshmallow_SQLAlchemy <https://pypi.org/project/marshmallow_sqlalchemy>`__
-  `Pyro5 <https://github.com/irmen/Pyro5>`__
-  `SQLAlchemy <https://www.sqlalchemy.org>`__
-  `SQLite <https://www.sqlite.org>`__
-  `toastr <https://github.com/CodeSeven/toastr>`__
-  `Werkzeug <https://palletsprojects.com/p/werkzeug/>`__
-  `WTForms <https://pypi.org/project/wtforms>`__


.. |Build Status| image:: https://github.com/kizniche/Mycodo/actions/workflows/main.yml/badge.svg
   :target: https://github.com/kizniche/Mycodo/actions/workflows/main.yml
.. |Codacy Badge| image:: https://app.codacy.com/project/badge/Grade/bb5ffc43e4444231b813ca6e81359336
   :target: https://www.codacy.com/gh/kizniche/Mycodo/dashboard?utm_source=github.com&amp;utm_medium=referral&amp;utm_content=kizniche/Mycodo&amp;utm_campaign=Badge_Grade
.. |Translation Badge| image:: https://translate.kylegabriel.com/widget/mycodo/git-translation/svg-badge.svg
   :target: https://translate.kylegabriel.com/engage/mycodo/
.. |Translation Table| image:: https://translate.kylegabriel.com/widget/mycodo/git-translation/multi-auto.svg
   :target: https://translate.kylegabriel.com/engage/mycodo/
.. |DOI| image:: https://zenodo.org/badge/DOI/10.5281/zenodo.824199.svg
   :target: https://doi.org/10.5281/zenodo.824199
.. |Mycodo| image:: https://kylegabriel.com/projects/wp-content/uploads/sites/3/2016/05/Mycodo-3.6.0-tango-Graph-2016-05-21-11-15-26.png
   :target: https://kylegabriel.com/projects/
