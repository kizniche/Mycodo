Mycodo
======

Environmental Regulation System

Latest version: 6.4.4 |Build Status| |Codacy Badge| |DOI|

`Mycodo Manual <https://github.com/kizniche/Mycodo/blob/master/mycodo-manual.rst>`__
(`PDF <https://github.com/kizniche/Mycodo/raw/master/mycodo-manual.pdf>`__,
`HTML <http://htmlpreview.github.io/?https://github.com/kizniche/Mycodo/blob/master/mycodo-manual.html>`__,
`TEXT <https://raw.githubusercontent.com/kizniche/Mycodo/master/mycodo-manual.txt>`__)

`Mycodo Wiki <https://github.com/kizniche/Mycodo/wiki>`__

Mycodo is an automated monitoring and regulation system that was built
to run on the `Raspberry
Pi <https://en.wikipedia.org/wiki/Raspberry_Pi>`__ (versions Zero, 1, 2,
and 3).

Originally designed to cultivate edible mushrooms, Mycodo has grown to
include the ability to do much more, including cultivating plants,
culturing microorganisms, maintaining honey bee apiary homeostasis,
incubating animals and eggs, maintaining aquatic systems, aging cheeses,
fermenting foods and tobacco, cooking food (sous-vide), and more.

The system comprises a backend (daemon) and a frontend (user interface).
The backend conducts measurements from sensors and devices, then
coordinate a diverse set of responses to those measurements, including
the ability to modulate outputs (relays, PWM, wireless outlets),
regulate environmental conditions with electrical devices under PID
control (steady regulation or changing over time), schedule timers,
capture photos and stream video, trigger actions when measurements meet
certain conditions (modulate relays, execute commands, notify by email,
etc.), and more. The frontend is a web interface that enables easy
navigation and configuration from any browser-enabled device.

.. contents::
   :depth: 3


What is PID Control?
--------------------

A `proportional-derivative-integral (PID)
controller <https://en.wikipedia.org/wiki/PID_controller>`__ is a
control loop feedback mechanism used throughout industry for controlling
systems. It efficiently brings a measurable condition, such as
temperature, to a desired state (setpoint). A well-tuned PID controller
can raise to a setpoint quickly, have minimal overshoot, and maintain
the setpoint with little oscillation.

.. figure:: manual_images/PID-animation.gif
   :alt: PID Animation


|Mycodo|

The top graph visualizes the regulation of temperature. The red line is
the desired temperature (setpoint) that has been configured to change
over the course of each day. The blue line is the actual recorded
temperature. The green vertical bars represent how long a heater has
been activated for every 20-second period. This regulation was achieved
with minimal tuning, and already displays a very minimal deviation from
the setpoint (Â±0.5Â° Celsius). Further tuning would reduce this
variability further.

Software Features
-----------------

-  Inputs: Periodically measure devices, such as analog-to-digital
   converters (ADCs), sensors (temperature, humidity, etc.), or add your
   own.
-  Outputs: Manipulate the environment by switching GPIO pins High or
   Low, switching relays, generating PWM signals, email notifications,
   executing Linux commands, and more.
-  PID Controllers: Couple inputs with outputs to create feedback loops
   in order to regulate environmental conditions.
-  Methods: Change the desired condition over time (useful for reflow
   ovens, thermal cyclers, mimicking natural environmental changes,
   etc.)
-  Timers: Schedule the execution of actions at various times and
   intervals.
-  LCDs: Display measurements and data on 16x2 and 20x4 I2C-enabled LCD
   displays.
-  I2C Multiplexer Support: Allow multiple devices/sensors with the same
   I2C address to be used simultaneously.
-  Camera support: Raspberry Pi Camera and USB cameras, to stream live
   video (only Pi camera), capture still images and video, and create
   time-lapses.
-  Web Interface: Access using a web browser on your local network or
   anywhere in the world with an internet connection.
-  Secure Login: High-security login system utilizing the latest
   encryption and authorization standards.
-  System upgrade: When a new version is released on github, an upgrade
   can be initiated from the web interface.
-  Languages: English, `EspaÃ±ol (Spanish) <#espa%C3%B1ol-spanish>`__,
   `Deutsche (German) <#deutsche-german>`__,
   `FranÃ§ais (French) <#fran%C3%A7ais-french>`__,
   `Italian <#italian>`__,
   `Portuguese <#portuguese>`__,
   `Russian <#russian>`__, and
   `Chinese <#chinese>`__ (Change
   language under Configure -> Language)

