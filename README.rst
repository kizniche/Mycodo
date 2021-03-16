Mycodo
======

Environmental Regulation System

Latest version: 8.9.2

Mycodo is open source software for the Raspberry Pi that couples inputs and outputs in interesting ways to sense and manipulate the environment.

|Build Status| |Codacy Badge| |DOI|

`Mycodo Manual <https://kizniche.github.io/Mycodo>`__

`Mycodo API <https://kizniche.github.io/Mycodo/mycodo-api.html>`__ (Latest Version: v1)

`Mycodo Support Android App <https://play.google.com/store/apps/details?id=com.mycodo.mycododocs>`__

`Mycodo Wiki <https://github.com/kizniche/Mycodo/wiki>`__

`Mycodo Custom Inputs and Controllers Repository <https://github.com/kizniche/Mycodo-custom>`__

For technical support discussion, use the `Mycodo Forum <https://kylegabriel.com/forum>`__

Donate
------

I have always made Mycodo free and I don't intend on changing that. However, if you find Mycodo useful and would like to support its continued development, please consider becoming a sponsor at `github.com/sponsors/kizniche <https://github.com/sponsors/kizniche>`__ or donate at `kylegabriel.com/donate <https://kylegabriel.com/donate>`__.

--------------

.. contents:: Table of Contents
   :depth: 1

Features
--------

-  `Inputs <https://kizniche.github.io/Mycodo/Inputs/>`__ that record measurements from sensors, GPIO pin states, analog-to-digital converters, and more (or create your own `Custom Inputs <#custom-inputs>`__).
-  `Outputs <https://kizniche.github.io/Mycodo/Outputs/>`__ that perform actions such as switching GPIO pins high/low, generating PWM signals, executing shell scripts and Python code, and more (or create your own `Custom Outputs <#custom-outputs>`__).
-  `Functions <https://kizniche.github.io/Mycodo/Functions/>`__ that perform tasks, such as coupling Inputs and Outputs in interesting ways, such as `PID controllers <https://kizniche.github.io/Mycodo/Functions/#pid-controller>`__, `Conditional Controllers <https://kizniche.github.io/Mycodo/Functions/#conditional>`__, `Trigger Controllers <https://kizniche.github.io/Mycodo/Functions/#trigger>`__, to name a few (or create your own `Custom Functions <https://kizniche.github.io/Mycodo/Functions/#custom-functions>`__).
-  `Web Interface <https://kizniche.github.io/Mycodo/About/#web-interface>`__ for securely accessing Mycodo using a web browser on your local network or anywhere in the world with an internet connection, to view and configure the system, which includes several light and dark themes.
-  `Dashboards <https://kizniche.github.io/Mycodo/Data-Viewing/#dashboard>`__ that display configurable widgets, including interactive live and historical graphs, gauges, output state indicators, measurements, and more (or create your own `Custom Widgets <https://kizniche.github.io/Mycodo/Widgets/#custom-widgets>`__).
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

My projects
~~~~~~~~~~~

-  `Hydroponic System Automation <https://kylegabriel.com/projects/2020/06/automated-hydroponic-system-build.html>`__ (`Archive <http://archive.is/mB2zc>`__)
-  `Mushroom cultivation <https://kylegabriel.com/projects/2015/04/mushroom-cultivation-revisited.html>`__ (`Archive <http://archive.is/J92Xa>`__)
-  `Ground-based plant cultivation <https://www.youtube.com/watch?v=QNCx_VE7D-8>`__
-  `Maintaining honey bee apiary homeostasis <https://kylegabriel.com/projects/2015/12/environmentally-controlled-apiary.html>`__ (`Archive <http://archive.is/RLo6n>`__)
-  `Maintaining humidity in an underground artificial bat cave <https://kylegabriel.com/projects/2015/10/artificial-bat-cave.html>`__ (`Archive <http://archive.is/QIJ5G>`__)
-  `Remote radiation monitoring and mapping <https://kylegabriel.com/projects/2019/08/remote-radiation-monitoring.html>`__ (`Archive <http://archive.is/PF44Z>`__)
-  `Cooking sous-vide <https://hackaday.io/project/11997-mycodo-environmental-regulation-system/log/45733-sous-vide-pid-tuning-and-the-unexpected-electrical-fire>`__ (`Archive <http://archive.is/Mx52U>`__)
-  `Maintaining a light schedule and regulating humidity <https://fieldstation.kennesaw.edu/summer-days-2020.php#2020_07_16_gabriel_chestnut>`__, ramping from 90 % to 50 % over a 4 week period to acclimatize micropropagated American chestnut plantlets from laboratory to ambient outdoor conditions (`Archive <http://archive.is/Jp60P>`__)

