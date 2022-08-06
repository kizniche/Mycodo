
There are numerous places where Python 3 code can be used within Mycodo, including the Python Code Input, the Python Code Output, and Conditional Function.

Here are a few example that demonstrates some useful ways to interact with Mycodo with Python 3 code.

In all the Mycodo environments where your code will be executed, the [DaemonControl() Class](API.md#daemon-control-object) of mycodo/mycodo_client.py is available to communicate with the daemon using the object "control".

## Outputs

### PWM Fan with a Minimum Duty Cycle to Spin

Some PWM-controlled fans do not start spinning until a minimum duty cycle is set. Once the fan is spinning, the duty cycle can be set much lower and the fan will continue to spin. Because of this, there needs to be a "charging" step if the fan is turning on from a duty cycle of 0. This code detects if the requested duty cycle will need to execute the charging step prior to setting the duty cycle. For this, you will need A GPIO PWM Output and a Python Code PWM Output. The GPIO PWM Output will be configured for the fan, and the Python Code PWM Output will be configured with the following code:

```python
import time

# Set the variables the first time the code is executed
if not hasattr(self, "output_id_gpio_pwm"):
    self.logger.debug("Initializing")
    self.output_id_gpio_pwm = "a3dade60-091a-49d7-9c79-cd2adf41bc23"  # UUID of GPIO PWM Output
    self.fan_spinning = False  # saves the state of the fan
    self.fan_min_duty_cycle = 2  # The lowest duty cycle that will keep the fan spinning
    self.fan_spin_duty_cycle = 25  # The minimum duty cycle to get the fan spinning if it's been off
    self.fan_charge_duty_cycle = 45  # The charging duty cycle to get the fan initially spinning
    self.fan_spin_duration_sec = 1.5  # The duration to run the fan at the charge duty cycle

# Charge the fan if it's not spinning and the desired duty cycle is too low
if duty_cycle and not self.fan_spinning and duty_cycle < self.fan_spin_duty_cycle:
    self.logger.debug("Duty cycle too low and fan is off. Charging.")
    self.logger.debug("Setting duty cycle of {} %".format(self.fan_charge_duty_cycle))
    control.output_on(self.output_id_gpio_pwm,
                      output_type='pwm',
                      amount=self.fan_charge_duty_cycle,
                      output_channel=0)
    time.sleep(self.fan_spin_duration_sec)
    self.fan_spinning = True

if duty_cycle == 0:
    self.logger.debug("Fan turned off")
    self.fan_spinning = False
elif duty_cycle > self.fan_spin_duty_cycle:
    self.fan_spinning = True

self.logger.debug("Setting duty cycle of {} %".format(duty_cycle))
control.output_on(self.output_id_gpio_pwm,
                  output_type='pwm',
                  amount=duty_cycle,
                  output_channel=0)
```
