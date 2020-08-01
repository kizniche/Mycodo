## I2C Information

The I2C interface should be enabled with `raspi-config` or from the `[Gear Icon] -> Configure -> Raspberry Pi` page.

## 1-Wire Information

The 1-Wire interface should be enabled with `raspi-config` or from the `[Gear Icon] -> Configure -> Raspberry Pi` page.

## UART Information

[This documentation](http://www.co2meters.com/Documentation/AppNotes/AN137-Raspberry-Pi.zip) provides specific installation procedures for configuring UART with the Raspberry Pi version 1 or 2.

Because the UART is handled differently higher after the Raspberry Pi 2 (due to the addition of bluetooth), there are a different set of instructions. If installing Mycodo on a Raspberry Pi 3 or above, you only need to perform these steps to configure UART:

Run raspi-config

`sudo raspi-config`

Go to `Advanced Options -> Serial` and disable. Then edit `/boot/config.txt`

`sudo nano /boot/config.txt`

Find the line "enable_uart=0" and change it to "enable_uart=1", then reboot.