Featured
~~~~~~~~

.. image:: https://kylegabriel.com/projects/wp-content/uploads/sites/3/2020/07/VID_PROJ_HYDRO_512x288.jpg
   :target: https://www.youtube.com/watch?v=nyqykZK2Ev4

Projects of others
~~~~~~~~~~~~~~~~~~

-  Maintaining aquatic systems (e.g. fish, hydroponic, aquaponic)
-  Maintaining terrarium, herpetarium, and vivarium environments
-  Incubating young animals and eggs
-  Aging cheese
-  `Dry-aging, curing, and smoking meat <http://www.charcuterie-worst.nl/forum/index.php/topic,425.0.html>`__ (`Archive <http://archive.is/NHKqp>`__)
-  Fermenting beer, food, and tobacco
-  Controlling reflow ovens
-  Culturing microorganisms
-  `Treating agricultural waste water <https://projects.sare.org/project-reports/gne17-158/>`__ (`Archive <http://archive.is/enJQs>`__)
-  ...and more

`Let me know <https://kylegabriel.com/contact/>`__ how you use Mycodo and I may include it on this list.

Screenshots
-----------

Visit the `Screenshots <https://github.com/kizniche/Mycodo/wiki/Screenshots>`__ page of the Wiki.

Install Mycodo
--------------

Prerequisites
~~~~~~~~~~~~~

-  `Raspberry Pi <https://www.raspberrypi.org>`__ single-board computer (any version: Zero, 1, 2, 3, or 4)
-  `Raspberry Pi Operating System <https://www.raspberrypi.org/downloads/raspberry-pi-os/>`__ flashed to a micro SD card
-  An active internet connection

Mycodo has been tested to work with Raspberry Pi OS Lite (2020-05-27), and also the Desktop version if using Mycodo version => 8.6.0.

Install
~~~~~~~

Once you have the Raspberry Pi booted into the Raspberry Pi OS with an internet connection, run the following command in a terminal to initiate the Mycodo install:

.. code:: bash

    curl -L https://kizniche.github.io/Mycodo/install | bash


Install Notes
~~~~~~~~~~~~~

Make sure the install script finishes without errors. A log of the output will be created at ``~/Mycodo/install/setup.log``.

If the install is successful, the web user interface should be accessible by navigating a web browser to ``https://127.0.0.1/``, replacing ``127.0.0.1`` with your Raspberry Pi's IP address. Upon your first visit, you will be prompted to create an admin user before being redirected to the login page. Once logged in, check that the time is correct at the top left of the page. Incorrect time can cause a number of issues with measurement storage and retrieval, among others. Also ensure the host name and version number at the top left of the page is green, indicating the daemon is running. Red indicates the daemon is inactive or unresponsive. Last, ensure any java-blocking plugins of your browser are disabled for all parts of the web interface to function properly.

If you receive an error during the install that you believe is preventing your system from operating, please `create an issue <https://github.com/kizniche/Mycodo/issues>`__ with the install log attached. If you would first like to attempt to diagnose the issue yourself, see `Diagnosing Issues <#diagnosing-issues>`__.

