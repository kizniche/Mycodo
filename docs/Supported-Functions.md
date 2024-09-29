## Built-In Functions

### Average (Last, Multiple)


This function acquires the last measurement of those that are selected, averages them, then stores the resulting value as the selected measurement and unit.
<table><thead><tr class="header"><th>Option</th><th>Type</th><th>Description</th></tr></thead><tbody><tr><td>Period (Seconds)</td><td>Decimal
- Default Value: 60</td><td>The duration between measurements or actions</td></tr><tr><td>Start Offset (Seconds)</td><td>Integer
- Default Value: 10</td><td>The duration to wait before the first operation</td></tr><tr><td>Max Age (Seconds)</td><td>Integer
- Default Value: 360</td><td>The maximum age of the measurement to use</td></tr><tr><td>Measurement</td></td><td>Measurement to replace "x" in the equation</td></tr></tbody></table>

### Average (Past, Single)


This function acquires the past measurements (within Max Age) for the selected measurement, averages them, then stores the resulting value as the selected measurement and unit. Note: There is a bug in InfluxDB 1.8.10 that prevents the mean() function from working properly. Therefore, if you are using Influxdb v1.x, the median() function will be used. InfluxDB 2.x is unaffected and uses mean(). To get the true mean, upgrade to InfluxDB 2.x.
<table><thead><tr class="header"><th>Option</th><th>Type</th><th>Description</th></tr></thead><tbody><tr><td>Period (Seconds)</td><td>Decimal
- Default Value: 60</td><td>The duration between measurements or actions</td></tr><tr><td>Start Offset (Seconds)</td><td>Integer
- Default Value: 10</td><td>The duration to wait before the first operation</td></tr><tr><td>Measurement</td><td>Select Measurement (Input, Function)</td><td>Measurement to replace "x" in the equation</td></tr><tr><td>Max Age (Seconds)</td><td>Integer
- Default Value: 360</td><td>The maximum age of the measurement to use</td></tr></tbody></table>

### Backup to Remote Host (rsync)

- Dependencies: [rsync](https://packages.debian.org/search?keywords=rsync)

This function will use rsync to back up assets on this system to a remote system. Your remote system needs to have an SSH server running and rsync installed. This system will need rsync installed and be able to access your remote system via SSH keyfile (login without a password). You can do this by creating an SSH key on this system running Mycodo with "ssh-keygen" (leave the password field empty), then run "ssh-copy-id -i ~/.ssh/id_rsa.pub pi@REMOTE_HOST_IP" to transfer your public SSH key to your remote system (changing pi and REMOTE_HOST_IP to the appropriate user and host of your remote system). You can test if this worked by trying to connect to your remote system with "ssh pi@REMOTE_HOST_IP" and you should log in without being asked for a password. Be careful not to set the Period too low, which could cause the function to begin running before the previous operation(s) complete. Therefore, it is recommended to set a relatively long Period (greater than 10 minutes). The default Period is 15 days. Note that the Period will reset if the system or the Mycodo daemon restarts and the Function will run, generating new settings and measurement archives that will be synced. There are two common ways to use this Function: 1) A short period (1 hour), only have Backup Camera Directories enabled, and use the Backup Settings Now and Backup Measurements Now buttons manually to perform a backup, and 2) A long period (15 days), only have Backup Settings and Backup Measurements enabled. You can even create two of these Functions with one set up to perform long-Period settings and measurement backups and the other set up to perform short-Period camera backups.
<table><thead><tr class="header"><th>Option</th><th>Type</th><th>Description</th></tr></thead><tbody><tr><td>Period (Seconds)</td><td>Decimal
- Default Value: 1296000</td><td>The duration between measurements or actions</td></tr><tr><td>Start Offset (Seconds)</td><td>Integer
- Default Value: 300</td><td>The duration to wait before the first operation</td></tr><tr><td>Local User</td><td>Text
- Default Value: pi</td><td>The user on this system that will run rsync</td></tr><tr><td>Remote User</td><td>Text
- Default Value: pi</td><td>The user to log in to the remote host</td></tr><tr><td>Remote Host</td><td>Text
- Default Value: 192.168.0.50</td><td>The IP or host address to send the backup to</td></tr><tr><td>Remote Backup Path</td><td>Text
- Default Value: /home/pi/backup_mycodo</td><td>The path to backup to on the remote host</td></tr><tr><td>Rsync Timeout (Seconds)</td><td>Integer
- Default Value: 3600</td><td>How long to allow rsync to complete</td></tr><tr><td>Local Backup Path</td><td>Text</td><td>A local path to backup (leave blank to disable)</td></tr><tr><td>Backup Settings Export File</td><td>Boolean
- Default Value: True</td><td>Create and backup exported settings file</td></tr><tr><td>Remove Local Settings Backups</td><td>Boolean</td><td>Remove local settings backups after successful transfer to remote host</td></tr><tr><td>Backup Measurements</td><td>Boolean
- Default Value: True</td><td>Backup all influxdb measurements</td></tr><tr><td>Remove Local Measurements Backups</td><td>Boolean</td><td>Remove local measurements backups after successful transfer to remote host</td></tr><tr><td>Backup Camera Directories</td><td>Boolean
- Default Value: True</td><td>Backup all camera directories</td></tr><tr><td>Remove Local Camera Images</td><td>Boolean</td><td>Remove local camera images after successful transfer to remote host</td></tr><tr><td>SSH Port</td><td>Integer
- Default Value: 22</td><td>Specify a nonstandard SSH port</td></tr><tr><td colspan="3">Commands</td></tr><tr><td colspan="3">Backup of settings are only created if the Mycodo version or database versions change. This is due to this Function running periodically- if it created a new backup every Period, there would soon be many identical backups. Therefore, if you want to induce the backup of settings, measurements, or camera directories and sync them to your remote system, use the buttons below.</td></tr><tr><td>Backup Settings Now</td><td>Button</td><td></td></tr><tr><td>Backup Measurements Now</td><td>Button</td><td></td></tr><tr><td>Backup Camera Directories Now</td><td>Button</td><td></td></tr></tbody></table>

### Bang-Bang Hysteretic (On/Off) (Raise/Lower)


