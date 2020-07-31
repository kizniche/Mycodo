The Mycodo client is a command-line tool used to communicate with the daemon.

```
    pi@raspberry:~ $ mycodo-client --help
    usage: mycodo-client [-h] [--activatecontroller CONTROLLER ID]
                         [--deactivatecontroller CONTROLLER ID] [--pid_pause ID]
                         [--pid_hold ID] [--pid_resume ID] [--pid_get_setpoint ID]
                         [--pid_get_error ID] [--pid_get_integrator ID]
                         [--pid_get_derivator ID] [--pid_get_kp ID]
                         [--pid_get_ki ID] [--pid_get_kd ID]
                         [--pid_set_setpoint ID SETPOINT]
                         [--pid_set_integrator ID INTEGRATOR]
                         [--pid_set_derivator ID DERIVATOR] [--pid_set_kp ID KP]
                         [--pid_set_ki ID KI] [--pid_set_kd ID KD] [-c] [--ramuse]
                         [--input_force_measurements INPUTID]
                         [--lcd_backlight_on LCDID] [--lcd_backlight_off LCDID]
                         [--lcd_reset LCDID] [--output_state OUTPUTID]
                         [--output_currently_on OUTPUTID] [--outputoff OUTPUTID]
                         [--outputon OUTPUTID] [--duration SECONDS]
                         [--dutycycle DUTYCYCLE] [--trigger_action ACTIONID]
                         [--trigger_all_actions FUNCTIONID] [-t]

    Client for Mycodo daemon.

    optional arguments:
      -h, --help            show this help message and exit
      --activatecontroller CONTROLLER ID
                            Activate controller. Options: Conditional, LCD, Math,
                            PID, Input
      --deactivatecontroller CONTROLLER ID
                            Deactivate controller. Options: Conditional, LCD,
                            Math, PID, Input
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
      -c, --checkdaemon     Check if all active daemon controllers are running
      --ramuse              Return the amount of ram used by the Mycodo daemon
      --input_force_measurements INPUTID
                            Force acquiring measurements for Input ID
      --lcd_backlight_on LCDID
                            Turn on LCD backlight with LCD ID
      --lcd_backlight_off LCDID
                            Turn off LCD backlight with LCD ID
      --lcd_reset LCDID     Reset LCD with LCD ID
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
      --trigger_action ACTIONID
                            Trigger action with Action ID
      --trigger_all_actions FUNCTIONID
                            Trigger all actions belonging to Function with ID
      -t, --terminate       Terminate the daemon
```