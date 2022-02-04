## Error Codes

Mycodo can return a number of different errors. Below are a few of the numbered errors that you may receive and information about how to diagnose the issue.

### Error 100

> Cannot set a value of '***X***' of type ***Y***. Must be a float or string representing a float.

 - Examples:
   - Cannot set a value of '***1.33.4***' of type ***str***.
   - Cannot set a value of '***Output: 1.2***' of type ***str***.
   - Cannot set a value of '***[1.3, 2.4]***' of type ***list***.
   - Cannot set a value of '***{"output": 1.99}***' of type ***dict***.
   - Cannot set a value of '***None***' of type ***Nonetype***.

This error occurs because the value provided to be stored in the influxdb time-series database is not a numerical value (integer or decimal/float) or it is not a string that represents a float (e.g. "5", "3.14"). There are a number of reasons why this error occurs, but the most common reason is the sensor being ready by an Input did not return a measurement when queried, or it returned something other than something that represents a numerical value, indicating the sensor is not working. This could be from a number of reasons, including but not limited to, faulty wiring, faulty/insufficient power supply, defective sensor, I2C bus hasn't been enabled, misconfigured settings, etc. Often, a sensor can fail or not get set up correctly during Input initialization when the daemon starts, leading to this error every measurement period. You will need to review the Daemon Log (`[Gear Icon] -> Mycodo Logs`) all the way back to when the daemon started (since this is when the Input started and potentially failed with an initial error that may be more informative). Enabling Log Level: Debug in the Controller setting can also be useful by providing debugging log lines (when available) in addition to the info and error log lines.

### Error 101

> ***X*** not set up properly

 - Examples
   - Device not set up
   - Output channel ***Y*** not set up

This error occurs when the Controller (Input/Output/Function/etc.) could not properly initialize the device or channel when it started and is now trying to access an uninitialized device or channel. For Inputs, this could be loading the 3rd party library used to communicate with the sensor. If there was an error loading the library, then the library cannot be used to communicate with the sensor. You will often need to review the Daemon Log (`[Gear Icon] -> Mycodo Logs`) for any relevant errors that occurred when the Controller was initially activated to determine the issue setting up the device. Try deactivating, then activating the device, to see the initialization error again. Enabling Log Level: Debug in the Controller setting can also be useful by providing debugging log lines (when available) in addition to the info and error log lines.