`Read the manual <#manual>`__ for details.

Supported Inputs
----------------

All supported Inputs can be found under `Sensor
Interfaces <https://github.com/kizniche/Mycodo/blob/master/mycodo-manual.rst#sensor-interfaces>`__
and `Device
Setup <https://github.com/kizniche/Mycodo/blob/master/mycodo-manual.rst#device-setup>`__.

Install
-------

These install procedures have been tested to work with the Raspberry Pi
(versions Zero, 1, 2, and 3) following a fresh install of
`Raspbian <https://www.raspberrypi.org/downloads/raspbian/>`__ (Full or
Lite version), with an active internet connection.

Once Raspbian has been installed, follow the guide below to set up the
system prior to installing Mycodo.

Configure raspi-config
~~~~~~~~~~~~~~~~~~~~~~

**It's very important that you don't skip the file system expansion and
reboot steps! These need to be done before continuing or there won't be
enough free disk space to install Mycodo.**

After writing Raspbian to an SD card and enabling ssh by creating a file
named ``ssh`` on the boot partition, insert the SD card into the Pi and
power the system. Whether you log in with the GUI or terminal via SSH to
your Raspberry Pi's IP address for the first time (user: pi, password:
raspberry), issue the following command to start raspi-config and set
the following options.

::

    sudo raspi-config

Then change the following settings

-  ``Change User Password`` (change the password from the default
   'raspberry')
-  ``Localisation Options`` -> ``Change Locale`` (set and select
   en\_US.UTF-8, if US)
-  ``Localisation Options`` -> ``Change Timezone``
-  ``Interfacing Options`` -> ``SSH`` -> ``Enable``
-  ``Advanced Options`` -> ``Expand Filesystem`` (***required***)
-  Reboot (***required***)

Install Mycodo
~~~~~~~~~~~~~~

Mycodo will be installed by executing install.sh. As a part of the
installation, you will be prompted with a few options to determine which
components to install and configure.

.. code:: bash

    curl -L https://raw.githubusercontent.com/kizniche/Mycodo/master/install/install | bash


Make sure the install script finishes without errors. A log of the
output will be created at ``~/Mycodo/install/setup.log``.

If the install is successful, the web user interface should be
accessible by navigating a web browser to ``https://0.0.0.0/``,
replacing ``0.0.0.0`` with your Raspberry Pi's IP address. The first
time you visit this page, you will be prompted to create an admin user.
After creating an admin user, you will be redirected to the login page.
Once logged in, make sure the host name and version number at the top
left is green, indicating the daemon is running. Red indicates the
daemon is inactive or unresponsive. Ensure any java-blocking plugins are
disabled for all parts of the web interface to function properly.

Install Notes
~~~~~~~~~~~~~

If you want write access to the mycodo files, add your user to the
mycodo group, changing 'pi' to your user if it differs, then re-log in
for the changes to take effect.

::

    sudo adduser pi mycodo

In certain circumstances after the initial install or an upgrade, the
mycodo daemon will not be able to start because of a missing or corrupt
pip package. I'm still trying to understand why this happens and how to
prevent it. If you cannot start the daemon, try to reinstall the
required python modules with the following command:

::

    sudo ~/Mycodo/env/bin/pip install -r ~/Mycodo/install/requirements.txt --upgrade --force-reinstall --no-deps

Then reboot

::

    sudo shutdown now -r

If you receive an unresolvable error during the install, please `create
an issue <https://github.com/kizniche/Mycodo/issues>`__. If you want to
try to diagnose the issue yourself, see `Diagnosing
Issues <#diagnosing-issues>`__.

A minimal set of anonymous usage statistics are collected to help
improve development. No identifying information is saved from the
information that is collected and it is only used to improve Mycodo. No
other sources will have access to this information. The data collected
is mainly how much specific features are used, and other similar
statistics. The data that's collected can be viewed from the 'View
collected statistics' link in the Settings -> General page or in the
file ``~/Mycodo/databases/statistics.csv``. You may opt out from
transmitting this information in the General settings.

Web Server Security
-------------------

An SSL certificate will be generated (expires in 10 years) and stored at
``~/Mycodo/mycodo/mycodo_flask/ssl_certs/`` during the install process
to allow SSL to be used to securely connect to the web interface. If you
want to use your own SSL certificates, replace them with your own.

