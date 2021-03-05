Here are a few frequently asked questions about Mycodo. There is also an [Question & Answer Forum](https://kylegabriel.com/forum/questions-answers-mycodo) that you can post new questions. However, to ensure it's relevant to the topic, read the [stickied Q&A Post](https://kylegabriel.com/forum/questions-answers-mycodo/when-should-you-post-in-this-forum) to determine if it may be better suited for the [General Discussion Forum](https://kylegabriel.com/forum/general-discussion).

--------------

*What should I do if I have an issue?*

First, read though this manual to make sure you understand how the system works and you're using the system properly. Also check out the [Mycodo Wiki](https://github.com/kizniche/Mycodo/wiki). You may even want to look through recent [GitHub Issues](https://github.com/kizniche/Mycodo/issues). If you haven't resolved your issue by this point, make a [New GitHub Issue](https://github.com/kizniche/Mycodo/issues/new) describing the issue and attaching a sufficient amount of evidence (screenshots, log files, etc.) to aid in diagnosing the issue.

--------------

*Can I communicate with Mycodo from the command line?*

Yes, there is a [REST API](API.md) as well as the [Mycodo Client](Mycodo-Client.md).

--------------

*Can I add a new Input, Output, or custom functions to the system if they're not currently supported?*

Yes, Mycodo supports importing [Custom Inputs](Inputs.md#custom-inputs), [Custom Outputs](Outputs.md#custom-outputs), and [Custom Functions](Functions.md#custom-functions).

Another way to add an Input is to create a bash or Python script that obtains and returns a numerical value when executed from the linux command line on the Raspberry Pi. This script may be configured to be executed by the "Linux Command" or "Python Code" Inputs. These Inputs will periodically execute the command(s) and store the returned measurement(s) to the database for use with the rest of the Mycodo system.

--------------

*How do I set up simple environmental monitoring and regulation?*

Here is how I generally set up Mycodo to monitor and regulate:

1.  Determine what environmental condition you want to measure or regulate. Consider the devices that must be coupled to achieve this. For instance, temperature regulation would require a temperature sensor input and an electric heater (or cooler) output.
2.  Determine what relays you will need to control power to your electric devices. The Raspberry Pi is capable of directly switching relays (using a controllable 3.3-volt signal from the Pi's GPIO pins). Remember to select a relay that can handle the electrical current load from your switched device and won't exceed the maximum current draw from the Raspberry Pi GPIO pin the relay is connected to.
3.  See the [Input Devices](Supported-Inputs.md) section for information about supported inputs. Acquire sensor(s) and relay(s) and connect them to the Raspberry Pi according to the manufacturer’s instructions. For instance, a sensor that communicates via the I2C bus will connect the SDA, SCL, Power, and Ground pins of the sensor to the SDA, SCL, 3.3 volt, and Ground pins of the Raspberry Pi. Make sure to enable the I2C interface under `[Gear Icon] -> Configure -> Raspberry Pi`. Additionally, the simplest way to connect a relay is to connect the controlling side of the relay to a GPIO pin and Ground of the Raspberry Pi (remember to select a relay that will not exceed the current limitation of the GPIO pin). Some relays require the proper polarity for the controlling voltage, so refer to the manufacturer's datasheet to determine if this is the case.
4.  On the ``Setup -> input`` page, add a new input using the drop-down menu. Configure the input with the correct communication pins and other options. Activate the input to begin recording measurements to the Mycodo measurement database.
5.  Go to the ``Data -> Live`` page to ensure there are measurements being acquired from the input.
6.  On the ``Setup -> Output`` page, add an On/Off GPIO Output and configure the GPIO pin that's connected to the relay, whether the relay switches On when the signal is HIGH or LOW, and what state (On or Off) to set the relay when Mycodo starts. There are a number of other Outputs to choose from, but this is the most basic to start with, that will simply switch the GPIO pin HIGH (3.3 volts) or LOW (0 volts) to switch the relay that's connected to the pin.
7.  Connect your device to the relay. This can be dont a number of ways, and will depend on a number of factors, including whether you're using DC or AC voltage, whether there are screw terminals or a connector/socket, etc. In the simplest scenario, AC mains voltage can be applied by cutting the live wire and connecting each of the newly-cut ends to each of the terminals on the switching side fo the relay. This enables the relay to short/connect or break/disconnect the connection, which will power and depower your device.
8.  Test the Output by switching it On and Off (or generating a PWM signal if it's a PWM Output) from the ``Setup -> Output`` page and make sure the device connected to the relay turns On when you select "On", and Off when you select "Off".
9.  On the ``Setup -> Function`` page, create a PID controller with the appropriate input measurement, output, and other parameters. Activate the PID controller.
10. On the ``Data -> Dashboard`` page, create a graph that includes the input measurement, the output, and the PID output and setpoint. This provides a good visualization for tuning the PID. See [Quick Setup Examples](Functions.md#quick-setup-examples) for a greater detail of this process and tuning tips.

--------------

*Can I variably-control the speed of motors or other devices with the PWM output signal from the PID?*

Yes, as long as you have the proper hardware to do that. The PWM signal being produced by the PID should be handled appropriately, whether by a fast-switching solid state relay, [AC modulation circuitry](Outputs.md#schematics-for-ac-modulation), [DC modulation circuitry](Outputs.md#schematics-for-dc-fan-control), or something else.

--------------

*I have a PID controller that uses one temperature sensor. If this sensor stops working, my PID controller stops operating. Is there a way to prevent this by setting up a second sensor to be used as a backup in case the first one fails?*

Yes, you can use as many sensors as you would like to create a redundant system so your PID or other functions don't stop working if one or more sensors fail. To do this, follow the below instructions:

1. Add and activate all your sensors. For this example, we will use three temperature sensors, Sensor1, Sensor2, and Sensor3, that return measurements in degrees Celsius.
2. Go to the ``Setup -> Input`` page and add the Redundancy Math controller.
3. In the options of the Redundancy controller, set the Period, Start Offset, and Max Age, then select Sensors 1, 2, and 3 for the Input option, then Save.
4. In the options of the Redundancy controller, change the order you wish to use the sensors under Order of Use. For this example, we will use the default order (Sensor1, Sensor2, Sensor3).
5. In the options of the Redundancy controller, under Measurement Settings, select Celsius for the Measurement Unit and click the Save under Measurement Settings (a different Save button from the general options).
6. Activate the Redundancy Math controller.
7. Go to the ``Data -> Live`` page and verify the Redundancy Math controller is working correctly by returning a value from the input you selected to be first. If the first sensor is working correctly, its value should be displayed. You can deactivate the first sensor (mimicking the first sensor stopped working) and see if the second sensor's value is then returned.
8. Go to the ``Setup -> Function`` page and select the new Redundancy Math controller for the PID Measurement option.

The PID controller will now use the measurement returned from the Redundancy Math controller, which in turn will acquire its measurement in the following way:

If a measurement can be found within the Max Age for Sensor1, the measurement for Sensor1 will be returned. If a measurement from Sensor1 could not be acquired, and if a measurement can be found within the Max Age for Sensor2, the measurement for Sensor2 will be returned. If a measurement from Sensor1 or Sensor2 could not be acquired, and if a measurement can be found within the Max Age for Sensor3, the measurement for Sensor3 will be returned. If a measurement from Sensor1, Sensor2, or Sensor3 could not be acquired, then the Redundancy Math controller will not return a measurement at all (indicating all three sensors are not working). It is advised to set up a Conditional Controller to send a notification email to yourself if one or more measurements are unable to be acquired so you can investigate the issue.