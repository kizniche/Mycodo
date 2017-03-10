# Mycodo 

## Environmental Regulation System

### Latest version: 5.0.0 [![Build Status](https://travis-ci.org/kizniche/Mycodo.svg?branch=master)](https://travis-ci.org/kizniche/Mycodo) [![Codacy Badge](https://api.codacy.com/project/badge/Grade/5b9c21d5680f4f7fb87df1cf32f71e80)](https://www.codacy.com/app/Mycodo/Mycodo?utm_source=github.com&amp;utm_medium=referral&amp;utm_content=kizniche/Mycodo&amp;utm_campaign=Badge_Grade)

Mycodo is a remote monitoring and automated regulation system with a focus on modulating environmental conditions. It was built to run on the Raspberry Pi (versions Zero, 1, 2, and 3) and aims to be easy to install and set up.

The core system coordinates a diverse set of responses to sensor measurements, including actions such as camera captures, email notifications, relay activation/deactivation, regulation with PID control, and more. Mycodo has been used for cultivating gourmet mushrooms, cultivating plants, culturing microorganisms, maintaining honey bee apiary homeostasis, incubating snake eggs and young animals, aging cheeses, fermenting foods, maintaining aquatic systems, and more.

Languages: [Español](#espa%C3%B1ol-spanish), [Français](#fran%C3%A7ais-french), [한국어](#%ED%95%9C%EA%B5%AD%EC%96%B4-korean)


## What is PID Control?

[![Mycodo](http://kylegabriel.com/projects/wp-content/uploads/sites/3/2016/05/Mycodo-3.6.0-tango-Graph-2016-05-21-11-15-26.png)](http://kylegabriel.com/projects/)

A [proportional-derivative-integral (PID) controller](https://en.wikipedia.org/wiki/PID_controller) is a control loop feedback mechanism used throughout industry for controlling systems. It efficiently brings a measurable condition, such as the temperature, to a desired state and maintains it there with little overshoot and oscillation. A well-tuned PID controller will raise to the setpoint quickly, have minimal overshoot, and maintain the setpoint with little oscillation.

In the top graph of the above screenshot visualizes the regulation of temperature in a sealed chamber. The red line is the desired temperature setpoint that has been configured (which also happens to have been configured to change over the course of each day). The blue line is the actual recorded temperature. The green vertical bars represent how long a heater is activated for, per every 20-second period. This regulation was achieved with minimal tuning (Actual tuned gains: K<sub>P</sub>=0.08, K<sub>I</sub>=0.005, K<sub>D</sub>=0.001), and already displays a very minimal deviation from the setpoint (±0.5° Celsius). Further tuning would reduce this variability even more.


## Table of Contents

- [Features](#features)
- [TODO](#todo)
- [Install](#install)
- [Install Notes](#install-notes)
- [Web Server](#web-server-security)
- [Upgrading](#upgrading)
- [License](#license)
- [Links](#links)
- [Languages](#languages)
    - [Español (Spanish)](#espa%C3%B1ol-spanish)
    - [Français (French)](#fran%C3%A7ais-french)
    - [한국어 (Korean)](#%ED%95%9C%EA%B5%AD%EC%96%B4-korean)
- [From the Wiki](#from-the-wiki)
    - [Backup and Restore](https://github.com/kizniche/Mycodo/wiki/Backup-and-Restore)
    - [Diagnosing Issues](https://github.com/kizniche/Mycodo/wiki/Diagnosing-Issues)
    - [Directory Structure](https://github.com/kizniche/Mycodo/wiki/Directory-Structure)
    - [Preserving Custom Code](https://github.com/kizniche/Mycodo/wiki/Preserving-Custom-Code)
    - [Screenshots](https://github.com/kizniche/Mycodo/wiki/Screenshots)
    - [Sensors and Devices](https://github.com/kizniche/Mycodo/wiki/Sensors-and-Devices)
    - [Translations](https://github.com/kizniche/Mycodo/wiki/Translations)
    - [User Roles](https://github.com/kizniche/Mycodo/wiki/User-Roles)



## Features

* Web Interface - Access anywhere with an internet connection
* Relays - Control electrical devices, manually and automatic
* Sensors - Measure environmental conditions (temperature, humidity, CO<sub>2</sub>, atmospheric pressure, luminosity, infrared heat, soil moisture, and more)
* Analog to digital converter support for reading any analog sensor or signal.
* Timers - Execute actions at various times and intervals
* Conditional Statements - Execute actions based on inputs or measurements (such as email notification, relay actuation, camera recording, and more)
* PID (Proportional Integral Derivative) Controller - Couple relays with sensors and regulate environmental conditions with prediction and precision
* Methods - Change an environmental condition over time (setpoint tracking, useful for reflow ovens, thermal cyclers, mimicking natural environments, and more)
* LCDs - Display measurements and data on a physical display (cheaper than a monitor)
* I<sup>2</sup>C Multiplexer Support - Allow using multiple devices/sensors with the same I<sup>2</sup>C address.
* Camera support - Raspberry Pi Camera and USB cameras, to stream live video, capture still images, and create time-lapses
* Automated system upgrade - When there's new release on github, an upgrade can be initiated from the web user interface.
* Languages: English, [Español](#espa%C3%B1ol-spanish), [Français](#fran%C3%A7ais-french), and [한국어](#%ED%95%9C%EA%B5%AD%EC%96%B4-korean)


## TODO

* Support Serial Port Expander
* Support more Atlas Scientific sensors
* Add PID filters (of input or output) and alternate PID functions
* Add support for wireless communication (z-wave, xbee, or other)
* Support for PWM and servo/stepper motors
* Continue development of Remote Admin Dashboard to monitor other Mycodo servers
* Add graph export options (width, height, scale)
* Create custom log from influxdb query
* Notes, flag points of time on graph (text, file upload, graph saving, etc.)


## Install

These install procedures have been tested to work with a Raspberry Pi following a fresh install of [Raspbian Jessie](https://www.raspberrypi.org/downloads/raspbian/) (Full or Lite version), with an active internet connection.

It appears that with the current version of Raspbian, SSH is not enabled by default. This necessitates the use of a keyboard and monitor to run raspi-config and enable SSH.

Set up the initial settings with raspi-config. **It's very important that you don't skip the file system expansion and reboot! This needs to be done before continuing or there won't be any free disk space.**

```sudo raspi-config```

 + Expand File system (required)**
 + Change User Password
 + Internationalisation Options -> Change Locale (set and select en_US.UTF-8 if US)
 + Internationalisation Options -> Change Timezone
 + Enable Camera
 + Advanced Options -> Enable SSH
 + Advanced Options -> Enable I<sup>2</sup>C (required if using certain sensors)
 + **Reboot (required)**


Mycodo will be installed by executing setup.sh. As a part of the installation, it will install and modify the default apache2 configuration to host the Mycodo web UI. If you require a custom setup, examine and modify this script accordingly. If you do not require a custom setup, just run the install script with the following commands:

```
sudo apt-get install jq
cd ~
curl -s https://api.github.com/repos/kizniche/Mycodo/releases/latest | \
jq -r '.tarball_url' | wget -i - -O mycodo-latest.tar.gz
mkdir Mycodo
tar xzf mycodo-latest.tar.gz -C Mycodo --strip-components=1
rm -f mycodo-latest.tar.gz
cd Mycodo/install
sudo /bin/bash ./setup.sh
```

Make sure the setup.sh script finishes without errors. A log of the setup.sh script output will be created at ~/Mycodo/install/setup.log.

If the install is successful, the web user interface should be accessible with your PI's IP address https://IPaddress/. The first time you visit this page, you will be prompted to create an admin user. After creating an admin user, you should be redirected to the login page to use the credentials just created to log in. Once logged in, make sure the host name and version number at the top left is green, indicating the daemon is running. Red indicates the daemon is inactive or unresponsive. Ensure any java-blocking plugins are disabled for all the web UI features to work.

Alternatively, an admin user may also be created with the following command:

```sudo ~/Mycodo/init_databases.py --addadmin```


## Install Notes

If you want write access to the mycodo files, add your user to the mycodo group, changing 'username' to your user.

```sudo usermod -a -G mycodo username```

In certain circumstances after the initial install, the mycodo service will not be able to start because of a missing or corrupt package. I'm still trying to understand why this happens and how to prevent it. If you cannot start the daemon, try to reinstall the required python modules with the following command:

```sudo pip install -r ~/Mycodo/install/requirements.txt --upgrade --force-reinstall --no-deps```

Then reboot

```sudo shutdown now -r```

If you receive an unresolvable error during the install, please [create an issue](https://github.com/kizniche/Mycodo/issues). If you want to try to diagnose the issue yourself, see [Diagnosing Issues](#diagnosing-issues).

A minimal set of anonymous usage statistics are collected to help improve development. No identifying information is saved from the information that is collected and it is only used to improve Mycodo. No other sources will have access to this information. The data collected is mainly how much specific features are used, how often errors occur, and other similar statistics. The data that's collected can be viewed from the 'View collected statistics' link in the Settings/General panel of the UI or in the file Mycodo/databases/statistics.csv. You may opt out from transmitting this information from the General settings in the Admin panel.

Mycodo/mycodo/scripts/mycodo_wrapper is a binary executable used to update the system from the web interface. It has the setuid bit to permit it to be executed as root ('sudo bash ~/Mycodo/mycodo/scripts/upgrade_commands.sh initialize' sets the correct permissions and setuid). Since shell scripts cannot be setuid (ony binary files), the mycodo_wrapper binary permits these operations to be executed as root by a non-root user (in this case, members of the group 'mycodo'). You can audit the source code of Mycodo/mycodo/scripts/mycodo_wrapper.c and if you want to ensure the binary is indeed compiled from that source, you may compile it yourself with the following command. Otherwise, the compiled binary is already included and no further action is needed.

```sudo gcc ~/Mycodo/mycodo/scripts/mycodo_wrapper.c -o ~/Mycodo/mycodo/scripts/mycodo_wrapper```


## Web Server Security

An SSL certificate will be generated and stored at ~/Mycodo/mycodo/mycodo_flask/ssl_certs/ during the install process. If you want to use your own SSL certificates, replace them with your own.

The certificate that is automatically generated are set to expire in 365 days. If you would like to regenerate new certificate, delete the old certificates, create a new one, and restart the web server with the following commands.

```
rm -rf ~/Mycodo/mycodo/mycodo_flask/ssl_certs/*.pem
/bin/bash ~/Mycodo/mycodo/scripts/upgrade_commands.sh generate-ssl-certs
sudo /etc/init.d/apache2 restart
```

If using the auto-generated certificate from the install, be aware that it will not be verified when visiting the web UI at the "https://" address (opposed to "http://"). You may receive a warning message about the security of your site, unless you add the certificate to your browser's trusted list.


## Upgrading

If you already have Mycodo installed (version >= 4.0.0), you can perform an upgrade to the latest [release](https://github.com/kizniche/Mycodo/releases) on github by either using the Upgrade option in the web UI (recommended) or by issuing the following command in a terminal. A log of the upgrade process is created at /var/log/mycodo/mycodoupgrade.log

```sudo /bin/bash ~/Mycodo/mycodo/scripts/upgrade_commands.sh upgrade```

Upgrading the mycodo database is performed automatically during the upgrade process, however it can also be performed manually with the following commands (Note: This does not create the database, only upgrade them. You must already have a database created in order to upgrade):

```bash
cd ~/Mycodo/databases
alembic upgrade head
```

Refer to the [alembic documentation](http://alembic.readthedocs.org/en/latest/tutorial.html) for other functions.



## License

Mycodo is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.

Mycodo is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the [GNU General Public License](http://www.gnu.org/licenses/gpl-3.0.en.html) for more details.

A full copy of the GNU General Public License can be found at <a href="http://www.gnu.org/licenses/gpl-3.0.en.html" target="_blank">http://www.gnu.org/licenses/gpl-3.0.en.html</a>

This software includes third party open source software components: Discrete PID Controller. Each of these software components have their own license. Please see Mycodo/mycodo/controller_PID.py for license information.


## Links

Thanks for using and supporting Mycodo, however it may not be the latest version or it may have been altered if not obtained through an official distribution site. You should be able to find the latest version on github or my web site.

https://github.com/kizniche/Mycodo

http://KyleGabriel.com


## Languages

Mycodo has been translated (to varying degrees) to [Spanish (Español)](#espa%C3%B1ol-spanish), [French (Français)](#fran%C3%A7ais-french), and [Korean (한국어)](#%ED%95%9C%EA%B5%AD%EC%96%B4-korean). By default, mycodo will display the default language set by your browser. You may also force a language in the settings at Configure->General Settings->Language.

### Español (Spanish)

Mycodo es un sistema de control remoto y automatizado con un enfoque en la modulación de las condiciones ambientales. Fue construido para ejecutarse en el Raspberry Pi (versiones Zero, 1, 2 y 3) y tiene como objetivo ser fácil de instalar y operar.

El sistema central coordina un conjunto diverso de respuestas a las mediciones de sensores, incluyendo acciones tales como grabación de cámara, notificaciones por correo electrónico, activación / desactivación de relés, regulación con control PID y más.

Mycodo se ha utilizado para cultivar hongos gourmet, cultivar plantas, cultivar microorganismos, mantener la homeostasis del apiario de abejas, incubar huevos de serpiente y animales jóvenes, envejecer quesos, fermentar alimentos, mantener sistemas acuáticos y mucho más.

### Français (French)

Mycodo est un système de surveillance à distance et de régulation automatisée, axé sur la modulation des conditions environnementales. Il a été construit pour exécuter dans le Raspberry Pi (versions Zero, 1, 2 et 3) et vise à être facile à installer et à utiliser.

Le système de base coordonne un ensemble divers de réponses aux mesures de capteurs, y compris des actions telles que l'enregistrement de caméra, les notifications par courrier électronique, l'activation / désactivation de relais, la régulation avec contrôle PID, et plus encore.

Mycodo a été utilisé pour cultiver des champignons gourmands, cultiver des plantes, cultiver des micro-organismes, entretenir l'homéostasie du rucher des abeilles, incuber les œufs de serpent et les jeunes animaux, vieillir les fromages, fermenter les aliments, entretenir les systèmes aquatiques et plus encore.

### 한국어 (Korean)

Mycodo는 환경 조건을 조절하는 데 중점을 둔 원격 모니터링 및 자동화 된 규제 시스템입니다. Raspberry Pi (버전 Zero, 1, 2, 3)를 실행하기 위해 제작되었으며 설치 및 작동이 쉽도록 설계되었습니다.

핵심 시스템은 카메라 기록, 전자 메일 알림, 릴레이 활성화 / 비활성화, PID 제어 규정 등과 같은 조치를 포함하여 센서 측정에 대한 다양한 응답을 조정합니다.

Mycodo는 미식가 버섯을 재배하고, 식물을 재배하고, 미생물을 배양하고, 꿀벌 양봉장의 항상성을 유지하고, 뱀의 달걀과 어린 동물을 키우고, 치즈를 생산하고, 발효 식품을 만들고, 수생 시스템을 유지하는 데 사용되었습니다.



## From the Wiki

The following sections can be found in the wiki.

 - [Backup and Restore](https://github.com/kizniche/Mycodo/wiki/Backup-and-Restore)
 - [Diagnosing Issues](https://github.com/kizniche/Mycodo/wiki/Diagnosing-Issues)
 - [Directory Structure](https://github.com/kizniche/Mycodo/wiki/Directory-Structure)
 - [Preserving Custom Code](https://github.com/kizniche/Mycodo/wiki/Preserving-Custom-Code)
 - [Screenshots](https://github.com/kizniche/Mycodo/wiki/Screenshots)
 - [Sensors and Devices](https://github.com/kizniche/Mycodo/wiki/Sensors-and-Devices)
 - [Translations](https://github.com/kizniche/Mycodo/wiki/Translations)
 - [User Roles](https://github.com/kizniche/Mycodo/wiki/User-Roles)