A minimal set of anonymous usage statistics are collected to help improve development. No identifying information is saved from the information that is collected and it is only used to improve Mycodo. No other sources will have access to this information. The data collected is mainly what and how many features are used, and other similar information. The data that's collected can be viewed from the 'View collected statistics' link in the ``Settings -> General`` page. There is an opt out option on the General Settings page.

Support
-------

Before making a post to the forum or issue tracker on github, please read the
`Manual <https://kizniche.github.io/Mycodo>`__.

Need assistance with Mycodo
~~~~~~~~~~~~~~~~~~~~~~~~~~~

If Mycodo is supposedly operating correctly and you would like assistance with how to configure the system or to merely discuss something related to Mycodo, do a search on the `Mycodo Forum <https://kylegabriel.com/forum/mycodo/>`__ for a similar discussion. If a similar topic doesn't already exist on the forum, create a new post in the appropriate subforum.

Bug in the Mycodo Software
~~~~~~~~~~~~~~~~~~~~~~~~~~

If you believe there is a bug in the Mycodo software, first search through the guthub `Issues <https://github.com/kizniche/Mycodo/issues>`__ and see if your issue has already recently been discussed or resolved. If your issue is novel or significantly mre recent than a similar one, you should create a `New Issue <https://github.com/kizniche/Mycodo/issues/new>`__. When creating a new issue, make sure to read all information in the issue template and follow the instructions. Replace the template text with the information being requested (e.g. "step 1" under "Steps to Reproduce the issue" should be replaced with the actual steps to reproduce the issue). The more information you provide, the easier it is to reproduce and diagnose the issue. If the issue is not able to reproduced because not enough information is provided, it may delay or prevent solving the issue.

Manual
------

The Mycodo Manual may be found at `https://kizniche.github.io/Mycodo <https://kizniche.github.io/Mycodo>`__

The `Mycodo Wiki <https://github.com/kizniche/Mycodo/wiki>`__ also contains useful information.

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

All supported Inputs, Outputs, and other devices can be found under the `Supported Devices <https://kizniche.github.io/Mycodo/Input-Devices/>`__ section of the manual.

Custom Inputs, Outputs, and Controllers
---------------------------------------

Mycodo supports importing custom Input, Output, and Controller modules. you can find more information about each in the manual under `Custom Inputs <https://kizniche.github.io/Mycodo/Inputs/#custom-inputs>`__, `Custom Outputs <https://kizniche.github.io/Mycodo/Outputs/#custom-outputs>`__, and `Custom Functions <https://kizniche.github.io/Mycodo/Functions/#custom-functions>`__.

If you would like to add to the list of supported Inputs, Outputs, and Controllers, submit a pull request with the module you created or start a `New Issue <https://github.com/kizniche/Mycodo/issues/new?assignees=&labels=&template=feature-request.md&title=>`__.

Additionally, I have another github repository devoted to custom Inputs, Outputs, and Controllers that do not necessarily fit with the built-in set and are not included by default with Mycodo, but can be imported. These can be found at `kizniche/Mycodo-custom <https://github.com/kizniche/Mycodo-custom>`__.

Links
-----

Thanks for using and supporting Mycodo, however depending where you found this documentation, you may not have the latest version or it may have been altered, if not obtained through an official distribution site. You should be able to find the latest version on github or my web site at the following links.

https://github.com/kizniche/Mycodo

https://KyleGabriel.com

License
-------

See `License.txt <https://github.com/kizniche/Mycodo/blob/master/LICENSE.txt>`__

Mycodo is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.

Mycodo is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the `GNU General Public License <http://www.gnu.org/licenses/gpl-3.0.en.html>`__ for more details.

A full copy of the GNU General Public License can be found at http://www.gnu.org/licenses/gpl-3.0.en.html

This software includes third party open source software components. Please see individual files for license information, if applicable.

Languages
---------