If using the auto-generated certificate from the install, be aware that
it will not be verified when visiting the web interface using the
``https://`` address prefix (opposed to ``http://``). You may
continually receive a warning message about the security of your site,
unless you add the certificate to your browser's trusted list.

Upgrade
-------

Mycodo can be easily upgraded from the web interface by selecting
``Upgrade`` from the configuration menu. Alternatively, an upgrade can
be initiated from a terminal with the following command:

::

    sudo /bin/bash ~/Mycodo/mycodo/scripts/upgrade_commands.sh upgrade

Manual
------

The Mycodo Manual may be viewed as
`Markdown <https://github.com/kizniche/Mycodo/blob/master/mycodo-manual.rst>`__,
`PDF <https://github.com/kizniche/Mycodo/raw/master/mycodo-manual.pdf>`__,
`HTML <http://htmlpreview.github.io/?https://github.com/kizniche/Mycodo/blob/master/mycodo-manual.html>`__,
or `Plain
Text <https://raw.githubusercontent.com/kizniche/Mycodo/master/mycodo-manual.txt>`__

Donate
------

I have always made Mycodo free, and I don't intend on changing that to
make a profit. However, if you would like to make a donation, you can
find several options to do so at
`KyleGabriel.com/donate <http://kylegabriel.com/donate>`__

Links
-----

Thanks for using and supporting Mycodo, however it may not be the latest
version or it may have been altered if not obtained through an official
distribution site. You should be able to find the latest version on
github or my web site.

https://github.com/kizniche/Mycodo

http://KyleGabriel.com

License
-------

Mycodo is free software: you can redistribute it and/or modify it under
the terms of the GNU General Public License as published by the Free
Software Foundation, either version 3 of the License, or (at your
option) any later version.

Mycodo is distributed in the hope that it will be useful, but WITHOUT
ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
FITNESS FOR A PARTICULAR PURPOSE. See the `GNU General Public
License <http://www.gnu.org/licenses/gpl-3.0.en.html>`__ for more
details.

A full copy of the GNU General Public License can be found at
http://www.gnu.org/licenses/gpl-3.0.en.html

This software includes third party open source software components.
Please see individual files for license information, if applicable.

Languages
---------

-  Native: English
-  Complete: `EspaÃ±ol (Spanish) <#espa%C3%B1ol-spanish>`__,
   `Deutsche (German) <#deutsche-german>`__,
   `FranÃ§ais (French) <#fran%C3%A7ais-french>`__,
   `Italian <#italian>`__,
   `Portuguese <#portuguese>`__,
   `Russian <#russian>`__, and
   `Chinese <#chinese>`__

By default, mycodo will display the default language set by your browser. You may also
force a language in the settings at ``[Gear Icon]`` -> ``Configure`` ->
``General`` -> ``Language``

If you would like to improve the translations, you can submit a pull request with an
amended .po file from ~/Mycodo/mycodo/mycodo_flask/translations/ or start a
`New Issue <https://github.com/kizniche/Mycodo/issues/new>`__ detailing the corrections.

English
~~~~~~~

The native language used in the software.

Deutsche (German)
~~~~~~~~~~~~~~~~~

Mycodo ist ein automatisiertes Ãœberwachungs- und Regelsystem, das auf
dem Raspberry Pi (Versionen Zero, 1, 2 und 3) lÃ¤uft.

UrsprÃ¼nglich zur Kultivierung von essbaren Pilzen entwickelt, hat Mycodo
die FÃ¤higkeit, viel mehr zu tun, einschlieÃŸlich der Kultivierung von
Pflanzen, Kultivierung von Mikroorganismen, Aufrechterhaltung der
Imkerei-HomÃ¶ostase, Inkubation von Tieren und Eiern, Aufrechterhaltung
aquatischer Systeme, Alterung von KÃ¤se, Fermentierung von Lebensmitteln
und Tabak, Kochen Essen (sous-vide) und mehr.

