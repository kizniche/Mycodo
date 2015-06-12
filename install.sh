#!/bin/bash
#
# Mycodo install script
# Still a work-in-progress, use at your own risk

if [ "$EUID" -ne 0 ]
  then echo "Please run as root"
  exit
fi

STARTDIR=$PWD

echo "#### apt-get update && apt-get upgrade ####" >&2
apt-get update
apt-get upgrade

echo "#### Install required software ####" >&2
apt-get install apache2 build-essential python-dev gnuplot git-core libconfig-dev php5 libapache2-mod-php5 mysql-server mysql-client pip wget

echo "#### Install phpmyadmin ####" >&2
apt-get install phpmyadmin

echo "#### Download required software ####" >&2
git clone git://git.drogon.net/wiringPi /var/www/mycodo/source/WiringPi
git clone https://github.com/adafruit/Adafruit_Python_DHT /var/www/mycodo/source/Adafruit_Python_DHT

echo "#### Install software ####" >&2
cd /var/www/mycodo/source/WiringPi
./build

cd /var/www/mycodo/source/Adafruit_Python_DHT
python setup.py install

pip install lockfile rpyc

read -p "Install photo and streaming video support for the raspberry pi camera (Default: y)? [y/n] " -n 1 -r
if [[ $REPLY =~ ^[Yy]$ ]]
then
    echo "#### #Set permissions for www to use the RPi camera ####" >&2
    echo 'SUBSYSTEM=="vchiq",GROUP="video",MODE="0660"' | sudo tee /etc/udev/rules.d/10-vchiq-permissions.rules
    usermod -a -G video www-data
    echo "#### Setup streaming capabilities ####" >&2
    apt-get install libjpeg8-dev libv4l-dev
    ln -s /usr/include/linux/videodev2.h /usr/include/linux/videodev.h
    wget -P /var/www/mycodo/source http://sourceforge.net/code-snapshots/svn/m/mj/mjpg-streamer/code/mjpg-streamer-code-182.zip
    cd /var/www/mycodo/source
    unzip mjpg-streamer-code-182.zip
    cd mjpg-streamer-code-182/mjpg-streamer
    make mjpg_streamer input_file.so output_http.so
    cp mjpg_streamer /usr/local/bin
    cp output_http.so input_file.so /usr/local/lib/
fi

echo "#### Set up directories and links ####" >&2
mkdir -p /var/log/mycodo
mkdir -p /var/log/mycodo/images

if [ ! -h /var/www/mycodo/images ]; then
    ln -s /var/log/mycodo/images /var/www/mycodo/images
    chown www-data.www-data /var/www/mycodo/images
fi

if [ ! -e /var/log/mycodo/sensor-tmp.log ]; then
    touch /var/log/mycodo/sensor-tmp.log
fi
if [ ! -e /var/www/mycodo/log/sensor.log ]; then
    touch /var/www/mycodo/log/sensor.log
fi
if [ ! -h /var/www/mycodo/log/sensor-tmp.log ]; then
    ln -s /var/log/mycodo/sensor-tmp.log /var/www/mycodo/log/sensor-tmp.log
fi

if [ ! -e /var/log/mycodo/relay-tmp.log ]; then
    touch /var/log/mycodo/relay-tmp.log
fi
if [ ! -e /var/www/mycodo/log/relay.log ]; then
    touch /var/www/mycodo/log/relay.log
fi
if [ ! -h /var/www/mycodo/log/relay-tmp.log ]; then
    ln -s /var/log/mycodo/relay-tmp.log /var/www/mycodo/log/relay-tmp.log
fi

if [ ! -e /var/log/mycodo/daemon-tmp.log ]; then
    touch /var/log/mycodo/daemon-tmp.log
fi
if [ ! -e /var/www/mycodo/log/daemon.log ]; then
    touch /var/www/mycodo/log/daemon.log
fi
if [ ! -h /var/www/mycodo/log/daemon-tmp.log ]; then
    ln -s /var/log/mycodo/daemon-tmp.log /var/www/mycodo/log/daemon-tmp.log
fi

chown -R www-data.www-data /var/log/mycodo
chmod -R 660 /var/log/mycodo

chown -R www-data:www-data /var/www/mycodo
chmod 660 /var/www/mycodo/config/* /var/www/mycodo/log/*.log

read -p "Alter /etc/fstab to use tempfs (recommended)? [y/n] " -n 1 -r
if [[ $REPLY =~ ^[Yy]$ ]]
then
    echo 'tmpfs    /tmp    tmpfs    defaults,noatime,nosuid,size=100m    0 0' >> /etc/fstab
    echo 'tmpfs    /var/tmp    tmpfs    defaults,noatime,nosuid,size=30m    0 0' >> /etc/fstab
    echo 'tmpfs    /var/log    tmpfs    defaults,noatime,nosuid,mode=0755,size=100m    0 0' >> /etc/fstab
    echo 'tmpfs    /var/run    tmpfs    defaults,noatime,nosuid,mode=0755,size=2m    0 0' >> /etc/fstab
    echo 'tmpfs    /var/spool/mqueue    tmpfs    defaults,noatime,nosuid,mode=0700,gid=12,size=30m    0 0' >> /etc/fstab
    cp /var/www/mycodo/source/init.d/apache2-tmpfs /etc/init.d/
    chmod 0755 /etc/init.d/apache2-tmpfs
    update-rc.d apache2-tmpfs defaults 90 10
fi

cp /var/www/mycodo/source/init.d/mycodo /etc/init.d/
chmod 0755 /etc/init.d/mycodo
update-rc.d mycodo defaults

read -p "Add cron job to initialize GPIO pins at boot (Default: y)? [y/n] " -n 1 -r
if [[ $REPLY =~ ^[Yy]$ ]]
then
    crontab -l > mycron
    echo "@reboot /usr/bin/python /var/www/mycodo/cgi-bin/GPIO-initialize.py &" >> mycron
    crontab mycron
    rm mycron
fi

cd $STARTDIR/source/init.d