-  Native: English
-  Complete: `Dutch <#dutch>`__,
   `German <#german>`__,
   `French <#french>`__,
   `Italian <#italian>`__,
   `Norwegian <#norwegian>`__,
   `Polish <#polish>`__,
   `Portuguese <#portuguese>`__,
   `Russian <#russian>`__,
   `Serbian <#serbian>`__,
   `Spanish <#spanish>`__,
   `Swedish <#swedish>`__,
   `Chinese <#chinese>`__.

By default, mycodo will display the default language set by your browser. You may also force a language in the settings at ``[Gear Icon] -> Configure -> General -> Language``

If you would like to improve the translations, you can submit a pull request with an amended .po file from ~/Mycodo/mycodo/mycodo_flask/translations/ or start a `New Issue <https://github.com/kizniche/Mycodo/issues/new>`__ detailing the corrections.

English
~~~~~~~

The native language used in the software.

Dutch
~~~~~

Mycodo is een geautomatiseerd monitoring- en regelsysteem dat is gebouwd
om op de Raspberry Pi te draaien (versies Zero, 1, 2, 3 en 4).

Oorspronkelijk ontworpen om eetbare paddenstoelen te kweken, is Mycodo
uitgegroeid tot het vermogen om veel meer te doen, waaronder het kweken
van planten, het kweken van micro-organismen, het onderhouden van
bijenbijen bij de bijen, het incuberen van dieren en eieren, het
onderhouden van aquatische systemen, het ouder worden van kazen, het
fermenteren van voedsel en tabak, het koken eten (sous-vide) en meer.

Het systeem bestaat uit een backend (daemon) en een frontend
(gebruikersinterface). De backend voert metingen uit van sensoren en
apparaten, coördineert vervolgens een diverse reeks antwoorden op die
metingen, inclusief het vermogen om outputs te moduleren (relais, PWM,
draadloze outlets), omgevingsomstandigheden te regelen met elektrische
apparaten onder PID-regeling (gestage regeling of omschakeling tijd),
timers plannen, foto's maken en video streamen, acties activeren wanneer
metingen aan bepaalde voorwaarden voldoen (relais moduleren, opdrachten
uitvoeren, per e-mail op de hoogte stellen, etc.) en meer. De frontend is
een webinterface die gemakkelijke navigatie en configuratie mogelijk
maakt vanaf elk apparaat met een browser.

French
~~~~~~

Mycodo est un système de surveillance et de régulation automatisé conçu
pour fonctionner sur le Raspberry Pi (versions zéro, 1, 2, 3 et 4).

Conçu à l'origine pour cultiver des champignons comestibles, Mycodo s'est
développé pour inclure la capacité de faire beaucoup plus, notamment la
culture de plantes, la culture de micro-organismes, le maintien de
l'homéostasie du rucher des abeilles, la mise en incubation des animaux
et des œufs, la maintenance des systèmes aquatiques, le vieillissement
des fromages, la fermentation nourriture (sous vide), et plus.

Le système comprend un serveur (démon) et une interface utilisateur
(interface utilisateur). Le système effectue des mesures à partir de
capteurs et d’appareils, puis coordonne un ensemble divers de réponses à
ces mesures, notamment la possibilité de moduler les sorties (relais,
PWM, prises sans fil), de réguler les conditions environnementales avec
des appareils électriques sous contrôle PID (régulation continue ou
basculement temps), planifiez des minuteries, capturez des photos et des
flux vidéo, déclenchez des actions lorsque les mesures répondent à
certaines conditions (moduler des relais, exécuter des commandes, notifier
par courrier électronique, etc.), etc. L'interface Web est une interface
Web qui facilite la navigation et la configuration à partir de tout
appareil compatible avec le navigateur.

German
~~~~~~

Mycodo ist ein automatisiertes Überwachungs- und Regulierungssystem, das
für den Raspberry Pi (Versionen Zero, 1, 2, 3 und 4) entwickelt wurde.

