# Mycodo 3.5-beta (experimental)

This is an experimental branch of mycodo. It is undergoing constant changes and may or may not work at any time (although it has matured somewhat and is relatively stable at the moment). If you are looking for a stable version, I recommend you check out the [v3.0 branch](../3.0).

---

## Index

+ [Screenshots](#screenshots)
  + [Web Interface](#web-interface)
  + [Terminal](#terminal)
+ [Changelog](#changelog)
+ [Sensors, Devices, and Interfaces](#sensors-devices-and-interfaces)
+ [Software Install](#software-install)
  + [Prerequisites](#prerequisites)
  + [Wifi](#wifi)
  + [TempFS](#tempfs)
  + [Resolve Hosnames](#resolve-hostnames)
  + [Security](#security)
    + [Enable SSL](#enable-ssl)
    + [Enable .htaccess](#enable-htaccess)
  + [Enable mod_rewrite](#enable-mod_rewrite)
  + [Database Creation](#database-creation)
  + [Daemon](#daemon)
+ [Manual](#manual)
+ [License](#license)
+ [Useful Links](#useful-links)

---

## Screenshots

### Web Interface

<table>
  <tr>
    <td style="text-align: center">
      Graph
    </td>
    <td style="text-align: center">
      Sensor
    </td>
    <td style="text-align: center">
      Custom
    </td>
  </tr>
    <td>
      <a href="http://kylegabriel.com/projects/wp-content/uploads/sites/3/2015/09/Mycodo-3.5.75-beesl2-01-Graph.png" target="_blank"><img src="http://kylegabriel.com/projects/wp-content/uploads/sites/3/2015/09/Mycodo-3.5.75-beesl2-01-Graph-150x150.png"></a>
    </td>
    <td>
      <a href="http://kylegabriel.com/projects/wp-content/uploads/sites/3/2015/09/Mycodo-3.5.75-beesl2-01-Sensor.png" target="_blank"><img src="http://kylegabriel.com/projects/wp-content/uploads/sites/3/2015/09/Mycodo-3.5.75-beesl2-01-Sensor-150x150.png"></a>
    </td>
    <td>
      <a href="http://kylegabriel.com/projects/wp-content/uploads/sites/3/2015/09/Mycodo-3.5.75-beesl2-01-Custom.png" target="_blank"><img src="http://kylegabriel.com/projects/wp-content/uploads/sites/3/2015/09/Mycodo-3.5.75-beesl2-01-Custom-150x150.png"></a>
    </td>
  </tr>
  <tr>
    <td style="text-align: center; padding-top 1em;">
      Camera
    </td>
    <td style="text-align: center; padding-top 1em;">
      Data
    </td>
    <td style="text-align: center; padding-top 1em;">
      Settings
    </td>
  </tr>
  <tr>
    <td>
      <a href="http://kylegabriel.com/projects/wp-content/uploads/sites/3/2015/09/Mycodo-3.5.75-beesl2-01-Camera.png" target="_blank"><img src="http://kylegabriel.com/projects/wp-content/uploads/sites/3/2015/09/Mycodo-3.5.75-beesl2-01-Camera-150x150.png"></a>
    </td>
    <td>
      <a href="http://kylegabriel.com/projects/wp-content/uploads/sites/3/2015/09/Mycodo-3.5.75-beesl2-01-Data.png" target="_blank"><img src="http://kylegabriel.com/projects/wp-content/uploads/sites/3/2015/09/Mycodo-3.5.75-beesl2-01-Data-150x150.png"></a>
    </td>
    <td>
      <a href="http://kylegabriel.com/projects/wp-content/uploads/sites/3/2015/09/Mycodo-3.5.75-beesl2-01-Settings.png" target="_blank"><img src="http://kylegabriel.com/projects/wp-content/uploads/sites/3/2015/09/Mycodo-3.5.75-beesl2-01-Settings-150x150.png"></a>
    </td>
  </tr>
</table>

---

### Terminal

#### Daemon

<a href="http://kylegabriel.com/projects/wp-content/uploads/sites/3/2015/09/mycodo.py_.png" target="_blank"><img src="http://kylegabriel.com/projects/wp-content/uploads/sites/3/2015/09/mycodo.py_-300x124.png"></a>

#### Client

<a href="http://kylegabriel.com/projects/wp-content/uploads/sites/3/2015/09/mycodo-client.py_.png" target="_blank"><img src="http://kylegabriel.com/projects/wp-content/uploads/sites/3/2015/09/mycodo-client.py_-300x219.png"></a>

---

## Changelog

Major changes for each versioned release

#### 3.5.91
+ Add ability to use Raspberry Pi internal CPU and GPU thermal sensors (log, PID, conditionals)

#### 3.5.91
+ Add ability to use multiple BMP085/180 pressure sensors with the TCA9548A multiplexer

#### 3.5.90
+ Add Support for I<sup>2</sup>C multiplexer (TCA9548A) for using multiple AM2315 humidity/temperature sensors (same I<sup>2</sup>C address)

#### 3.5.89
+ Add support for the AM2315 Humidity/Temperature sensor

#### 3.5.88
+ Add theme support (light/dark) and ability to set user as guest/admin

#### 3.5.87
+ Add display of Notes on dynamic humidity/temperature graph, add title to notes (for graph display)

#### 3.5.86
+ Change the PID period to a constant interval (thanks @KnyazSh)"

#### 3.5.85
+ New client-side graph generation using HighCharts/HighStock

#### 3.5.84
+ Add relay and power usage statistics to the Data Tab

#### 3.5.83
+ Add ability to define combined graph values: relays to plot and y-axis values (min, max, tics, and mtics)

#### 3.5.82
+ Add sensor measurement verification with second sensor (Only for temperature/humidity sensors at the moment)

#### 3.5.81
+ Add image/file upload to notes

#### 3.5.80
+ Add basic note-taking functionality ("Notes" under Data tab)

#### 3.5.79
+ Add backup restore feature to revert back to a previously-backed up system and databases (found in "Git Commits" of the Data tab)

#### 3.5.78
+ Record history of changes to sensor/relay values, reduce number of spaces between values in relay/sensor logs to one (reduce file size)

#### 3.5.77
+ Implement ability to provide custom raspistill options from web interface

#### 3.5.76
+ Add minimum relay on duration for PID controllers (to complement maximum on duration)

#### 3.5.75
+ Ability to execute command or notify by email if relay or sensor conditional is true

#### 3.5.74
+ Ability to add amp draw for each device and set maximum allowed amps to be drawn (will prevent relays from turning on that would exceed the set max)

#### 3.5.73
+ Ability to create relay conditional statements based on relay states

#### 3.5.72
+ Ability to choose which relays are graphed and what direction (up or down from the 0 y-axis)

#### 3.5.71
+ Ability to set y-axis min/max/tics/mtics for each sensor graph, for both relays and measured condition(s)

#### 3.5.70
+ Ability to create sensor conditional statements that manipulate relays based on sensor measurements

#### 3.5.69
+ Add pressure sensors: BMP085/BMP180 pressure/temperature sensors

#### 3.5.68
+ Set pre- and post-capture commands (for image, stream, and timelapse)

#### 3.5.67
+ Set maximum on duration for relays under PID-control

#### 3.5.66
+ Ability to upgrade database upgrade instead of erasing everything each Mycodo update

#### 3.5.65
+ Ability to activate a relay for a predefined period before reading a sensor
+ Automated update from github (from Settings tab)

#### 3.5.64
+ Unlimited number of sensor/relays/timers that can be added

#### 3.5.63
+ Add custom Sensor/PID presets (save/load/overwrite/delete)

#### 3.5.62
+ Set the desired startup state of each relay (On or Off)

#### 3.5.61
+ Add time-lapse image acquisition

#### 3.5.60
+ PID-controllers can now regulate up, down, or both (previously only up)

#### 3.5.58
+ Add DS18B20 temperature sensor support

#### 3.5.55
+ Add locks for sensor reads (prevents reading too often)

#### 3.5.54
+ Ability to set relay to turn on while the camera is active

#### 3.5.51/3.5.52
+ Security improvements

#### 3.5.50
+ Add log parsing (40%-70% speed increase with generating graphs)

#### 3.5.0
+ Add K30 CO<sub>2</sub> sensor support
+ Moved to simpler login system (log in, log out, remember me cookie)
+ Moved to SQLite settings database (previously plain-text)
+ Moved to SQLite login database (previously MySQL)

---

## Sensors, Devices, and Interfaces

Certain sensors will require extra steps to be taken in order to set up the interface to communicate with them. The DS18B20 needs one-wire support enabled, The sensors that communicate by the I<sup>2</sup>C interface (AM2315, BMP085/180, TCA9548A) will require enabling I<sup>2</sup>C, and the K30 will require configuring UART. Because these procedures are already documented in the following links, they will not appear in the Mycodo install documentation. Therefore, follow the following procedures for any sensors or devices if you wish to use.

### I<sup>2</sup>C Interface

[Configuring I<sup>2</sup>C](https://learn.adafruit.com/adafruits-raspberry-pi-lesson-4-gpio-setup/configuring-i2c)

The AM2315 Humidity/Temperature Sensor, BMP085/180 Pressure Sensor, and TCA9548A I<sup>2</sup>C Multiplexer communicate with the I<sup>2</sup>C interface.

### Temperature Sensors

> [DS18B20](https://learn.adafruit.com/adafruits-raspberry-pi-lesson-11-ds18b20-temperature-sensing)

The DS18B20 is a simple 1-wire sensor. Once the one-wire interface has been configured with the above instructions, it may be used with Mycodo.

### Humidity & Temperature Sensors

> [DHT11, DHT22, AM2302](https://learn.adafruit.com/dht-humidity-sensing-on-raspberry-pi-with-gdocs-logging/wiring)

Afer [insatlling the Adafruit_Python_DHT library](#prerequisites), it can be tested whether the sensor is able to be read, by executing cgi-bin/Test-Sensor-HT-DHT.py

> [AM2315](https://github.com/lexruee/tentacle_pi)

After [configuring I<sup>2</sup>C](https://learn.adafruit.com/adafruits-raspberry-pi-lesson-4-gpio-setup/configuring-i2c) and [installing the tentacle_pi libraries](#prerequisites), it can be tested whether the sensor is able to be read, by executing cgi-bin/Test-Sensor-HT-AM2315.py

### CO<sub>2</sub> Sensors

> [K30](http://www.co2meters.com/Documentation/AppNotes/AN137-Raspberry-Pi.zip)

This documentation provides specific installation proceedures for the Raspberry Pi as well as example code. Once the K30 has been configured with this documentation, it can be tested whether the sensor is able to be read, by executing cgi-bin/Test-Sensor-CO2-K30.py

### Pressure Sensors

> [BMP085/BMP180](https://learn.adafruit.com/using-the-bmp085-with-raspberry-pi)

After [configuring I<sup>2</sup>C](https://learn.adafruit.com/adafruits-raspberry-pi-lesson-4-gpio-setup/configuring-i2c) and [installing the Adafruit_Python_BMP library](#prerequisites), it can be tested whether the sensor is able to be read, by executing cgi-bin/Test-Sensor-Press-BMP085-180.py

### I<sup>2</sup>C Multiplexer

> [TCA9548A](https://learn.adafruit.com/adafruit-tca9548a-1-to-8-i2c-multiplexer-breakout/overview)

The TCA9548A I<sup>2</sup>C allows multiple sensors that have the same I<sup>2</sup>C address to be used with mycodo (such as the AM2315). The multiplexer has a selectable address, from 0x70 through 0x77, allowing up to 8 multiplexers to be used at once. With 8 channels per multiplexer, this allows up to 64 devices with the same address to be used.

---

## Software Install

This installation assumes you are starting with a fresh install of Raspbian linux on a Raspberry Pi. If not, adjust your installation accordingly. Once <a href="https://www.raspberrypi.org/documentation/installation/installing-images/README.md" target="_blank">Raspbian has been installed</a> and the system is up and running, configure the system with raspi-config before doing anything else.

`sudo raspi-config`

Using raspi-config, perform the following:

 + Change the default user (pi) password
 + Set the locale to en_US.UTF-8 (Important! For some reason this isn't initially set)
 + Set the timezone (required for setting the proper time)
 + Enable the camera (optional)
 * Enable I<sup>2</sup>C
 + Advanced A2: change the hostname (optional)
 + Expand the file system **Warning! This needs to be done before continuing to Prerequisites!**
 + Reboot

`sudo shutdown now -r`

### Prerequisites

`sudo apt-get update`

`sudo apt-get upgrade`

`sudo apt-get install build-essential apache2 sqlite3 gnuplot git-core python-pip python-dev python-smbus libconfig-dev php5 libapache2-mod-php5 php5-sqlite php5-gd i2c-tools libi2c-dev`

`git clone https://github.com/kizniche/Mycodo.git ~/Mycodo`

`git clone git://git.drogon.net/wiringPi ~/WiringPi && cd ~/WiringPi && sudo ./build`

`git clone https://github.com/adafruit/Adafruit_Python_DHT.git ~/Adafruit_Python_DHT && cd ~/Adafruit_Python_DHT && sudo python setup.py install`

`git clone https://github.com/adafruit/Adafruit_Python_BMP.git ~/Adafruit_Python_BMP && cd ~/Adafruit_Python_BMP && sudo python setup.py install`

`git clone --recursive https://github.com/lexruee/tentacle_pi ~/tentacle_pi && cd ~/tentacle_pi && sudo python setup.py install`

Create a symlink to Mycodo

`sudo ln -s ~/Mycodo/3.5 /var/www/mycodo`

Install LockFile and RPyC

`sudo pip install lockfile rpyc`

To access /dev/vchiq (to read the GPU temperature or access the Pi camera), the user www-data needs to be added to the group video

`sudo usermod -a -G video www-data`

If you want mycodo to support using the Raspberry Pi camera module, a SUBSYSTEM line must be added to 10-vchiq-permissions.rules

`echo 'SUBSYSTEM=="vchiq",GROUP="video",MODE="0660"' | sudo tee /etc/udev/rules.d/10-vchiq-permissions.rules`

To be able to place a timestamp on an still image captures, the command 'convert' is required from the package imagemagick. Additionally, php5-gd is required for the creation of thumbnails when images are uploaded to notes.

`sudo apt-get install imagemagick`

Install video streaming capabilities

`sudo apt-get install libjpeg8-dev libv4l-dev wget subversion`

`sudo ln -s /usr/include/linux/videodev2.h /usr/include/linux/videodev.h`

`sudo wget -P ~/ http://sourceforge.net/code-snapshots/svn/m/mj/mjpg-streamer/code/mjpg-streamer-code-182.zip`

`cd ~ && unzip mjpg-streamer-code-182.zip && cd mjpg-streamer-code-182/mjpg-streamer`

`make mjpg_streamer input_file.so output_http.so`

`sudo cp mjpg_streamer /usr/local/bin`

`sudo cp output_http.so input_file.so /usr/local/lib/`

Clean Up

`cd ~ && sudo rm -rf WiringPi Adafruit_Python_BMP Adafruit_Python_DHT mjpg-streamer-code-182 mjpg-streamer-code-182.zip`

### Wifi

With a supported usb wifi dongle, setting up a wireless connection is as simple as the next few commands and a reboot. Consult documentation for your wireless card or google if this doesn’t work.

`sudo vi /etc/wpa_supplicant/wpa_supplicant.conf`

Edit wpa_supplicant.conf with the above command and add the following, changing the name and password for your wifi network.

```
network={
    ssid="NAME"
    psk="PASSWORD"
}
```

### TempFS

A temporary file system in RAM can be created for areas of the disk that are written often, prolonging the life of the SD card and speeding up disk read/writes. Keep in mind that all content on temporary file systems will be lost upon reboot. If you need to analyze logs, remember to disable these lines in /etc/fstab before doing so.

Edit /etc/fstab with `sudo vi /etc/fstab` and add the following lines

```
tmpfs /tmp     tmpfs nodev,nosuid,mode=1777,size=30M              0 0
tmpfs /var/log tmpfs defaults,noatime,nosuid,mode=0755,size=100M  0 0
```

Using a tempfs does create some issues with certain software. Apache does not start if there is no directory structure in /var/log, and the designation of /var/log as a tempfs means that at every bootup this directory is empty. This init script will ensure that the proper directory structure is created at every boot, prior to Apache starting.

`sudo cp /var/www/mycodo/init.d/apache2-tmpfs /etc/init.d/`

`sudo chmod 0755 /etc/init.d/apache2-tmpfs`

`sudo update-rc.d apache2-tmpfs defaults 90 10`

### Resolve Hostnames

To allow resolving of IP addresses in the login log, edit /etc/apache2/apache2.conf with `sudo vi /etc/apache2/apache2.conf` and find and change HostnameLookups to match the following line

`HostnameLookups On`

### Security

In each web-accessible directory is a file (.htaccess) which denies access to certain files and folders (such as the user database, sensor data, and camera photos). It is strongly recommended that you ensure this works properly (or alternatively, configure your web server to accomplish the same result), to ensure no one has direct access to these directories, as potentially sensitive information may be able to be accessed otherwise. Optionally, for higher security, enable SSL/HTTPS.

If your system is remotely accessible or publically available on the internet, it is strongly recommended to enable both SSL and .htaccess use. If your server is not, you can skip the next two steps.

#### Enable SSL

`sudo apt-get install openssl`

`sudo mkdir /etc/ssl/localcerts`

Generate your self-signed certificate with the following command. You will be prompted for information (which can be left blank), however it is recommended that if you have a fully-qualified domain name (FQDN) to enter that when prompted, to prevent a browser warning of a FQDN that doesn't match the certificate. The -days option specifies the certificate's expiration will be in 365 days.

`sudo openssl req -new -x509 -sha256 -days 365 -nodes -out /etc/ssl/localcerts/apache.crt -keyout /etc/ssl/localcerts/apache.key`

`sudo chmod 600 /etc/ssl/localcerts/apache*`

Change the symlink from non-SSL to SSL

If using Raspbian Wheezy:

`sudo ln -sf /etc/apache2/sites-available/default-ssl /etc/apache2/sites-enabled/000-default`

If using Raspbian Jessie:

`sudo ln -sf /etc/apache2/sites-available/default-ssl.conf /etc/apache2/sites-enabled/000-default.conf`

Edit /etc/apache2/sites-enabled/000-default (or 000-default.conf if running Jessie) and make sure the top looks similar to this:

```
<IfModule mod_ssl.c>
    <VirtualHost *:80>
            RewriteEngine on
            RewriteCond  %{HTTPS} !=on
            RewriteCond  %{HTTP_HOST} ^(.*)$
            RewriteRule  ^(.*)/? https://%1$1 [L,R]
    </VirtualHost>
            
    <VirtualHost _default_:443>
    SSLEngine On
    SSLCertificateFile /etc/ssl/localcerts/apache.crt
    SSLCertificateKeyFile /etc/ssl/localcerts/apache.key

    ServerAdmin webmaster@localhost

    DocumentRoot /var/www/
    <Directory />
            Options FollowSymLinks
            AllowOverride None
    </Directory>
    <Directory /var/www/>
            Options FollowSymLinks MultiViews
            AllowOverride All
            Order allow,deny
            allow from all
    </Directory>
```

Add `ServerName your.domain.com` to /etc/apache2/apache2.conf

Ensure SSL is enabled

`sudo a2enmod ssl`

You will need to add the self-signed certificate that was created (/etc/ssl/localcerts/apache.pem) to your browser as trusted in order not to receive warnings. You can copy this from the /etc/ssl/localcerts/ directory or it can be obtained by visiting your server with your browser. The process for adding this file to your browser as trusted may be different for each browser, however there are many resources online that detail how to do so. Adding your certificate to your browser is highly recommended to ensure the site's certificate is what it's supposed to be, however you will still be able to access your site without adding the certificate, but you may receive a warning stating your site's security may be compromised.

#### Enable .htaccess

If your server is accessible from the internet but you don't want to enable SSL (this was enabled with SSL, above), this is a crucial step that will ensure sensitive files (images/logs/databases) will not be accessible to anyone. If your server is not publically accessible, you can skip this step. Otherwise, it's imperative that `AllowOverride All` is added to your apache2 config to allow the .htaccess files throughout mycodo to restrict access to certain files and folders. Modify /etc/apache2/sites-enabled/000-default to appear as below:

```
    DocumentRoot /var/www
    <Directory />
         Order deny,allow
         Deny from all
    </Directory>
    <Directory /var/www>
        Options Indexes FollowSymLinks MultiViews
        AllowOverride All
        Order allow,deny
        allow from all
    </Directory>
```

### Enable mod_rewrite

`sudo a2enmod rewrite`

A reboot is necessary for the tempfs to be operational and apache2 to start correctly.

It is highly recommended that the configuration change be tested to determine if they actually worked. This can be done by going to https://yourwebaddress/mycodo/includes/ with your browser, and if you get an error, "Forbidden: You don't have permission to access /mycodo/includes on this server," or similar, then everything is working correctly. If the page actually loads or there is any other error than "forbidden", there is a problem and you should diagnose the issue before opening your server to beyond your local network.

### Database Creation

Use the following command and type 'all' when prompted to create both the user and mycodo databases.

`sudo /var/www/mycodo/update-database.py -i`

Follow the prompts to create an admin password, optionally create another user, and enable/disable guest access.

### Daemon

To initialize GPIO pins at startup, open crontab with `sudo crontab -e` and add the following lines, then save with `Ctrl+x`

`@reboot /usr/bin/python /var/www/mycodo/cgi-bin/GPIO-initialize.py &`

Last, set the daemon to automatically start

`sudo cp /var/www/mycodo/init.d/mycodo /etc/init.d/`

`sudo chmod 0755 /etc/init.d/mycodo`

`sudo update-rc.d mycodo defaults`

You can either reboot or start the daemon with the following command.

`sudo service mycodo start`

Note: cgi-bin/mycodo-wrapper is a binary executable used to start and stop the mycodo daemon, and to create and restore backups, from the web interface. It has the setuid bit to permit it to be executed as root (the init.d/mycodo script sets the correct permissions and setuid). Since shell scripts cannot be setuid (ony binary files), the mycodo-wrapper binay permits init.d/mycodo to be executed as root by a non-root user. You can audit the source code of cgi-bin/mycodo-wrapper.c and if you want to ensure the binary is indeed compiled from that source, you may compile it yourself with the following command. Otherwise, the compiled binary is already included and no further action is needed. I mention this to explain the need for setuid, for transparency, for security, and to maintain all code of this project as open source.

`sudo gcc /var/www/mycodo/cgi-bin/mycodo-wrapper.c -o /var/www/mycodo/cgi-bin/mycodo-wrapper`

---

## Manual

The Mycodo 3.5 manual is provided in the file manual.html. You can find a link to this manual at the top of the Settings Tab of the web interface. The manual can be accessed directly [here](http://htmlpreview.github.io/?https://github.com/kizniche/Mycodo/blob/master/3.5/manual.html) or the link at the end of this document in the [Useful Links](#useful-links) section.

## License

Mycodo is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.

Mycodo is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the [GNU General Public License](http://www.gnu.org/licenses/gpl-3.0.en.html) for more details.

A full copy of the GNU General Public License can be found at <a href="http://www.gnu.org/licenses/gpl-3.0.en.html" target="_blank">http://www.gnu.org/licenses/gpl-3.0.en.html</a> and in license.txt in the root directory for this software.

This software includes third party open source software components: Discrete PID Controller. Each of these software components have their own license. Please see ./cgi-bin/mycodoPID.py for license information.

## Useful Links

Thanks for using and supporting my software, however it may not be the latest version or it may have been altered if not obtained through an official distribution site. You should be able to find the latest version on github or my web site.

[Mycodo Manual](http://htmlpreview.github.io/?https://github.com/kizniche/Mycodo/blob/master/3.5/manual.html)

[Mycodo on Github](https://github.com/kizniche/Mycodo)

[KyleGabriel.com](http://KyleGabriel.com)
