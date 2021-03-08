Mycodo is an open-source environmental monitoring and regulation system that was built to run on the [Raspberry Pi](https://en.wikipedia.org/wiki/Raspberry_Pi).

Originally developed for cultivating edible mushrooms, Mycodo has grown to do much more. The system consists of two parts: a backend (daemon) and a frontend (web server). The backend performs tasks such as acquiring measurements from sensors and devices and coordinating a diverse set of responses to those measurements, including the ability to modulate outputs (switch relays, generate PWM signals, operate pumps, switch wireless outlets, publish/subscribe to MQTT, among others), regulate environmental conditions with PID control, schedule timers, capture photos and stream video, trigger actions when measurements meet certain conditions, and more. The frontend hosts a web interface that enables viewing and configuration from any browser-enabled device.

There are a number of different uses for Mycodo. Some users simply store sensor measurements to monitor conditions remotely, others regulate the environmental conditions of a physical space, while others capture motion-activated or time-lapse photography, among other uses.

Input controllers acquire measurements and store them in the InfluxDB [time series database](https://en.wikipedia.org/wiki/Time_series_database). Measurements typically come from sensors, but may also be configured to use the return value of linux or Python commands, or math equations, making a very powerful system for acquiring and generating data.

Output controllers produce changes to the general input/output (GPIO) pins or may be configured to execute linux or Python commands, enabling a large number of potential uses. There are a few different types of outputs: simple switching of GPIO pins (HIGH/LOW), generating pulse-width modulated (PWM) signals, switching 315/433 MHz wireless outlets, controlling Atlas Scientific peristaltic pumps, as well as executing linux and Python commands. The most common output is using a relay to switch electrical devices on and off.

When Inputs and Outputs are combined, PID controllers may be used to create a feedback loop that uses the Output device to modulate an environmental condition the Input measures. Certain Inputs may be coupled with certain Outputs to create a variety of different control and regulation applications. Beyond simple regulation, Methods may be used to create a changing setpoint over time, enabling such things as thermal cyclers, reflow ovens, environmental simulation for terrariums, food and beverage fermentation or curing, and cooking food ([sous-vide](https://en.wikipedia.org/wiki/Sous-vide)), to name a few.

Triggers can be set to activate events based on specific dates and times, according to durations of time, or the sunrise/sunset at a specific latitude and longitude. Conditionals are used to activates certain events based on the truth of custom user conditional statements (e.g. "Sensor1 > 23 and 10 < Sensor2 < 30").

## Web User Interface

The main frontend of Mycodo is a web user interface that allows any device with a web browser to view collected data and configure the backend, or the daemon, of the system. The web interface supports an authentication system with user/password credentials, user roles that grant/deny access to parts of the system, and SSL for encrypted browsing.

An SSL certificate with an expiration of 10 years will be generated and stored in ``~/Mycodo/mycodo/mycodo_flask/ssl_certs/`` during the install process to allow SSL to be used to securely connect to the web interface. If you want to use your own SSL certificates, replace them with your own.

If using the auto-generated certificate from the install, be aware that it will not be verified when visiting the web interface in your browser. You may continually receive a warning message about the security of your site unless you add the certificate to your browser's trusted list.

## Languages

The Mycodo user interface has been translated from English to Dutch, German, French, Italian, Norwegian, Polish, Portuguese, Russian, Serbian, Spanish, Swedish, and Chinese. If the default language for your web browser is one of these languages, it will be automatically selected. Otherwise, you can manually set the language from the Configuration menu.