Ursprünglich für die Kultivierung von Speisepilzen konzipiert, hat Mycodo
die Fähigkeit zu weitaus mehr erweitert, darunter die Kultivierung von
Pflanzen, die Kultivierung von Mikroorganismen, die Aufrechterhaltung der
Homöostase der Bienenhaus-Bienenhäuser, die Inkubation von Tieren und
Eiern, die Aufrechterhaltung von Wassersystemen, das Altern von Käse, das
Gären von Lebensmitteln und Tabak sowie das Kochen Essen (Sous-Vide) und
mehr.

Das System besteht aus einem Backend (Daemon) und einem Frontend
(Benutzeroberfläche). Das Backend führt Messungen von Sensoren und Geräten
durch und koordiniert dann eine Vielzahl von Reaktionen auf diese
Messungen, einschließlich der Möglichkeit, Ausgänge (Relais, PWM,
drahtlose Ausgänge) zu modulieren und Umgebungsbedingungen mit elektrischen
Geräten unter PID-Steuerung zu regulieren (stetige Regelung oder
Umschaltung) Zeit), Zeitpläne planen, Fotos aufnehmen und Videos streamen,
Aktionen auslösen, wenn Messungen bestimmte Bedingungen erfüllen (Relais
modulieren, Befehle ausführen, per E-Mail benachrichtigen usw.) und vieles
mehr. Das Frontend ist eine Weboberfläche, die eine einfache Navigation und
Konfiguration von jedem Browser-fähigen Gerät aus ermöglicht.

Italian
~~~~~~~

Mycodo è un sistema di monitoraggio e regolazione automatico che è stato
creato per funzionare sul Raspberry Pi (versioni Zero, 1, 2, 3 e 4).

Originariamente progettato per coltivare funghi commestibili, Mycodo è
cresciuto fino a comprendere la capacità di fare molto di più, coltivando
piante, coltivando microrganismi, mantenendo l'omeostasi delle api apistiche
del miele, incubando animali e uova, mantenendo sistemi acquatici, formaggi
stagionati, alimenti fermentati e tabacco, cucinando cibo (sous-vide) e
altro ancora.

Il sistema comprende un backend (demone) e un frontend (interfaccia utente).
Il back-end esegue misurazioni da sensori e dispositivi, quindi coordina un
insieme diversificato di risposte a tali misurazioni, inclusa la possibilità
di modulare le uscite (relè, PWM, prese wireless), regola le condizioni
ambientali con dispositivi elettrici sotto controllo PID (regolazione costante
o commutazione tempo), programmare i timer, acquisire foto e trasmettere
video, attivare azioni quando le misurazioni soddisfano determinate condizioni
(modulazione di relè, esecuzione di comandi, notifica via e-mail, ecc.) e
altro. Il frontend è un'interfaccia web che consente una facile navigazione e
configurazione da qualsiasi dispositivo abilitato per il browser.

Norwegian
~~~~~~~~~

Mycodo er et automatisert overvåkings- og reguleringssystem som ble bygget
for å kjøre på Raspberry Pi (versjoner Zero, 1, 2, 3 og 4).

Mycodo er opprinnelig utviklet for å dyrke spiselige sopp, og har vokst
til å inkludere muligheten til å gjøre mye mer, inkludert dyrking av
planter, dyrking av mikroorganismer, opprettholder honningbi apiary
homeostasis, inkubering av dyr og egg, opprettholde akvatiske systemer,
aldrende oster, fermenterende matvarer og tobakk, matlaging mat (sous-vide)
og mer.

