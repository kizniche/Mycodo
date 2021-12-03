Supported Functions are listed below.

## Built-In Functions

### Average (Last, Multiple)


This function acquires the last measurement of those that are selected, averages them, then stores the resulting value as the selected measurement and unit.

#### Options

##### Period (seconds)

- Type: Decimal
- Default Value: 60
- Description: The duration (seconds) between measurements or actions

##### Start Offset

- Type: Integer
- Default Value: 10
- Description: The duration (seconds) to wait before the first operation

##### Max Age

- Type: Integer
- Default Value: 360
- Description: The maximum age (seconds) of the measurement to use

##### Measurement

- Description: Measurement to replace "x" in the equation

### Average (Past, Single)


This function acquires the past measurements (within Max Age) for the selected measurement, averages them, then stores the resulting value as the selected measurement and unit.

#### Options

##### Period (seconds)

- Type: Decimal
- Default Value: 60
- Description: The duration (seconds) between measurements or actions

##### Start Offset

- Type: Integer
- Default Value: 10
- Description: The duration (seconds) to wait before the first operation

##### Measurement

- Type: Select Measurement
- Selections: Input, Math, Function, 
- Description: Measurement to replace "x" in the equation

##### Max Age

- Type: Integer
- Default Value: 360
- Description: The maximum age (seconds) of the measurement to use

### Backup to Remote Host (rsync)

- Dependencies: [rsync](https://packages.debian.org/buster/rsync)

This function will use rsync to back up assets on this system to a remote system. Your remote system needs to have an SSH server running and rsync installed. This system will need rsync installed and be able to access your remote system via SSH keyfile (login without a password). You can do this by creating an SSH key on this system running Mycodo with "ssh-keygen" (leave the password field empty), then run "ssh-copy-id -i ~/.ssh/id_rsa.pub pi@REMOTE_HOST_IP" to transfer your public SSH key to your remote system (changing pi and REMOTE_HOST_IP to the appropriate user and host of your remote system). You can test if this worked by trying to connect to your remote system with "ssh pi@REMOTE_HOST_IP" and you should log in without being asked for a password. Be careful not to set the Period too low, which could cause the function to begin running before the previous operation(s) complete. Therefore, it is recommended to set a relatively long Period (greater than 10 minutes). The default Period is 15 days. Note that the Period will reset if the system or the Mycodo daemon restarts and the Function will run, generating new settings and measurement archives that will be synced. There are two common ways to use this Function: 1) A short period (1 hour), only have Backup Camera Directories enabled, and use the Backup Settings Now and Backup Measurements Now buttons manually to perform a backup, and 2) A long period (15 days), only have Backup Settings and Backup Measurements enabled. You can even create two of these Functions with one set up to perform long-Period settings and measurement backups and the other set up to perform short-Period camera backups.

#### Options

##### Period (seconds)

- Type: Decimal
- Default Value: 1296000
- Description: The duration (seconds) between measurements or actions

##### Start Offset

- Type: Integer
- Default Value: 300
- Description: The duration (seconds) to wait before the first operation

##### Local User

- Type: Text
- Default Value: pi
- Description: The user on this system that will run rsync

##### Remote User

- Type: Text
- Default Value: pi
- Description: The user to log in to the remote host

##### Remote Host

- Type: Text
- Default Value: 192.168.0.50
- Description: The IP or host address to send the backup to

##### Remote Backup Path

- Type: Text
- Default Value: /home/pi/backup_mycodo
- Description: The path to backup to on the remote host

##### Rsync Timeout

- Type: Integer
- Default Value: 3600
- Description: How long to allow rsync to complete (seconds)

##### Backup Settings Export File

- Type: Boolean
- Default Value: True
- Description: Create and backup exported settings file

##### Remove Local Settings Backups

- Type: Boolean
- Description: Remove local settings backups after successful transfer to remote host

##### Backup Measurements

- Type: Boolean
- Default Value: True
- Description: Backup all influxdb measurements

##### Remove Local Measurements Backups

- Type: Boolean
- Description: Remove local measurements backups after successful transfer to remote host

##### Backup Camera Directories

- Type: Boolean
- Default Value: True
- Description: Backup all camera directories

##### Remove Local Camera Images

- Type: Boolean
- Description: Remove local camera images after successful transfer to remote host

##### SSH Port

- Type: Integer
- Default Value: 22
- Description: Specify a nonstandard SSH port

#### Actions

##### Backup of settings are only created if the Mycodo version or database versions change. This is due to this Function running periodically- if it created a new backup every Period, there would soon be many identical backups. Therefore, if you want to induce the backup of settings, measurements, or camera directories and sync them to your remote system, use the buttons below.

##### Backup Settings Now

- Type: Button
##### Backup Measurements Now

- Type: Button
##### Backup Camera Directories Now

- Type: Button
### Bang-Bang Hysteretic (On/Off) (Raise/Lower)


A simple bang-bang control for controlling one output from one input. Select an input, an output, enter a setpoint and a hysteresis, and select a direction. The output will turn on when the input is below (lower = setpoint - hysteresis) and turn off when the input is above (higher = setpoint + hysteresis). This is the behavior when Raise is selected, such as when heating. Lower direction has the opposite behavior - it will try to turn the output on in order to drive the input lower.

#### Options

##### Measurement

- Type: Select Measurement
- Selections: Input, Math, Function, 
- Description: Select a measurement the selected output will affect

##### Output

- Description: Select an output to control that will affect the measurement

##### Setpoint

- Type: Decimal
- Default Value: 50
- Description: The desired setpoint

##### Hysteresis

- Type: Decimal
- Default Value: 1
- Description: The amount above and below the setpoint that defines the control band

##### Direction

- Type: Select
- Options: \[**Raise** | Lower\] (Default in **bold**)
- Description: Raise means the measurement will increase when the control is on (heating). Lower means the measurement will decrease when the output is on (cooling)

##### Period (seconds)

- Type: Decimal
- Default Value: 5
- Description: The duration (seconds) between measurements or actions

### Bang-Bang Hysteretic (On/Off) (Raise/Lower/Both)