Das System umfasst ein Backend (Daemon) und ein Frontend
(Benutzerschnittstelle). Das Backend fÃ¼hrt Messungen von Sensoren und
GerÃ¤ten durch und koordiniert dann verschiedene Reaktionen auf diese
Messungen, einschlieÃŸlich der FÃ¤higkeit, AusgÃ¤nge (Relais, PWM,
drahtlose AusgÃ¤nge) zu modulieren, Umgebungsbedingungen mit elektrischen
GerÃ¤ten unter PID-Kontrolle zu regulieren (stetige Regelung oder
Umschaltung) Zeit), Timer planen, Fotos aufnehmen und Videos streamen,
Aktionen auslÃ¶sen, wenn Messungen bestimmte Bedingungen erfÃ¼llen (Relais
modulieren, Befehle ausfÃ¼hren, per E-Mail benachrichtigen usw.) und
vieles mehr. Das Frontend ist eine Webschnittstelle, die eine einfache
Navigation und Konfiguration von jedem browserfÃ¤higen GerÃ¤t ermÃ¶glicht.

EspaÃ±ol (Spanish)
~~~~~~~~~~~~~~~~~

Mycodo es un sistema de control remoto y automatizado con un enfoque en
la modulaciÃ³n de las condiciones ambientales. Fue construido para
ejecutarse en el Raspberry Pi (versiones Zero, 1, 2 y 3) y tiene como
objetivo ser fÃ¡cil de instalar y operar.

El sistema central coordina un conjunto diverso de respuestas a las
mediciones de sensores, incluyendo acciones tales como grabaciÃ³n de
cÃ¡mara, notificaciones por correo electrÃ³nico, activaciÃ³n /
desactivaciÃ³n de relÃ©s, regulaciÃ³n con control PID y mÃ¡s.

Mycodo se ha utilizado para cultivar hongos gourmet, cultivar plantas,
cultivar microorganismos, mantener la homeostasis del apiario de abejas,
incubar huevos de serpiente y animales jÃ³venes, envejecer quesos,
fermentar alimentos, mantener sistemas acuÃ¡ticos y mucho mÃ¡s.

FranÃ§ais (French)
~~~~~~~~~~~~~~~~~

Mycodo est un systÃ¨me de surveillance Ã  distance et de rÃ©gulation
automatisÃ©e, axÃ© sur la modulation des conditions environnementales. Il
a Ã©tÃ© construit pour exÃ©cuter dans le Raspberry Pi (versions Zero, 1, 2
et 3) et vise Ã  Ãªtre facile Ã  installer et Ã  utiliser.

Le systÃ¨me de base coordonne un ensemble divers de rÃ©ponses aux mesures
de capteurs, y compris des actions telles que l'enregistrement de
camÃ©ra, les notifications par courrier Ã©lectronique, l'activation /
dÃ©sactivation de relais, la rÃ©gulation avec contrÃ´le PID, et plus
encore.

Mycodo a Ã©tÃ© utilisÃ© pour cultiver des champignons gourmands, cultiver
des plantes, cultiver des micro-organismes, entretenir l'homÃ©ostasie du
rucher des abeilles, incuber les Å“ufs de serpent et les jeunes animaux,
vieillir les fromages, fermenter les aliments, entretenir les systÃ¨mes
aquatiques et plus encore.

Italian
~~~~~~~

Mycodo Ã¨ un sistema di monitoraggio e regolazione automatico che Ã¨
stato creato per funzionare su Raspberry Pi (versioni Zero, 1, 2 e 3).

Originariamente progettato per coltivare funghi commestibili, Mycodo
Ã¨ cresciuto fino a comprendere la possibilitÃ  di fare molto di piÃ¹,
coltivando piante, coltivando microrganismi, mantenendo l'omeostasi
delle api apistiche del miele, incubando animali e uova, mantenendo
sistemi acquatici, formaggi stagionati, alimenti fermentati e tabacco,
cucinando cibo (sous-vide), e altro ancora.

Il sistema comprende un backend (demone) e un frontend (interfaccia
utente). Il back-end esegue misurazioni da sensori e dispositivi,
quindi coordina una serie diversificata di risposte a tali misurazioni,
inclusa la possibilitÃ  di modulare le uscite (relÃ¨, PWM, prese wireless),
regola le condizioni ambientali con dispositivi elettrici sotto controllo
PID (regolazione costante o commutazione tempo), programmare i timer,
acquisire foto e riprodurre video in streaming, attivare azioni quando
le misurazioni soddisfano determinate condizioni (moduli relÃ¨, comandi
di esecuzione, notifica via e-mail, ecc.) e altro. Il frontend Ã¨
un'interfaccia web che consente una facile navigazione e configurazione
da qualsiasi dispositivo abilitato per il browser.