Systemet består av en backend (daemon) og en frontend (brukergrensesnitt).
Backend utfører målinger fra sensorer og enheter, og koordinerer deretter
et mangfoldig sett med svar på disse målingene, inkludert muligheten til å
modulere utganger (reléer, PWM, trådløse uttak), regulere miljøforhold med
elektriske enheter under PID-kontroll (stabil regulering eller endring over
tid), planlegge timere, ta bilder og streame video, utløse handlinger når
målingene oppfyller visse forhold (modulere reléer, utføre kommandoer,
varsle via e-post, etc.) og mer. Frontend er et webgrensesnitt som gjør det
enkelt å navigere og konfigurere fra hvilken som helst nettleseraktivert
enhet.

Polish
~~~~~~

Mycodo to zautomatyzowany system monitorowania i regulacji, który został zbudowany do pracy na Raspberry Pi (wersje Zero, 1, 2 i 3).

Pierwotnie zaprojektowany do uprawy grzybów jadalnych, Mycodo rozwinęło się, aby umożliwić znacznie więcej, w tym uprawę roślin, hodowlę mikroorganizmów, utrzymanie homeostazy pszczół miodnych, inkubację zwierząt i jaj, utrzymanie systemów wodnych, dojrzewanie serów, fermentację żywności i tytoniu, gotowanie jedzenie (sous-vide) i nie tylko.

System składa się z zaplecza (demona) i frontendu (interfejsu użytkownika). Backend przeprowadza pomiary z czujników i urządzeń, a następnie koordynuje zróżnicowany zestaw odpowiedzi na te pomiary, w tym możliwość modulacji wyjść (przekaźniki, PWM, wyjścia bezprzewodowe), regulację warunków środowiskowych za pomocą urządzeń elektrycznych pod kontrolą PID (regulacja stała lub przełączanie czas), ustawianie timerów, robienie zdjęć i strumieniowanie wideo, wyzwalanie działań, gdy pomiary spełniają określone warunki (modulacja przekaźników, wykonywanie poleceń, powiadamianie przez e-mail itp.) i nie tylko. Frontend to interfejs sieciowy, który umożliwia łatwą nawigację i konfigurację z dowolnego urządzenia obsługującego przeglądarkę.

Portuguese
~~~~~~~~~~

O Mycodo é um sistema automatizado de monitoramento e regulação que foi
construído para rodar no Raspberry Pi (versões Zero, 1, 2, 3 e 4).

Originalmente concebido para cultivar cogumelos comestíveis, o Mycodo
cresceu para incluir a capacidade de fazer muito mais, incluindo cultivar
plantas, cultivar microorganismos, manter a homeostase do apiário de
abelhas, incubar animais e ovos, manter sistemas aquáticos, queijos
envelhecidos, fermentar alimentos e tabaco, cozinhar comida (sous-vide) e
muito mais.

O sistema compreende um backend (daemon) e um frontend (interface de
usuário). O backend conduz medições a partir de sensores e dispositivos e
coordena um conjunto diversificado de respostas a essas medições,
incluindo a capacidade de modular saídas (relés, PWM, tomadas sem fio),
regular as condições ambientais com dispositivos elétricos sob controle
PID (regulação estável ou troca tempo), agendar cronômetros, capturar
fotos e transmitir vídeo, acionar ações quando as medições atenderem a
determinadas condições (modular relés, executar comandos, notificar por
e-mail etc.) e muito mais. O frontend é uma interface da web que permite
fácil navegação e configuração a partir de qualquer dispositivo habilitado
para navegador.

Russian
~~~~~~~

Mycodo - это автоматизированная система мониторинга и регулирования,
созданная для работы на Raspberry Pi (версии Zero, 1, 2, 3 и 4).

Первоначально разработанный для выращивания съедобных грибов, Mycodo
вырос и теперь способен делать гораздо больше, включая выращивание
растений, выращивание микроорганизмов, поддержание гомеостаза пасеки
медоносных пчел, инкубацию животных и яиц, поддержание водных систем,
старение сыров, ферментацию продуктов и табака, приготовление пищи. еда
(sous-vide) и многое другое.