A simple bang-bang control for controlling one output from one input. Select an input, an output, enter a setpoint and a hysteresis, and select a direction. The output will turn on when the input is below (lower = setpoint - hysteresis) and turn off when the input is above (higher = setpoint + hysteresis). This is the behavior when Raise is selected, such as when heating. Lower direction has the opposite behavior - it will try to turn the output on in order to drive the input lower. The Both option will raise and lower.

#### Options

##### Measurement

- Type: Select Measurement
- Selections: Input, Math, Function, 
- Description: Select a measurement the selected output will affect

##### Output (Raise)

- Description: Select an output to control that will raise the measurement

##### Output (Lower)

- Description: Select an output to control that will lower the measurement

##### Setpoint

- Type: Decimal
- Default Value: 50
- Description: The desired setpoint

##### Hysteresis

- Type: Decimal
- Default Value: 1
- Description: The amount above and below the setpoint that defines the control band

##### Direction

- Type: Select
- Options: \[Raise | Lower | **Both**\] (Default in **bold**)
- Description: Raise means the measurement will increase when the control is on (heating). Lower means the measurement will decrease when the output is on (cooling)

##### Period (seconds)

- Type: Decimal
- Default Value: 5
- Description: The duration (seconds) between measurements or actions

### Bang-Bang Hysteretic (PWM) (Raise/Lower/Both)


A simple bang-bang control for controlling one PWM output from one input. Select an input, a PWM output, enter a setpoint and a hysteresis, and select a direction. The output will turn on when the input is below below (lower = setpoint - hysteresis) and turn off when the input is above (higher = setpoint + hysteresis). This is the behavior when Raise is selected, such as when heating. Lower direction has the opposite behavior - it will try to turn the output on in order to drive the input lower. The Both option will raise and lower.

#### Options

##### Measurement

- Type: Select Measurement
- Selections: Input, Math, Function, 
- Description: Select a measurement the selected output will affect

##### Output

- Description: Select an output to control that will affect the measurement

##### Setpoint

- Type: Decimal
- Default Value: 50
- Description: The desired setpoint

##### Hysteresis

- Type: Decimal
- Default Value: 1
- Description: The amount above and below the setpoint that defines the control band

##### Direction

- Type: Select
- Options: \[Raise | Lower | **Both**\] (Default in **bold**)
- Description: Raise means the measurement will increase when the control is on (heating). Lower means the measurement will decrease when the output is on (cooling)

##### Period (seconds)

- Type: Decimal
- Default Value: 5
- Description: The duration (seconds) between measurements or actions

##### Duty Cycle (increase)

- Type: Decimal
- Default Value: 90
- Description: The duty cycle to increase the measurement

##### Duty Cycle (maintain)

- Type: Decimal
- Default Value: 55
- Description: The duty cycle to maintain the measurement

##### Duty Cycle (decrease)

- Type: Decimal
- Default Value: 20
- Description: The duty cycle to decrease the measurement

##### Duty Cycle (shutdown)

- Type: Decimal
- Description: The duty cycle to set when the function shuts down

### Difference


This function acquires 2 measurements, calculates the difference, and stores the resulting value as the selected measurement and unit.

#### Options

##### Period (seconds)

- Type: Decimal
- Default Value: 60
- Description: The duration (seconds) between measurements or actions

##### Measurement A

- Type: Select Measurement
- Selections: Input, Math, Function, 
- Description: 

##### Measurement A Max Age

- Type: Integer
- Default Value: 360
- Description: The maximum age (seconds) of the measurement to use

##### Measurement B

- Type: Select Measurement
- Selections: Input, Math, Function, 
- Description: 

##### Measurement B Max Age

- Type: Integer
- Default Value: 360
- Description: The maximum age (seconds) of the measurement to use

##### Reverse Order

- Type: Boolean
- Description: Reverse the order in the calculation

##### Absolute Difference

- Type: Boolean
- Description: Return the absolute value of the difference

### Display: Generic LCD 16x2 (I2C)


This Function outputs to a generic 16x2 LCD display via I2C. Since this display can show 2 lines at a time, channels are added in sets of 2 when Number of Line Sets is modified. Every Period, the LCD will refresh and display the next set of lines. Therefore, the first 2 lines that are displayed are channels 0 and 1, then 2 and 3, and so on. After all channels have been displayed, it will cycle back to the beginning.

#### Options

##### Period (seconds)

- Type: Decimal
- Default Value: 10
- Description: The duration (seconds) between measurements or actions

##### I2C Address

- Type: Text
- Default Value: 0x20
- Description: The I2C address of the device

##### I2C Bus

- Type: Integer
- Default Value: 1
- Description: The I2C bus the device is connected to

##### Number of Line Sets

- Type: Integer
- Default Value: 1
- Description: How many sets of lines to cycle on the LCD

#### Channel Options

##### Line Display Type

- Type: Select
- Description: What to display on the line

##### Measurement

- Type: Select Measurement
- Selections: Input, Math, Function, Output, PID, 
- Description: Measurement to display on the line

##### Measurement Max Age

- Type: Decimal
- Default Value: 360
- Description: The maximum age (seconds) of the measurement to use

##### Measurement Decimal

- Type: Integer
- Default Value: 1
- Description: The number of digits after the decimal

##### Text

- Type: Text
- Default Value: Text
- Description: Text to display

### Display: Generic LCD 20x4 (I2C)


This Function outputs to a generic 20x4 LCD display via I2C. Since this display can show 4 lines at a time, channels are added in sets of 4 when Number of Line Sets is modified. Every Period, the LCD will refresh and display the next set of lines. Therefore, the first 4 lines that are displayed are channels 0, 1, 2, and 3, then 4, 5, 6, and 7, and so on. After all channels have been displayed, it will cycle back to the beginning.

#### Options

##### Period (seconds)

- Type: Decimal
- Default Value: 10
- Description: The duration (seconds) between measurements or actions

##### I2C Address

- Type: Text
- Default Value: 0x20
- Description: The I2C address of the device

##### I2C Bus

- Type: Integer
- Default Value: 1
- Description: The I2C bus the device is connected to

##### Number of Line Sets

- Type: Integer
- Default Value: 1
- Description: How many sets of lines to cycle on the LCD

#### Channel Options

##### Line Display Type

- Type: Select
- Description: What to display on the line

##### Measurement

- Type: Select Measurement
- Selections: Input, Math, Function, Output, PID, 
- Description: Measurement to display on the line

