# Mycodo 3.5-beta (experimental)

This is an experimental branch of mycodo. Unless I have been in direct contact with you regarding testing of this branch, I will not be providing technical support for any issues with this version. Instead, I recommend you check out the v3.0 stable branch.

### Progress

- [X] Change configuration storage (from config file to SQLite database)
- [X] Change login authentication (from MySQL to SQLite database)
- [X] Add log parsing (40%-70% speed increase in graph generation)
- [X] K30 CO2 sensor support
- [X] DS18B20 Temperature sensor support
- [ ] Timelapse (Working on)
- [ ] Email notification or audible alarm during critical failure or condition (working on)
- [ ] O2 sensor support
- [ ] More graph generation options
- [ ] Set electrical current draw of each device and prevent exceeding total current limit with different combinations of devices on
- [ ] HDR Photo creation (capture series of photos at different ISOs and combine) (Initial testing was slow: 3 photos = 15 minutes processing)

### New Dependencies

php5-sqlite

sqlite3

### Supported Sensors

##### Temperature

[DS18B20](https://learn.adafruit.com/adafruits-raspberry-pi-lesson-11-ds18b20-temperature-sensing)

##### Humidity & Temperature

[DHT11, DHT22 and AM2302](https://learn.adafruit.com/dht-humidity-sensing-on-raspberry-pi-with-gdocs-logging/wiring)

##### CO2

[K30](http://www.co2meters.com/Documentation/AppNotes/AN137-Raspberry-Pi.zip)

### Mycodo Setup

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

Install video streaming capabilities (Note that it is recommended to require SSL on your web server to prevent potential viewing of video streams by unautorized users, details on forcing SSL below)

`sudo apt-get install libjpeg8-dev libv4l-dev wget`

`sudo ln -s /usr/include/linux/videodev2.h /usr/include/linux/videodev.h`

`sudo wget -P ~/ http://sourceforge.net/code-snapshots/svn/m/mj/mjpg-streamer/code/mjpg-streamer-code-182.zip`

`cd ~`

`unzip mjpg-streamer-code-182.zip`

`cd mjpg-streamer-code-182/mjpg-streamer`

`make mjpg_streamer input_file.so output_http.so`

`sudo cp mjpg_streamer /usr/local/bin`

`sudo cp output_http.so input_file.so /usr/local/lib/`

Set www permissions

`sudo chown -R www-data:www-data /var/www/mycodo`

`sudo chmod 660 /var/www/mycodo/config/* /var/www/mycodo/log/*`

With a supported usb wifi dongle, setting up a wireless connection is as simple as the next few commands and a reboot. Consult documentation for your wireless card or google if this doesn’t work. Edit wpa_supplicant.conf with `sudo vi /etc/wpa_supplicant/wpa_supplicant.conf` and add the following, then change the name and password.

```
network={
    ssid="NAME"
    psk="PASSWORD"
}
```

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


To allow resolving of IP addresses in the login log, edit /etc/apache2/apache2.conf with `sudo vi /etc/apache2/apache2.conf` and find and change HostnameLookups to match the following line

`HostnameLookups On`

In each web directory is an.htaccess which denies access to those folders. It is strongly recommended that you ensure this works properly (or alternatively, configure your web server to accomplish the same result), to ensure no one has direct access to these directories, as log, configuration, graph images, and other potentially sensitive information is stored there. Optionally, for higher security, enable SSL/HTTPS.


### Security

If your system is remotely accessible or publically available on the internet, it is strongly recommended to enable both SSL and .htaccess overrides. If your server is not, you can skip the next two steps.

#### SSL

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

#### .htaccess

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

I highly recommend testing whether the configuration change actually worked. This can be tested by going to https://yourwebaddress/mycodo/includes/ with your browser, and if you get an error, "Forbidden: You don't have permission to access /mycodo/includes on this server," then everything is working correctly. If the page actually loads or there is any other error than "forbidden", there is a problem and you will need to diagnose the issue before opening your server to beyond your local network.

### Final Steps

#### Database Creation

Create the databases with the following commands

`cd /var/www/mycodo/`

`sudo ./setup-databases.py -i`

Follow the prompts to create an admin password, optionally create another user, and enable/disable guest access.

#### Starting the Daemon

To initialize GPIO pins at startup, open crontab with `sudo crontab -e` and add the following lines, then save with `Ctrl+e`

`@reboot /usr/bin/python /var/www/mycodo/cgi-bin/GPIO-initialize.py &`

Last, set the daemon to automatically start

`sudo cp /var/www/mycodo/init.d/mycodo /etc/init.d/`

`sudo chmod 0755 /etc/init.d/mycodo`

`sudo update-rc.d mycodo defaults`

Reboot to allow everything to start up

`sudo shutdown now -r`

After the system is back up, go to http://your.rpi.address/mycodo

Login with the credentials you created with setup-database.py, then go to the Settings tab.

Select the number of relays that are connected and save.

Change the `GPIO Pin` and `Trigger ON` of each relay. The `GPIO Pin` is the pin on the raspberry pi (using BCM numbering, not board numbering) and the `Trigger ON` is the required signal to activate the relay (close the circuit). If your relay activates when it receives a LOW (0 volt, ground) signal, set the `Trigger ON` to LOW, otherwise set it HIGH. Save all your changes.

Go to the Sensors tab and select the number of each type of sensors that are connected and save. T=Temperature Sensors, HT=Humidity/Temperature Sensors, and CO2=CO2 Sensors.

Change the `Sensor Device` and `GPIO Pin` for each sensor. Once these have been set, you can activate logging and/or graphing. When logging is activated, a log entry will be written to a file at the duration defined under `Log Interval` and when graphing is activated, the `Generate Graph` button on the main tab will generate preset graphs with the data logged with that particular sensor.

For any PID controllers that are desired to be used, ensure you have set the `Relay No.`, `PID Set Point`, `P`, `I`, and `D` before attempting to activate it. The `Relay No.` is the number found under Relays that you would like to be controlled by the PID. The `PID Set point` is the desired condition (temperature, humidity, or co2 concentration, depending on which PID controller). The `P`, `I`, and `D` are the most crucial variables of the controller. It is advised to set `I` and `D` to 0 until the controller can reasonably stabilize with the `P` alone. That exact value will depend on the size of your system and degree of impact the device connected to the relay has on the system, but it is generally advisable to start low and work your way higher until you find something that works.

My current optimal temperature PID values are P=30, I=1.0, and D=0.5 and my humidity PID values are P=1.0, I=0.2, and D=0.5, however this may not be the case for your system. I'm merely providing an example of how ideal values can vary.