Система включает в себя бэкэнд (демон) и интерфейс (пользовательский
интерфейс). Бэкэнд проводит измерения от датчиков и устройств, затем
координирует разнообразный набор ответов на эти измерения, включая
возможность модулировать выходы (реле, ШИМ, беспроводные выходы),
регулировать условия окружающей среды с помощью электрических устройств
под управлением ПИД (постоянное регулирование или переключение). время),
планировать таймеры, захватывать фотографии и потоковое видео, запускать
действия, когда измерения соответствуют определенным условиям
(модулировать реле, выполнять команды, отправлять уведомления по
электронной почте и т. д.) и многое другое. Интерфейс представляет собой
веб-интерфейс, который обеспечивает простую навигацию и настройку с любого
устройства с поддержкой браузера.

Serbian
~~~~~~~

Мицодо је аутоматски систем за надзор и регулацију који је направљен да
ради на Распберри Пи (верзије Зеро, 1, 2, 3 и 4).

Оригинално дизајниран за узгајање јестивих гљива, Мицодо је нарастао на
могућност да уради много више, укључујући култивирање биљака, култивисање
микроорганизама, одржавање хомеостазе пчелињег меда, инкубирање животиња
и јаја, одржавање водених система, старење сирева, ферментисање хране и
дуван, кухање храна (соус-виде), и више.

Систем садржи бацкенд (даемон) и фронтенд (кориснички интерфејс). Бацкенд
врши мерења од сензора и уређаја, затим координира различите одговоре на
та мерења, укључујући могућност модулације излаза (релеји, ПВМ, бежичне
утичнице), регулисање услова околине са електричним уређајима под ПИД
контролом (стална регулација или промена време), распоред времена, снимање
фотографија и стримовање видео снимака, акције покретања када мерења
испуњавају одређене услове (модулација релеја, извршавање команди,
обавештавање путем е-поште, итд.), и још много тога. Фронтенд је веб
интерфејс који омогућава једноставну навигацију и конфигурацију са било
ког уређаја са омогућеним претраживачем.

Spanish
~~~~~~~

Mycodo es un sistema automatizado de monitoreo y regulación que fue creado
para ejecutarse en la Raspberry Pi (versiones cero, 1, 2, 3 y 4).

Originalmente diseñado para cultivar hongos comestibles, Mycodo ha crecido
para incluir la capacidad de hacer mucho más, incluido el cultivo de plantas,
el cultivo de microorganismos, el mantenimiento de la homeostasis de las
abejas, la incubación de animales y huevos, el mantenimiento de los sistemas
acuáticos, el envejecimiento de los quesos, la fermentación de alimentos y el
tabaco, la cocina. comida (sous-vide), y más.

El sistema comprende un backend (daemon) y un frontend (interfaz de usuario).
El backend realiza mediciones desde sensores y dispositivos, luego coordina
un conjunto diverso de respuestas a esas mediciones, incluida la capacidad
de modular salidas (relés, PWM, salidas inalámbricas), regular las
condiciones ambientales con dispositivos eléctricos bajo control PID
(regulación constante o cambio tiempo), programe temporizadores, capture
fotos y transmita videos, active acciones cuando las mediciones cumplan
ciertas condiciones (module relés, ejecute comandos, notifique por correo
electrónico, etc.) y más. La interfaz es una interfaz web que permite una
fácil navegación y configuración desde cualquier dispositivo con navegador.

Swedish
~~~~~~~

Mycodo är ett automatiserat övervaknings- och reglersystem som byggdes
för att springa på Raspberry Pi (versioner noll, 1, 2, 3 och 4).

Mycodo har ursprungligen utformats för att odla ätliga svampar, och har
därmed ökat möjligheten att göra mycket mer, inklusive odling av växter,
odlingsmikroorganismer, upprätthållande av honeybee apiary homeostasis,
inkubering av djur och ägg, upprätthållande av vattenlevande system,
åldrande ostar, jäsning av mat och tobak, matlagning mat (sous-vide)
och mer.