##### Max Age

- Type: Decimal
- Default Value: 360
- Description: The maximum age (seconds) of the measurement to use

##### Measurement Decimal

- Type: Integer
- Default Value: 1
- Description: The number of digits after the decimal

##### Text

- Type: Text
- Default Value: Text
- Description: Text to display

### Display: Grove LCD 16x2 (I2C)


This Function outputs to the Grove 16x2 LCD display via I2C. Since this display can show 2 lines at a time, channels are added in sets of 2 when Number of Line Sets is modified. Every Period, the LCD will refresh and display the next set of lines. Therefore, the first 2 lines that are displayed are channels 0 and 1, then 2 and 3, and so on. After all channels have been displayed, it will cycle back to the beginning.

#### Options

##### Period (seconds)

- Type: Decimal
- Default Value: 10
- Description: The duration (seconds) between measurements or actions

##### I2C Address

- Type: Text
- Default Value: 0x3e
- Description: The I2C address of the device

##### I2C Bus

- Type: Integer
- Default Value: 1
- Description: The I2C bus the device is connected to

##### Backlight I2C Address

- Type: Text
- Default Value: 0x62
- Description: I2C address to control the backlight

##### Number of Line Sets

- Type: Integer
- Default Value: 1
- Description: How many sets of lines to cycle on the LCD

##### Backlight Red (0 - 255)

- Type: Integer
- Default Value: 255
- Description: Set the red color value of the backlight on startup.

##### Backlight Green (0 - 255)

- Type: Integer
- Default Value: 255
- Description: Set the green color value of the backlight on startup.

##### Backlight Blue (0 - 255)

- Type: Integer
- Default Value: 255
- Description: Set the blue color value of the backlight on startup.

#### Channel Options

##### Line Display Type

- Type: Select
- Description: What to display on the line

##### Measurement

- Type: Select Measurement
- Selections: Input, Math, Function, Output, PID, 
- Description: Measurement to display on the line

##### Max Age

- Type: Decimal
- Default Value: 360
- Description: The maximum age (seconds) of the measurement to use

##### Measurement Decimal

- Type: Integer
- Default Value: 1
- Description: The number of digits after the decimal

##### Text

- Type: Text
- Default Value: Text
- Description: Text to display

### Display: SSD1306 OLED 128x32 [2 Lines] (I2C)

