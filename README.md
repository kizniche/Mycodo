---------------------------------------------------------------------------
Title: Automated Mushroom Cultivator  
Author: Kyle T. Gabriel  
Date: 2012-2015  
Version: 1.9

Description: This is a system designed for the Raspberry Pi, for regulating
the temperature and humidity of an airspace with the use of a DHT22
temperature/humidity sensor and relays that control a heater, humidifier,
and fans. It is written in html, php, python, C, and bash script. Cron is
used to periodically write sensor data to a log file. This data is
periodically checked and if the temperature or humidity is outside the set
range, the heater, humidifier, and/or fans will modulate until all
environmental conditions are back within the set range. An authenticated
php-web interface is available for viewing the data history on a graphical
plot as well as to change configuration parameters.

---------------------------------------------------------------------------

TODO
----

- [x] Authorization log (for successful and unsuccessful logins)  
- [ ] Support naming/renaming relay identifier from the web interface  
- [ ] Support Raspberry Pi camera module for video/snapshot monitoring and timelapse photography  
- [ ] Support for more than one temperature/humidity sensor  
- [ ] Support for guest login (view only)  
- [ ] Update user interface  
  - [ ] Tabs instead of link menus  
  - [ ] Graphics (temperature, humidity, time, date, etc.)  
  - [ ] Touch screen improvements


INTRODUCTION
============

   This installation assumes you are starting with a fresh install of
Raspbian linux on your Raspberry Pi. If not, please adjust your install
accordingly.

   This README is a work in progress. This system is currently undergoing a
redesign, to expand the number of relays from 4 to 8, and to add support for
the Raspberry Pi camera module for remote viewing. The hardware upgrade is
nearly complete. At that time, there will be code updates to support the new
hardware.


HARDWARE
--------

* Raspberry Pi
* DHT22 Temperature/humidity sensor
* Relays (Keyes Funduino 4 board, but any opto-isolated relays will do)
* Humidifier
* Heater
* Circulatory Fan
* Exhaust Fan (HEPA filter recommended)


SOFTWARE
--------

* git
* apache2
* gnuplot
* php
* python
* libconfig-dev
* build-essential
* Adafruit_Python_DHT
* gpio (WiringPi)

INSTALL
=======


Hardware Setup
--------------

Relay1, Exhaust Fan: GPIO 23, pin 16  
Relay2, Humidifier: GPIO 22, pin 15  
Relay3, Circulatory Fan: GPIO 18, pin 12  
Relay4, Heater: GPIO 17, pin 11  
DHT22 sensor: GPIO 4, pin 7  
DHT22 Power: 3.3v, pin 1  
Relays and DHT22 Ground: Ground, pin 6  


Software Setup
--------------
```
sudo apt-get update
```

```
sudo apt-get upgrade
```

```
sudo apt-get install apache2 build-essential python-dev gnuplot git-core libconfig-dev
```

Download the latest code for the controller/web interface, WireingPi, and Adafruit_Python_DHT

```
sudo git clone https://github.com/kizniche/Automated-Mushroom-Cultivator /var/www/mycodo
```

```
sudo git clone git://git.drogon.net/wiringPi /var/www/mycodo/source/WiringPi
```

```
sudo git clone https://github.com/adafruit/Adafruit_Python_DHT /var/www/mycodo/source/Python_DHT
```

Compile temperature/humidity controller

```
gcc /var/www/mycodo/source/mycodo-1.9.c -I/usr/local/include -L/usr/local/lib -lconfig -lwiringPi -o /var/www/mycodo/cgi-bin/mycodo
```

Compile WiringPi and DHT python library

```
cd /var/www/mycodo/source/WiringPi
```

```
sudo ./build
```

```
cd /var/www/mycodo/source/Python_DHT
```

```
sudo python setup.py install
```

Apache Setup
----------------

There is an `.htaccess` file in each directory that denys web access to these folders. It is strongly recommended that you make sure this works properly, to ensure no one can read from these directories, as log, configuration, and graph images are stored there.

Generate an SSL certificate, enable SSL/HTTPS in apache, then add the following to /etc/apache2/sites-avalable/default-ssl, or modify to suit your needs.

	DocumentRoot /var/www
    <Directory />
         Order deny,allow
         Deny from all
    </Directory>
	<Directory /var/www/mycodo>
        Options Indexes FollowSymLinks MultiViews
        Order allow,deny
        allow from all
    </Directory>


Web Interface Setup
-------------------

To create login credentials for the web interface, uncomment line 25 of auth.php and go to http://localhost/graph/index.php

Enter a password in the password field and click submit, then Copy the Hash from the next page and replace the warning in the quotes of $Password1 or $Password2 of auth.php.

Don't forget to change the user name in auth.php to your choosing and re-comment line 25.


Automation Setup
----------------

Once the following cron jobs are set, the relays may become energized, depending on what the ranges are set. Check that the sensors are properly working by testing if the script 'mycodo-sense.sh -d' can display sensor data, as well as if gpio can alter the GPIO, with 'gpio write [pin] [value], where pin is the GPIO pin and value is 1=on and 0=off.

   Set up sensor data logging and relay changing by adding the following lines to cron (with 'sudo crontab -e')

```
*/2 * * * * /usr/bin/python /var/www/mycodo/cgi-bin/sense.py -w /var/www/mycodo/log/sensor.log
```

````
*/2 * * * * /var/www/mycodo/cgi-bin/mycodo-auto.sh
```

Go to http://localhost/graph/index.php and log in with the credentials created earlier. You should see the menu to the left displaying the current humidity and temperature, and a graph to the right with the corresponding values.



Updates
=======

Congratulations on using my software, however it may not be the latest version, or it may have been altered if not obtained through an official distribution site. You should be able to find the latest version on github or my web site.

https://github.com/kizniche/Automated-Mushroom-Cultivator  
http://KyleGabriel.com


								- Kyle Gabriel -
								