Systemet innefattar en backend (daemon) och en frontend
(användargränssnitt). Bakgrunden utför mätningar från sensorer och
enheter och samordnar sedan en mängd olika svar på dessa mätningar,
inklusive möjligheten att modulera utgångar (reläer, PWM, trådlösa
uttag), reglera miljöförhållandena med elektriska enheter under
PID-kontroll (ständig reglering eller byte över tid), schemalägg timer,
ta bilder och strömma video, utlös åtgärder när mätningar uppfyller
vissa villkor (modulera reläer, utföra kommandon, meddela via e-post
etc.) och mer. Frontend är ett webbgränssnitt som möjliggör enkel
navigering och konfiguration från alla webbläsaraktiverade enheter.

Chinese
~~~~~~~

Mycodo是一个自动监控和调节系统，可在Raspberry Pi上运行（版本为Zero，1,2,3和4）。

Mycodo最初设计用于种植可食用的蘑菇，已经发展到能够做更多的事情，包括种植植物，培养微生物，保持蜂蜜蜂房稳态，孵化动物和鸡蛋，维持水生系统，陈年奶酪，发酵食品和烟草，烹饪食物（sous-vide）等等。

该系统包括后端（守护进程）和前端（用户界面）。后端从传感器和设备进行测量，然后协调对这些测量的各种响应，包括调制输出（继电器，PWM，无线插座）的能力，通过PID控制的电气设备调节环境条件（稳定调节或转换时间），安排计时器，捕获照片和流视频，在测量满足特定条件时触发操作（调制继电器，执行命令，通过电子邮件通知等）等等。前端是一个Web界面，可以从任何支持浏览器的设备轻松导航和配置。


.. |Build Status| image:: https://travis-ci.com/kizniche/Mycodo.svg?branch=master
   :target: https://travis-ci.com/kizniche/Mycodo
.. |Codacy Badge| image:: https://api.codacy.com/project/badge/Grade/5b9c21d5680f4f7fb87df1cf32f71e80
   :target: https://www.codacy.com/app/Mycodo/Mycodo?utm_source=github.com&utm_medium=referral&utm_content=kizniche/Mycodo&utm_campaign=Badge_Grade
.. |DOI| image:: https://zenodo.org/badge/DOI/10.5281/zenodo.824199.svg
   :target: https://doi.org/10.5281/zenodo.824199
.. |Mycodo| image:: https://kylegabriel.com/projects/wp-content/uploads/sites/3/2016/05/Mycodo-3.6.0-tango-Graph-2016-05-21-11-15-26.png
   :target: https://kylegabriel.com/projects/

Thanks
------

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
-  `Flask_RESTX <https://pypi.org/project/flask_restx>`__
-  `Flask_SQLAlchemy <https://pypi.org/project/flask_sqlalchemy>`__
-  `Flask_Talisman <https://pypi.org/project/flask_talisman>`__
-  `Flask_WTF <https://pypi.org/project/flask_wtf>`__
-  `FontAwesome <https://fontawesome.com>`__
-  `Geocoder <https://pypi.org/project/geocoder>`__
-  `gridstack.js <https://github.com/gridstack/gridstack.js>`__
-  `Gunicorn <https://gunicorn.org>`__
-  `Highcharts <https://www.highcharts.com>`__
-  `InfluxDB <https://github.com/influxdata/influxdb>`__
-  `jQuery <https://jquery.com>`__
-  `Marshmallow_SQLAlchemy <https://pypi.org/project/marshmallow_sqlalchemy>`__
-  `Pyro5 <https://github.com/irmen/Pyro5>`__
-  `SQLAlchemy <https://www.sqlalchemy.org>`__
-  `SQLite <https://www.sqlite.org>`__
-  `toastr <https://github.com/CodeSeven/toastr>`__
-  `WTForms <https://pypi.org/project/wtforms>`__