Portuguese
~~~~~~~~~~
Mycodo Ã© um sistema automatizado de monitoramento e regulaÃ§Ã£o que foi
construÃ­do para rodar no Raspberry Pi (versÃµes Zero, 1, 2 e 3).

Originalmente projetado para cultivar cogumelos comestÃ­veis, o Mycodo
cresceu para incluir a capacidade de fazer muito mais, incluindo
cultivar plantas, cultivar microorganismos, manter a homeostase do
apiÃ¡rio de abelhas, incubar animais e ovos, manter sistemas aquÃ¡ticos,
queijos envelhecidos, fermentar alimentos e tabaco, cozinhar comida
(sous-vide) e muito mais.

O sistema compreende um backend (daemon) e um frontend (interface de
usuÃ¡rio). O backend realiza mediÃ§Ãµes a partir de sensores e dispositivos
e coordena um conjunto diversificado de respostas a essas mediÃ§Ãµes,
incluindo a capacidade de modular saÃ­das (relÃ©s, PWM, tomadas sem fio),
regular condiÃ§Ãµes ambientais com dispositivos elÃ©tricos sob controle PID
(regulaÃ§Ã£o estÃ¡vel ou troca tempo), agendar cronÃ´metros, capturar fotos
e transmitir vÃ­deo, desencadear aÃ§Ãµes quando as mediÃ§Ãµes atenderem a
determinadas condiÃ§Ãµes (modular relÃ©s, executar comandos, notificar por
e-mail etc.) e muito mais. O frontend Ã© uma interface da Web que permite
fÃ¡cil navegaÃ§Ã£o e configuraÃ§Ã£o a partir de qualquer dispositivo
habilitado para navegador.

Russian
~~~~~~~

ÐŸÐµÑ€Ð²Ð¾Ð½Ð°Ñ‡Ð°Ð»ÑŒÐ½Ð¾ Ñ€Ð°Ð·Ñ€Ð°Ð±Ð¾Ñ‚Ð°Ð½Ð½Ñ‹Ð¹ Ð´Ð»Ñ� Ð²Ñ‹Ñ€Ð°Ñ‰Ð¸Ð²Ð°Ð½Ð¸Ñ� Ñ�ÑŠÐµÐ´Ð¾Ð±Ð½Ñ‹Ñ… Ð³Ñ€Ð¸Ð±Ð¾Ð², Mycodo
Ð²Ñ‹Ñ€Ð¾Ñ�, Ñ‡Ñ‚Ð¾Ð±Ñ‹ Ð²ÐºÐ»ÑŽÑ‡Ð°Ñ‚ÑŒ Ð² Ñ�ÐµÐ±Ñ� Ñ�Ð¿Ð¾Ñ�Ð¾Ð±Ð½Ð¾Ñ�Ñ‚ÑŒ Ð´ÐµÐ»Ð°Ñ‚ÑŒ Ð³Ð¾Ñ€Ð°Ð·Ð´Ð¾ Ð±Ð¾Ð»ÑŒÑˆÐµ, Ð² Ñ‚Ð¾Ð¼
Ñ‡Ð¸Ñ�Ð»Ðµ Ð²Ñ‹Ñ€Ð°Ñ‰Ð¸Ð²Ð°Ñ‚ÑŒ Ñ€Ð°Ñ�Ñ‚ÐµÐ½Ð¸Ñ�, ÐºÑƒÐ»ÑŒÑ‚Ð¸Ð²Ð¸Ñ€Ð¾Ð²Ð°Ñ‚ÑŒ Ð¼Ð¸ÐºÑ€Ð¾Ð¾Ñ€Ð³Ð°Ð½Ð¸Ð·Ð¼Ñ‹, Ð¿Ð¾Ð´Ð´ÐµÑ€Ð¶Ð¸Ð²Ð°Ñ‚ÑŒ
Ð³Ð¾Ð¼ÐµÐ¾Ñ�Ñ‚Ð°Ð· Ð¼ÐµÐ´Ð¾Ð½Ð¾Ñ�Ð½Ð¾Ð¹ Ð¿Ñ‡ÐµÐ»Ñ‹, Ð¸Ð½ÐºÑƒÐ±Ð¸Ñ€Ð¾Ð²Ð°Ñ‚ÑŒ Ð¶Ð¸Ð²Ð¾Ñ‚Ð½Ñ‹Ñ… Ð¸ Ñ�Ð¹Ñ†Ð°, Ð¿Ð¾Ð´Ð´ÐµÑ€Ð¶Ð¸Ð²Ð°Ñ‚ÑŒ
Ð²Ð¾Ð´Ð½Ñ‹Ðµ Ñ�Ð¸Ñ�Ñ‚ÐµÐ¼Ñ‹, Ñ�Ñ‚Ð°Ñ€ÐµÑŽÑ‰Ð¸Ðµ Ñ�Ñ‹Ñ€Ñ‹, Ñ„ÐµÑ€Ð¼ÐµÐ½Ñ‚Ð¸Ñ€Ð¾Ð²Ð°Ñ‚ÑŒ Ð¿Ñ€Ð¾Ð´ÑƒÐºÑ‚Ñ‹ Ð¸ Ñ‚Ð°Ð±Ð°Ðº,
Ð³Ð¾Ñ‚Ð¾Ð²Ð¸Ñ‚ÑŒ ÐµÐ´Ð° (sous-vide) Ð¸ Ð¼Ð½Ð¾Ð³Ð¾Ðµ Ð´Ñ€ÑƒÐ³Ð¾Ðµ.

