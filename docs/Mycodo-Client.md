The Mycodo client is a command-line tool used to communicate with the daemon.

```console
pi@raspberry:~ $ mycodo-client --help
usage: mycodo-client [-h] [-c] [--activatecontroller CONTROLLER ID]
                     [--deactivatecontroller CONTROLLER ID] [--ramuse] [-t]
                     [--trigger_action ACTIONID]
                     [--trigger_all_actions FUNCTIONID]
                     [--input_force_measurements INPUTID]
                     [--backlight_on DEVID] [--backlight_off DEVID]
                     [--lcd_reset DEVID] [--get_measurement ID UNIT CHANNEL]
                     [--output_state OUTPUTID]
                     [--output_currently_on OUTPUTID] [--outputoff OUTPUTID]
                     [--outputon OUTPUTID] [--duration SECONDS]
                     [--dutycycle DUTYCYCLE] [--pid_pause ID] [--pid_hold ID]
                     [--pid_resume ID] [--pid_get_setpoint ID]
                     [--pid_get_error ID] [--pid_get_integrator ID]
                     [--pid_get_derivator ID] [--pid_get_kp ID]
                     [--pid_get_ki ID] [--pid_get_kd ID]
                     [--pid_set_setpoint ID SETPOINT]
                     [--pid_set_integrator ID INTEGRATOR]
                     [--pid_set_derivator ID DERIVATOR] [--pid_set_kp ID KP]
                     [--pid_set_ki ID KI] [--pid_set_kd ID KD]

Client for Mycodo daemon.

optional arguments:
  -h, --help            show this help message and exit
  -c, --checkdaemon     Check if all active daemon controllers are running
  --activatecontroller CONTROLLER ID
                        Activate controller. Options: Conditional,
                        PID, Input
  --deactivatecontroller CONTROLLER ID
                        Deactivate controller. Options: Conditional,
                        PID, Input
  --ramuse              Return the amount of ram used by the Mycodo daemon
  -t, --terminate       Terminate the daemon
  --trigger_action ACTIONID
                        Trigger action with Action ID
  --trigger_all_actions FUNCTIONID
                        Trigger all actions belonging to Function with ID
  --input_force_measurements INPUTID
                        Force acquiring measurements for Input ID
  --backlight_on DEVID
                        Turn on display backlight with device ID
  --backlight_off DEVID
                        Turn off display backlight with device ID
  --lcd_reset DEVID     Reset display with device ID
  --get_measurement ID UNIT CHANNEL
                        Get the last measurement
  --output_state OUTPUTID
                        State of output with output ID
  --output_currently_on OUTPUTID
                        How many seconds an output has currently been active
                        for
  --outputoff OUTPUTID  Turn off output with output ID
  --outputon OUTPUTID   Turn on output with output ID
  --duration SECONDS    Turn on output for a duration of time (seconds)
  --dutycycle DUTYCYCLE
                        Turn on PWM output for a duty cycle (%)
  --pid_pause ID        Pause PID controller.
  --pid_hold ID         Hold PID controller.
  --pid_resume ID       Resume PID controller.
  --pid_get_setpoint ID
                        Get the setpoint value of the PID controller.
  --pid_get_error ID    Get the error value of the PID controller.
  --pid_get_integrator ID
                        Get the integrator value of the PID controller.
  --pid_get_derivator ID
                        Get the derivator value of the PID controller.
  --pid_get_kp ID       Get the Kp gain of the PID controller.
  --pid_get_ki ID       Get the Ki gain of the PID controller.
  --pid_get_kd ID       Get the Kd gain of the PID controller.
  --pid_set_setpoint ID SETPOINT
                        Set the setpoint value of the PID controller.
  --pid_set_integrator ID INTEGRATOR
                        Set the integrator value of the PID controller.
  --pid_set_derivator ID DERIVATOR
                        Set the derivator value of the PID controller.
  --pid_set_kp ID KP    Set the Kp gain of the PID controller.
  --pid_set_ki ID KI    Set the Ki gain of the PID controller.
  --pid_set_kd ID KD    Set the Kd gain of the PID controller.
```