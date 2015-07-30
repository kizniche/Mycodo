# Mycodo 3.5-beta (experimental)

This is an experimental branch of mycodo. It is undergoing constant changes and may or may not work at any time (although it has matured somewhat and is relatively stable at the moment). If you are looking for a stable version, I recommend you check out the [v3.0 branch](../3.0).

## Progress

- [X] Added Feature: Set desired startup state of relay (on or off)
- [X] Added Feature: Time-lapse image acquisition
- [X] Added Feature: PID regulation up, down, or both (previously only up)
- [X] Added Feature: Log parsing (40%-70% increase in graph-generation speed)
- [X] Added Sensor: K30 CO<sub>2</sub> sensor
- [X] Added Sensor: DS18B20 temperature sensor
- [X] New configuration database (from plain-text file to SQLite)
- [X] New user database (from MySQL to SQLite)
- [ ] More graph options (y-axis min/max, select sensors to be graphed)
- [ ] Email notification or audible alarm during critical failure or condition (working on)
- [ ] Convert time-lapse images to video
- [ ] Barometric Pressure sensor support
- [ ] O<sub>2</sub> sensor support
- [ ] Set electrical current draw of each device and prevent exceeding total current limit with different combinations of devices on
- [ ] HDR Photo creation (capture series of photos at different ISOs and combine) (Initial testing was slow: 3 photos = 15 minutes processing)

## New Dependencies

php5-sqlite

sqlite3

## Supported Sensors

### Temperature