Ð¡Ð¸Ñ�Ñ‚ÐµÐ¼Ð° Ñ�Ð¾Ð´ÐµÑ€Ð¶Ð¸Ñ‚ Ð±Ñ�ÐºÑ�Ð½Ð´ (Ð´ÐµÐ¼Ð¾Ð½) Ð¸ Ð¸Ð½Ñ‚ÐµÑ€Ñ„ÐµÐ¹Ñ� (Ð¿Ð¾Ð»ÑŒÐ·Ð¾Ð²Ð°Ñ‚ÐµÐ»ÑŒÑ�ÐºÐ¸Ð¹
Ð¸Ð½Ñ‚ÐµÑ€Ñ„ÐµÐ¹Ñ�). Ð‘Ñ�ÐºÑ�Ð½Ð´ Ð²Ñ‹Ð¿Ð¾Ð»Ð½Ñ�ÐµÑ‚ Ð¸Ð·Ð¼ÐµÑ€ÐµÐ½Ð¸Ñ� Ð¾Ñ‚ Ð´Ð°Ñ‚Ñ‡Ð¸ÐºÐ¾Ð² Ð¸ ÑƒÑ�Ñ‚Ñ€Ð¾Ð¹Ñ�Ñ‚Ð², Ð·Ð°Ñ‚ÐµÐ¼
ÐºÐ¾Ð¾Ñ€Ð´Ð¸Ð½Ð¸Ñ€ÑƒÐµÑ‚ Ñ€Ð°Ð·Ð½Ð¾Ð¾Ð±Ñ€Ð°Ð·Ð½Ñ‹Ðµ Ð¾Ñ‚Ð²ÐµÑ‚Ñ‹ Ð½Ð° Ñ�Ñ‚Ð¸ Ð¸Ð·Ð¼ÐµÑ€ÐµÐ½Ð¸Ñ�, Ð² Ñ‚Ð¾Ð¼ Ñ‡Ð¸Ñ�Ð»Ðµ
Ð²Ð¾Ð·Ð¼Ð¾Ð¶Ð½Ð¾Ñ�Ñ‚ÑŒ Ð¼Ð¾Ð´ÑƒÐ»Ð¸Ñ€Ð¾Ð²Ð°Ñ‚ÑŒ Ð²Ñ‹Ñ…Ð¾Ð´Ñ‹ (Ñ€ÐµÐ»Ðµ, Ð¨Ð˜Ðœ, Ð±ÐµÑ�Ð¿Ñ€Ð¾Ð²Ð¾Ð´Ð½Ñ‹Ðµ Ñ€Ð¾Ð·ÐµÑ‚ÐºÐ¸),
Ñ€ÐµÐ³ÑƒÐ»Ð¸Ñ€Ð¾Ð²Ð°Ñ‚ÑŒ ÑƒÑ�Ð»Ð¾Ð²Ð¸Ñ� Ð¾ÐºÑ€ÑƒÐ¶Ð°ÑŽÑ‰ÐµÐ¹ Ñ�Ñ€ÐµÐ´Ñ‹ Ñ� Ð¿Ð¾Ð¼Ð¾Ñ‰ÑŒÑŽ Ñ�Ð»ÐµÐºÑ‚Ñ€Ð¸Ñ‡ÐµÑ�ÐºÐ¸Ñ… ÑƒÑ�Ñ‚Ñ€Ð¾Ð¹Ñ�Ñ‚Ð²
Ð¿Ð¾Ð´ ÐŸÐ˜Ð”-Ñ€ÐµÐ³ÑƒÐ»Ð¸Ñ€Ð¾Ð²Ð°Ð½Ð¸ÐµÐ¼ (ÑƒÑ�Ñ‚Ð¾Ð¹Ñ‡Ð¸Ð²Ð¾Ðµ Ñ€ÐµÐ³ÑƒÐ»Ð¸Ñ€Ð¾Ð²Ð°Ð½Ð¸Ðµ Ð¸Ð»Ð¸ Ð¸Ð·Ð¼ÐµÐ½ÐµÐ½Ð¸Ðµ Ð²Ñ€ÐµÐ¼Ñ�),
Ñ€Ð°Ñ�Ð¿Ð¸Ñ�Ð°Ð½Ð¸Ðµ Ñ‚Ð°Ð¹Ð¼ÐµÑ€Ð¾Ð², Ñ�Ð±Ð¾Ñ€ Ñ„Ð¾Ñ‚Ð¾Ð³Ñ€Ð°Ñ„Ð¸Ð¹ Ð¸ Ð¿Ð¾Ñ‚Ð¾ÐºÐ¾Ð²Ð¾Ðµ Ð²Ð¸Ð´ÐµÐ¾, Ñ‚Ñ€Ð¸Ð³Ð³ÐµÑ€Ð½Ñ‹Ðµ
Ð´ÐµÐ¹Ñ�Ñ‚Ð²Ð¸Ñ�, ÐºÐ¾Ð³Ð´Ð° Ð¸Ð·Ð¼ÐµÑ€ÐµÐ½Ð¸Ñ� Ñ�Ð¾Ð¾Ñ‚Ð²ÐµÑ‚Ñ�Ñ‚Ð²ÑƒÑŽÑ‚ Ð¾Ð¿Ñ€ÐµÐ´ÐµÐ»ÐµÐ½Ð½Ñ‹Ð¼ ÑƒÑ�Ð»Ð¾Ð²Ð¸Ñ�Ð¼
(Ð¼Ð¾Ð´ÑƒÐ»Ð¸Ñ€Ð¾Ð²Ð°Ñ‚ÑŒ Ñ€ÐµÐ»Ðµ, Ð²Ñ‹Ð¿Ð¾Ð»Ð½Ñ�Ñ‚ÑŒ ÐºÐ¾Ð¼Ð°Ð½Ð´Ñ‹, ÑƒÐ²ÐµÐ´Ð¾Ð¼Ð»Ñ�Ñ‚ÑŒ Ð¿Ð¾ Ñ�Ð»ÐµÐºÑ‚Ñ€Ð¾Ð½Ð½Ð¾Ð¹ Ð¿Ð¾Ñ‡Ñ‚Ðµ
Ð¸ Ñ‚. Ð´.) Ð¸ Ð¼Ð½Ð¾Ð³Ð¾Ðµ Ð´Ñ€ÑƒÐ³Ð¾Ðµ. Ð˜Ð½Ñ‚ÐµÑ€Ñ„ÐµÐ¹Ñ� - Ñ�Ñ‚Ð¾ Ð²ÐµÐ±-Ð¸Ð½Ñ‚ÐµÑ€Ñ„ÐµÐ¹Ñ�, ÐºÐ¾Ñ‚Ð¾Ñ€Ñ‹Ð¹
Ð¾Ð±ÐµÑ�Ð¿ÐµÑ‡Ð¸Ð²Ð°ÐµÑ‚ ÑƒÐ´Ð¾Ð±Ð½ÑƒÑŽ Ð½Ð°Ð²Ð¸Ð³Ð°Ñ†Ð¸ÑŽ Ð¸ Ð½Ð°Ñ�Ñ‚Ñ€Ð¾Ð¹ÐºÑƒ Ñ� Ð»ÑŽÐ±Ð¾Ð³Ð¾ ÑƒÑ�Ñ‚Ñ€Ð¾Ð¹Ñ�Ñ‚Ð²Ð° Ñ�
Ð¿Ð¾Ð´Ð´ÐµÑ€Ð¶ÐºÐ¾Ð¹ Ð±Ñ€Ð°ÑƒÐ·ÐµÑ€Ð°.

