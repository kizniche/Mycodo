All devices that connected to the Raspberry Pi by the I2C bus need to have a unique address in order to communicate. Some inputs may have the same address (such as the AM2315), which prevents more than one from being connected at the same time. Others may provide the ability to change the address, however the address range may be limited, which limits by how many you can use at the same time. I2C multiplexers are extremely clever and useful in these scenarios because they allow multiple sensors with the same I2C address to be connected.

For instance, the TCA9548A/PCA9548A: I2C Multiplexer has 8 selectable addresses, so 8 multiplexers can be connected to one Raspberry Pi. Each multiplexer has 8 channels, allowing up to 8 devices/sensors with the same address to be connected to each multiplexer. 8 multiplexers x 8 channels = 64 devices/sensors with the same I2C address.

Multiplexers can be set up by loading a kernel driver to handle the communication, producing a new I2C bus device for each multiplexer channel. To enable the driver for the TCA9548A/PCA9548A, visit [GPIO-pca9548](https://github.com/Theoi-Meteoroi/GPIO-pca9548) to get the code and latest install instructions. If successfully set up, there will be 8 new I2C buses on the `[Gear Icon] -> System Information` page.

The driver for the TCA9545A can be found at <https://github.com/camrex/i2c-mux-pca9545a> and other drivers are available elsewhere. See the manufacturer or user forums for details. Some multiplexers I've tested are below.

- TCA9548A/PCA9548A: I2C Multiplexer [link](https://learn.adafruit.com/adafruit-tca9548a-1-to-8-i2c-multiplexer-breakout/overview) (I2C): 8 selectable addresses, 8 channels

- TCA9545A: I2C Bus Multiplexer [link](http://store.switchdoc.com/i2c-4-channel-mux-extender-expander-board-grove-pin-headers-for-arduino-and-raspberry-pi/) (I2C): The linked Grove board creates 4 new I2C buses, each with their own selectable voltage, either 3.3 or 5.0 volts.
