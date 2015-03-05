-----------------------------------------
Title:   Automated Mushroom Cultivator
Author:  Kyle T. Gabriel
Date:    2012-2015
Version: 1.9
-----------------------------------------


---- HARDWARE ----
Raspberry Pi
DHT22 Temperature/humidity sensor
Relays (Keyes Funduino 4, but any opto-isolated relay board will do)
Humidifier
Heater
Circulatory Fan
Exhaust Fan (HEPA filter recommended)


---- SOFTWARE ----
Raspbian (debian variant)
git
apache2
gnuplot
php
python
Adafruit_Python_DHT
gpio (WiringPi)
libconfig-dev
build-essential


---- INSTALL ----
# Update
sudo apt-get update
sudo apt-get upgrade

# Install essential software
sudo apt-get install apache2 build-essential python-dev gnuplot git-core libconfig-dev

# Download the latest code for the controller, web interface, and Adafruit_Python_DHT
sudo git clone https://github.com/kizniche/Automated-Mushroom-Cultivator /var/www/graph
sudo git clone git://git.drogon.net/wiringPi /var/www/graph/source/WiringPi
sudo git clone https://github.com/adafruit/Adafruit_Python_DHT /var/www/graph/source/Python_DHT

# Compile temperature/humidity controller
cd /var/www/graph/source
gcc mycodo-1.0.c -I/usr/local/include -L/usr/local/lib -lconfig -lwiringPi -o mycodo
mv ./mycodo ../mycodo/mycodo

# Compile WiringPi and DHT python library
cd /var/www/graph/source/WiringPi
sudo ./build
cd /var/www/graph/source/Python_DHT
sudo python setup.py install

# Create login credentials for the web interface:
# Uncomment line 25 of auth.php and go to http://localhost/graph/index.php
# Enter a password in the password field and click submit.
# Copy the Hash from the next page and replace the warning in the quotes of $Password1 or $Password2 of auth.php.
# Change the user name in auth.php and comment line 25.

# Set up sensor data logging and relay changing by adding the following lines to cron (with "sudo crontab -e")
*/2 * * * * /usr/bin/python /var/www/graph/mycodo/mycodo-sense.py -w /var/www/graph/mycodo/PiSensorData
*/2 * * * * /var/www/graph/mycodo/mycodo-auto

# Go to http://localhost/graph/index.php
# Log in with the credentials you created earlier.
# You should see the menu to the left with the current humidity and temperature and a graph to the right with the corresponding values.

**** NEEDS TO BE COMPLETED **** WORK IN PROGRESS ****


---- Hardware Setup ----
Relay1, Exhaust Fan: GPIO 23, pin 16
Relay2, Humidifier: GPIO 22, pin 15
Relay3, Circulatory Fan: GPIO 18, pin 12
Relay4, Heater: GPIO 17, pin 11
DHT22 sensor: GPIO 4, pin 7
DHT22 Power: 3.3v, pin 1
Relays and DHT22 Ground: Ground, pin 6