- Dependencies: [libjpeg-dev](https://packages.debian.org/buster/libjpeg-dev), [Pillow](https://pypi.org/project/Pillow), [pyusb](https://pypi.org/project/pyusb), [adafruit-extended-bus](https://pypi.org/project/adafruit-extended-bus), [adafruit-circuitpython-framebuf](https://pypi.org/project/adafruit-circuitpython-framebuf), [Adafruit-Circuitpython-SSD1306](https://pypi.org/project/Adafruit-Circuitpython-SSD1306)

This Function outputs to a 128x32 SSD1306 OLED display via I2C. This display Function will show 2 lines at a time, so channels are added in sets of 2 when Number of Line Sets is modified. Every Period, the LCD will refresh and display the next set of lines. Therefore, the first set of lines that are displayed are channels 0 - 1, then 2 - 3, and so on. After all channels have been displayed, it will cycle back to the beginning.

#### Options

##### Period (seconds)

- Type: Decimal
- Default Value: 10
- Description: The duration (seconds) between measurements or actions

##### I2C Address

- Type: Text
- Default Value: 0x3c
- Description: The I2C address of the device

##### I2C Bus

- Type: Integer
- Default Value: 1
- Description: The I2C bus the device is connected to

##### Number of Line Sets

- Type: Integer
- Default Value: 1
- Description: How many sets of lines to cycle on the LCD

##### Reset Pin

- Type: Integer
- Default Value: 17
- Description: The pin (BCM numbering) connected to RST of the display

##### Characters Per Line

- Type: Integer
- Default Value: 17
- Description: The maximum number of characters to display per line

##### Use Non-Default Font

- Type: Boolean
- Description: Don't use the default font. Enable to specify the path to a font to use.

##### Non-Default Font Path

- Type: Text
- Default Value: /usr/share/fonts/truetype/dejavu//DejaVuSans.ttf
- Description: The path to the non-default font to use

##### Font Size (pt)

- Type: Integer
- Default Value: 12
- Description: The size of the font, in points

#### Channel Options

##### Line Display Type

- Type: Select
- Description: What to display on the line

##### Measurement

- Type: Select Measurement
- Selections: Input, Math, Function, Output, PID, 
- Description: Measurement to display on the line

##### Max Age

- Type: Decimal
- Default Value: 360
- Description: The maximum age (seconds) of the measurement to use

##### Measurement Decimal

- Type: Integer
- Default Value: 1
- Description: The number of digits after the decimal

##### Text

- Type: Text
- Default Value: Text
- Description: Text to display

##### Display Unit

- Type: Boolean
- Default Value: True
- Description: Display the measurement unit (if available)

### Display: SSD1306 OLED 128x32 [2 Lines] (SPI)

- Dependencies: [libjpeg-dev](https://packages.debian.org/buster/libjpeg-dev), [Pillow](https://pypi.org/project/Pillow), [pyusb](https://pypi.org/project/pyusb), [Adafruit-GPIO](https://pypi.org/project/Adafruit-GPIO), [adafruit-extended-bus](https://pypi.org/project/adafruit-extended-bus), [adafruit-circuitpython-framebuf](https://pypi.org/project/adafruit-circuitpython-framebuf), [Adafruit-Circuitpython-SSD1306](https://pypi.org/project/Adafruit-Circuitpython-SSD1306)

This Function outputs to a 128x32 SSD1306 OLED display via SPI. This display Function will show 2 lines at a time, so channels are added in sets of 2 when Number of Line Sets is modified. Every Period, the LCD will refresh and display the next set of lines. Therefore, the first set of lines that are displayed are channels 0 - 1, then 2 - 3, and so on. After all channels have been displayed, it will cycle back to the beginning.

#### Options

##### Period (seconds)

- Type: Decimal
- Default Value: 10
- Description: The duration (seconds) between measurements or actions

##### Number of Line Sets

- Type: Integer
- Default Value: 1
- Description: How many sets of lines to cycle on the LCD

##### SPI Device

- Type: Integer
- Description: The SPI device

##### SPI Bus

- Type: Integer
- Description: The SPI bus

##### DC Pin

- Type: Integer
- Default Value: 16
- Description: The pin (BCM numbering) connected to DC of the display

##### Reset Pin

- Type: Integer
- Default Value: 19
- Description: The pin (BCM numbering) connected to RST of the display

##### CS Pin

- Type: Integer
- Default Value: 17
- Description: The pin (BCM numbering) connected to CS of the display

##### Characters Per Line

- Type: Integer
- Default Value: 17
- Description: The maximum number of characters to display per line

##### Use Non-Default Font

- Type: Boolean
- Description: Don't use the default font. Enable to specify the path to a font to use.

##### Non-Default Font Path

- Type: Text
- Default Value: /usr/share/fonts/truetype/dejavu//DejaVuSans.ttf
- Description: The path to the non-default font to use

##### Font Size (pt)

- Type: Integer
- Default Value: 12
- Description: The size of the font, in points

#### Channel Options

##### Line Display Type

- Type: Select
- Description: What to display on the line

##### Measurement

- Type: Select Measurement
- Selections: Input, Math, Function, Output, PID, 
- Description: Measurement to display on the line

##### Max Age

- Type: Decimal
- Default Value: 360
- Description: The maximum age (seconds) of the measurement to use

##### Measurement Decimal

- Type: Integer
- Default Value: 1
- Description: The number of digits after the decimal

##### Text

- Type: Text
- Default Value: Text
- Description: Text to display

##### Display Unit

- Type: Boolean
- Default Value: True
- Description: Display the measurement unit (if available)

### Display: SSD1306 OLED 128x32 [4 Lines] (I2C)

- Dependencies: [libjpeg-dev](https://packages.debian.org/buster/libjpeg-dev), [Pillow](https://pypi.org/project/Pillow), [pyusb](https://pypi.org/project/pyusb), [adafruit-extended-bus](https://pypi.org/project/adafruit-extended-bus), [adafruit-circuitpython-framebuf](https://pypi.org/project/adafruit-circuitpython-framebuf), [Adafruit-Circuitpython-SSD1306](https://pypi.org/project/Adafruit-Circuitpython-SSD1306)

This Function outputs to a 128x32 SSD1306 OLED display via I2C. This display Function will show 4 lines at a time, so channels are added in sets of 4 when Number of Line Sets is modified. Every Period, the LCD will refresh and display the next set of lines. Therefore, the first set of lines that are displayed are channels 0 - 3, then 4 - 7, and so on. After all channels have been displayed, it will cycle back to the beginning.

#### Options

##### Period (seconds)

- Type: Decimal
- Default Value: 10
- Description: The duration (seconds) between measurements or actions

##### I2C Address

- Type: Text
- Default Value: 0x3c
- Description: The I2C address of the device

##### I2C Bus

- Type: Integer
- Default Value: 1
- Description: The I2C bus the device is connected to

##### Number of Line Sets

- Type: Integer
- Default Value: 1
- Description: How many sets of lines to cycle on the LCD

##### Reset Pin

- Type: Integer
- Default Value: 17
- Description: The pin (BCM numbering) connected to RST of the display

##### Characters Per Line

- Type: Integer
- Default Value: 21
- Description: The maximum number of characters to display per line

##### Use Non-Default Font

- Type: Boolean
- Description: Don't use the default font. Enable to specify the path to a font to use.

##### Non-Default Font Path

- Type: Text
- Default Value: /usr/share/fonts/truetype/dejavu//DejaVuSans.ttf
- Description: The path to the non-default font to use

##### Font Size (pt)

- Type: Integer
- Default Value: 10
- Description: The size of the font, in points

#### Channel Options

##### Line Display Type

- Type: Select
- Description: What to display on the line

##### Measurement

- Type: Select Measurement
- Selections: Input, Math, Function, Output, PID, 
- Description: Measurement to display on the line

##### Max Age

- Type: Decimal
- Default Value: 360
- Description: The maximum age (seconds) of the measurement to use

##### Measurement Decimal

- Type: Integer
- Default Value: 1
- Description: The number of digits after the decimal

##### Text

- Type: Text
- Default Value: Text
- Description: Text to display

##### Display Unit

- Type: Boolean
- Default Value: True
- Description: Display the measurement unit (if available)

### Display: SSD1306 OLED 128x32 [4 Lines] (SPI)

- Dependencies: [libjpeg-dev](https://packages.debian.org/buster/libjpeg-dev), [Pillow](https://pypi.org/project/Pillow), [pyusb](https://pypi.org/project/pyusb), [Adafruit-GPIO](https://pypi.org/project/Adafruit-GPIO), [adafruit-extended-bus](https://pypi.org/project/adafruit-extended-bus), [adafruit-circuitpython-framebuf](https://pypi.org/project/adafruit-circuitpython-framebuf), [Adafruit-Circuitpython-SSD1306](https://pypi.org/project/Adafruit-Circuitpython-SSD1306)

This Function outputs to a 128x32 SSD1306 OLED display via SPI. This display Function will show 4 lines at a time, so channels are added in sets of 4 when Number of Line Sets is modified. Every Period, the LCD will refresh and display the next set of lines. Therefore, the first set of lines that are displayed are channels 0 - 3, then 4 - 7, and so on. After all channels have been displayed, it will cycle back to the beginning.

#### Options

##### Period (seconds)

- Type: Decimal
- Default Value: 10
- Description: The duration (seconds) between measurements or actions

##### Number of Line Sets

- Type: Integer
- Default Value: 1
- Description: How many sets of lines to cycle on the LCD

##### SPI Device

- Type: Integer
- Description: The SPI device

##### SPI Bus

- Type: Integer
- Description: The SPI bus

##### DC Pin

- Type: Integer
- Default Value: 16
- Description: The pin (BCM numbering) connected to DC of the display

##### Reset Pin

- Type: Integer
- Default Value: 19
- Description: The pin (BCM numbering) connected to RST of the display

##### CS Pin

- Type: Integer
- Default Value: 17
- Description: The pin (BCM numbering) connected to CS of the display

##### Characters Per Line

- Type: Integer
- Default Value: 21
- Description: The maximum number of characters to display per line

##### Use Non-Default Font

- Type: Boolean
- Description: Don't use the default font. Enable to specify the path to a font to use.

##### Non-Default Font Path

- Type: Text
- Default Value: /usr/share/fonts/truetype/dejavu//DejaVuSans.ttf
- Description: The path to the non-default font to use

##### Font Size (pt)

- Type: Integer
- Default Value: 10
- Description: The size of the font, in points

##### Display Unit

- Type: Boolean
- Default Value: True
- Description: Display the measurement unit (if available)

#### Channel Options

##### Line Display Type

- Type: Select
- Description: What to display on the line

##### Measurement

- Type: Select Measurement
- Selections: Input, Math, Function, Output, PID, 
- Description: Measurement to display on the line

##### Max Age

- Type: Decimal
- Default Value: 360
- Description: The maximum age (seconds) of the measurement to use

##### Measurement Decimal

- Type: Integer
- Default Value: 1
- Description: The number of digits after the decimal

##### Text

- Type: Text
- Default Value: Text
- Description: Text to display

##### Display Unit

- Type: Boolean
- Default Value: True
- Description: Display the measurement unit (if available)

### Display: SSD1306 OLED 128x64 [4 Lines] (I2C)

- Dependencies: [libjpeg-dev](https://packages.debian.org/buster/libjpeg-dev), [Pillow](https://pypi.org/project/Pillow), [pyusb](https://pypi.org/project/pyusb), [adafruit-extended-bus](https://pypi.org/project/adafruit-extended-bus), [adafruit-circuitpython-framebuf](https://pypi.org/project/adafruit-circuitpython-framebuf), [Adafruit-Circuitpython-SSD1306](https://pypi.org/project/Adafruit-Circuitpython-SSD1306)

This Function outputs to a 128x64 SSD1306 OLED display via I2C. This display Function will show 4 lines at a time, so channels are added in sets of 4 when Number of Line Sets is modified. Every Period, the LCD will refresh and display the next set of lines. Therefore, the first set of lines that are displayed are channels 0 - 3, then 4 - 7, and so on. After all channels have been displayed, it will cycle back to the beginning.

#### Options

##### Period (seconds)

- Type: Decimal
- Default Value: 10
- Description: The duration (seconds) between measurements or actions

##### I2C Address

- Type: Text
- Default Value: 0x3c
- Description: The I2C address of the device

##### I2C Bus

- Type: Integer
- Default Value: 1
- Description: The I2C bus the device is connected to

##### Number of Line Sets

- Type: Integer
- Default Value: 1
- Description: How many sets of lines to cycle on the LCD

##### Reset Pin

- Type: Integer
- Default Value: 17
- Description: The pin (BCM numbering) connected to RST of the display

##### Characters Per Line

- Type: Integer
- Default Value: 17
- Description: The maximum number of characters to display per line

##### Use Non-Default Font

- Type: Boolean
- Description: Don't use the default font. Enable to specify the path to a font to use.

##### Non-Default Font Path

- Type: Text
- Default Value: /usr/share/fonts/truetype/dejavu//DejaVuSans.ttf
- Description: The path to the non-default font to use

##### Font Size (pt)

- Type: Integer
- Default Value: 12
- Description: The size of the font, in points

#### Channel Options

##### Line Display Type

- Type: Select
- Description: What to display on the line

##### Measurement

- Type: Select Measurement
- Selections: Input, Math, Function, Output, PID, 
- Description: Measurement to display on the line

##### Max Age

- Type: Decimal
- Default Value: 360
- Description: The maximum age (seconds) of the measurement to use

##### Measurement Decimal

- Type: Integer
- Default Value: 1
- Description: The number of digits after the decimal

##### Text

- Type: Text
- Default Value: Text
- Description: Text to display

##### Display Unit

- Type: Boolean
- Default Value: True
- Description: Display the measurement unit (if available)

### Display: SSD1306 OLED 128x64 [4 Lines] (SPI)

- Dependencies: [libjpeg-dev](https://packages.debian.org/buster/libjpeg-dev), [Pillow](https://pypi.org/project/Pillow), [pyusb](https://pypi.org/project/pyusb), [Adafruit-GPIO](https://pypi.org/project/Adafruit-GPIO), [adafruit-extended-bus](https://pypi.org/project/adafruit-extended-bus), [adafruit-circuitpython-framebuf](https://pypi.org/project/adafruit-circuitpython-framebuf), [Adafruit-Circuitpython-SSD1306](https://pypi.org/project/Adafruit-Circuitpython-SSD1306)

This Function outputs to a 128x64 SSD1306 OLED display via SPI. This display Function will show 4 lines at a time, so channels are added in sets of 4 when Number of Line Sets is modified. Every Period, the LCD will refresh and display the next set of lines. Therefore, the first set of lines that are displayed are channels 0 - 3, then 4 - 7, and so on. After all channels have been displayed, it will cycle back to the beginning.

#### Options

##### Period (seconds)

- Type: Decimal
- Default Value: 10
- Description: The duration (seconds) between measurements or actions

##### Number of Line Sets

- Type: Integer
- Default Value: 1
- Description: How many sets of lines to cycle on the LCD

##### SPI Device

- Type: Integer
- Description: The SPI device

##### SPI Bus

- Type: Integer
- Description: The SPI bus

##### DC Pin

- Type: Integer
- Default Value: 16
- Description: The pin (BCM numbering) connected to DC of the display

##### Reset Pin

- Type: Integer
- Default Value: 19
- Description: The pin (BCM numbering) connected to RST of the display

##### CS Pin

- Type: Integer
- Default Value: 17
- Description: The pin (BCM numbering) connected to CS of the display

##### Characters Per Line

- Type: Integer
- Default Value: 17
- Description: The maximum number of characters to display per line

##### Use Non-Default Font

- Type: Boolean
- Description: Don't use the default font. Enable to specify the path to a font to use.

##### Non-Default Font Path

- Type: Text
- Default Value: /usr/share/fonts/truetype/dejavu//DejaVuSans.ttf
- Description: The path to the non-default font to use

##### Font Size (pt)

- Type: Integer
- Default Value: 12
- Description: The size of the font, in points

#### Channel Options

##### Line Display Type

- Type: Select
- Description: What to display on the line

##### Measurement

- Type: Select Measurement
- Selections: Input, Math, Function, Output, PID, 
- Description: Measurement to display on the line

##### Max Age

- Type: Decimal
- Default Value: 360
- Description: The maximum age (seconds) of the measurement to use

##### Measurement Decimal

- Type: Integer
- Default Value: 1
- Description: The number of digits after the decimal

##### Text

- Type: Text
- Default Value: Text
- Description: Text to display

##### Display Unit

- Type: Boolean
- Default Value: True
- Description: Display the measurement unit (if available)

### Display: SSD1306 OLED 128x64 [8 Lines] (I2C)

- Dependencies: [libjpeg-dev](https://packages.debian.org/buster/libjpeg-dev), [Pillow](https://pypi.org/project/Pillow), [pyusb](https://pypi.org/project/pyusb), [adafruit-extended-bus](https://pypi.org/project/adafruit-extended-bus), [adafruit-circuitpython-framebuf](https://pypi.org/project/adafruit-circuitpython-framebuf), [Adafruit-Circuitpython-SSD1306](https://pypi.org/project/Adafruit-Circuitpython-SSD1306)

This Function outputs to a 128x64 SSD1306 OLED display via I2C. This display Function will show 8 lines at a time, so channels are added in sets of 8 when Number of Line Sets is modified. Every Period, the LCD will refresh and display the next set of lines. Therefore, the first set of lines that are displayed are channels 0 - 7, then 8 - 15, and so on. After all channels have been displayed, it will cycle back to the beginning.

#### Options

##### Period (seconds)

- Type: Decimal
- Default Value: 10
- Description: The duration (seconds) between measurements or actions

##### I2C Address

- Type: Text
- Default Value: 0x3c
- Description: The I2C address of the device

##### I2C Bus

- Type: Integer
- Default Value: 1
- Description: The I2C bus the device is connected to

##### Number of Line Sets

- Type: Integer
- Default Value: 1
- Description: How many sets of lines to cycle on the LCD

##### Reset Pin

- Type: Integer
- Default Value: 17
- Description: The pin (BCM numbering) connected to RST of the display

##### Characters Per Line

- Type: Integer
- Default Value: 21
- Description: The maximum number of characters to display per line

##### Use Non-Default Font

- Type: Boolean
- Description: Don't use the default font. Enable to specify the path to a font to use.

##### Non-Default Font Path

- Type: Text
- Default Value: /usr/share/fonts/truetype/dejavu//DejaVuSans.ttf
- Description: The path to the non-default font to use

##### Font Size (pt)

- Type: Integer
- Default Value: 10
- Description: The size of the font, in points

#### Channel Options

##### Line Display Type

- Type: Select
- Description: What to display on the line

##### Measurement

- Type: Select Measurement
- Selections: Input, Math, Function, Output, PID, 
- Description: Measurement to display on the line

##### Max Age

- Type: Decimal
- Default Value: 360
- Description: The maximum age (seconds) of the measurement to use

##### Measurement Decimal

- Type: Integer
- Default Value: 1
- Description: The number of digits after the decimal

##### Text

- Type: Text
- Default Value: Text
- Description: Text to display

##### Display Unit

- Type: Boolean
- Default Value: True
- Description: Display the measurement unit (if available)

### Display: SSD1306 OLED 128x64 [8 Lines] (SPI)

- Dependencies: [libjpeg-dev](https://packages.debian.org/buster/libjpeg-dev), [Pillow](https://pypi.org/project/Pillow), [pyusb](https://pypi.org/project/pyusb), [Adafruit-GPIO](https://pypi.org/project/Adafruit-GPIO), [adafruit-extended-bus](https://pypi.org/project/adafruit-extended-bus), [adafruit-circuitpython-framebuf](https://pypi.org/project/adafruit-circuitpython-framebuf), [Adafruit-Circuitpython-SSD1306](https://pypi.org/project/Adafruit-Circuitpython-SSD1306)

This Function outputs to a 128x64 SSD1306 OLED display via SPI. This display Function will show 8 lines at a time, so channels are added in sets of 8 when Number of Line Sets is modified. Every Period, the LCD will refresh and display the next set of lines. Therefore, the first set of lines that are displayed are channels 0 - 7, then 8 - 15, and so on. After all channels have been displayed, it will cycle back to the beginning.

#### Options

##### Period (seconds)

- Type: Decimal
- Default Value: 10
- Description: The duration (seconds) between measurements or actions

##### Number of Line Sets

- Type: Integer
- Default Value: 1
- Description: How many sets of lines to cycle on the LCD

##### SPI Device

- Type: Integer
- Description: The SPI device

##### SPI Bus

- Type: Integer
- Description: The SPI bus

##### DC Pin

- Type: Integer
- Default Value: 16
- Description: The pin (BCM numbering) connected to DC of the display

##### Reset Pin

- Type: Integer
- Default Value: 19
- Description: The pin (BCM numbering) connected to RST of the display

##### CS Pin

- Type: Integer
- Default Value: 17
- Description: The pin (BCM numbering) connected to CS of the display

##### Characters Per Line

- Type: Integer
- Default Value: 21
- Description: The maximum number of characters to display per line

##### Use Non-Default Font

- Type: Boolean
- Description: Don't use the default font. Enable to specify the path to a font to use.

##### Non-Default Font Path

- Type: Text
- Default Value: /usr/share/fonts/truetype/dejavu//DejaVuSans.ttf
- Description: The path to the non-default font to use

##### Font Size (pt)

- Type: Integer
- Default Value: 10
- Description: The size of the font, in points

#### Channel Options

##### Line Display Type

- Type: Select
- Description: What to display on the line

##### Measurement

- Type: Select Measurement
- Selections: Input, Math, Function, Output, PID, 
- Description: Measurement to display on the line

##### Max Age

- Type: Decimal
- Default Value: 360
- Description: The maximum age (seconds) of the measurement to use

##### Measurement Decimal

- Type: Integer
- Default Value: 1
- Description: The number of digits after the decimal

##### Text

- Type: Text
- Default Value: Text
- Description: Text to display

##### Display Unit

- Type: Boolean
- Default Value: True
- Description: Display the measurement unit (if available)

### Display: SSD1309 OLED 128x64 [8 Lines] (I2C)

- Dependencies: [pyusb](https://pypi.org/project/pyusb), [luma.oled](https://pypi.org/project/luma.oled), [Pillow](https://pypi.org/project/Pillow), [libjpeg-dev](https://packages.debian.org/buster/libjpeg-dev), [zlib1g-dev](https://packages.debian.org/buster/zlib1g-dev), [libfreetype6-dev](https://packages.debian.org/buster/libfreetype6-dev), [liblcms2-dev](https://packages.debian.org/buster/liblcms2-dev), [libopenjp2-7](https://packages.debian.org/buster/libopenjp2-7), [libtiff5](https://packages.debian.org/buster/libtiff5)

This Function outputs to a 128x64 SSD1309 OLED display via I2C. This display Function will show 8 lines at a time, so channels are added in sets of 8 when Number of Line Sets is modified. Every Period, the LCD will refresh and display the next set of lines. Therefore, the first set of lines that are displayed are channels 0 - 7, then 8 - 15, and so on. After all channels have been displayed, it will cycle back to the beginning.

#### Options

##### Period (seconds)

- Type: Decimal
- Default Value: 10
- Description: The duration (seconds) between measurements or actions

##### I2C Address

- Type: Text
- Default Value: 0x3c
- Description: The I2C address of the device

##### I2C Bus

- Type: Integer
- Default Value: 1
- Description: The I2C bus the device is connected to

##### Number of Line Sets

- Type: Integer
- Default Value: 1
- Description: How many sets of lines to cycle on the LCD

##### Reset Pin

- Type: Integer
- Default Value: 17
- Description: The pin (BCM numbering) connected to RST of the display

#### Channel Options

##### Line Display Type

- Type: Select
- Description: What to display on the line

##### Measurement

- Type: Select Measurement
- Selections: Input, Math, Function, Output, PID, 
- Description: Measurement to display on the line

##### Max Age

- Type: Decimal
- Default Value: 360
- Description: The maximum age (seconds) of the measurement to use

##### Measurement Decimal

- Type: Integer
- Default Value: 1
- Description: The number of digits after the decimal

##### Text

- Type: Text
- Default Value: Text
- Description: Text to display

##### Display Unit

- Type: Boolean
- Default Value: True
- Description: Display the measurement unit (if available)

### Equation (Multi-Measure)


This function acquires two measurements and uses them within a user-set equation and stores the resulting value as the selected measurement and unit.

#### Options

##### Period (seconds)

- Type: Decimal
- Default Value: 60
- Description: The duration (seconds) between measurements or actions

##### Measurement A

- Type: Select Measurement
- Selections: Input, Math, Function, 
- Description: Measurement to replace a

##### Measurement A Max Age

- Type: Integer
- Default Value: 360
- Description: The maximum age (seconds) of the measurement to use

##### Measurement B

- Type: Select Measurement
- Selections: Input, Math, Function, 
- Description: Measurement to replace b

##### Measurement B Max Age

- Type: Integer
- Default Value: 360
- Description: The maximum age (seconds) of the measurement to use

##### Equation

- Type: Text
- Default Value: a*(2+b)
- Description: Equation using measurements a and b

### Equation (Single-Measure)


This function acquires a measurement and uses it within a user-set equation and stores the resulting value as the selected measurement and unit.

#### Options

##### Period (seconds)

- Type: Decimal
- Default Value: 60
- Description: The duration (seconds) between measurements or actions

##### Measurement

- Type: Select Measurement
- Selections: Input, Math, Function, 
- Description: Measurement to replace "x" in the equation

##### Max Age

- Type: Integer
- Default Value: 360
- Description: The maximum age (seconds) of the measurement to use

##### Equation

- Type: Text
- Default Value: x*5+2
- Description: Equation using the measurement

### Humidity (Wet/Dry-Bulb)


This function calculates the humidity based on wet and dry bulb temperature measurements.

#### Options

##### Measurements Enabled

- Type: Multi-Select
- Description: The measurements to record

##### Period (seconds)

- Type: Decimal
- Default Value: 60
- Description: The duration (seconds) between measurements or actions

##### Start Offset

- Type: Integer
- Default Value: 10
- Description: The duration (seconds) to wait before the first operation

##### Dry Bulb Temperature

- Type: Select Measurement
- Selections: Input, Math, Function, 
- Description: Dry Bulb temperature measurement

##### Dry Bulb Max Age

- Type: Integer
- Default Value: 360
- Description: The maximum age (seconds) of the measurement to use

##### Wet Bulb Temperature

- Type: Select Measurement
- Selections: Input, Math, Function, 
- Description: Wet Bulb temperature measurement

##### Wet Bulb Max Age

- Type: Integer
- Default Value: 360
- Description: The maximum age (seconds) of the measurement to use

##### Pressure

- Type: Select Measurement
- Selections: Input, Math, Function, 
- Description: Pressure measurement

##### Pressure Max Age

- Type: Integer
- Default Value: 360
- Description: The maximum age (seconds) of the measurement to use

### PID Autotune


This function will attempt to perform a PID controller autotune. That is, an output will be powered and the response measured from a sensor several times to calculate the P, I, and D gains. Updates about the operation will be sent to the Daemon log. If the autotune successfully completes, a summary will be sent to the Daemon log as well. Currently, only raising a Measurement is supported, but lowering should be possible with some modification to the function controller code. It is recommended to create a graph on a dashboard with the Measurement and Output to monitor that the Output is successfully raising the Measurement beyond the Setpoint. Note: Autotune is an experimental feature, it is not well-developed, and it has a high likelihood of failing to generate PID gains. Do not rely on it for accurately tuning your PID controller.

#### Options

##### Measurement

- Type: Select Measurement
- Selections: Input, Math, Function, 
- Description: Select a measurement the selected output will affect

##### Output

- Description: Select an output to modulate that will affect the measurement

##### Period

- Type: Integer
- Default Value: 30
- Description: The period between powering the output

##### Setpoint

- Type: Decimal
- Default Value: 50
- Description: A value sufficiently far from the current measured value that the output is capable of pushing the measurement toward

##### Noise Band

- Type: Decimal
- Default Value: 0.5
- Description: The amount above the setpoint the measurement must reach

##### Outstep

- Type: Decimal
- Default Value: 10
- Description: How many seconds the output will turn on every Period

##### Currently, only autotuning to raise a condition (measurement) is supported.

##### Direction

- Type: Select
- Options: \[**Raise**\] (Default in **bold**)
- Description: The direction the Output will push the Measurement

### Redundancy


This function stores the first available measurement. This is useful if you have multiple sensors that you want to serve as backups in case one stops working, you can set them up in the order of importance. This function will check if a measurement exits, starting with the first measurement. If it doesn't, the next is checked, until a measurement is found. Once a measurement is found, it is stored in the database with the user-set measurement and unit. The output of this function can be used as an input throughout Mycodo. If you need more than 3 measurements to be checked, you can string multiple Redundancy Functions by creating a second Function and setting the first Function's output as the second Function's input.

#### Options

##### Period (seconds)

- Type: Decimal
- Default Value: 60
- Description: The duration (seconds) between measurements or actions

##### Measurement A

- Type: Select Measurement
- Selections: Input, Math, Function, 
- Description: Measurement to replace a

##### Measurement A Max Age

- Type: Integer
- Default Value: 360
- Description: The maximum age (seconds) of the measurement to use

##### Measurement B

- Type: Select Measurement
- Selections: Input, Math, Function, 
- Description: Measurement to replace b

##### Measurement B Max Age

- Type: Integer
- Default Value: 360
- Description: The maximum age (seconds) of the measurement to use

##### Measurement C

- Type: Select Measurement
- Selections: Input, Math, Function, 
- Description: Measurement to replace C

##### Measurement C Max Age

- Type: Integer
- Default Value: 360
- Description: The maximum age (seconds) of the measurement to use

### Spacer


A spacer to organize Functions.

#### Options

##### Color

- Type: Text
- Default Value: #000000
- Description: The color of the name text

### Statistics (Last, Multiple)


This function acquires multiple measurements, calculates statistics, and stores the resulting values as the selected unit.

#### Options

##### Measurements Enabled

- Type: Multi-Select
- Description: The measurements to record

##### Period (seconds)

- Type: Decimal
- Default Value: 60
- Description: The duration (seconds) between measurements or actions

##### Max Age

- Type: Integer
- Default Value: 360
- Description: The maximum age (seconds) of the measurement to use

##### Measurement

- Description: Measurements to perform statistics on

##### Halt on Missing Measurement

- Type: Boolean
- Description: Don't calculate statistics if >= 1 measurement is not found within Max Age

### Statistics (Past, Single)


This function acquires multiple values from a single measurement, calculates statistics, and stores the resulting values as the selected unit.

#### Options

##### Measurements Enabled

- Type: Multi-Select
- Description: The measurements to record

##### Period (seconds)

- Type: Decimal
- Default Value: 60
- Description: The duration (seconds) between measurements or actions

##### Max Age

- Type: Integer
- Default Value: 360
- Description: The maximum age (seconds) of the measurement to use

##### Measurement

- Type: Select Measurement
- Selections: Input, Math, Function, 
- Description: Measurement to perform statistics on

### Sum (Last, Multiple)


This function acquires the last measurement of those that are selected, sums them, then stores the resulting value as the selected measurement and unit.

#### Options

##### Period (seconds)

- Type: Decimal
- Default Value: 60
- Description: The duration (seconds) between measurements or actions

##### Start Offset

- Type: Integer
- Default Value: 10
- Description: The duration (seconds) to wait before the first operation

##### Max Age

- Type: Integer
- Default Value: 360
- Description: The maximum age (seconds) of the measurement to use

##### Measurement

- Description: Measurement to replace "x" in the equation

### Sum (Past, Single)


This function acquires the past measurements (within Max Age) for the selected measurement, sums them, then stores the resulting value as the selected measurement and unit.

#### Options

##### Period (seconds)

- Type: Decimal
- Default Value: 60
- Description: The duration (seconds) between measurements or actions

##### Start Offset

- Type: Integer
- Default Value: 10
- Description: The duration (seconds) to wait before the first operation

##### Measurement

- Type: Select Measurement
- Selections: Input, Math, Function, 
- Description: Measurement to replace "x" in the equation

##### Max Age

- Type: Integer
- Default Value: 360
- Description: The maximum age (seconds) of the measurement to use

### Vapor Pressure Deficit


This function calculates the vapor pressure deficit based on leaf temperature and humidity.

#### Options

##### Period (seconds)

- Type: Decimal
- Default Value: 60
- Description: The duration (seconds) between measurements or actions

##### Start Offset

- Type: Integer
- Default Value: 10
- Description: The duration (seconds) to wait before the first operation

##### Temperature

- Type: Select Measurement
- Selections: Input, Math, Function, 
- Description: Temperature measurement

##### Temperature Max Age

- Type: Integer
- Default Value: 360
- Description: The maximum age (seconds) of the measurement to use

##### Humidity

- Type: Select Measurement
- Selections: Input, Math, Function, 
- Description: Humidity measurement

##### Humidity Max Age

- Type: Integer
- Default Value: 360
- Description: The maximum age (seconds) of the measurement to use

### Verification


This function acquires 2 measurements, calculates the difference, and if the difference is not larger than the set threshold, the Measurement A value is stored. This enables verifying one sensor's measurement with another sensor's measurement. Only when they are both in agreement is a measurement stored. This stored measurement can be used in functions such as Conditional Statements that will notify the user if no measurement is avilable to indicate there may be an issue with a sensor.

#### Options

##### Period (seconds)

- Type: Decimal
- Default Value: 60
- Description: The duration (seconds) between measurements or actions

##### Measurement A

- Type: Select Measurement
- Selections: Input, Math, Function, 
- Description: Measurement A

##### Measurement A Max Age

- Type: Integer
- Default Value: 360
- Description: The maximum age (seconds) of the measurement to use

##### Measurement B

- Type: Select Measurement
- Selections: Input, Math, Function, 
- Description: Measurement B

##### Measurement A Max Age

- Type: Integer
- Default Value: 360
- Description: The maximum age (seconds) of the measurement to use

##### Maximum Difference

- Type: Decimal
- Default Value: 10.0
- Description: The maximum allowed difference between the measurements

