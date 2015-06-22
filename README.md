# Mycodo

   Originally designed for gourmet mushroom cultivation, Mycodo is a system that regulates the temperature and humidity of an airspace with PID control. It utilizes a temperature/humidity sensor to monitor the environment and software PID controllers to modulate any of 8 relays for powering devices to alter the environment. A web-interface features viewing of current and past conditions as well as graph generation, configuration modification, and image and video acquisition, to name a few (a full list of features is below).
   
   The main application, mycodo.py, runs in the background as a daemon. It performs all crucial tasks, such as periodically reading sensors, writing sensor and relay logs, turning timer-activated relays on and off, running PID controllers for temperature and humidity regulation, and reading and writing to the configuration file, among others.
   
   The client application, mycodo-client.py, communicates and issues commands for the daemonized mycodo.py to carry out, such as specific configuration changes, relay changes, turning automation on and off, to name a few.
   
   The HTTP control interface runs on a common LAMP (Linux Apache MySQL PHP/Python) system.

#### Index

+ [History](#history)
+ [Features](#feat)
+ [Todo](#future)
+ [Hardware Brief](#hard-brief)
+ [Software Brief](#soft-brief)
+ [Installation](#instructions)
    - [Software](#soft-setup)
    - [TempFS](#tempfs)
    - [Apache2](#apache2)
    - [MySQL and User Login](#mysql)
    - [Sensor and Relay](#sensor-relay)
    - [Daemon](#cron)
+ [Web Interface login](#web-interface)
+ [Useful Links](#links)

<a name="history"></a>
### History

This started out as a small project to regulate the temperature and humidity of a growth chamber I used for cultivating gourmet mushrooms. At that time (2010), I used an ATMega interfaced to a network-connected computer running linux. When the Raspberry Pi was introduced in 2012, I decided to migrate my code from the ATMega and my linux computer to work on this one compact device. My first relay bank consisted of 4 relays, controlling a heater, humidifier, circulatory fan, and HEPA-filtered exhaust fan.

I'm since upgraded to a new set of hardware that support 8 individually-switchable 120-volt AC outlets. The majority of the code has undergone drastic changes and feature additions.

### Features - v2.0 (old)

* Supports the DHT22 digital humidity and temperature sensor
* Manual or automatic switching of up to four 120-volt AC relays
* Automatic operation by simple proportional temperature/humidity regulation
* Temperature, humidity, and relay state-change logging
* Basic web interface
  * View historical temperature and humidity data as text and graphs
  * Generate custom graphs of current and past data
    * Presets of pre-defined time periods (past 1 hour, 6 hours, 1 day, 3 days...)
    * Specify specific time period to generate graph

<a name="feat"></a>
### Features - v3.0 (stable)

* Switch up to eight 120-volt AC relays
* Support for up to 8 simple timers (define on duration, off duration)
* True PID control for temperature and humidity regulation
* Support more humidity & temperature sensors (DHT11, DHT22, and AM2302)
* Multi-sensors support to regulate multiple environments
* TempFS to reduce writes to and extend the life of the SD card
* Lock files to prevent file access conflicts
* New web interface
  * Tabs allow everything to be loaded on one page
  * Generate new types of graphs
    * Combined: generate a graph combining all temperatures or humidities
    * Separate: generate a graph of the temperature, humidity, and dew point of each sensor
    * Define graph image width (custom graph only)
  * Acquire still image or stream live video using the Raspberry Pi camera module
  * View authorization, daemon, sensor, and relay logs
  * Easy configuration changes through the web interface
    * Edit all variables related to each sensor and relay (names, pins, durations, etc.)
    * Set desired temperature/humidity as well as respective P, I, and D variables of each PID controller
  * Login Authentication (written by php-login.net)
    * Optional cookie to keep session authenticated
    * Guest account for viewing only (no config changes permitted) (user: guest, password: anonymous)
    * Authorization log of successful and unsuccessful login attempts
    * User profile, gravatar support (from email), lost/forgot email password reset
    
### Features - v4.0-beta (experimental)

* CO2 Sensor support

<a name="future"></a>
### Todo

- [ ] Allow setting the maximum current draw of device(s) connected to each relay to ensure no combination of devices are ever activated that surpass the limit of the wiring/breaker (commonly 15 amps)
- [ ] Alarm if a critical failure has occurred (daemon stopped, critical temperature/humidity, etc.)
- [ ] Lock file for sensor reading (sensor reads too close together cause sensor instability)
- [ ] Take series of photos at different ISOs, combine to make HDR photo
- [ ] Timelapse video creation ability (define start, end, duration between, etc.)  
- [X] Logs written to TempFS and periodically concatenated with SD card logs
  - [ ] Automatic log file backup when a certain size is reached  
- [X] Support for more than one temperature/humidity sensor
  - [X] Support using multiple sensors at the same time (Maximum of 4 at the moment)
  - [ ] Expand support for sensors (limited to when/if I get sensors to test)
- [X] Update user interface  
  - [ ] Graphics (temperature, humidity, time, date, etc.)  
  - [ ] Touch screen improvements
  - [X] Tabbed interface

<a name="hard-brief"></a>
### Hardware

* Raspberry Pi
* Temperature/humidity sensor (DHT22)
* Relays (2x Crydom 1240 and 1x Keyes Funduino 8-relay board)
* Humidifier
* Heater
* Circulatory Fan
* Exhaust Fan (preferably with a HEPA filter)

<a name="soft-brief"></a>
### Software

The following software is required

* apache2
* git
* gnuplot
* mysql
* php >= 5.3.7
* phpmyadmin (optional but recommended)
* python and modules
  * Adafruit_Python_DHT
  * LockFile
  * WiringPi
* wget

<a name="instructions"></a>
# Installation

This installation assumes you are starting with a fresh install of Raspbian linux on a Raspberry Pi. If not, adjust your installation accordingly.

<a name="soft-setup"></a>
### Software

`sudo apt-get update`

`sudo apt-get upgrade`

`sudo apt-get install apache2 build-essential python-dev gnuplot git-core libconfig-dev php5 libapache2-mod-php5 pip subversion`

If you will have your RPi exposed to the internet with SSH access, I recommend installing fail2ban to monitor auth.log and ban IP addresses that fail a certain number of login attempts. This has successfully thwarted many script kiddies from mounting a useful attack on my RPi system.

`sudo apt-get install fail2ban`

Set up MySQL with the following command and create a password when prompted.

`sudo apt-get install mysql-server mysql-client`

To set up PHPMyAdmin, use the following command, then select to configure Apache2 automatically (use the spacebar to select). If prompted, allow dbconfig-common to configure the phpmyadmin database. When asked, give the same password that you created during the MySQL installation.

`sudo apt-get install phpmyadmin`

Download the latest code for Mycodo along with python modules.

`sudo svn checkout https://github.com/kizniche/Mycodo/trunk/3.0 /var/www/mycodo`

`sudo git clone git://git.drogon.net/wiringPi /var/www/mycodo/source/WiringPi`

`sudo git clone https://github.com/adafruit/Adafruit_Python_DHT /var/www/mycodo/source/Adafruit_Python_DHT`

Install WiringPi

`cd /var/www/mycodo/source/WiringPi`

`sudo ./build`

Install Adafruit_Python_DHT

`cd /var/www/mycodo/source/Adafruit_Python_DHT`

`sudo python setup.py install`

Install LockFile and RPyC

`pip install lockfile rpyc`

Set permissions for www to use the RPi camera

`echo 'SUBSYSTEM=="vchiq",GROUP="video",MODE="0660"' | sudo tee /etc/udev/rules.d/10-vchiq-permissions.rules`

`sudo usermod -a -G video www-data`

Setup streaming capabilities

`sudo apt-get install libjpeg8-dev libv4l-dev wget`

`sudo ln -s /usr/include/linux/videodev2.h /usr/include/linux/videodev.h`

`wget -P /var/www/mycodo/source http://sourceforge.net/code-snapshots/svn/m/mj/mjpg-streamer/code/mjpg-streamer-code-182.zip`

`cd /var/www/mycodo/source`

`unzip mjpg-streamer-code-182.zip`

`cd mjpg-streamer-code-182/mjpg-streamer`

`make mjpg_streamer input_file.so output_http.so`

`sudo cp mjpg_streamer /usr/local/bin`

`sudo cp output_http.so input_file.so /usr/local/lib/` 

Set permissions

`sudo chown -R www-data:www-data /var/www/mycodo`

`sudo chmod 660 /var/www/mycodo/config/* /var/www/mycodo/log/*.log`

<a name="tempfs"></a>
### TempFS

A temporary filesystem in RAM is created for areas of the disk that are written often, preserving the life of the SD card and speeding up disk read/writes. Keep in mind all contents will be deleted upon reboot. If you need to analyze logs, remember to disable these lines in fstab before doing so.

Edit fstab with `sudo vi /etc/fstab` add the following lines, then save.

```
tmpfs    /tmp    tmpfs    defaults,noatime,nosuid,size=100m    0 0
tmpfs    /var/tmp    tmpfs    defaults,noatime,nosuid,size=30m    0 0
tmpfs    /var/log    tmpfs    defaults,noatime,nosuid,mode=0755,size=100m    0 0
tmpfs    /var/run    tmpfs    defaults,noatime,nosuid,mode=0755,size=2m    0 0
tmpfs    /var/spool/mqueue    tmpfs    defaults,noatime,nosuid,mode=0700,gid=12,size=30m    0 0
```

Apache does not start if there is not a proper directory structure set up in /var/log for its log files. The creation of /var/log as a tempfs means that at every bootup this directory is empty. This script will ensure that the proper directory structure is created before Apache is started.

`sudo cp /var/www/mycodo/source/init.d/apache2-tmpfs /etc/init.d/`

`sudo chmod 0755 /etc/init.d/apache2-tmpfs`

`sudo update-rc.d apache2-tmpfs defaults 90 10`

<a name="apache2"></a>
### Apache

To resolve the IP address in the auth.log, the following line in /etc/apache2/apache2.conf needs to be changed from 'Off' to 'On', without the quotes:

`HostnameLookups On`

There is an `.htaccess` file in each directory that denies web access to these folders. It is strongly recommended that you make sure this works properly (or alternatively configure your web server to accomplish the same result), to ensure no one can read from these directories, as log, configuration, graph images, and other potentially sensitive information is stored there.

Optionally for higher security, generate an SSL certificate and enable SSL/HTTPS in apache.

Add the following to /etc/apache2/sites-available/default-ssl (or just 'default' if not using SSL), or modify to suit your needs.

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
    
<a name="mysql"></a>
### MySQL and User Login

Set up phpmyadmin to only allow trusted sources. Edit phpmyadmin.conf

`sudo vi /etc/apache2/conf.d/phpmyadmin.conf`

Add the following lines after `<Directory /usr/share/phpmyadmin>` and change YOUR-IP with the IP address you will be connecting from.

```
Order Allow,Deny
Allow from 127.0.0.1
Allow from YOUR-IP
```

Download the files in source/php-login-mysql-install to your local computer. Go to http://127.0.0.1/phpmyadmin and login with root and the password you created. Click 'Import' and select 01-create-database.sql, then click 'OK'. Repeat with the file 02-create-user-table.sql. This will wet up your MySQL database to allow user registration.

Edit the file /var/www/mycodo/config/config.php and change 'password' for the defined DB-PASS to the password you created when you installed MySQL. Completely fill out the Cookie and SMTP sections. The cookie section ensures proper cookie creation and authentication. The SMTP section is important because you will need to receive a verification email after registration. As of 3/28/2015, GMail works as a SMTP server. Just create a new account and enter the credentials in as the config file instructs.

Go to http://127.0.0.1/mycodo/register.php, enter your desired login information, click 'Register' and hope there are no errors reported. You will be sent an email to activate your user.

Revoke read access to register.php to prevent further users from being created. If this is not done, anyone can access the user registration page and create users to log in to the system.

`sudo chmod 000 /var/www/mycodo/register.php`

This can be changed back with the following command if you wish to create more users in the future.

`sudo chmod 640 /var/www/mycodo/register.php`

<a name="sensor-relay"></a>
### Sensors and Relays

A few variables need to be manually set in mycodo.cfg and tested before starting the daemon. Edit /var/www/mycodo/config/mycodo.cfg and change the values of sensor1sensor and sensor1pin. Options for sensor1device are ‘DHT11′, ‘DHT22′, and ‘AM2302′ (without the quotes) and refer to your specific RPi BCM GPIO numbering for the pin. The default is DHT22 on pin 4. After editing the config file, start up the daemon with `sudo /var/www/mycodo/cgi-bin/mycodo.py -d v d`

If set up correctly, the daemon should start and begin logging sensor data.

You can view the daemon log with

`tail /var/www/mycodo/log/daemon-tmp.log`

and the sensor log with

`tail /var/www/mycodo/log/sensor-tmp.log`

The following command should also retrieve a current temperature and humidity measurement. Change the values if your pin and device are different. Options for device are DHT11, DHT22, and AM2302.

`/var/www/mycodo/cgi-bin/mycodo-client.py -s 4 DHT22`

Connect the relays to any GPIOs that are not normally HIGH or LOW upon boot. Change the variables relayXpin and relayXtrigger, where X is the relay number. relayXpin is the BCM GPIO pin the relay is connected to, and relayXtrigger is the state at which the relay turns on, where 0 means it turns on when LOW (0-VDC) and 1 means it turns on when HIGH (5-VDC). The GPIO-initialize.py script will set the pins to output the opposite of relayXtrigger, that is if you select 1 (HIGH), the initialization script will set them to 0 (LOW) at boot.

You can test the function of the relays with the following command, replacing [RELAY] with the relay number (1 – 8) and either 0 for off or 1 for on.

`/var/www/mycodo/cgi-bin/mycodo-client.py [RELAY] [0/1]`

If you are receiving temperature and humidity data, and relays are turning on and off with mycodo-client.py, you can set the daemon to start at boot and begin using the web interface.

<a name="cron"></a>
### Daemon Setup

If you are properly receiving temperature and humidity data, set up the daemon to automatically log sensor data with the following commands:

`sudo cp /var/www/mycodo/source/init.d/mycodo /etc/init.d/`

`sudo chmod 0755 /etc/init.d/mycodo`

`sudo update-rc.d mycodo defaults`

Open crontab with `sudo crontab -e`, add the following lines, then save with `Ctrl+e`

`@reboot /usr/bin/python /var/www/mycodo/cgi-bin/GPIO-initialize.py &`

Reboot to allow everything to start up

`sudo shutdown now -r`

<a name="web-interface"></a>
### Web Interface

Go to http://127.0.0.1/mycodo/index.php and log in with the credentials created earlier. You should see the menu to the left displaying the current humidity and temperature, and a graph to the right with the corresponding values.

Select the "Config" tab and set up the proper GPIO pin numbers for your connected relays by referencing the GPIO BCM numbering for your particular board. These GPIO pins should be connected to your relay control pins. Ensure you select the proper HIGH/LOW state for when the relay turns on. For instance, if the relay turns on when there is a HIGH signal sent to it (5 volts), select HIGH, otherwise if it is energized when a LOW signal (0 volts) is sent to it, select LOW.

<a name="links"></a>
### Useful Links

Congratulations on using my software, however it may not be the latest version, or it may have been altered if not obtained through an official distribution site. You should be able to find the latest version on github or my web site.

https://github.com/kizniche/Automated-Mushroom-Cultivator  
http://KyleGabriel.com

								- Kyle Gabriel -
								
