/* 
*  Title:   Automated Mushroom Cultivator
*  Author:  Kyle T. Gabriel
*  Date:    2012-2015
*  Version: 1.8
*/

SOFTWARE
nginx
gnuplot
php
python
DHT_Read (now depreciated, originally named Adafruit_DHT.c from https://github.com/adafruit/Adafruit-Raspberry-Pi-Python-Code/tree/master/Adafruit_DHT_Driver)
gpio (raspberry pi-specific)

HARDWARE
Raspberry Pi
Relays (Keyes Funduino 4 opto-isolated relay board)
Temperature/humidity sensor (DHT22)
Humidifier
Heater
Circulatory Fan
Exhaust Fan (HEPA filter recommended)

Connect the pins as follows:
Relay1, Exhaust Fan: GPIO 23, pin 16
Relay2, Humidifier: GPIO 22, pin 15
Relay3, Circulatory Fan: GPIO 18, pin 12
Relay4, Heater: GPIO 17, pin 11
DHT22 sensor: GPIO 4, pin 7
DHT22 Power: 3.3v, pin 1
Relay and DHT22 Ground: Ground, pin 6

INSTALL
place contents of /www in your web root directory.

SETUP
Create login credentials for the web interface:
1. Uncomment line 25 of auth.php and load it in your browser.
2. Enter a name and click submit.
3. Copy the Hash from the next page and replace the warning in the quotes of $Password1 or $Password2 of auth.php.
4. Change the user name in auth.php and recomment line 25.

Set up sensor data logging and relay changing by adding the following lines to cron:
*/2 * * * * /usr/bin/python /var/www/mycodo/mycodo-sense.py -w /var/www/mycodo/PiSensorData
*/2 * * * * /var/www/mycodo/mycodo-auto

Go to http://localhost/graph/index.php
Log in with the credentials you created earlier.
You should see the menu to the left with the current humidity and temperature and a graph to the right with the corresponding values.