A simple bang-bang control for controlling one output from one input. Select an input, an output, enter a setpoint and a hysteresis, and select a direction. The output will turn on when the input is below (lower = setpoint - hysteresis) and turn off when the input is above (higher = setpoint + hysteresis). This is the behavior when Raise is selected, such as when heating. Lower direction has the opposite behavior - it will try to turn the output on in order to drive the input lower.
<table><thead><tr class="header"><th>Option</th><th>Type</th><th>Description</th></tr></thead><tbody><tr><td>Measurement</td><td>Select Measurement (Input, Function)</td><td>Select a measurement the selected output will affect</td></tr><tr><td>Measurement: Max Age (Seconds)</td><td>Integer
- Default Value: 360</td><td>The maximum age of the measurement to use</td></tr><tr><td>Output</td><td>Select Device, Measurement, and Channel (Output)</td><td>Select an output to control that will affect the measurement</td></tr><tr><td>Setpoint</td><td>Decimal
- Default Value: 50</td><td>The desired setpoint</td></tr><tr><td>Hysteresis</td><td>Decimal
- Default Value: 1</td><td>The amount above and below the setpoint that defines the control band</td></tr><tr><td>Direction</td><td>Select(Options: [<strong>Raise</strong> | Lower] (Default in <strong>bold</strong>)</td><td>Raise means the measurement will increase when the control is on (heating). Lower means the measurement will decrease when the output is on (cooling)</td></tr><tr><td>Period (Seconds)</td><td>Decimal
- Default Value: 5</td><td>The duration between measurements or actions</td></tr></tbody></table>

### Bang-Bang Hysteretic (On/Off) (Raise/Lower/Both)


A simple bang-bang control for controlling one or two outputs from one input. Select an input, a raise and/or lower output, enter a setpoint and a hysteresis, and select a direction. The output will turn on when the input is below (lower = setpoint - hysteresis) and turn off when the input is above (higher = setpoint + hysteresis). This is the behavior when Raise is selected, such as when heating. Lower direction has the opposite behavior - it will try to turn the output on in order to drive the input lower. The Both option will raise and lower. Note: This output will only work with On/Off Outputs.
<table><thead><tr class="header"><th>Option</th><th>Type</th><th>Description</th></tr></thead><tbody><tr><td>Measurement</td><td>Select Measurement (Input, Function)</td><td>Select a measurement the selected output will affect</td></tr><tr><td>Measurement: Max Age (Seconds)</td><td>Integer
- Default Value: 360</td><td>The maximum age of the measurement to use</td></tr><tr><td>Output (Raise)</td><td>Select Device, Measurement, and Channel (Output)</td><td>Select an output to control that will raise the measurement</td></tr><tr><td>Output (Lower)</td><td>Select Device, Measurement, and Channel (Output)</td><td>Select an output to control that will lower the measurement</td></tr><tr><td>Setpoint</td><td>Decimal
- Default Value: 50</td><td>The desired setpoint</td></tr><tr><td>Hysteresis</td><td>Decimal
- Default Value: 1</td><td>The amount above and below the setpoint that defines the control band</td></tr><tr><td>Direction</td><td>Select(Options: [Raise | Lower | <strong>Both</strong>] (Default in <strong>bold</strong>)</td><td>Raise means the measurement will increase when the control is on (heating). Lower means the measurement will decrease when the output is on (cooling)</td></tr><tr><td>Period (Seconds)</td><td>Decimal
- Default Value: 5</td><td>The duration between measurements or actions</td></tr></tbody></table>

### Bang-Bang Hysteretic (PWM) (Raise/Lower/Both)


A simple bang-bang control for controlling one PWM output from one input. Select an input, a PWM output, enter a setpoint and a hysteresis, and select a direction. The output will turn on when the input is below below (lower = setpoint - hysteresis) and turn off when the input is above (higher = setpoint + hysteresis). This is the behavior when Raise is selected, such as when heating. Lower direction has the opposite behavior - it will try to turn the output on in order to drive the input lower. The Both option will raise and lower. Note: This output will only work with PWM Outputs.
<table><thead><tr class="header"><th>Option</th><th>Type</th><th>Description</th></tr></thead><tbody><tr><td>Measurement</td><td>Select Measurement (Input, Function)</td><td>Select a measurement the selected output will affect</td></tr><tr><td>Measurement: Max Age (Seconds)</td><td>Integer
- Default Value: 360</td><td>The maximum age of the measurement to use</td></tr><tr><td>Output</td><td>Select Device, Measurement, and Channel (Output)</td><td>Select an output to control that will affect the measurement</td></tr><tr><td>Setpoint</td><td>Decimal
- Default Value: 50</td><td>The desired setpoint</td></tr><tr><td>Hysteresis</td><td>Decimal
- Default Value: 1</td><td>The amount above and below the setpoint that defines the control band</td></tr><tr><td>Direction</td><td>Select(Options: [Raise | Lower | <strong>Both</strong>] (Default in <strong>bold</strong>)</td><td>Raise means the measurement will increase when the control is on (heating). Lower means the measurement will decrease when the output is on (cooling)</td></tr><tr><td>Period (Seconds)</td><td>Decimal
- Default Value: 5</td><td>The duration between measurements or actions</td></tr><tr><td>Duty Cycle (increase)</td><td>Decimal
- Default Value: 90</td><td>The duty cycle to increase the measurement</td></tr><tr><td>Duty Cycle (maintain)</td><td>Decimal
- Default Value: 55</td><td>The duty cycle to maintain the measurement</td></tr><tr><td>Duty Cycle (decrease)</td><td>Decimal
- Default Value: 20</td><td>The duty cycle to decrease the measurement</td></tr><tr><td>Duty Cycle (shutdown)</td><td>Decimal</td><td>The duty cycle to set when the function shuts down</td></tr></tbody></table>

### Camera: libcamera: Image/Video

- Dependencies: [libcamera-apps](https://packages.debian.org/search?keywords=libcamera-apps), [ffmpeg](https://packages.debian.org/search?keywords=ffmpeg)

NOTE: THIS IS CURRENTLY EXPERIMENTAL - USE AT YOUR OWN RISK UNTIL THIS NOTICE IS REMOVED. Capture images and videos from a camera using libcamera-still and libcamera-vid. The Function must be activated in order to capture still and timelapse images and use the Camera Widget.
<table><thead><tr class="header"><th>Option</th><th>Type</th><th>Description</th></tr></thead><tbody><tr><td>Status Period (seconds)</td><td>Integer
- Default Value: 60</td><td>The duration (seconds) to update the Function status on the UI</td></tr><tr><td colspan="3">Image options.</td></tr><tr><td>Custom Image Path</td><td>Text</td><td>Set a non-default path for still images to be saved</td></tr><tr><td>Custom Timelapse Path</td><td>Text</td><td>Set a non-default path for timelapse images to be saved</td></tr><tr><td>Image Extension</td><td>Select(Options: [<strong>JPG</strong> | PNG | BMP | RGB | YUV420] (Default in <strong>bold</strong>)</td><td>The file type/format to save images</td></tr><tr><td>Image: Resolution: Width</td><td>Integer
- Default Value: 720</td><td>The width of still images</td></tr><tr><td>Image: Resolution: Height</td><td>Integer
- Default Value: 480</td><td>The height of still images</td></tr><tr><td>Brightness</td><td>Decimal</td><td>The brightness of still images (-1 to 1)</td></tr><tr><td>Image: Contrast</td><td>Decimal
- Default Value: 1.0</td><td>The contrast of still images. Larger values produce images with more contrast.</td></tr><tr><td>Saturation</td><td>Decimal
- Default Value: 1.0</td><td>The saturation of still images. Larger values produce more saturated colours; 0.0 produces a greyscale image.</td></tr><tr><td>Sharpness</td><td>Decimal</td><td>The sharpness of still images. Larger values produce more saturated colours; 0.0 produces a greyscale image.</td></tr><tr><td>Shutter Speed (Microseconds)</td><td>Integer</td><td>The shutter speed, in microseconds. 0 disables and returns to auto exposure.</td></tr><tr><td>Gain</td><td>Decimal
- Default Value: 1.0</td><td>The gain of still images.</td></tr><tr><td>White Balance: Auto</td><td>Select(Options: [<strong>Auto</strong> | Incandescent | Tungsten | Fluorescent | Indoor | Daylight | Cloudy | Custom] (Default in <strong>bold</strong>)</td><td>The white balance of images</td></tr><tr><td>White Balance: Red Gain</td><td>Decimal</td><td>The red gain of white balance for still images (disabled Auto White Balance if red and blue are not set to 0)</td></tr><tr><td>White Balance: Blue Gain</td><td>Decimal</td><td>The red gain of white balance for still images (disabled Auto White Balance if red and blue are not set to 0)</td></tr><tr><td>Flip Horizontally</td><td>Boolean</td><td>Flip the image horizontally.</td></tr><tr><td>Flip Vertically</td><td>Boolean</td><td>Flip the image vertically.</td></tr><tr><td>Rotate (Degrees)</td><td>Integer</td><td>Rotate the image.</td></tr><tr><td>Custom libcamera-still Options</td><td>Text</td><td>Pass custom options to the libcamera-still command.</td></tr><tr><td colspan="3">Video options.</td></tr><tr><td>Custom Video Path</td><td>Text</td><td>Set a non-default path for videos to be saved</td></tr><tr><td>Video Extension</td><td>Select(Options: [<strong>H264 -> MP4 (with ffmpeg)</strong> | H264 | MJPEG | YUV420] (Default in <strong>bold</strong>)</td><td>The file type/format to save videos</td></tr><tr><td>Video: Resolution: Width</td><td>Integer
- Default Value: 720</td><td>The width of videos</td></tr><tr><td>Video: Resolution: Height</td><td>Integer
- Default Value: 480</td><td>The height of videos</td></tr><tr><td>Custom libcamera-vid Options</td><td>Text</td><td>Pass custom options to the libcamera-vid command.</td></tr><tr><td colspan="3">Commands</td></tr><tr><td>Capture Image</td><td>Button</td><td></td></tr><tr><td colspan="3">To capture a video, enter the duration and press Capture Video.</td></tr><tr><td>Video Duration (Seconds)</td><td>Integer
- Default Value: 5</td><td>How long to record the video</td></tr><tr><td>Capture Video</td><td>Button</td><td></td></tr><tr><td colspan="3">To start a timelapse, enter the duration and period and press Start Timelapse.</td></tr><tr><td>Timelapse Duration (Seconds)</td><td>Integer
- Default Value: 2592000</td><td>How long the timelapse will run</td></tr><tr><td>Timelapse Period (Seconds)</td><td>Integer
- Default Value: 600</td><td>How often to take a timelapse photo</td></tr><tr><td>Start Timelapse</td><td>Button</td><td></td></tr><tr><td colspan="3">To stop an active timelapse, press Stop Timelapse.</td></tr><tr><td>Stop Timelapse</td><td>Button</td><td></td></tr><tr><td colspan="3">To pause or resume an active timelapse, press Pause Timelapse or Resume Timelapse.</td></tr><tr><td>Pause Timelapse</td><td>Button</td><td></td></tr><tr><td>Resume Timelapse</td><td>Button</td><td></td></tr></tbody></table>

### Difference


This function acquires 2 measurements, calculates the difference, and stores the resulting value as the selected measurement and unit.
<table><thead><tr class="header"><th>Option</th><th>Type</th><th>Description</th></tr></thead><tbody><tr><td>Period (Seconds)</td><td>Decimal
- Default Value: 60</td><td>The duration between measurements or actions</td></tr><tr><td>Measurement: A</td><td>Select Measurement (Input, Function)</td><td></td></tr><tr><td>Measurement A: Max Age (Seconds)</td><td>Integer
- Default Value: 360</td><td>The maximum age of the measurement to use</td></tr><tr><td>Measurement: B</td><td>Select Measurement (Input, Function)</td><td></td></tr><tr><td>Measurement B: Max Age (Seconds)</td><td>Integer
- Default Value: 360</td><td>The maximum age of the measurement to use</td></tr><tr><td>Reverse Order</td><td>Boolean</td><td>Reverse the order in the calculation</td></tr><tr><td>Absolute Difference</td><td>Boolean</td><td>Return the absolute value of the difference</td></tr></tbody></table>

### Display: Generic LCD 16x2 (I2C)

- Dependencies: [smbus2](https://pypi.org/project/smbus2)

This Function outputs to a generic 16x2 LCD display via I2C. Since this display can show 2 lines at a time, channels are added in sets of 2 when Number of Line Sets is modified. Every Period, the LCD will refresh and display the next set of lines. Therefore, the first 2 lines that are displayed are channels 0 and 1, then 2 and 3, and so on. After all channels have been displayed, it will cycle back to the beginning.
<table><thead><tr class="header"><th>Option</th><th>Type</th><th>Description</th></tr></thead><tbody><tr><td>Period (Seconds)</td><td>Decimal
- Default Value: 10</td><td>The duration between measurements or actions</td></tr><tr><td>I2C Address</td><td>Text
- Default Value: 0x20</td><td></td></tr><tr><td>I2C Bus</td><td>Integer
- Default Value: 1</td><td></td></tr><tr><td>Number of Line Sets</td><td>Integer
- Default Value: 1</td><td>How many sets of lines to cycle on the LCD</td></tr><tr><td colspan="3">Channel Options</td></tr><tr><td>Line Display Type</td><td>Select</td><td>What to display on the line</td></tr><tr><td>Measurement</td><td>Select Measurement (Input, Function, Output, PID)</td><td>Measurement to display on the line</td></tr><tr><td>Max Age (Seconds)</td><td>Integer
- Default Value: 360</td><td>The maximum age of the measurement to use</td></tr><tr><td>Measurement Label</td><td>Text</td><td>Set to overwrite the default measurement label</td></tr><tr><td>Measurement Decimal</td><td>Integer
- Default Value: 1</td><td>The number of digits after the decimal</td></tr><tr><td>Text</td><td>Text
- Default Value: Text</td><td>Text to display</td></tr><tr><td>Display Unit</td><td>Boolean
- Default Value: True</td><td>Display the measurement unit (if available)</td></tr><tr><td colspan="3">Commands</td></tr><tr><td>Backlight On</td><td>Button</td><td></td></tr><tr><td>Backlight Off</td><td>Button</td><td></td></tr><tr><td>Backlight Flashing On</td><td>Button</td><td></td></tr><tr><td>Backlight Flashing Off</td><td>Button</td><td></td></tr></tbody></table>

### Display: Generic LCD 20x4 (I2C)

- Dependencies: [smbus2](https://pypi.org/project/smbus2)

This Function outputs to a generic 20x4 LCD display via I2C. Since this display can show 4 lines at a time, channels are added in sets of 4 when Number of Line Sets is modified. Every Period, the LCD will refresh and display the next set of lines. Therefore, the first 4 lines that are displayed are channels 0, 1, 2, and 3, then 4, 5, 6, and 7, and so on. After all channels have been displayed, it will cycle back to the beginning.
<table><thead><tr class="header"><th>Option</th><th>Type</th><th>Description</th></tr></thead><tbody><tr><td>Period (Seconds)</td><td>Decimal
- Default Value: 10</td><td>The duration between measurements or actions</td></tr><tr><td>I2C Address</td><td>Text
- Default Value: 0x20</td><td></td></tr><tr><td>I2C Bus</td><td>Integer
- Default Value: 1</td><td></td></tr><tr><td>Number of Line Sets</td><td>Integer
- Default Value: 1</td><td>How many sets of lines to cycle on the LCD</td></tr><tr><td colspan="3">Channel Options</td></tr><tr><td>Line Display Type</td><td>Select</td><td>What to display on the line</td></tr><tr><td>Measurement</td><td>Select Measurement (Input, Function, Output, PID)</td><td>Measurement to display on the line</td></tr><tr><td>Max Age (Seconds)</td><td>Integer
- Default Value: 360</td><td>The maximum age of the measurement to use</td></tr><tr><td>Measurement Label</td><td>Text</td><td>Set to overwrite the default measurement label</td></tr><tr><td>Measurement Decimal</td><td>Integer
- Default Value: 1</td><td>The number of digits after the decimal</td></tr><tr><td>Text</td><td>Text
- Default Value: Text</td><td>Text to display</td></tr><tr><td>Display Unit</td><td>Boolean
- Default Value: True</td><td>Display the measurement unit (if available)</td></tr><tr><td colspan="3">Commands</td></tr><tr><td>Backlight On</td><td>Button</td><td></td></tr><tr><td>Backlight Off</td><td>Button</td><td></td></tr></tbody></table>

### Display: Grove LCD 16x2 (I2C)

- Dependencies: [smbus2](https://pypi.org/project/smbus2)

This Function outputs to the Grove 16x2 LCD display via I2C. Since this display can show 2 lines at a time, channels are added in sets of 2 when Number of Line Sets is modified. Every Period, the LCD will refresh and display the next set of lines. Therefore, the first 2 lines that are displayed are channels 0 and 1, then 2 and 3, and so on. After all channels have been displayed, it will cycle back to the beginning.
<table><thead><tr class="header"><th>Option</th><th>Type</th><th>Description</th></tr></thead><tbody><tr><td>Period (Seconds)</td><td>Decimal
- Default Value: 10</td><td>The duration between measurements or actions</td></tr><tr><td>I2C Address</td><td>Text
- Default Value: 0x3e</td><td></td></tr><tr><td>I2C Bus</td><td>Integer
- Default Value: 1</td><td></td></tr><tr><td>Backlight I2C Address</td><td>Text
- Default Value: 0x62</td><td>I2C address to control the backlight</td></tr><tr><td>Number of Line Sets</td><td>Integer
- Default Value: 1</td><td>How many sets of lines to cycle on the LCD</td></tr><tr><td>Backlight Red (0 - 255)</td><td>Integer
- Default Value: 255</td><td>Set the red color value of the backlight on startup.</td></tr><tr><td>Backlight Green (0 - 255)</td><td>Integer
- Default Value: 255</td><td>Set the green color value of the backlight on startup.</td></tr><tr><td>Backlight Blue (0 - 255)</td><td>Integer
- Default Value: 255</td><td>Set the blue color value of the backlight on startup.</td></tr><tr><td colspan="3">Channel Options</td></tr><tr><td>Line Display Type</td><td>Select</td><td>What to display on the line</td></tr><tr><td>Measurement</td><td>Select Measurement (Input, Function, Output, PID)</td><td>Measurement to display on the line</td></tr><tr><td>Max Age (Seconds)</td><td>Integer
- Default Value: 360</td><td>The maximum age of the measurement to use</td></tr><tr><td>Measurement Label</td><td>Text</td><td>Set to overwrite the default measurement label</td></tr><tr><td>Measurement Decimal</td><td>Integer
- Default Value: 1</td><td>The number of digits after the decimal</td></tr><tr><td>Text</td><td>Text
- Default Value: Text</td><td>Text to display</td></tr><tr><td>Display Unit</td><td>Boolean
- Default Value: True</td><td>Display the measurement unit (if available)</td></tr><tr><td colspan="3">Commands</td></tr><tr><td>Backlight On</td><td>Button</td><td></td></tr><tr><td>Backlight Off</td><td>Button</td><td></td></tr><tr><td>Color (RGB)</td><td>Text
- Default Value: 255,0,0</td><td>Color as R,G,B values (e.g. "255,0,0" without quotes)</td></tr><tr><td>Set Backlight Color</td><td>Button</td><td></td></tr></tbody></table>

### Display: SSD1306 OLED 128x32 [2 Lines] (I2C)

- Dependencies: [libjpeg-dev](https://packages.debian.org/search?keywords=libjpeg-dev), [Pillow](https://pypi.org/project/Pillow), [pyusb](https://pypi.org/project/pyusb), [Adafruit-extended-bus](https://pypi.org/project/Adafruit-extended-bus), [adafruit-circuitpython-framebuf](https://pypi.org/project/adafruit-circuitpython-framebuf), [adafruit-circuitpython-ssd1306](https://pypi.org/project/adafruit-circuitpython-ssd1306)

This Function outputs to a 128x32 SSD1306 OLED display via I2C. This display Function will show 2 lines at a time, so channels are added in sets of 2 when Number of Line Sets is modified. Every Period, the LCD will refresh and display the next set of lines. Therefore, the first set of lines that are displayed are channels 0 - 1, then 2 - 3, and so on. After all channels have been displayed, it will cycle back to the beginning.
<table><thead><tr class="header"><th>Option</th><th>Type</th><th>Description</th></tr></thead><tbody><tr><td>Period (Seconds)</td><td>Decimal
- Default Value: 10</td><td>The duration between measurements or actions</td></tr><tr><td>I2C Address</td><td>Text
- Default Value: 0x3c</td><td></td></tr><tr><td>I2C Bus</td><td>Integer
- Default Value: 1</td><td></td></tr><tr><td>Number of Line Sets</td><td>Integer
- Default Value: 1</td><td>How many sets of lines to cycle on the LCD</td></tr><tr><td>Reset Pin</td><td>Integer
- Default Value: 17</td><td>The pin (BCM numbering) connected to RST of the display</td></tr><tr><td>Characters Per Line</td><td>Integer
- Default Value: 17</td><td>The maximum number of characters to display per line</td></tr><tr><td>Use Non-Default Font</td><td>Boolean</td><td>Don't use the default font. Enable to specify the path to a font to use.</td></tr><tr><td>Non-Default Font Path</td><td>Text
- Default Value: /usr/share/fonts/truetype/dejavu//DejaVuSans.ttf</td><td>The path to the non-default font to use</td></tr><tr><td>Font Size (pt)</td><td>Integer
- Default Value: 12</td><td>The size of the font, in points</td></tr><tr><td colspan="3">Channel Options</td></tr><tr><td>Line Display Type</td><td>Select</td><td>What to display on the line</td></tr><tr><td>Measurement</td><td>Select Measurement (Input, Function, Output, PID)</td><td>Measurement to display on the line</td></tr><tr><td>Max Age (Seconds)</td><td>Integer
- Default Value: 360</td><td>The maximum age of the measurement to use</td></tr><tr><td>Measurement Label</td><td>Text</td><td>Set to overwrite the default measurement label</td></tr><tr><td>Measurement Decimal</td><td>Integer
- Default Value: 1</td><td>The number of digits after the decimal</td></tr><tr><td>Text</td><td>Text
- Default Value: Text</td><td>Text to display</td></tr><tr><td>Display Unit</td><td>Boolean
- Default Value: True</td><td>Display the measurement unit (if available)</td></tr></tbody></table>

### Display: SSD1306 OLED 128x32 [2 Lines] (SPI)

- Dependencies: [libjpeg-dev](https://packages.debian.org/search?keywords=libjpeg-dev), [Pillow](https://pypi.org/project/Pillow), [pyusb](https://pypi.org/project/pyusb), [Adafruit-GPIO](https://pypi.org/project/Adafruit-GPIO), [Adafruit-extended-bus](https://pypi.org/project/Adafruit-extended-bus), [adafruit-circuitpython-framebuf](https://pypi.org/project/adafruit-circuitpython-framebuf), [adafruit-circuitpython-ssd1306](https://pypi.org/project/adafruit-circuitpython-ssd1306)

This Function outputs to a 128x32 SSD1306 OLED display via SPI. This display Function will show 2 lines at a time, so channels are added in sets of 2 when Number of Line Sets is modified. Every Period, the LCD will refresh and display the next set of lines. Therefore, the first set of lines that are displayed are channels 0 - 1, then 2 - 3, and so on. After all channels have been displayed, it will cycle back to the beginning.
<table><thead><tr class="header"><th>Option</th><th>Type</th><th>Description</th></tr></thead><tbody><tr><td>Period (Seconds)</td><td>Decimal
- Default Value: 10</td><td>The duration between measurements or actions</td></tr><tr><td>Number of Line Sets</td><td>Integer
- Default Value: 1</td><td>How many sets of lines to cycle on the LCD</td></tr><tr><td>SPI Device</td><td>Integer</td><td>The SPI device</td></tr><tr><td>SPI Bus</td><td>Integer</td><td>The SPI bus</td></tr><tr><td>DC Pin</td><td>Integer
- Default Value: 16</td><td>The pin (BCM numbering) connected to DC of the display</td></tr><tr><td>Reset Pin</td><td>Integer
- Default Value: 19</td><td>The pin (BCM numbering) connected to RST of the display</td></tr><tr><td>CS Pin</td><td>Integer
- Default Value: 17</td><td>The pin (BCM numbering) connected to CS of the display</td></tr><tr><td>Characters Per Line</td><td>Integer
- Default Value: 17</td><td>The maximum number of characters to display per line</td></tr><tr><td>Use Non-Default Font</td><td>Boolean</td><td>Don't use the default font. Enable to specify the path to a font to use.</td></tr><tr><td>Non-Default Font Path</td><td>Text
- Default Value: /usr/share/fonts/truetype/dejavu//DejaVuSans.ttf</td><td>The path to the non-default font to use</td></tr><tr><td>Font Size (pt)</td><td>Integer
- Default Value: 12</td><td>The size of the font, in points</td></tr><tr><td colspan="3">Channel Options</td></tr><tr><td>Line Display Type</td><td>Select</td><td>What to display on the line</td></tr><tr><td>Measurement</td><td>Select Measurement (Input, Function, Output, PID)</td><td>Measurement to display on the line</td></tr><tr><td>Max Age (Seconds)</td><td>Integer
- Default Value: 360</td><td>The maximum age of the measurement to use</td></tr><tr><td>Measurement Label</td><td>Text</td><td>Set to overwrite the default measurement label</td></tr><tr><td>Measurement Decimal</td><td>Integer
- Default Value: 1</td><td>The number of digits after the decimal</td></tr><tr><td>Text</td><td>Text
- Default Value: Text</td><td>Text to display</td></tr><tr><td>Display Unit</td><td>Boolean
- Default Value: True</td><td>Display the measurement unit (if available)</td></tr></tbody></table>

### Display: SSD1306 OLED 128x32 [4 Lines] (I2C)

- Dependencies: [libjpeg-dev](https://packages.debian.org/search?keywords=libjpeg-dev), [Pillow](https://pypi.org/project/Pillow), [pyusb](https://pypi.org/project/pyusb), [Adafruit-extended-bus](https://pypi.org/project/Adafruit-extended-bus), [adafruit-circuitpython-framebuf](https://pypi.org/project/adafruit-circuitpython-framebuf), [adafruit-circuitpython-ssd1306](https://pypi.org/project/adafruit-circuitpython-ssd1306)

This Function outputs to a 128x32 SSD1306 OLED display via I2C. This display Function will show 4 lines at a time, so channels are added in sets of 4 when Number of Line Sets is modified. Every Period, the LCD will refresh and display the next set of lines. Therefore, the first set of lines that are displayed are channels 0 - 3, then 4 - 7, and so on. After all channels have been displayed, it will cycle back to the beginning.
<table><thead><tr class="header"><th>Option</th><th>Type</th><th>Description</th></tr></thead><tbody><tr><td>Period (Seconds)</td><td>Decimal
- Default Value: 10</td><td>The duration between measurements or actions</td></tr><tr><td>I2C Address</td><td>Text
- Default Value: 0x3c</td><td></td></tr><tr><td>I2C Bus</td><td>Integer
- Default Value: 1</td><td></td></tr><tr><td>Number of Line Sets</td><td>Integer
- Default Value: 1</td><td>How many sets of lines to cycle on the LCD</td></tr><tr><td>Reset Pin</td><td>Integer
- Default Value: 17</td><td>The pin (BCM numbering) connected to RST of the display</td></tr><tr><td>Characters Per Line</td><td>Integer
- Default Value: 21</td><td>The maximum number of characters to display per line</td></tr><tr><td>Use Non-Default Font</td><td>Boolean</td><td>Don't use the default font. Enable to specify the path to a font to use.</td></tr><tr><td>Non-Default Font Path</td><td>Text
- Default Value: /usr/share/fonts/truetype/dejavu//DejaVuSans.ttf</td><td>The path to the non-default font to use</td></tr><tr><td>Font Size (pt)</td><td>Integer
- Default Value: 10</td><td>The size of the font, in points</td></tr><tr><td colspan="3">Channel Options</td></tr><tr><td>Line Display Type</td><td>Select</td><td>What to display on the line</td></tr><tr><td>Measurement</td><td>Select Measurement (Input, Function, Output, PID)</td><td>Measurement to display on the line</td></tr><tr><td>Max Age (Seconds)</td><td>Integer
- Default Value: 360</td><td>The maximum age of the measurement to use</td></tr><tr><td>Measurement Label</td><td>Text</td><td>Set to overwrite the default measurement label</td></tr><tr><td>Measurement Decimal</td><td>Integer
- Default Value: 1</td><td>The number of digits after the decimal</td></tr><tr><td>Text</td><td>Text
- Default Value: Text</td><td>Text to display</td></tr><tr><td>Display Unit</td><td>Boolean
- Default Value: True</td><td>Display the measurement unit (if available)</td></tr></tbody></table>

### Display: SSD1306 OLED 128x32 [4 Lines] (SPI)

- Dependencies: [libjpeg-dev](https://packages.debian.org/search?keywords=libjpeg-dev), [Pillow](https://pypi.org/project/Pillow), [pyusb](https://pypi.org/project/pyusb), [Adafruit-GPIO](https://pypi.org/project/Adafruit-GPIO), [Adafruit-extended-bus](https://pypi.org/project/Adafruit-extended-bus), [adafruit-circuitpython-framebuf](https://pypi.org/project/adafruit-circuitpython-framebuf), [adafruit-circuitpython-ssd1306](https://pypi.org/project/adafruit-circuitpython-ssd1306)

This Function outputs to a 128x32 SSD1306 OLED display via SPI. This display Function will show 4 lines at a time, so channels are added in sets of 4 when Number of Line Sets is modified. Every Period, the LCD will refresh and display the next set of lines. Therefore, the first set of lines that are displayed are channels 0 - 3, then 4 - 7, and so on. After all channels have been displayed, it will cycle back to the beginning.
<table><thead><tr class="header"><th>Option</th><th>Type</th><th>Description</th></tr></thead><tbody><tr><td>Period (Seconds)</td><td>Decimal
- Default Value: 10</td><td>The duration between measurements or actions</td></tr><tr><td>Number of Line Sets</td><td>Integer
- Default Value: 1</td><td>How many sets of lines to cycle on the LCD</td></tr><tr><td>SPI Device</td><td>Integer</td><td>The SPI device</td></tr><tr><td>SPI Bus</td><td>Integer</td><td>The SPI bus</td></tr><tr><td>DC Pin</td><td>Integer
- Default Value: 16</td><td>The pin (BCM numbering) connected to DC of the display</td></tr><tr><td>Reset Pin</td><td>Integer
- Default Value: 19</td><td>The pin (BCM numbering) connected to RST of the display</td></tr><tr><td>CS Pin</td><td>Integer
- Default Value: 17</td><td>The pin (BCM numbering) connected to CS of the display</td></tr><tr><td>Characters Per Line</td><td>Integer
- Default Value: 21</td><td>The maximum number of characters to display per line</td></tr><tr><td>Use Non-Default Font</td><td>Boolean</td><td>Don't use the default font. Enable to specify the path to a font to use.</td></tr><tr><td>Non-Default Font Path</td><td>Text
- Default Value: /usr/share/fonts/truetype/dejavu//DejaVuSans.ttf</td><td>The path to the non-default font to use</td></tr><tr><td>Font Size (pt)</td><td>Integer
- Default Value: 10</td><td>The size of the font, in points</td></tr><tr><td>Display Unit</td><td>Boolean
- Default Value: True</td><td>Display the measurement unit (if available)</td></tr><tr><td colspan="3">Channel Options</td></tr><tr><td>Line Display Type</td><td>Select</td><td>What to display on the line</td></tr><tr><td>Measurement</td><td>Select Measurement (Input, Function, Output, PID)</td><td>Measurement to display on the line</td></tr><tr><td>Max Age (Seconds)</td><td>Integer
- Default Value: 360</td><td>The maximum age of the measurement to use</td></tr><tr><td>Measurement Label</td><td>Text</td><td>Set to overwrite the default measurement label</td></tr><tr><td>Measurement Decimal</td><td>Integer
- Default Value: 1</td><td>The number of digits after the decimal</td></tr><tr><td>Text</td><td>Text
- Default Value: Text</td><td>Text to display</td></tr><tr><td>Display Unit</td><td>Boolean
- Default Value: True</td><td>Display the measurement unit (if available)</td></tr></tbody></table>

### Display: SSD1306 OLED 128x64 [4 Lines] (I2C)

- Dependencies: [libjpeg-dev](https://packages.debian.org/search?keywords=libjpeg-dev), [Pillow](https://pypi.org/project/Pillow), [pyusb](https://pypi.org/project/pyusb), [Adafruit-extended-bus](https://pypi.org/project/Adafruit-extended-bus), [adafruit-circuitpython-framebuf](https://pypi.org/project/adafruit-circuitpython-framebuf), [adafruit-circuitpython-ssd1306](https://pypi.org/project/adafruit-circuitpython-ssd1306)

This Function outputs to a 128x64 SSD1306 OLED display via I2C. This display Function will show 4 lines at a time, so channels are added in sets of 4 when Number of Line Sets is modified. Every Period, the LCD will refresh and display the next set of lines. Therefore, the first set of lines that are displayed are channels 0 - 3, then 4 - 7, and so on. After all channels have been displayed, it will cycle back to the beginning.
<table><thead><tr class="header"><th>Option</th><th>Type</th><th>Description</th></tr></thead><tbody><tr><td>Period (Seconds)</td><td>Decimal
- Default Value: 10</td><td>The duration between measurements or actions</td></tr><tr><td>I2C Address</td><td>Text
- Default Value: 0x3c</td><td></td></tr><tr><td>I2C Bus</td><td>Integer
- Default Value: 1</td><td></td></tr><tr><td>Number of Line Sets</td><td>Integer
- Default Value: 1</td><td>How many sets of lines to cycle on the LCD</td></tr><tr><td>Reset Pin</td><td>Integer
- Default Value: 17</td><td>The pin (BCM numbering) connected to RST of the display</td></tr><tr><td>Characters Per Line</td><td>Integer
- Default Value: 17</td><td>The maximum number of characters to display per line</td></tr><tr><td>Use Non-Default Font</td><td>Boolean</td><td>Don't use the default font. Enable to specify the path to a font to use.</td></tr><tr><td>Non-Default Font Path</td><td>Text
- Default Value: /usr/share/fonts/truetype/dejavu//DejaVuSans.ttf</td><td>The path to the non-default font to use</td></tr><tr><td>Font Size (pt)</td><td>Integer
- Default Value: 12</td><td>The size of the font, in points</td></tr><tr><td colspan="3">Channel Options</td></tr><tr><td>Line Display Type</td><td>Select</td><td>What to display on the line</td></tr><tr><td>Measurement</td><td>Select Measurement (Input, Function, Output, PID)</td><td>Measurement to display on the line</td></tr><tr><td>Max Age (Seconds)</td><td>Integer
- Default Value: 360</td><td>The maximum age of the measurement to use</td></tr><tr><td>Measurement Label</td><td>Text</td><td>Set to overwrite the default measurement label</td></tr><tr><td>Measurement Decimal</td><td>Integer
- Default Value: 1</td><td>The number of digits after the decimal</td></tr><tr><td>Text</td><td>Text
- Default Value: Text</td><td>Text to display</td></tr><tr><td>Display Unit</td><td>Boolean
- Default Value: True</td><td>Display the measurement unit (if available)</td></tr></tbody></table>

### Display: SSD1306 OLED 128x64 [4 Lines] (SPI)

- Dependencies: [libjpeg-dev](https://packages.debian.org/search?keywords=libjpeg-dev), [Pillow](https://pypi.org/project/Pillow), [pyusb](https://pypi.org/project/pyusb), [Adafruit-GPIO](https://pypi.org/project/Adafruit-GPIO), [Adafruit-extended-bus](https://pypi.org/project/Adafruit-extended-bus), [adafruit-circuitpython-framebuf](https://pypi.org/project/adafruit-circuitpython-framebuf), [adafruit-circuitpython-ssd1306](https://pypi.org/project/adafruit-circuitpython-ssd1306)

This Function outputs to a 128x64 SSD1306 OLED display via SPI. This display Function will show 4 lines at a time, so channels are added in sets of 4 when Number of Line Sets is modified. Every Period, the LCD will refresh and display the next set of lines. Therefore, the first set of lines that are displayed are channels 0 - 3, then 4 - 7, and so on. After all channels have been displayed, it will cycle back to the beginning.
<table><thead><tr class="header"><th>Option</th><th>Type</th><th>Description</th></tr></thead><tbody><tr><td>Period (Seconds)</td><td>Decimal
- Default Value: 10</td><td>The duration between measurements or actions</td></tr><tr><td>Number of Line Sets</td><td>Integer
- Default Value: 1</td><td>How many sets of lines to cycle on the LCD</td></tr><tr><td>SPI Device</td><td>Integer</td><td>The SPI device</td></tr><tr><td>SPI Bus</td><td>Integer</td><td>The SPI bus</td></tr><tr><td>DC Pin</td><td>Integer
- Default Value: 16</td><td>The pin (BCM numbering) connected to DC of the display</td></tr><tr><td>Reset Pin</td><td>Integer
- Default Value: 19</td><td>The pin (BCM numbering) connected to RST of the display</td></tr><tr><td>CS Pin</td><td>Integer
- Default Value: 17</td><td>The pin (BCM numbering) connected to CS of the display</td></tr><tr><td>Characters Per Line</td><td>Integer
- Default Value: 17</td><td>The maximum number of characters to display per line</td></tr><tr><td>Use Non-Default Font</td><td>Boolean</td><td>Don't use the default font. Enable to specify the path to a font to use.</td></tr><tr><td>Non-Default Font Path</td><td>Text
- Default Value: /usr/share/fonts/truetype/dejavu//DejaVuSans.ttf</td><td>The path to the non-default font to use</td></tr><tr><td>Font Size (pt)</td><td>Integer
- Default Value: 12</td><td>The size of the font, in points</td></tr><tr><td colspan="3">Channel Options</td></tr><tr><td>Line Display Type</td><td>Select</td><td>What to display on the line</td></tr><tr><td>Measurement</td><td>Select Measurement (Input, Function, Output, PID)</td><td>Measurement to display on the line</td></tr><tr><td>Max Age (Seconds)</td><td>Integer
- Default Value: 360</td><td>The maximum age of the measurement to use</td></tr><tr><td>Measurement Label</td><td>Text</td><td>Set to overwrite the default measurement label</td></tr><tr><td>Measurement Decimal</td><td>Integer
- Default Value: 1</td><td>The number of digits after the decimal</td></tr><tr><td>Text</td><td>Text
- Default Value: Text</td><td>Text to display</td></tr><tr><td>Display Unit</td><td>Boolean
- Default Value: True</td><td>Display the measurement unit (if available)</td></tr></tbody></table>

### Display: SSD1306 OLED 128x64 [8 Lines] (I2C)

- Dependencies: [libjpeg-dev](https://packages.debian.org/search?keywords=libjpeg-dev), [Pillow](https://pypi.org/project/Pillow), [pyusb](https://pypi.org/project/pyusb), [Adafruit-extended-bus](https://pypi.org/project/Adafruit-extended-bus), [adafruit-circuitpython-framebuf](https://pypi.org/project/adafruit-circuitpython-framebuf), [adafruit-circuitpython-ssd1306](https://pypi.org/project/adafruit-circuitpython-ssd1306)

This Function outputs to a 128x64 SSD1306 OLED display via I2C. This display Function will show 8 lines at a time, so channels are added in sets of 8 when Number of Line Sets is modified. Every Period, the LCD will refresh and display the next set of lines. Therefore, the first set of lines that are displayed are channels 0 - 7, then 8 - 15, and so on. After all channels have been displayed, it will cycle back to the beginning.
<table><thead><tr class="header"><th>Option</th><th>Type</th><th>Description</th></tr></thead><tbody><tr><td>Period (Seconds)</td><td>Decimal
- Default Value: 10</td><td>The duration between measurements or actions</td></tr><tr><td>I2C Address</td><td>Text
- Default Value: 0x3c</td><td></td></tr><tr><td>I2C Bus</td><td>Integer
- Default Value: 1</td><td></td></tr><tr><td>Number of Line Sets</td><td>Integer
- Default Value: 1</td><td>How many sets of lines to cycle on the LCD</td></tr><tr><td>Reset Pin</td><td>Integer
- Default Value: 17</td><td>The pin (BCM numbering) connected to RST of the display</td></tr><tr><td>Characters Per Line</td><td>Integer
- Default Value: 21</td><td>The maximum number of characters to display per line</td></tr><tr><td>Use Non-Default Font</td><td>Boolean</td><td>Don't use the default font. Enable to specify the path to a font to use.</td></tr><tr><td>Non-Default Font Path</td><td>Text
- Default Value: /usr/share/fonts/truetype/dejavu//DejaVuSans.ttf</td><td>The path to the non-default font to use</td></tr><tr><td>Font Size (pt)</td><td>Integer
- Default Value: 10</td><td>The size of the font, in points</td></tr><tr><td colspan="3">Channel Options</td></tr><tr><td>Line Display Type</td><td>Select</td><td>What to display on the line</td></tr><tr><td>Measurement</td><td>Select Measurement (Input, Function, Output, PID)</td><td>Measurement to display on the line</td></tr><tr><td>Max Age (Seconds)</td><td>Integer
- Default Value: 360</td><td>The maximum age of the measurement to use</td></tr><tr><td>Measurement Label</td><td>Text</td><td>Set to overwrite the default measurement label</td></tr><tr><td>Measurement Decimal</td><td>Integer
- Default Value: 1</td><td>The number of digits after the decimal</td></tr><tr><td>Text</td><td>Text
- Default Value: Text</td><td>Text to display</td></tr><tr><td>Display Unit</td><td>Boolean
- Default Value: True</td><td>Display the measurement unit (if available)</td></tr></tbody></table>

### Display: SSD1306 OLED 128x64 [8 Lines] (SPI)

- Dependencies: [libjpeg-dev](https://packages.debian.org/search?keywords=libjpeg-dev), [Pillow](https://pypi.org/project/Pillow), [pyusb](https://pypi.org/project/pyusb), [Adafruit-GPIO](https://pypi.org/project/Adafruit-GPIO), [Adafruit-extended-bus](https://pypi.org/project/Adafruit-extended-bus), [adafruit-circuitpython-framebuf](https://pypi.org/project/adafruit-circuitpython-framebuf), [adafruit-circuitpython-ssd1306](https://pypi.org/project/adafruit-circuitpython-ssd1306)

This Function outputs to a 128x64 SSD1306 OLED display via SPI. This display Function will show 8 lines at a time, so channels are added in sets of 8 when Number of Line Sets is modified. Every Period, the LCD will refresh and display the next set of lines. Therefore, the first set of lines that are displayed are channels 0 - 7, then 8 - 15, and so on. After all channels have been displayed, it will cycle back to the beginning.
<table><thead><tr class="header"><th>Option</th><th>Type</th><th>Description</th></tr></thead><tbody><tr><td>Period (Seconds)</td><td>Decimal
- Default Value: 10</td><td>The duration between measurements or actions</td></tr><tr><td>Number of Line Sets</td><td>Integer
- Default Value: 1</td><td>How many sets of lines to cycle on the LCD</td></tr><tr><td>SPI Device</td><td>Integer</td><td>The SPI device</td></tr><tr><td>SPI Bus</td><td>Integer</td><td>The SPI bus</td></tr><tr><td>DC Pin</td><td>Integer
- Default Value: 16</td><td>The pin (BCM numbering) connected to DC of the display</td></tr><tr><td>Reset Pin</td><td>Integer
- Default Value: 19</td><td>The pin (BCM numbering) connected to RST of the display</td></tr><tr><td>CS Pin</td><td>Integer
- Default Value: 17</td><td>The pin (BCM numbering) connected to CS of the display</td></tr><tr><td>Characters Per Line</td><td>Integer
- Default Value: 21</td><td>The maximum number of characters to display per line</td></tr><tr><td>Use Non-Default Font</td><td>Boolean</td><td>Don't use the default font. Enable to specify the path to a font to use.</td></tr><tr><td>Non-Default Font Path</td><td>Text
- Default Value: /usr/share/fonts/truetype/dejavu//DejaVuSans.ttf</td><td>The path to the non-default font to use</td></tr><tr><td>Font Size (pt)</td><td>Integer
- Default Value: 10</td><td>The size of the font, in points</td></tr><tr><td colspan="3">Channel Options</td></tr><tr><td>Line Display Type</td><td>Select</td><td>What to display on the line</td></tr><tr><td>Measurement</td><td>Select Measurement (Input, Function, Output, PID)</td><td>Measurement to display on the line</td></tr><tr><td>Max Age (Seconds)</td><td>Integer
- Default Value: 360</td><td>The maximum age of the measurement to use</td></tr><tr><td>Measurement Label</td><td>Text</td><td>Set to overwrite the default measurement label</td></tr><tr><td>Measurement Decimal</td><td>Integer
- Default Value: 1</td><td>The number of digits after the decimal</td></tr><tr><td>Text</td><td>Text
- Default Value: Text</td><td>Text to display</td></tr><tr><td>Display Unit</td><td>Boolean
- Default Value: True</td><td>Display the measurement unit (if available)</td></tr></tbody></table>

### Display: SSD1309 OLED 128x64 [8 Lines] (I2C)

- Dependencies: [pyusb](https://pypi.org/project/pyusb), [luma.oled](https://pypi.org/project/luma.oled), [Pillow](https://pypi.org/project/Pillow), [libjpeg-dev](https://packages.debian.org/search?keywords=libjpeg-dev), [zlib1g-dev](https://packages.debian.org/search?keywords=zlib1g-dev), [libfreetype6-dev](https://packages.debian.org/search?keywords=libfreetype6-dev), [liblcms2-dev](https://packages.debian.org/search?keywords=liblcms2-dev), [libopenjp2-7](https://packages.debian.org/search?keywords=libopenjp2-7), [libtiff5](https://packages.debian.org/search?keywords=libtiff5)

This Function outputs to a 128x64 SSD1309 OLED display via I2C. This display Function will show 8 lines at a time, so channels are added in sets of 8 when Number of Line Sets is modified. Every Period, the LCD will refresh and display the next set of lines. Therefore, the first set of lines that are displayed are channels 0 - 7, then 8 - 15, and so on. After all channels have been displayed, it will cycle back to the beginning.
<table><thead><tr class="header"><th>Option</th><th>Type</th><th>Description</th></tr></thead><tbody><tr><td>Period (Seconds)</td><td>Decimal
- Default Value: 10</td><td>The duration between measurements or actions</td></tr><tr><td>I2C Address</td><td>Text
- Default Value: 0x3c</td><td></td></tr><tr><td>I2C Bus</td><td>Integer
- Default Value: 1</td><td></td></tr><tr><td>Number of Line Sets</td><td>Integer
- Default Value: 1</td><td>How many sets of lines to cycle on the LCD</td></tr><tr><td>Reset Pin</td><td>Integer
- Default Value: 17</td><td>The pin (BCM numbering) connected to RST of the display</td></tr><tr><td colspan="3">Channel Options</td></tr><tr><td>Line Display Type</td><td>Select</td><td>What to display on the line</td></tr><tr><td>Measurement</td><td>Select Measurement (Input, Function, Output, PID)</td><td>Measurement to display on the line</td></tr><tr><td>Max Age (Seconds)</td><td>Integer
- Default Value: 360</td><td>The maximum age of the measurement to use</td></tr><tr><td>Measurement Label</td><td>Text</td><td>Set to overwrite the default measurement label</td></tr><tr><td>Measurement Decimal</td><td>Integer
- Default Value: 1</td><td>The number of digits after the decimal</td></tr><tr><td>Text</td><td>Text
- Default Value: Text</td><td>Text to display</td></tr><tr><td>Display Unit</td><td>Boolean
- Default Value: True</td><td>Display the measurement unit (if available)</td></tr></tbody></table>

### Equation (Multi-Measure)


This function acquires two measurements and uses them within a user-set equation and stores the resulting value as the selected measurement and unit.
<table><thead><tr class="header"><th>Option</th><th>Type</th><th>Description</th></tr></thead><tbody><tr><td>Period (Seconds)</td><td>Decimal
- Default Value: 60</td><td>The duration between measurements or actions</td></tr><tr><td>Measurement: A</td><td>Select Measurement (Input, Output, Function)</td><td>Measurement to replace a</td></tr><tr><td>Measurement A: Max Age (Seconds)</td><td>Integer
- Default Value: 360</td><td>The maximum age of the measurement to use</td></tr><tr><td>Measurement: B</td><td>Select Measurement (Input, Output, Function)</td><td>Measurement to replace b</td></tr><tr><td>Measurement B: Max Age (Seconds)</td><td>Integer
- Default Value: 360</td><td>The maximum age of the measurement to use</td></tr><tr><td>Equation</td><td>Text
- Default Value: a*(2+b)</td><td>Equation using measurements a and b</td></tr></tbody></table>

### Equation (Single-Measure)


This function acquires a measurement and uses it within a user-set equation and stores the resulting value as the selected measurement and unit.
<table><thead><tr class="header"><th>Option</th><th>Type</th><th>Description</th></tr></thead><tbody><tr><td>Period (Seconds)</td><td>Decimal
- Default Value: 60</td><td>The duration between measurements or actions</td></tr><tr><td>Measurement</td><td>Select Measurement (Input, Output, Function)</td><td>Measurement to replace "x" in the equation</td></tr><tr><td>Max Age (Seconds)</td><td>Integer
- Default Value: 360</td><td>The maximum age of the measurement to use</td></tr><tr><td>Equation</td><td>Text
- Default Value: x*5+2</td><td>Equation using the measurement</td></tr></tbody></table>

### Example: Generic

- Dependencies: [build-essential](https://packages.debian.org/search?keywords=build-essential)

This is an example Function Module that showcases all the different type of UI options. It is not useful beyond showing how to develop new custom Function modules.This message will appear above the Function options. It will retrieve the last selected measurement, turn the selected output on for 15 seconds, then deactivate itself. Study the code to develop your own Function Module that can be imported on the Function Import page.
<table><thead><tr class="header"><th>Option</th><th>Type</th><th>Description</th></tr></thead><tbody><tr><td>Period (Seconds)</td><td>Decimal
- Default Value: 60</td><td>The duration between measurements or actions</td></tr><tr><td colspan="3">The following fields are for text, integers, and decimal inputs. This message will automatically create a new line for the options that come after it. Alternatively, a new line can be created instead without a message, which are what separates each of the following three inputs.</td></tr><tr><td>Text Input</td><td>Text
- Default Value: Text_1</td><td>Type in text</td></tr><tr><td>Integer Input</td><td>Integer
- Default Value: 100</td><td>Type in an Integer</td></tr><tr><td>Devimal Input</td><td>Decimal
- Default Value: 50.2</td><td>Type in a decimal value</td></tr><tr><td colspan="3">A boolean value can be made using a checkbox.</td></tr><tr><td>Boolean Value</td><td>Boolean
- Default Value: True</td><td>Set to either True (checked) or False (Unchecked)</td></tr><tr><td colspan="3">A dropdown selection can be made of any user-defined options, with any of the options selected by default when the Function is added by the user.</td></tr><tr><td>Select Option</td><td>Select(Options: [First Option Selected | <strong>Second Option Selected</strong> | Third Option Selected] (Default in <strong>bold</strong>)</td><td>Select an option from the dropdown</td></tr><tr><td colspan="3">A specific measurement from an Input, Function, or PID Controller can be selected. The following dropdown will be populated if at least one Input, Function, or PID Controller has been created (as long as the Function has measurements, e.g. Statistics Function).</td></tr><tr><td>Controller Measurement</td><td>Select Measurement (Input, Function, PID)</td><td>Select a controller Measurement</td></tr><tr><td colspan="3">An output channel measurement can be selected that will return the Output ID, Channel ID, and Measurement ID. This is useful if you need more than just the Output and Channel IDs and require the user to select the specific Measurement of a channel.</td></tr><tr><td>Output Channel Measurement</td><td>Select Device, Measurement, and Channel (Output)</td><td>Select an output channel and measurement </td></tr><tr><td colspan="3">An output can be selected that will return the Output ID if only the output ID is needed.</td></tr><tr><td>Output Device</td><td>Select Device</td><td>Select an Output device</td></tr><tr><td colspan="3">An Input, Output, Function, PID, or Trigger can be selected that will return the ID if only the controller ID is needed (e.g. for activating/deactivating a controller)</td></tr><tr><td>Controller Device</td><td>Select Device</td><td>Select an Input/Output/Function/PID/Trigger controller</td></tr><tr><td colspan="3">Commands</td></tr><tr><td colspan="3">Button One will pass the Button One Value to the button_one() function of this module. This allows functions to be executed with user-specified inputs. These can be text, integers, decimals, or boolean values.</td></tr><tr><td>Button One Value</td><td>Integer
- Default Value: 650</td><td>Value for button one.</td></tr><tr><td>Button One</td><td>Button</td><td></td></tr><tr><td colspan="3">Here is another action with another user input that will be passed to the function. Note that Button One Value will also be passed to this second function, so be sure to use unique ids for each input.</td></tr><tr><td>Button Two Value</td><td>Integer
- Default Value: 1500</td><td>Value for button two.</td></tr><tr><td>Button Two</td><td>Button</td><td></td></tr></tbody></table>

### Humidity (Wet/Dry-Bulb)


This function calculates the humidity based on wet and dry bulb temperature measurements.
<table><thead><tr class="header"><th>Option</th><th>Type</th><th>Description</th></tr></thead><tbody><tr><td>Measurements Enabled</td><td>Multi-Select</td><td>The measurements to record</td></tr><tr><td>Period (Seconds)</td><td>Decimal
- Default Value: 60</td><td>The duration between measurements or actions</td></tr><tr><td>Start Offset (Seconds)</td><td>Integer
- Default Value: 10</td><td>The duration to wait before the first operation</td></tr><tr><td>Dry Bulb Temperature</td><td>Select Measurement (Input, Function)</td><td>Dry Bulb temperature measurement</td></tr><tr><td>Dry Bulb: Max Age (Seconds)</td><td>Integer
- Default Value: 360</td><td>The maximum age of the measurement to use</td></tr><tr><td>Wet Bulb Temperature</td><td>Select Measurement (Input, Function)</td><td>Wet Bulb temperature measurement</td></tr><tr><td>Wet Bulb: Max Age (Seconds)</td><td>Integer
- Default Value: 360</td><td>The maximum age of the measurement to use</td></tr><tr><td>Pressure</td><td>Select Measurement (Input, Function)</td><td>Pressure measurement</td></tr><tr><td>Pressure: Max Age (Seconds)</td><td>Integer
- Default Value: 360</td><td>The maximum age of the measurement to use</td></tr></tbody></table>

### Neokey 4x1 Neopixel Keyboard (Execute Actions)

- Dependencies: [pyusb](https://pypi.org/project/pyusb), [Adafruit-extended-bus](https://pypi.org/project/Adafruit-extended-bus), [adafruit-circuitpython-neokey](https://pypi.org/project/adafruit-circuitpython-neokey)

This Function executes actions when a key is pressed. Add actions at the bottom of this module, then enter one or more short action IDs for each key, separated by commas. The Action ID is found next to the Action (for example, the Action "[Action 0559689e] Controller: Activate" has an Action ID of 0559689e. When entering Action ID(s), separate multiple IDs by commas (for example, "asdf1234" or "asdf1234,qwer5678,zxcv0987"). Actions will be executed in the order they are entered in the text string. Enter Action IDs to execute those actions when the key is pressed. If enable Toggling Actions, every other key press will execute Actions listed in Toggled Action IDs. The LED color of the key before being pressed, after being pressed, and while the last action is running. Color is an RGB string, with 0-255 for each color. For example, red is "255, 0, 0" and blue is "0, 0, 255".
<table><thead><tr class="header"><th>Option</th><th>Type</th><th>Description</th></tr></thead><tbody><tr><td>I2C Address</td><td>Text
- Default Value: 0x30</td><td></td></tr><tr><td>I2C Bus</td><td>Integer
- Default Value: 1</td><td></td></tr><tr><td>LED Brightness (0.0-1.0)</td><td>Decimal
- Default Value: 0.2</td><td>The brightness of the LEDs</td></tr><tr><td>LED Flash Period (Seconds)</td><td>Decimal
- Default Value: 1.0</td><td>Set the period if the LED begins flashing</td></tr><tr><td colspan="3">Channel Options</td></tr><tr><td>Name</td><td>Text</td><td>A name to distinguish this from others</td></tr><tr><td>LED Delay (Seconds)</td><td>Decimal
- Default Value: 1.5</td><td>How long to leave the LED on after the last action executes.</td></tr><tr><td>Action ID(s)</td><td>Text</td><td>Set which action(s) execute when the key is pressed. Enter one or more Action IDs, separated by commas</td></tr><tr><td>Enable Toggling Actions</td><td>Boolean</td><td>Alternate between executing two sets of Actions</td></tr><tr><td>Toggled Action ID(s)</td><td>Text</td><td>Set which action(s) execute when the key is pressed on even presses. Enter one or more Action IDs, separated by commas</td></tr><tr><td>Resting LED Color (RGB)</td><td>Text
- Default Value: 0, 0, 0</td><td>The RGB color while no actions are running (e.g 10, 0, 0)</td></tr><tr><td>Actions Running LED Color: (RGB)</td><td>Text
- Default Value: 0, 255, 0</td><td>The RGB color while all but the last action is running (e.g 10, 0, 0)</td></tr><tr><td>Last Action LED Color (RGB)</td><td>Text
- Default Value: 0, 0, 255</td><td>The RGB color while the last action is running (e.g 10, 0, 0)</td></tr><tr><td>Shutdown LED Color (RGB)</td><td>Text
- Default Value: 0, 0, 0</td><td>The RGB color when the Function is disabled (e.g 10, 0, 0)</td></tr></tbody></table>

### PID Autotune


This function will attempt to perform a PID controller autotune. That is, an output will be powered and the response measured from a sensor several times to calculate the P, I, and D gains. Updates about the operation will be sent to the Daemon log. If the autotune successfully completes, a summary will be sent to the Daemon log as well. Currently, only raising a Measurement is supported, but lowering should be possible with some modification to the function controller code. It is recommended to create a graph on a dashboard with the Measurement and Output to monitor that the Output is successfully raising the Measurement beyond the Setpoint. Note: Autotune is an experimental feature, it is not well-developed, and it has a high likelihood of failing to generate PID gains. Do not rely on it for accurately tuning your PID controller.
<table><thead><tr class="header"><th>Option</th><th>Type</th><th>Description</th></tr></thead><tbody><tr><td>Measurement</td><td>Select Measurement (Input, Function)</td><td>Select a measurement the selected output will affect</td></tr><tr><td>Output</td><td>Select Device, Measurement, and Channel (Output)</td><td>Select an output to modulate that will affect the measurement</td></tr><tr><td>Period</td><td>Integer
- Default Value: 30</td><td>The period between powering the output</td></tr><tr><td>Setpoint</td><td>Decimal
- Default Value: 50</td><td>A value sufficiently far from the current measured value that the output is capable of pushing the measurement toward</td></tr><tr><td>Noise Band</td><td>Decimal
- Default Value: 0.5</td><td>The amount above the setpoint the measurement must reach</td></tr><tr><td>Outstep</td><td>Decimal
- Default Value: 10</td><td>How many seconds the output will turn on every Period</td></tr><tr><td colspan="3">Currently, only autotuning to raise a condition (measurement) is supported.</td></tr><tr><td>Direction</td><td>Select(Options: [<strong>Raise</strong>] (Default in <strong>bold</strong>)</td><td>The direction the Output will push the Measurement</td></tr></tbody></table>

### Redundancy


This function stores the first available measurement. This is useful if you have multiple sensors that you want to serve as backups in case one stops working, you can set them up in the order of importance. This function will check if a measurement exits, starting with the first measurement. If it doesn't, the next is checked, until a measurement is found. Once a measurement is found, it is stored in the database with the user-set measurement and unit. The output of this function can be used as an input throughout Mycodo. If you need more than 3 measurements to be checked, you can string multiple Redundancy Functions by creating a second Function and setting the first Function's output as the second Function's input.
<table><thead><tr class="header"><th>Option</th><th>Type</th><th>Description</th></tr></thead><tbody><tr><td>Period (Seconds)</td><td>Decimal
- Default Value: 60</td><td>The duration between measurements or actions</td></tr><tr><td>Measurement A</td><td>Select Measurement (Input, Function)</td><td>Measurement to replace a</td></tr><tr><td>Measurement A: Max Age (Seconds)</td><td>Integer
- Default Value: 360</td><td>The maximum age of the measurement to use</td></tr><tr><td>Measurement B</td><td>Select Measurement (Input, Function)</td><td>Measurement to replace b</td></tr><tr><td>Measurement B: Max Age (Seconds)</td><td>Integer
- Default Value: 360</td><td>The maximum age of the measurement to use</td></tr><tr><td>Measurement C</td><td>Select Measurement (Input, Function)</td><td>Measurement to replace C</td></tr><tr><td>Measurement C: Max Age (Seconds)</td><td>Integer
- Default Value: 360</td><td>The maximum age of the measurement to use</td></tr></tbody></table>

### Regulate pH and Electrical Conductivity


This function regulates pH with 2 pumps (acid and base solutions) and electrical conductivity (EC) with up to 4 pumps (nutrient solutions A, B, C, and D). Set only the nutrient solution outputs you want to use. Any outputs not set will not dispense when EC is being adjusted, allowing as few as 1 pump or as many as 4 pumps. Outputs can be instructed to turn on for durations (seconds) or volumes (ml). Set each Output Type to the correct type for each selected Output Channel (only select on/off Output Channels for durations and volume Output Channels for volumes). The ratio of nutrient solutions being dispensed is defined by the duration or volume set for each EC output.<br>If an e-mail address (or multiple addresses separated by commas) is entered into the E-Mail Notification field, a notification e-mail will be sent if 1) pH is outside the set danger range, 2) EC is too high and water needs to be added to the reservoir, or 3) a measurement could not be found in the database for the specific Max Age. Each e-mail notification type has its own timer that prevents e-mail spam, and will only allow sending for each notification type every set E-Mail Timer Duration. After this duration, the timer will automatically reset to allow new notifications to be sent. You may also manually reset e-mail timers at any time with the Custom Commands, below.<br>When the Function is active, Status text will appear below indicating the regulation information and total duration/volume for each output.
<table><thead><tr class="header"><th>Option</th><th>Type</th><th>Description</th></tr></thead><tbody><tr><td>Period (Seconds)</td><td>Decimal
- Default Value: 300</td><td>The duration between measurements or actions</td></tr><tr><td>Start Offset (Seconds)</td><td>Integer
- Default Value: 10</td><td>The duration to wait before the first operation</td></tr><tr><td>Status Period (seconds)</td><td>Integer
- Default Value: 60</td><td>The duration (seconds) to update the Function status on the UI</td></tr><tr><td colspan="3">Measurement Options</td></tr><tr><td>pH Measurement</td><td>Select Measurement (Input, Function)</td><td>Measurement from the pH input</td></tr><tr><td>pH: Max Age (Seconds)</td><td>Integer
- Default Value: 360</td><td>The maximum age of the measurement to use</td></tr><tr><td>EC Measurement</td><td>Select Measurement (Input, Function)</td><td>Measurement from the EC input</td></tr><tr><td>Electrical Conductivity: Max Age (Seconds)</td><td>Integer
- Default Value: 360</td><td>The maximum age of the measurement to use</td></tr><tr><td colspan="3">Output Options</td></tr><tr><td>Output: pH Dose Raise (Base)</td><td>Select Channel (Output_Channels)</td><td>Select an output to raise the pH</td></tr><tr><td>Output: pH Dose Lower (Acid)</td><td>Select Channel (Output_Channels)</td><td>Select an output to lower the pH</td></tr><tr><td>pH Output Type</td><td>Select(Options: [<strong>Duration (seconds)</strong> | Volume (ml)] (Default in <strong>bold</strong>)</td><td>Select the output type for the selected Output Channel</td></tr><tr><td>pH Output Amount</td><td>Decimal
- Default Value: 2.0</td><td>The amount to send to the pH dosing pumps (duration or volume)</td></tr><tr><td>Output: EC Dose Nutrient A</td><td>Select Channel (Output_Channels)</td><td>Select an output to dose nutrient A</td></tr><tr><td>Nutrient A Output Type</td><td>Select(Options: [<strong>Duration (seconds)</strong> | Volume (ml)] (Default in <strong>bold</strong>)</td><td>Select the output type for the selected Output Channel</td></tr><tr><td>Nutrient A Output Amount</td><td>Decimal
- Default Value: 2.0</td><td>The amount to send to the Nutrient A dosing pump (duration or volume)</td></tr><tr><td>Output: EC Dose Nutrient B</td><td>Select Channel (Output_Channels)</td><td>Select an output to dose nutrient B</td></tr><tr><td>Nutrient B Output Type</td><td>Select(Options: [<strong>Duration (seconds)</strong> | Volume (ml)] (Default in <strong>bold</strong>)</td><td>Select the output type for the selected Output Channel</td></tr><tr><td>Nutrient B Output Amount</td><td>Decimal
- Default Value: 2.0</td><td>The amount to send to the Nutrient B dosing pump (duration or volume)</td></tr><tr><td>Output: EC Dose Nutrient C</td><td>Select Channel (Output_Channels)</td><td>Select an output to dose nutrient C</td></tr><tr><td>Nutrient C Output Type</td><td>Select(Options: [<strong>Duration (seconds)</strong> | Volume (ml)] (Default in <strong>bold</strong>)</td><td>Select the output type for the selected Output Channel</td></tr><tr><td>Nutrient C Output Amount</td><td>Decimal
- Default Value: 2.0</td><td>The amount to send to the Nutrient C dosing pump (duration or volume)</td></tr><tr><td>Output: EC Dose Nutrient D</td><td>Select Channel (Output_Channels)</td><td>Select an output to dose nutrient D</td></tr><tr><td>Nutrient D Output Type</td><td>Select(Options: [<strong>Duration (seconds)</strong> | Volume (ml)] (Default in <strong>bold</strong>)</td><td>Select the output type for the selected Output Channel</td></tr><tr><td>Nutrient D Output Amount</td><td>Decimal
- Default Value: 2.0</td><td>The amount to send to the Nutrient D dosing pump (duration or volume)</td></tr><tr><td colspan="3">Setpoint Options</td></tr><tr><td>pH Setpoint</td><td>Decimal
- Default Value: 5.85</td><td>The desired pH setpoint</td></tr><tr><td>pH Hysteresis</td><td>Decimal
- Default Value: 0.35</td><td>The hysteresis to determine the pH range</td></tr><tr><td>EC Setpoint</td><td>Decimal
- Default Value: 150.0</td><td>The desired electrical conductivity setpoint</td></tr><tr><td>EC Hysteresis</td><td>Decimal
- Default Value: 50.0</td><td>The hysteresis to determine the EC range</td></tr><tr><td>pH Danger Range (High Value)</td><td>Decimal
- Default Value: 7.0</td><td>This high pH value for the danger range</td></tr><tr><td>pH Danger Range (Low Value)</td><td>Decimal
- Default Value: 5.0</td><td>This low pH value for the danger range</td></tr><tr><td colspan="3">Alert Notification Options</td></tr><tr><td>Notification E-Mail</td><td>Text</td><td>E-mail to notify when there is an issue (blank to disable)</td></tr><tr><td>E-Mail Timer Duration (Hours)</td><td>Decimal
- Default Value: 12.0</td><td>How long to wait between sending e-mail notifications</td></tr><tr><td colspan="3">Commands</td></tr><tr><td colspan="3">Each e-mail notification timer can be manually reset before the expiration.</td></tr><tr><td>Reset EC E-mail Timer</td><td>Button</td><td></td></tr><tr><td>Reset pH E-mail Timer</td><td>Button</td><td></td></tr><tr><td>Reset Measurement Issue E-mail Timer</td><td>Button</td><td></td></tr><tr><td>Reset All E-Mail Timers</td><td>Button</td><td></td></tr><tr><td colspan="3">Each total duration and volume can be manually reset.</td></tr><tr><td>Reset All Totals</td><td>Button</td><td></td></tr><tr><td>Reset Total Raise pH Duration</td><td>Button</td><td></td></tr><tr><td>Reset Total Lower pH Duration</td><td>Button</td><td></td></tr><tr><td>Reset Total Raise pH Volume</td><td>Button</td><td></td></tr><tr><td>Reset Total Lower pH Volume</td><td>Button</td><td></td></tr><tr><td>Reset Total EC A Duration</td><td>Button</td><td></td></tr><tr><td>Reset Total EC A Volume</td><td>Button</td><td></td></tr><tr><td>Reset Total EC B Duration</td><td>Button</td><td></td></tr><tr><td>Reset Total EC B Volume</td><td>Button</td><td></td></tr><tr><td>Reset Total EC C Duration</td><td>Button</td><td></td></tr><tr><td>Reset Total EC C Volume</td><td>Button</td><td></td></tr><tr><td>Reset Total EC D Duration</td><td>Button</td><td></td></tr><tr><td>Reset Total EC D Volume</td><td>Button</td><td></td></tr></tbody></table>

### Spacer


A spacer to organize Functions.
<table><thead><tr class="header"><th>Option</th><th>Type</th><th>Description</th></tr></thead><tbody><tr><td>Color</td><td>Text
- Default Value: #000000</td><td>The color of the name text</td></tr></tbody></table>

### Statistics (Last, Multiple)


This function acquires multiple measurements, calculates statistics, and stores the resulting values as the selected unit.
<table><thead><tr class="header"><th>Option</th><th>Type</th><th>Description</th></tr></thead><tbody><tr><td>Measurements Enabled</td><td>Multi-Select</td><td>The measurements to record</td></tr><tr><td>Period (Seconds)</td><td>Decimal
- Default Value: 60</td><td>The duration between measurements or actions</td></tr><tr><td>Max Age (Seconds)</td><td>Integer
- Default Value: 360</td><td>The maximum age of the measurement to use</td></tr><tr><td>Measurement</td></td><td>Measurements to perform statistics on</td></tr><tr><td>Halt on Missing Measurement</td><td>Boolean</td><td>Don't calculate statistics if >= 1 measurement is not found within Max Age</td></tr></tbody></table>

### Statistics (Past, Single)


This function acquires multiple values from a single measurement, calculates statistics, and stores the resulting values as the selected unit.
<table><thead><tr class="header"><th>Option</th><th>Type</th><th>Description</th></tr></thead><tbody><tr><td>Measurements Enabled</td><td>Multi-Select</td><td>The measurements to record</td></tr><tr><td>Period (Seconds)</td><td>Decimal
- Default Value: 60</td><td>The duration between measurements or actions</td></tr><tr><td>Max Age (Seconds)</td><td>Integer
- Default Value: 360</td><td>The maximum age of the measurement to use</td></tr><tr><td>Measurement</td><td>Select Measurement (Input, Function)</td><td>Measurement to perform statistics on</td></tr></tbody></table>

### Sum (Last, Multiple)


This function acquires the last measurement of those that are selected, sums them, then stores the resulting value as the selected measurement and unit.
<table><thead><tr class="header"><th>Option</th><th>Type</th><th>Description</th></tr></thead><tbody><tr><td>Period (Seconds)</td><td>Decimal
- Default Value: 60</td><td>The duration between measurements or actions</td></tr><tr><td>Start Offset (Seconds)</td><td>Integer
- Default Value: 10</td><td>The duration to wait before the first operation</td></tr><tr><td>Max Age (Seconds)</td><td>Integer
- Default Value: 360</td><td>The maximum age of the measurement to use</td></tr><tr><td>Measurement</td></td><td>Measurement to replace "x" in the equation</td></tr></tbody></table>

### Sum (Past, Single)


This function acquires the past measurements (within Max Age) for the selected measurement, sums them, then stores the resulting value as the selected measurement and unit.
<table><thead><tr class="header"><th>Option</th><th>Type</th><th>Description</th></tr></thead><tbody><tr><td>Period (Seconds)</td><td>Decimal
- Default Value: 60</td><td>The duration between measurements or actions</td></tr><tr><td>Start Offset (Seconds)</td><td>Integer
- Default Value: 10</td><td>The duration to wait before the first operation</td></tr><tr><td>Measurement</td><td>Select Measurement (Input, Function, Output)</td><td>Measurement to replace "x" in the equation</td></tr><tr><td>Max Age (Seconds)</td><td>Integer
- Default Value: 360</td><td>The maximum age of the measurement to use</td></tr></tbody></table>

### Vapor Pressure Deficit


This function calculates the vapor pressure deficit based on leaf temperature and humidity.
<table><thead><tr class="header"><th>Option</th><th>Type</th><th>Description</th></tr></thead><tbody><tr><td>Period (Seconds)</td><td>Decimal
- Default Value: 60</td><td>The duration between measurements or actions</td></tr><tr><td>Start Offset (Seconds)</td><td>Integer
- Default Value: 10</td><td>The duration to wait before the first operation</td></tr><tr><td>Temperature</td><td>Select Measurement (Input, Function)</td><td>Temperature measurement</td></tr><tr><td>Temperature: Max Age (Seconds)</td><td>Integer
- Default Value: 360</td><td>The maximum age of the measurement to use</td></tr><tr><td>Humidity</td><td>Select Measurement (Input, Function)</td><td>Humidity measurement</td></tr><tr><td>Humidity: Max Age (Seconds)</td><td>Integer
- Default Value: 360</td><td>The maximum age of the measurement to use</td></tr></tbody></table>

### Verification


This function acquires 2 measurements, calculates the difference, and if the difference is not larger than the set threshold, the Measurement A value is stored. This enables verifying one sensor's measurement with another sensor's measurement. Only when they are both in agreement is a measurement stored. This stored measurement can be used in functions such as Conditional Functions that will notify the user if no measurement is available to indicate there may be an issue with a sensor.
<table><thead><tr class="header"><th>Option</th><th>Type</th><th>Description</th></tr></thead><tbody><tr><td>Period (Seconds)</td><td>Decimal
- Default Value: 60</td><td>The duration between measurements or actions</td></tr><tr><td>Measurement A</td><td>Select Measurement (Input, Function)</td><td>Measurement A</td></tr><tr><td>Measurement A: Max Age (Seconds)</td><td>Integer
- Default Value: 360</td><td>The maximum age of the measurement to use</td></tr><tr><td>Measurement B</td><td>Select Measurement (Input, Function)</td><td>Measurement B</td></tr><tr><td>Measurement B: Max Age (Seconds)</td><td>Integer
- Default Value: 360</td><td>The maximum age of the measurement to use</td></tr><tr><td>Maximum Difference</td><td>Decimal
- Default Value: 10.0</td><td>The maximum allowed difference between the measurements</td></tr><tr><td>Average Measurements</td><td>Boolean</td><td>Store the average of the measurements in the database</td></tr></tbody></table>