Chinese
~~~~~~~

Mycodoæœ€åˆ�è®¾è®¡ç”¨äºŽç§�æ¤�å�¯é£Ÿç”¨çš„è˜‘è�‡ï¼Œå·²ç»�å�‘å±•åˆ°èƒ½å¤Ÿå�šæ›´å¤šçš„å·¥ä½œï¼ŒåŒ…æ‹¬ç§�æ¤�æ¤�ç‰©ï¼Œ
åŸ¹å…»å¾®ç”Ÿç‰©ï¼Œç»´æŒ�èœ‚èœœèœ‚æˆ¿ç¨³æ€�ï¼Œå­µåŒ–åŠ¨ç‰©å’Œé¸¡è›‹ï¼Œç»´æŒ�æ°´ç”Ÿç³»ç»Ÿï¼Œé™ˆå¹´å¥¶é…ªï¼Œ
å�‘é…µé£Ÿå“�å’ŒçƒŸè�‰ï¼Œçƒ¹é¥ªé£Ÿç‰©ï¼ˆsous-videï¼‰ç­‰ç­‰ã€‚

è¯¥ç³»ç»ŸåŒ…æ‹¬å�Žç«¯ï¼ˆå®ˆæŠ¤è¿›ç¨‹ï¼‰å’Œå‰�ç«¯ï¼ˆç”¨æˆ·ç•Œé�¢ï¼‰ã€‚å�Žç«¯ä»Žä¼ æ„Ÿå™¨å’Œè®¾å¤‡è¿›è¡Œæµ‹é‡�ï¼Œ
ç„¶å�Žå��è°ƒå¯¹è¿™äº›æµ‹é‡�çš„å�„ç§�å“�åº”ï¼ŒåŒ…æ‹¬è°ƒåˆ¶è¾“å‡ºï¼ˆç»§ç”µå™¨ï¼ŒPWMï¼Œæ— çº¿æ�’åº§ï¼‰çš„èƒ½åŠ›ï¼Œ
é€šè¿‡PIDæŽ§åˆ¶çš„ç”µæ°”è®¾å¤‡è°ƒèŠ‚çŽ¯å¢ƒæ�¡ä»¶ï¼ˆç¨³å®šè°ƒèŠ‚æˆ–è½¬æ�¢æ—¶é—´ï¼‰ï¼Œå®‰æŽ’è®¡æ—¶å™¨ï¼Œæ�•èŽ·ç…§ç‰‡å’Œæµ�è§†é¢‘ï¼Œ
åœ¨æµ‹é‡�æ»¡è¶³ç‰¹å®šæ�¡ä»¶æ—¶è§¦å�‘åŠ¨ä½œï¼ˆè°ƒåˆ¶ç»§ç”µå™¨ï¼Œæ‰§è¡Œå‘½ä»¤ï¼Œé€šè¿‡ç”µå­�é‚®ä»¶é€šçŸ¥ç­‰ï¼‰
ç­‰ç­‰ã€‚å‰�ç«¯æ˜¯ä¸€ä¸ªWebç•Œé�¢ï¼Œå�¯ä»¥ä»Žä»»ä½•æ”¯æŒ�æµ�è§ˆå™¨çš„è®¾å¤‡è½»æ�¾å¯¼èˆªå’Œé…�ç½®ã€‚


.. |Build Status| image:: https://travis-ci.org/kizniche/Mycodo.svg?branch=master
   :target: https://travis-ci.org/kizniche/Mycodo
.. |Codacy Badge| image:: https://api.codacy.com/project/badge/Grade/5b9c21d5680f4f7fb87df1cf32f71e80
   :target: https://www.codacy.com/app/Mycodo/Mycodo?utm_source=github.com&utm_medium=referral&utm_content=kizniche/Mycodo&utm_campaign=Badge_Grade
.. |DOI| image:: https://zenodo.org/badge/30382555.svg
   :target: https://zenodo.org/badge/latestdoi/30382555
.. |Mycodo| image:: http://kylegabriel.com/projects/wp-content/uploads/sites/3/2016/05/Mycodo-3.6.0-tango-Graph-2016-05-21-11-15-26.png
   :target: http://kylegabriel.com/projects/
