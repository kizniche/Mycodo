# Mycodo

   A system designed around the Raspberry Pi, for regulating the temperature and humidity of an airspace. It has been specifically adapted for mushroom cultivation. It utilizes a DHT22 temperature/humidity sensor to monitor the enviroment(s) and relays to control a set of devices to alter the enviroment(s).

#### Index

+ [History](#history)
+ [Features](#feat)
+ [Todo](#future)
+ [Hardware Brief](#hard-brief)
+ [Software Brief](#soft-brief)
+ [Install Instructions](#instructions)
    - [Software Setup](#soft-setup)
    - [TempFS Setup](#tempfs)
    - [Apache2 Setup](#apache2)
    - [MySQL and User Setup](#mysql)
    - [Cron Setup](#cron)
+ [Web Interface login](#web-interface)
+ [Useful Links](#links)

<a name="history"></a>
### History of Mycodo

This started out as a small project to regulate the temperature and humidity of a chamber I grew gourmet mushrooms in. At that time, in 2010, I used an ATMega that was interfaced to a computer via USB. When the Raspberry Pi was introduced in 2012, I decided to migrate my code from the ATMega and my linux computer to work on this one compact device. My first relay bank consisted of 4 relays, controlling a heater, humidifier, circulatory fan, and HEPA-filtered exhaust fan.

I'm currently working on a new set of hardware that will support a range of new features. As such, until I unveil the new hardware, this code will be undergoing lots of updates. I hope to keep everything working throughout the update process.

<a name="feat"></a>
### Features

* Logging temperature, humidity, and relay states
* Configurable minimum and maximum allowable temperature and humidity
* Automatic operation of connected devices to raise/lower temperature and humidity
* Web-control interface
  * View raw data as well as generate graphs of current and past data
  * Acquire images or stream live video from a camera
  * Change modes of operation, such as minimum and maximum temperature/humidity
  * Independently control connected devices (turn on, off, on for [x] seconds)
  * Login Authentication (written by php-login.net)
    * Using official PHP password hashing functions and the most modern password hashing/salting web standards
    * Optional "remember me" cookie to keep session authenticated
    * Profile edit (change user name, password, or email address)
    * Gravitar support (if email used in registration is the same as on gravitar.com)
    * Lost/forgot password reset via email
    * Guest account for viewing only (user: guest, password: anonymous)
    * Authorization log of successful and unsuccessful login attempts

<a name="future"></a>
### Todo

- [ ] Timelapse video creation ability (define start, end, duration between, etc.)  
- [ ] Automatic log file backup when a certain size is reached  
- [ ] Support naming/renaming relay identifier from the web interface  
- [ ] Support for more than one temperature/humidity sensor  
- [ ] Update user interface  
  - [ ] Tabs instead of link menus  
  - [ ] Graphics (temperature, humidity, time, date, etc.)  
  - [ ] Touch screen improvements

<a name="hard-brief"></a>
### Hardware



* Raspberry Pi
* Temperature/humidity sensor (DHT22)
* Relays (2x Crydom 1240 and 1x Keyes Funduino relay board)
* Humidifier
* Heater
* Circulatory Fan
* Exhaust Fan, HEPA-filtered

Relay1, Exhaust Fan: GPIO 23, pin 16  
Relay2, Humidifier: GPIO 22, pin 15  
Relay3, Circulatory Fan: GPIO 18, pin 12  
Relay4, Heater: GPIO 17, pin 11  
DHT22 sensor: GPIO 4, pin 7  
DHT22 Power: 3.3v, pin 1  
Relays and DHT22 Ground: Ground, pin 6  

<a name="soft-brief"></a>
### Software

The following software is required

* apache2
* git
* gnuplot
* mysql
* php >= 5.3.7
* phpmyadmin
* python
* Python_DHT (Adafruit)
* wget
* WiringPi (gpio)

<a name="instructions"></a>
# Install Instructions

   This installation assumes you are starting with a fresh install of Raspbian linux on your Raspberry Pi. If not, please adjust your install accordingly.

<a name="soft-setup"></a>
### Software Setup

`sudo apt-get update`

`sudo apt-get upgrade`

`sudo apt-get install apache2 build-essential python-dev gnuplot git-core libconfig-dev php5 libapache2-mod-php5`

Download the latest code for the controller/web interface, WireingPi, and Adafruit_Python_DHT

`sudo git clone https://github.com/kizniche/Automated-Mushroom-Cultivator /var/www/mycodo`

`sudo git clone git://git.drogon.net/wiringPi /var/www/mycodo/source/WiringPi`

`sudo git clone https://github.com/adafruit/Adafruit_Python_DHT /var/www/mycodo/source/Python_DHT`

Set up MySQL with the following command and create a password when prompted.

`sudo apt-get install mysql-server mysql-client`

To set up PHPMyAdmin, use the following command, then select to configure Apache2 automatically (use the spacebar to select). If prompted, allow dbconfig-common to configure the phpmyadmin database. When asked, give the same password that you created during the MySQL installation.

`sudo apt-get install phpmyadmin`

Compile WiringPi and DHT python library

`cd /var/www/mycodo/source/WiringPi`

`sudo ./build`

Compile relay controller

`cd /var/www/mycodo/source/mycodo/1.9/ && sudo make`

`sudo mv mycodo ../../../cgi-bin/`

Install Python_DHT

`cd /var/www/mycodo/source/Python_DHT`

`sudo python setup.py install`

Set permissions for www to use the RPi camera

`sudo echo 'SUBSYSTEM=="vchiq",GROUP="video",MODE="0660"' > /etc/udev/rules.d/10-vchiq-permissions.rules`

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

Set www permissions

`sudo chown -R www-data:www-data /var/www/mycodo`

`sudo chmod 660 /var/www/mycodo/config/* /var/www/mycodo/images/*.png /var/www/mycodo/log/*.log`

<a name="tempfs"></a>
### TempFS Setup

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

`sudo cp /var/www/mycodo/source/apache2-tmpfs /etc/init.d/`

`sudo chmod 0755 /etc/init.d/apache2-tmpfs`

`sudo update-rc.d apache2-tmpfs defaults 90 10`

<a name="apache2"></a>
### Apache2 Setup

To resolve the IP address in the auth.log, the following line in /etc/apache2/apache2.conf needs to be changed from 'Off' to 'On' without the quotes.

`HostnameLookups On`

There is an `.htaccess` file in each directory that denys web access to these folders. It is strongly recommended that you make sure this works properly, to ensure no one can read from these directories, as log, configuration, and graph images, and other potentially sensitive imformation is stored there.

Generate an SSL certificate, enable SSL/HTTPS in apache, then add the following to /etc/apache2/sites-avalable/default-ssl (or just 'default' if not using SSL), or modify to suit your needs.

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
### MySQL and User Setup

Download the files in source/php-login-mysql-install to your local computer. Go to http://127.0.0.1/phpmyadmin and login with root and the password you created. Click 'Import' and select 01-create-database.sql, then click 'OK'. Repeat with the file 02-create-user-table.sql. This will wet up your MySQL database to allow registering users.

Edit the file /var/www/mycodo/config/db.php and change 'password' for the defined DB-PASS to the password you created when you installed MySQL. Fill out Cookie and SMTP section. The SMTP section is important because you will need to receive a verification email after registration. As of 3/19/2015, gmail works as a SMTP server. Just create a new account and enter the credentials in as the config file instructs.

Go to http://127.0.0.1/mycodo/register.php, enter your desired login information, then click Register and hope there are no errors reported. You will be sent an email to verify your login information. Once you get this email and click the link, you are able to login. You can verify this new user in MyPHPAdmin. It will appear in the MySQL database created earlier.

Revoke read access to register.php to prevent further users from being created.

`sudo chmod 000 /var/www/mycodo/register.php`

This can be changed back with the following command if you wish to create more users.

`sudo chmod 640 /var/www/mycodo/register.php`

<a name="cron"></a>
### Cron Setup

The following will enable automatic logging and relay control.

Once the following cron jobs are set, the relays may become energized, depending on what the ranges are set. Check that the sensors are properly working by testing if the script 'mycodo-sense.sh -d' can display sensor data, as well as if gpio can alter the GPIO, with 'gpio write [pin] [value], where pin is the GPIO pin and value is 1=on and 0=off.

   Set up sensor data logging and relay changing by adding the following lines to cron (with 'sudo crontab -e')

```
*/2 * * * * /usr/bin/python /var/www/mycodo/cgi-bin/sense.py -w /var/www/mycodo/log/sensor.log
```

````
*/2 * * * * /var/www/mycodo/cgi-bin/mycodo-auto.sh
```

<a name="web-interface"></a>
### Web Interface Login

Go to http://127.0.0.1/mycodo/index.php and log in with the credentials created earlier. You should see the menu to the left displaying the current humidity and temperature, and a graph to the right with the corresponding values.

<a name="links"></a>
### Useful Links

Congratulations on using my software, however it may not be the latest version, or it may have been altered if not obtained through an official distribution site. You should be able to find the latest version on github or my web site.

https://github.com/kizniche/Automated-Mushroom-Cultivator  
http://KyleGabriel.com


								- Kyle Gabriel -
								
