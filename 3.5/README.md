# Mycodo 3.5-beta (experimental)

This is an experimental branch of mycodo. Unless I have been in direct contact with you regarding testing of this branch, I will not be providing technical support for any issues with this version. Instead, I recommend you check out the v3.0 stable branch.

### Progress

- [X] Change configuration storage (from config file to SQLite database)
- [X] Change login authentication (from MySQL to SQLite database)
- [X] Add log parsing (40%-70% speed increase in graph generation)
- [X] K30 CO2 sensor support (debugging)
- [ ] Email notification or audible alarm during critical failure or condition (working on)
- [ ] O2 sensor support
- [ ] More graph generation options
- [ ] Set electrical current draw of each device and prevent exceeding total current limit with different combinations of devices on
- [ ] Capture series of photos at different ISOs, combine to make HDR photo
- [ ] Timelapse video creation ability (define start, end, duration between, etc.)

### New Dependencies

php5-sqlite

sqlite3

### Install

`sudo apt-get update`

`sudo apt-get upgrade`

`sudo apt-get install apache2 build-essential python-dev gnuplot git-core libconfig-dev php5 libapache2-mod-php5 pip subversion php5-sqlite sqlite3`

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

Install video streaming capabilities

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

Add the following to /etc/apache2/sites-available/default-ssl (or just ‘default’ if not using SSL), or modify to suit your needs.

```
    DocumentRoot /var/www
    <Directory />
         Order deny,allow
         Deny from all
    </Directory>
	<Directory /var/www/mycodo>
        Options Indexes FollowSymLinks MultiViews
        AllowOverride All
        Order allow,deny
        allow from all
    </Directory>
```

To initialize GPIO pins at startup, open crontab with `sudo crontab -e` and add the following lines, then save with `Ctrl+e`

`@reboot /usr/bin/python /var/www/mycodo/cgi-bin/GPIO-initialize.py &`

Last, set the daemon to automatically start

`sudo cp /var/www/mycodo/init.d/mycodo /etc/init.d/`

`sudo chmod 0755 /etc/init.d/mycodo`

`sudo update-rc.d mycodo defaults`

Reboot to allow everything to start up

`sudo shutdown now -r`

After the system is back up, go to http://your.rpi.address/mycodo

Login with the login and password given to you at the login page, then go to the config tab.

Select the number of relays that are connected and save.

Change the `GPIO Pin` and `Trigger ON` of each relay. The `GPIO Pin` is the pin on the raspberry pi (using BCM numbering, not board numbering) and the `Trigger ON` is the required signal to activate the relay (close the circuit). If your relay activates when it receives a LOW (0 volt, ground) signal, set the `Trigger ON` to LOW, otherwise set it HIGH. Save all your changes.

Select the number of Temperature/Humidity sensors that are connected and save.

Change the `Sensor Device` and `GPIO Pin` for each sensor. Once these have been set, you can activate logging and/or graphing. When logging is activated, a log entry will be written to a file at the duration defined under `Log Interval` and when graphing is activated, the `Generate Graph` button on the main tab will generate preset graphs with the data logged with that particular sensor.

Repeat the above steps for any CO2 sensors that are connected. For connecting a K30 CO2 sensor, read this [configuration guide](http://www.co2meters.com/Documentation/AppNotes/AN137-Raspberry-Pi.zi).

For any PID controllers that are desired to be used, ensure you have set the `Relay No.`, `PID Set Point`, `P`, `I`, and `D` before attempting to activate it. The `Relay No.` is the number found under Relays that you would like to be controlled by the PID. The `PID Set point` is the desired condition (temperature, humidity, or co2 concentration, depending on which PID controller). The `P`, `I`, and `D` are the most crucial variables of the controller. It is advised to set `I` and `D` to 0 until the controller can reasonably stabilize with the `P` alone. That exact value will depend on the size of your system and degree of impact the device connected to the relay has on the system, but it is generally advisable to start low and work your way higher until you find something that works.

My current optimal temperature PID values are P=30, I=1.0, and D=0.5 and my humidity PID values are P=1.0, I=0.2, and D=0.5, however this may not be the case for your system. I'm merely providing an example of how ideal values can vary.