> [DS18B20](https://learn.adafruit.com/adafruits-raspberry-pi-lesson-11-ds18b20-temperature-sensing)

### Humidity & Temperature

> [DHT11, DHT22 and AM2302](https://learn.adafruit.com/dht-humidity-sensing-on-raspberry-pi-with-gdocs-logging/wiring)

### CO<sub>2</sub>

> [K30](http://www.co2meters.com/Documentation/AppNotes/AN137-Raspberry-Pi.zip)

## Software Install

### Prerequisites

`sudo apt-get update`

`sudo apt-get upgrade`

`sudo apt-get install apache2 build-essential python-dev gnuplot git-core libconfig-dev php5 libapache2-mod-php5 python-pip subversion php5-sqlite sqlite3`

`svn checkout https://github.com/kizniche/Mycodo/trunk/3.5 /var/www/mycodo`

`sudo git clone git://git.drogon.net/wiringPi ~/WiringPi`

`sudo git clone https://github.com/adafruit/Adafruit_Python_DHT ~/Adafruit_Python_DHT`

Install WiringPi

`cd ~/WiringPi`

`sudo ./build`

Install Adafruit_Python_DHT

`cd ~/Adafruit_Python_DHT`

`sudo python setup.py install`

Install LockFile and RPyC

`pip install lockfile rpyc`

If using the Raspberry Pi camera module:

`echo 'SUBSYSTEM=="vchiq",GROUP="video",MODE="0660"' | sudo tee /etc/udev/rules.d/10-vchiq-permissions.rules`

`sudo usermod -a -G video www-data`

Install video streaming capabilities (Note that it is recommended to require SSL on your web server to prevent potential viewing of video streams by unauthorized users, details on forcing SSL below)

`sudo apt-get install libjpeg8-dev libv4l-dev wget`

`sudo ln -s /usr/include/linux/videodev2.h /usr/include/linux/videodev.h`

`sudo wget -P ~/ http://sourceforge.net/code-snapshots/svn/m/mj/mjpg-streamer/code/mjpg-streamer-code-182.zip`

`cd ~`

`unzip mjpg-streamer-code-182.zip`

`cd mjpg-streamer-code-182/mjpg-streamer`

`make mjpg_streamer input_file.so output_http.so`

`sudo cp mjpg_streamer /usr/local/bin`

`sudo cp output_http.so input_file.so /usr/local/lib/`

### Wifi

With a supported usb wifi dongle, setting up a wireless connection is as simple as the next few commands and a reboot. Consult documentation for your wireless card or google if this doesn’t work. Edit wpa_supplicant.conf with `sudo vi /etc/wpa_supplicant/wpa_supplicant.conf` and add the following, then change the name and password.

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
tmpfs    /tmp    tmpfs    defaults,noatime,nosuid,size=100m    0 0
tmpfs    /var/tmp    tmpfs    defaults,noatime,nosuid,size=30m    0 0
tmpfs    /var/log    tmpfs    defaults,noatime,nosuid,mode=0755,size=100m    0 0
tmpfs    /var/run    tmpfs    defaults,noatime,nosuid,mode=0755,size=2m    0 0
tmpfs    /var/spool/mqueue    tmpfs    defaults,noatime,nosuid,mode=0700,gid=12,size=30m    0 0
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

`sudo chmod 600 /etc/ssl/localcerts/apache`

Change the symlink from non-SSL to SSL

`sudo ln -sf /etc/apache2/sites-available/default-ssl /etc/apache2/sites-enabled/000-default`

Edit /etc/apache2/sites-enabled/000-default and make sure the top looks similar to this:

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
            Options Indexes FollowSymLinks MultiViews
            AllowOverride All
            Order allow,deny
            allow from all
    </Directory>
```

Add `ServerName your.domain.com` to /etc/apache2/apache2.conf

Ensure SSL is enabled in apache2 and restart the server

`sudo a2enmod ssl`

`sudo service apache2 restart`

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

Then restart apache with

`sudo service apache2 restart`

It is highly recommended that the configuration change be tested to determine if they actually worked. This can be done by going to https://yourwebaddress/mycodo/includes/ with your browser, and if you get an error, "Forbidden: You don't have permission to access /mycodo/includes on this server," or similar, then everything is working correctly. If the page actually loads or there is any other error than "forbidden", there is a problem and you should diagnose the issue before opening your server to beyond your local network.

### Database Creation

Use the following commands and type 'all' when prompted to create databases

`cd /var/www/mycodo/`

`sudo ./setup-databases.py -i`

Follow the prompts to create an admin password, optionally create another user, and enable/disable guest access.

### Starting the Daemon

To initialize GPIO pins at startup, open crontab with `sudo crontab -e` and add the following lines, then save with `Ctrl+e`

`@reboot /usr/bin/python /var/www/mycodo/cgi-bin/GPIO-initialize.py &`

Last, set the daemon to automatically start

`sudo cp /var/www/mycodo/init.d/mycodo /etc/init.d/`

`sudo chmod 0755 /etc/init.d/mycodo`

`sudo update-rc.d mycodo defaults`

Reboot to allow everything to start up

`sudo shutdown now -r`

## Usage

### Web Interface

After the system is back up, go to http://your.rpi.address/mycodo and log in with the credentials you created with setup-database.py. Input fields of the web interface will display descriptions or instructions when the mouse is hovered over them.

Ensure the Daemon indicator at the top-left is blue, indicating the daemon is running. If it is not, PID regulation cannot operate.

Additionally, relays must be properly set up before PID regulation can be achieved. Change the number of relays in the Settings tab and configure them. Change the `GPIO Pin` and `Signal ON` of each relay. The `GPIO Pin` is the pin on the raspberry pi (using BCM numbering, not board numbering) and the `Signal ON` is the required signal to activate the relay (close the circuit). If your relay activates when it receives a LOW (0 volt, ground) signal, set the `Signal ON` to LOW, otherwise set it HIGH.

### PID Control

The PID controller is the most common controller found in industrial settings, both for its simplicity and its complexity. PID stands for Proportional Integral Derivative.

#### P

The proportional path takes the error (the difference between the actual position and the desired position) and multiplies it by a constant, K<sub>p</sub>, to yield an output value. When the error is large, there will be a large proportional output.

#### I

The integral path takes the error and multiplies it by K<sub>i</sub>, then integrates it (K<sub>i</sub> · 1/s). As the error changes over time, the integral will continually sum it and multiply it by the constant K<sub>i</sub>. It integral is used to remove constant errors in the control system. If using P alone produces an output that allows a constant error, the integral will increase the output until the error decreases.

#### D

Last, the derivative path multiplies the error by K<sub>d</sub>, then differentiates it (K<sub>d</sub> · s). When the error rate changes over time, the output signal will change. The faster the change in error, the larger the derivative path becomes, decreasing the output rate of change.

#### Configurations

These K terms are called gains, and by adjusting them, the sensitivity of the system to each path is affected. When all three paths are summed, the PID output is produced. This output is used to turn on connected relays for certain durations of time, and hence, affect the environment.

Implementing a controller that effectively utilizes P, I, and D can be challenging (and is often unnecessary). For instance, the I and D can be set to 0, effectively turning them off and producing a P controller. Also popular is the PI controller. It is recommended to start with only P, then experiment with PI, before finally using PID.

Because systems will vary (e.g. airspace volume to regulate, degree of insulation, and the efficacy of the connected device(s) to modify the environment, etc.), each path will need to be adjusted to produce an effective output that attains the set point in both a reasonable amount of time and with as little oscillation possible around the set point. As such, your particular configuration will need to be determined through experimentation.

### Quick Set-up Examples

These example setups are meant to illustrate how to configure regulation in particular directions, and not how to properly configure your P, I, and D variables. There are a number of online resources that discuss techniques and methods that have been developed to determine ideal PID values, and since here are no universal values that will work for every system, it is recommended to conduct your own research to understand and implement them.

Provided merely as an example of the variance of PID values between sensors and environments, one of my setups had temperature PID values (up regulation) of P=30, I=1.0, and D=0.5, and humidity PID values (up regulation) of P=1.0, I=0.2, and D=0.5. Furthermore, these values may not have been optimal but they worked well for the conditions of my environmental chamber.

#### High-Humidity Regulation

This will set up the system to raise the humidity to a certain level with one regulatory device (one that can raise the humidity).

Select the number of Humidity & Temperature (HT) sensors that are connected. Select the proper device and GPIO pin for each sensor and activate logging and graphing.

***Stop here. Wait 10 minutes, then go the Main tab and generate a graph. If the graph generates with data on it, continue. If not, stop and investigate why there is no sensor data. The controller will not function if there is not sensor data being acquired.***

Under the Humidity PID for an active sensor, change `PID Set Point` to the desired humidity, `PID Regulate` to 'Up', and `PID Buffer` to 0.

Set the `Relay No.` of the up-regulating PID (represented by an Up arrow) to the relay attached to your humidification device.

Set `P` to 1, `I` to 0, `D` to 0, then turn the Humidity PID on with the ON button.

At this point, the humidifier should be turning on and off at some interval. Generate '6 Hour Seperate' graphs from the Main tab to identify how well the humidity is regulated to the set point. What is meant by well-regulated will vary, depending on your specific application and tolerances. Most applications would like to see the proper humidity attained within a reasonable amount of time and not oscillate (go higher and lower) too much from the set point.

If the humidity is not reaching the set point after a reasonable amount of time, increase the P value until it does. Experiment with different configurations involving `Read Interval` and `P` to achieve an acceptable regulation. Avoid changing the `I` and `D` from 0 until a working regulation is achieved with P alone.

Once regulation is achieved, experiment by reducing P slightly and increasing `I` by a low amount to start, such as 0.1 (or lower), then observe how the controller regulates. Slowly increase I until regulation becomes both quick yet there is little oscillation once regulation is achieved. At this point, you should be fairly familiar with experimenting with the system and the D value can be experimented with.

#### Low-Temperature Regulation

This will set up the system to lower the temperature to a certain level with one regulatory device (one that can lower the temperature).

Use the same configuration as the High-Humidity Regulation example, except change `PID Regulate` to 'Down' and change the `Relay No.` and `P`, `I`, and `D` values of the down-regulating PID (represented by a Down arrow).

#### Exact Temperature Regulation

This will set up the system to raise and lower the temperature to a certain level with two regulatory devices (one that can raise and one that can lower the temperature).

Use the same configuration as the High-Humidity Regulation example, except change PID Regulate to 'Both' and change `Relay No.`, `P`, `I`, and `D` variables for both the up and down regulation of the PID controller. It may be necessary to increase the `PID Buffer` to prevent aggressive competition between up and down regulation (See the section below about the buffer).

### Tips

#### PID Buffer

If regulation is set to 'Both' ways (up and down), the devices that regulate each direction may turn on excessively, essentially competing to maintain regulation of a precise set point. This is where the `PID Buffer` may be effective at reducing relay activity. By setting the PID Buffer, a zone is formed (Set Point ± Buffer) where relays will not activate while the environmental condition is measured within this range.