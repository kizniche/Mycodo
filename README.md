# Mycodo 

## Environmental Regulation System

### Latest version: 5.5.20 [![Build Status](https://travis-ci.org/kizniche/Mycodo.svg?branch=master)](https://travis-ci.org/kizniche/Mycodo) [![Codacy Badge](https://api.codacy.com/project/badge/Grade/5b9c21d5680f4f7fb87df1cf32f71e80)](https://www.codacy.com/app/Mycodo/Mycodo?utm_source=github.com&amp;utm_medium=referral&amp;utm_content=kizniche/Mycodo&amp;utm_campaign=Badge_Grade) [![DOI](https://zenodo.org/badge/30382555.svg)](https://zenodo.org/badge/latestdoi/30382555)

#### [Mycodo Manual](https://github.com/kizniche/Mycodo/blob/master/mycodo-manual.md) ([PDF](https://github.com/kizniche/Mycodo/raw/master/mycodo-manual.pdf), [HTML](http://htmlpreview.github.io/?https://github.com/kizniche/Mycodo/blob/master/mycodo-manual.html), [TEXT](https://raw.githubusercontent.com/kizniche/Mycodo/master/mycodo-manual.txt))

Mycodo is an automated monitoring and regulation system that was built to run on the [Raspberry Pi](https://en.wikipedia.org/wiki/Raspberry_Pi) (versions Zero, 1, 2, and 3).

Originally designed to cultivate edible mushrooms, Mycodo has grown to include the ability to do much more, including cultivating plants, culturing microorganisms, maintaining honey bee apiary homeostasis, incubating animals and eggs, maintaining aquatic systems, aging cheeses, fermenting foods and tobacco, cooking food (vous-vide), and more.

The system comprises a backend (daemon) and a frontend (user interface). The backend conducts measurements from sensors and devices, then coordinate a diverse set of responses to those measurements, including the ability to modulate outputs (relays, PWM, wireless outlets), regulate environmental conditions with electrical devices under PID control (steady regulation or changing over time), schedule timers, capture photos and stream video, trigger actions when measurements meet certain conditions (modulate relays, execute commands, notify by email, etc.), and more. The frontend is a web interface that enables easy navigation and configuration from any browser-enabled device.

#### Languages

  - Complete: [Español (Spanish)](#espa%C3%B1ol-spanish)
  - Partial: [Français (French)](#fran%C3%A7ais-french)
  - Change language under Configure -> Language

## Table of Contents

- [What is PID Control?](#what-is-pid-control)
- [Features](#features)
- [Supported Inputs](#supported-inputs)
- [Install](#install)
  - [Install Notes](#install-notes)
  - [Web Server Security](#web-server-security)
- [Upgrade](#upgrade)
- [Manual](#manual)
- [Donate](#donate)
- [Links](#links)
- [License](#license)

[Languages](#languages-1)

- [Español (Spanish)](#espa%C3%B1ol-spanish)
- [Français (French)](#fran%C3%A7ais-french)

[From the Wiki](#from-the-wiki)
 - [Backup and Restore](https://github.com/kizniche/Mycodo/wiki/Backup-and-Restore)
 - [Diagnosing Issues](https://github.com/kizniche/Mycodo/wiki/Diagnosing-Issues)
 - [Directory Structure](https://github.com/kizniche/Mycodo/wiki/Directory-Structure)
 - [Preserving Custom Code](https://github.com/kizniche/Mycodo/wiki/Preserving-Custom-Code)
 - [Screenshots](https://github.com/kizniche/Mycodo/wiki/Screenshots)
 - [Testing](https://github.com/kizniche/Mycodo/wiki/Testing)
 - [TODO](https://github.com/kizniche/Mycodo/wiki/TODO)
 - [Translations](https://github.com/kizniche/Mycodo/wiki/Translations)

## What is PID Control?

![PID Animation](manual_images/PID-animation.gif)

A [proportional-derivative-integral (PID) controller](https://en.wikipedia.org/wiki/PID_controller) is a control loop feedback mechanism used throughout industry for controlling systems. It efficiently brings a measurable condition, such as temperature, to a desired state (setpoint). A well-tuned PID controller can raise to a setpoint quickly, have minimal overshoot, and maintain the setpoint with little oscillation.

[![Mycodo](http://kylegabriel.com/projects/wp-content/uploads/sites/3/2016/05/Mycodo-3.6.0-tango-Graph-2016-05-21-11-15-26.png)](http://kylegabriel.com/projects/)

The top graph visualizes the regulation of temperature. The red line is the desired temperature setpoint that has been configured (which also has been configured to change over the course of each day). The blue line is the actual recorded temperature. The green vertical bars represent how long a heater is activated for, per every 20-second period. This regulation was achieved with minimal tuning (actual tuned gains: K<sub>P</sub>=0.08, K<sub>I</sub>=0.005, K<sub>D</sub>=0.001), and already displays a very minimal deviation from the setpoint (±0.5° Celsius). Further tuning would reduce this variability further.

## Features

* Inputs: Periodically measure devices, such as analog-to-digital converters (ADCs), sensors (temperature, humidity, CO<sub>2</sub>, atmospheric pressure, infrared heat, luminosity, magnetism, motion, pH, soil moisture, and more), or add your own.
* Outputs: Manipulate the environment by switching GPIO pins High/Low, switching relays, generating PWM signals, email notifications, executing linux commands, and more.
* PID Controllers - Couple inputs with outputs to create feedback loops in order to regulate environmental conditions.
* Methods: Change the desired condition over time (useful for reflow ovens, thermal cyclers, mimicking natural environmental changes, etc.)
* Timers: Schedule the execution of actions at various times and intervals.
* LCDs: Display measurements and data on 16x2 and 20x4 I<sup>2</sup>C-enabled LCD displays
* I<sup>2</sup>C Multiplexer Support: Allow multiple devices/sensors with the same I<sup>2</sup>C address to be used simultaneously.
* Camera support: Raspberry Pi Camera and USB cameras, to stream live video (only Pi cam), capture still images and video, and create time-lapses.
* Web Interface: Access using a web browser on your local network or anywhere in the world with an internet connection.
* Secure Login: High-security login system utilizing the latest encryption and authorization standards.
* Automated system upgrade: When a new version is released on github, an upgrade can be initiated from the web interface.
* Languages: English, [Español (Spanish)](#espa%C3%B1ol-spanish) (partial: [Français (French)](#fran%C3%A7ais-french), [한국어 (Korean)](#%ED%95%9C%EA%B5%AD%EC%96%B4-korean)) (Change language under Configure -> Language)

[Read the manual](#manual) for details.

## Supported Inputs

All supported Inputs can be found under [Sensor Interfaces](https://github.com/kizniche/Mycodo/blob/master/mycodo-manual.md#sensor-interfaces) and [Device Setup](https://github.com/kizniche/Mycodo/blob/master/mycodo-manual.md#device-setup).

## Install

These install procedures have been tested to work with the Raspberry Pi (versions Zero, 1, 2, and 3) following a fresh install of [Raspbian](https://www.raspberrypi.org/downloads/raspbian/) (Full or Lite version), with an active internet connection.

Latest version of Raspbian tested: Raspbian Stretch Nov/2017 version (2017-11-29)

Once Raspbian has been installed, follow the guide below to set up the system prior to installing Mycodo.

### Configure raspi-config

**It's very important that you don't skip the file system expansion and reboot steps! These need to be done before continuing or there won't be enough free disk space to install Mycodo.**

After writing Raspbian to an SD card and enabling ssh by creating a file named ```ssh``` on the boot partition, insert the SD card into the Pi and power the system. Whether you log in with the GUI or terminal via SSH to your Raspberry Pi's IP address for the first time (user: pi, password: raspberry), issue the following command to start raspi-config and set the following options.

```sudo raspi-config```

Then change the following settings

 + ```Change User Password``` (change the password from the default 'raspberry')
 + ```Localisation Options``` -> ```Change Locale``` (set and select en_US.UTF-8, if US)
 + ```Localisation Options``` -> ```Change Timezone```
 + ```Interfacing Options``` -> ```SSH``` -> ```Enable```
 + ```Interfacing Options``` -> ```Camera``` -> ```Enable``` (required if using a Pi camera)
 + ```Interfacing Options``` -> ```I2C``` -> ```Enable``` (required if using I<sup>2</sup>C sensors/devices)
 + ```Advanced Options``` -> ```Expand Filesystem``` (***required***)
 + Reboot (***required***)

### Install Mycodo

Mycodo will be installed by executing setup.sh. As a part of the installation, it will install and configure services to automatically start the Mycodo backend and frontend.

```
sudo apt-get install -y jq
cd ~
curl -s https://api.github.com/repos/kizniche/Mycodo/releases/latest | \
jq -r '.tarball_url' | wget -i - -O mycodo-latest.tar.gz
mkdir Mycodo
tar xzf mycodo-latest.tar.gz -C Mycodo --strip-components=1
rm -f mycodo-latest.tar.gz
cd Mycodo/install
sudo /bin/bash ./setup.sh
```

Make sure the setup.sh script finishes without errors. A log of the setup.sh script output will be created at ```~/Mycodo/install/setup.log```.

If the install is successful, the web user interface should be accessible by navigating a web browser to ```https://0.0.0.0/```, replacing ```0.0.0.0``` with your Raspberry Pi's IP address. The first time you visit this page, you will be prompted to create an admin user. After creating an admin user, you will be redirected to the login page. Once logged in, make sure the host name and version number at the top left is green, indicating the daemon is running. Red indicates the daemon is inactive or unresponsive. Ensure any java-blocking plugins are disabled for all parts of the web interface to function properly.

### Install Notes

If you want write access to the mycodo files, add your user to the mycodo group, changing 'pi' to your user if it differs, then re-log in for the changes to take effect.

```sudo adduser pi mycodo```

In certain circumstances after the initial install or an upgrade, the mycodo daemon will not be able to start because of a missing or corrupt pip package. I'm still trying to understand why this happens and how to prevent it. If you cannot start the daemon, try to reinstall the required python modules with the following command:

```sudo ~/Mycodo/env/bin/pip install -r ~/Mycodo/install/requirements.txt --upgrade --force-reinstall --no-deps```

Then reboot

```sudo shutdown now -r```

If you receive an unresolvable error during the install, please [create an issue](https://github.com/kizniche/Mycodo/issues). If you want to try to diagnose the issue yourself, see [Diagnosing Issues](#diagnosing-issues).

A minimal set of anonymous usage statistics are collected to help improve development. No identifying information is saved from the information that is collected and it is only used to improve Mycodo. No other sources will have access to this information. The data collected is mainly how much specific features are used, and other similar statistics. The data that's collected can be viewed from the 'View collected statistics' link in the Settings -> General page or in the file ```~/Mycodo/databases/statistics.csv```. You may opt out from transmitting this information in the General settings.

## Web Server Security

An SSL certificate will be generated and stored at ```~/Mycodo/mycodo/mycodo_flask/ssl_certs/``` during the install process to allow SSL to be used to securely connect to the web interface. If you want to use your own SSL certificates, replace them with your own.

The certificate that is automatically generated are set to expire in 365 days. If you would like to regenerate new certificate, delete the old certificates, create a new one, and restart the web server with the following commands:

```
sudo /bin/bash ~/Mycodo/mycodo/scripts/upgrade_commands.sh ssl-certs-regenerate
```

If using the auto-generated certificate from the install, be aware that it will not be verified when visiting the web interface using the ```https://``` address prefix (opposed to ```http://```). You may continually receive a warning message about the security of your site, unless you add the certificate to your browser's trusted list.

## Upgrade

Mycodo can be easily upgraded from the web interface by selecting ```Upgrade``` from the configuration menu. Alternatively, an upgrade can be initiated from a terminal with the following command:

```
sudo /bin/bash ~/Mycodo/mycodo/scripts/upgrade_commands.sh upgrade
```

## Manual

The Mycodo Manual may be viewed as [Markdown](https://github.com/kizniche/Mycodo/blob/master/mycodo-manual.md), [PDF](https://github.com/kizniche/Mycodo/raw/master/mycodo-manual.pdf), [HTML](http://htmlpreview.github.io/?https://github.com/kizniche/Mycodo/blob/master/mycodo-manual.html), or [Plain Text](https://raw.githubusercontent.com/kizniche/Mycodo/master/mycodo-manual.txt)


## Donate

I have always made Mycodo free, and I don't intend on changing that to make a profit. However, if you would like to make a donation, you can find several options to do so at [KyleGabriel.com/donate](http://kylegabriel.com/donate)


## Links

Thanks for using and supporting Mycodo, however it may not be the latest version or it may have been altered if not obtained through an official distribution site. You should be able to find the latest version on github or my web site.

https://github.com/kizniche/Mycodo

http://KyleGabriel.com


## License

Mycodo is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.

Mycodo is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the [GNU General Public License](http://www.gnu.org/licenses/gpl-3.0.en.html) for more details.

A full copy of the GNU General Public License can be found at <a href="http://www.gnu.org/licenses/gpl-3.0.en.html" target="_blank">http://www.gnu.org/licenses/gpl-3.0.en.html</a>

This software includes third party open source software components: Discrete PID Controller. Each of these software components have their own license. Please see Mycodo/mycodo/controller_PID.py for license information.


## Languages

Mycodo has been translated (to varying degrees) to [Spanish (Español)](#espa%C3%B1ol-spanish) and [French (Français)](#fran%C3%A7ais-french) (partially). By default, mycodo will display the default language set by your browser. You may also force a language in the settings at ```[Gear Icon]``` -> ```Configure``` -> ```General``` -> ```Language```

### Español (Spanish)

Mycodo es un sistema de control remoto y automatizado con un enfoque en la modulación de las condiciones ambientales. Fue construido para ejecutarse en el Raspberry Pi (versiones Zero, 1, 2 y 3) y tiene como objetivo ser fácil de instalar y operar.

El sistema central coordina un conjunto diverso de respuestas a las mediciones de sensores, incluyendo acciones tales como grabación de cámara, notificaciones por correo electrónico, activación / desactivación de relés, regulación con control PID y más.

Mycodo se ha utilizado para cultivar hongos gourmet, cultivar plantas, cultivar microorganismos, mantener la homeostasis del apiario de abejas, incubar huevos de serpiente y animales jóvenes, envejecer quesos, fermentar alimentos, mantener sistemas acuáticos y mucho más.

### Français (French)

Mycodo est un système de surveillance à distance et de régulation automatisée, axé sur la modulation des conditions environnementales. Il a été construit pour exécuter dans le Raspberry Pi (versions Zero, 1, 2 et 3) et vise à être facile à installer et à utiliser.

Le système de base coordonne un ensemble divers de réponses aux mesures de capteurs, y compris des actions telles que l'enregistrement de caméra, les notifications par courrier électronique, l'activation / désactivation de relais, la régulation avec contrôle PID, et plus encore.

Mycodo a été utilisé pour cultiver des champignons gourmands, cultiver des plantes, cultiver des micro-organismes, entretenir l'homéostasie du rucher des abeilles, incuber les œufs de serpent et les jeunes animaux, vieillir les fromages, fermenter les aliments, entretenir les systèmes aquatiques et plus encore.

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
