## Custom Controllers

There is a Custom Controller import system in Mycodo that allows user-created Controllers to be used in the Mycodo system. Custom Controllers can be uploaded on the `Configure -> Controllers` page. After import, they will be available to use on the `Setup -> Function` page.

There are also example Custom Controller files in `Mycodo/mycodo/controllers/custom_controllers/examples`

Additionally, I have another github repository devoted to Custom Inputs and Controllers that are not included in the built-in set. These can be found at [kizniche/Mycodo-custom](https://github.com/kizniche/Mycodo-custom).

## PID Controller

A [proportional-derivative-integral (PID) controller](https://en.wikipedia.org/wiki/PID_controller) is a control loop feedback mechanism used throughout industry for controlling systems. It efficiently brings a measurable condition, such as the temperature, to a desired state and maintains it there with little overshoot and oscillation. A well-tuned PID controller will raise to the setpoint quickly, have minimal overshoot, and maintain the setpoint with little oscillation.

PID settings may be changed while the PID is activated and the new settings will take effect immediately. If settings are changed while the controller is paused, the values will be used once the controller resumes operation.

### PID Controller Options

<table>
<col width="40%" />
<col width="59%" />
<thead>
<tr class="header">
<th align="left">Setting</th>
<th align="left">Description</th>
</tr>
</thead>
<tbody>
<tr class="odd">
<td align="left">Activate/Deactivate</td>
<td align="left">Turn a particular PID controller on or off.</td>
</tr>
<tr class="even">
<td align="left">Pause</td>
<td align="left">When paused, the control variable will not be updated and the PID will not turn on the associated outputs. Settings can be changed without losing current PID output values.</td>
</tr>
<tr class="odd">
<td align="left">Hold</td>
<td align="left">When held, the control variable will not be updated but the PID will turn on the associated outputs, Settings can be changed without losing current PID output values.</td>
</tr>
<tr class="even">
<td align="left">Resume</td>
<td align="left">Resume a PID controller from being held or paused.</td>
</tr>
<tr class="odd">
<td align="left">Direction</td>
<td align="left">This is the direction that you wish to regulate. For example, if you only require the temperature to be raised, set this to &quot;Up,&quot; but if you require regulation up and down, set this to &quot;Both.&quot;</td>
</tr>
<tr class="even">
<td align="left">Period</td>
<td align="left">This is the duration between when the PID acquires a measurement, the PID is updated, and the output is modulated.</td>
</tr>
<tr class="odd">
<td align="left">Start Offset (seconds)</td>
<td align="left">Wait this duration before attempting the first calculation/measurement.</td>
</tr>
<tr class="even">
<td align="left">Max Age</td>
<td align="left">The time (in seconds) that the sensor measurement age is required to be less than. If the measurement is not younger than this age, the measurement is thrown out and the PID will not actuate the output. This is a safety measure to ensure the PID is only using recent measurements.</td>
</tr>
<tr class="odd">
<td align="left">Setpoint</td>
<td align="left">This is the specific point you would like the environment to be regulated at. For example, if you would like the humidity regulated to 60%, enter 60.</td>
</tr>
<tr class="even">
<td align="left">Band (+/- Setpoint)</td>
<td align="left">Hysteresis option. If set to a non-0 value, the setpoint will become a band, which will be between the band_max=setpoint+band and band_min=setpoint-band. If Raising, the PID will raise above band_max, then wait until the condition falls below band_min to resume regulation. If Lowering, the PID will lower below band_min, then wait until the condition rises above band_max to resume regulating. If set to Both, regulation will only occur to the outside min and max of the band, and cease when within the band. Set to 0 to disable Hysteresis.</td>
</tr>
<tr class="odd">
<td align="left">Store Lower as Negative</td>
<td align="left">Checking this will store all output variables (PID and output duration/duty cycle) as a negative values in the measurement database. This is useful for displaying graphs that indicate whether the PID is currently lowering or raising. Disable this if you desire all positive values to be stored in the measurement database.</td>
</tr>
<tr class="even">
<td align="left">K<sub>P</sub> Gain</td>
<td align="left">Proportional coefficient (non-negative). Accounts for present values of the error. For example, if the error is large and positive, the control output will also be large and positive.</td>
</tr>
<tr class="odd">
<td align="left">K<sub>I</sub> Gain</td>
<td align="left">Integral coefficient (non-negative). Accounts for past values of the error. For example, if the current output is not sufficiently strong, the integral of the error will accumulate over time, and the controller will respond by applying a stronger action.</td>
</tr>
<tr class="even">
<td align="left">K<sub>D</sub> Gain</td>
<td align="left">Derivative coefficient (non-negative). Accounts for predicted future values of the error, based on its current rate of change.</td>
</tr>
<tr class="odd">
<td align="left">Integrator Min</td>
<td align="left">The minimum allowed integrator value, for calculating Ki_total: (Ki_total = Ki * integrator; and PID output = Kp_total + Ki_total + Kd_total)</td>
</tr>
<tr class="even">
<td align="left">Integrator Max</td>
<td align="left">The maximum allowed integrator value, for calculating Ki_total: (Ki_total = Ki * integrator; and PID output = Kp_total + Ki_total + Kd_total)</td>
</tr>
<tr class="odd">
<td align="left">Output (Raise/Lower)</td>
<td align="left">This is the output that will cause the particular environmental condition to rise or lower. In the case of raising the temperature, this may be a heating pad or coil.</td>
</tr>
<tr class="even">
<td align="left">Min On Duration, Duty Cycle, or Amount (Raise/Lower)</td>
<td align="left">This is the minimum value that the PID output must be before Output (Lower) turns on. If the PID output is less than this value, Duration Outputs will not turn on, and PWM Outputs will be turned off unless Always Min is enabled.</td>
</tr>
<tr class="odd">
<td align="left">Max On Duration, Duty Cycle, or Amount (Raise/Lower)</td>
<td align="left">This is the maximum duration, volume, or duty cycle the Output (Raise) can be set to. If the PID output is greater than this value, the Max value set here will be used.</td>
</tr>
<tr class="even">
<td align="left">Min Off Duration (Raise/Lower)</td>
<td align="left">For On/Off (Duration) Outputs, this is the minimum amount of time the Output must have been off for before it is allowed to turn back on. Ths is useful for devices that can be damaged by rapid power cycling (e.g. fridges).</td>
</tr>
<tr class="odd">
<td align="left">Always Min (Raise/Lower)</td>
<td align="left">For PWM Outputs only. If enabled, the duty cycle will never be set below the Min value.</td>
</tr>
<tr class="even">
<td align="left">Setpoint Tracking Method</td>
<td align="left">Set a method to change the setpoint over time.</td>
</tr>
</tbody>
</table>

### PID Output Calculation

PID Controllers can output as a duration or a duty cycle.

When outputting a duration, Duration = Control_Variable

When outputting a duty cycle, Duty Cycle = (Control_Variable / Period) * 100

Note: Control_Variable = P_Output + I_Output + D_Output. Duty cycle is limited within the 0 - 100 % range and the set Min Duty Cycle and Max Duty Cycle. Duration is limited by the set Min On Duration and Max On Duration.

### PID Tuning

PID tuning is a complex process, but not unattainable if enough time and effort is invested to learn how a PID operates. Below is a primer for understanding how a PID controller operates and a few examples of how to tune a PID controller. For further discussion, join the [Mycodo PID Tuning](https://kylegabriel.com/forum/pid-tuning/) forum.

#### PID Control Theory

The PID controller is the most common regulatory controller found in industrial settings, for it"s ability to handle both simple and complex regulation. The PID controller has three paths, the proportional, integral, and derivative.

The **P**roportional takes the error and multiplies it by the constant K<sub>P</sub>, to yield an output value. When the error is large, there will be a large proportional output.

The **I**ntegral takes the error and multiplies it by K<sub>I</sub>, then integrates it (K<sub>I</sub> · 1/s). As the error changes over time, the integral will continually sum it and multiply it by the constant K<sub>I</sub>. The integral is used to remove perpetual error in the control system. If using K<sub>P</sub> alone produces an output that produces a perpetual error (i.e. if the sensor measurement never reaches the Set Point), the integral will increase the output until the error decreases and the Set Point is reached.

The **D**erivative multiplies the error by K<sub>D</sub>, then differentiates it (K<sub>D</sub> · s). When the error rate changes over time, the output signal will change. The faster the change in error, the larger the derivative path becomes, decreasing the output rate of change. This has the effect of dampening overshoot and undershoot (oscillation) of the Set Point.

![PID Animation](manual_images/PID-Animation.gif)

The K<sub>P</sub>, K<sub>I</sub>, and K<sub>D</sub> gains determine how much each of the P, I, and D variables influence the final PID output value. For instance, the greater the value of the gain, the more influence that variable has on the output.

![PID Equation](manual_images/PID-Equation.jpg)

The output from the PID controller can be used in a number of ways. A simple use is to use this value as the number of seconds an output is turned on during a periodic interval (Period). For instance, if the Period is set to 30 seconds, the PID equation has the desired measurement and the actual measurement used to calculate the PID output every 30 seconds. The more the output is on during this period, the more it will affect the system. For example, an output on for 15 seconds every 30 seconds is at a 50 % duty cycle, and would affect the system roughly half as much as when the output is on for 30 seconds every 30 seconds, or at at 100 % duty cycle. The PID controller will calculate the output based on the amount of error (how far the actual measurement is from the desired measurement). If the error increases or persists, the output increases, causing the output to turn on for a longer duration within the Period, which usually in term causes the measured condition to change and the error to reduce. When the error reduces, the control variable decreases, meaning the output is turned on for a shorter duration of time. The ultimate goal of a well-tuned PID controller is to bring the actual measurement to the desired measurement quickly, with little overshoot, and maintain the setpoint with minimal oscillation.

* * * * *

Using temperature as an example, the Process Variable (PV) is the measured temperature, the Setpoint (SP) is the desired temperature, and the Error (e) is the distance between the measured temperature and the desired temperature (indicating if the actual temperature is too hot or too cold and to what degree). The error is manipulated by each of the three PID components, producing an output, called the Manipulated Variable (MV) or Control Variable (CV). To allow control of how much each path contributes to the output value, each path is multiplied by a gain (represented by K<sub>P</sub>, K<sub>I</sub>, and K<sub>D</sub>). By adjusting the gains, the sensitivity of the system to each path is affected. When all three paths are summed, the PID output is produced. If a gain is set to 0, that path does not contribute to the output and that path is essentially turned off.

The output can be used a number of ways, however this controller was designed to use the output to affect the measured value (PV). This feedback loop, with a *properly tuned* PID controller, can achieve a set point in a short period of time, maintain regulation with little oscillation, and respond quickly to disturbance.

Therefor, if one would be regulating temperature, the sensor would be a temperature sensor and the feedback device(s) would be able to heat and cool. If the temperature is lower than the Set Point, the output value would be positive and a heater would activate. The temperature would rise toward the desired temperature, causing the error to decrease and a lower output to be produced. This feedback loop would continue until the error reaches 0 (at which point the output would be 0). If the temperature continues to rise past the Set Point (this is may be acceptable, depending on the degree), the PID would produce a negative output, which could be used by the cooling device to bring the temperature back down, to reduce the error. If the temperature would normally lower without the aid of a cooling device, then the system can be simplified by omitting a cooler and allowing it to lower on its own.

Implementing a controller that effectively utilizes K<sub>P</sub>, K<sub>I</sub>, and K<sub>D</sub> can be challenging. Furthermore, it is often unnecessary. For instance, the K<sub>I</sub> and K<sub>D</sub> can be set to 0, effectively turning them off and producing the very popular and simple P controller. Also popular is the PI controller. It is recommended to start with only K<sub>P</sub> activated, then experiment with K<sub>P</sub> and K<sub>I</sub>, before finally using all three. Because systems will vary (e.g. airspace volume, degree of insulation, and the degree of impact from the connected device, etc.), each path will need to be adjusted through experimentation to produce an effective output.

#### Quick Setup Examples

These example setups are meant to illustrate how to configure regulation in particular directions, and not to achieve ideal values to configure your K<sub>P</sub>, K<sub>I</sub>, and K<sub>D</sub> gains. There are a number of online resources that discuss techniques and methods that have been developed to determine ideal PID values (such as [here](http://robotics.stackexchange.com/questions/167/what-are-good-strategies-for-tuning-pid-loops), [here](http://innovativecontrols.com/blog/basics-tuning-pid-loops), [here](https://hennulat.wordpress.com/2011/01/12/pid-loop-tuning-101/), [here](http://eas.uccs.edu/wang/ECE4330F12/PID-without-a-PhD.pdf), and [here](http://www.atmel.com/Images/doc2558.pdf)) and since there are no universal values that will work for every system, it is recommended to conduct your own research to understand the variables and essential to conduct your own experiments to effectively implement them.

Provided merely as an example of the variance of PID values, one of my setups had temperature PID values (up regulation) of K<sub>P</sub> = 30, K<sub>I</sub> = 1.0, and K<sub>D</sub> = 0.5, and humidity PID values (up regulation) of K<sub>P</sub> = 1.0, K<sub>I</sub> = 0.2, and K<sub>D</sub> = 0.5. Furthermore, these values may not have been optimal but they worked well for the conditions of my environmental chamber.

#### Exact Temperature Regulation

This will set up the system to raise and lower the temperature to a certain level with two regulatory devices (one that heats and one that cools).

Add a sensor, then save the proper device and pin/address for each sensor and activate the sensor.

Add two outputs, then save each GPIO and On Trigger state.

Add a PID, then select the newly-created sensor. Change *Setpoint* to the desired temperature, *Regulate Direction* to "Both". Set *Raise Output* to the relay attached to the heating device and the *Lower Relay* to the relay attached to the cooling device.

Set K<sub>P</sub> = 1, K<sub>I</sub> = 0, and K<sub>D</sub> = 0, then activate the PID.

If the temperature is lower than the Set Point, the heater should activate at some interval determined by the PID controller until the temperature rises to the set point. If the temperature goes higher than the Set Point (or Set Point + Buffer), the cooling device will activate until the temperature returns to the set point. If the temperature is not reaching the Set Point after a reasonable amount of time, increase the K<sub>P</sub> value and see how that affects the system. Experiment with different configurations involving only *Read Interval* and K<sub>P</sub> to achieve a good regulation. Avoid changing the K<sub>I</sub> and K<sub>D</sub> from 0 until a working regulation is achieved with K<sub>P</sub> alone.

View graphs in the 6 to 12 hour time span to identify how well the temperature is regulated to the Setpoint. What is meant by well-regulated will vary, depending on your specific application and tolerances. Most applications of a PID controller would like to see the proper temperature attained within a reasonable amount of time and with little oscillation around the Setpoint.

Once regulation is achieved, experiment by reducing K<sub>P</sub> slightly (~25%) and increasing K<sub>I</sub> by a low amount to start, such as 0.1 (or lower, 0.01), then start the PID and observe how well the controller regulates. Slowly increase K<sub>I</sub> until regulation becomes both quick and with little oscillation. At this point, you should be fairly familiar with experimenting with the system and the K<sub>D</sub> value can be experimented with once both K<sub>P</sub> and K<sub>I</sub> have been tuned.

#### High Temperature Regulation

Often the system can be simplified if two-way regulation is not needed. For instance, if cooling is unnecessary, this can be removed from the system and only up-regulation can be used.

Use the same configuration as the [Exact Temperature Regulation](#exact-temperature-regulation) example, except change *Regulate Direction* to "Raise" and do not touch the "Down Relay" section.

### PID Autotune

Note: This is an experimental feature. It is best nto used until you are familiar with the operation and tuning of a PID.

The Autotune feature is useful for determining appropriate Kp, Ki, and Kd gains of a PID controller. The autotuner will manipulate an output and measure the response in the environment being measured by a sensor. It will take several cycles to determine the gains according to several rules. In order to use this feature, the PID controller must be properly configured, and a Noise Band and Outstep selected, then select "Start Autotune". The output of the autotuner will appear in the daemon log (`Config -> Mycodo Logs -> Daemon`). While the autotune is being performed, it is recommended to create a graph that includes the Input, Output, and PID Setpoint/Output in order to see what the PID Autotuner is doing and to notice any issues. If your autotune is taking a long time to complete, there may not be enough stability in the system being manipulated to calculate a reliable set of PID gains. This may be because there are too many disturbances to the system, or conditions are changing too rapidly to acquire consistent measurement oscillations. If this is the case, try modifying your system to reduce disturbances. Once the autotune successfully completes, disturbances may be reintroduced in order to further tune the PID controller to handle them.

<table>
<col width="40%" />
<col width="59%" />
<thead>
<tr class="header">
<th align="left">Setting</th>
<th align="left">Description</th>
</tr>
</thead>
<tbody>
<tr class="odd">
<td align="left">Noise Band</td>
<td align="left">This is the amount above the setpoint the measured condition must reach before the output turns off. This is also how much below the setpoint the measured condition must fall before the output turns back on.</td>
</tr>
<tr class="even">
<td align="left">Outstep</td>
<td align="left">This is how many seconds the output will turn on every PID Period. For instance, to autotune with 50% power, ensure the Outstep is half the value of the PID Period.</td>
</tr>
</tbody>
</table>

Typical graph output will look like this:

![PID Autotune Output](manual_images/Autotune-Output-Example.png)

And typical Daemon Log output will look like this:

    2018-08-04 23:32:20,876 - mycodo.pid_3b533dff - INFO - Activated in 187.2 ms
    2018-08-04 23:32:20,877 - mycodo.pid_autotune - INFO - PID Autotune started
    2018-08-04 23:33:50,823 - mycodo.pid_autotune - INFO -
    2018-08-04 23:33:50,830 - mycodo.pid_autotune - INFO - Cycle: 19
    2018-08-04 23:33:50,831 - mycodo.pid_autotune - INFO - switched state: relay step down
    2018-08-04 23:33:50,832 - mycodo.pid_autotune - INFO - input: 32.52
    2018-08-04 23:36:00,854 - mycodo.pid_autotune - INFO -
    2018-08-04 23:36:00,860 - mycodo.pid_autotune - INFO - Cycle: 45
    2018-08-04 23:36:00,862 - mycodo.pid_autotune - INFO - found peak: 34.03
    2018-08-04 23:36:00,863 - mycodo.pid_autotune - INFO - peak count: 1
    2018-08-04 23:37:20,802 - mycodo.pid_autotune - INFO -
    2018-08-04 23:37:20,809 - mycodo.pid_autotune - INFO - Cycle: 61
    2018-08-04 23:37:20,810 - mycodo.pid_autotune - INFO - switched state: relay step up
    2018-08-04 23:37:20,811 - mycodo.pid_autotune - INFO - input: 31.28
    2018-08-04 23:38:30,867 - mycodo.pid_autotune - INFO -
    2018-08-04 23:38:30,874 - mycodo.pid_autotune - INFO - Cycle: 75
    2018-08-04 23:38:30,876 - mycodo.pid_autotune - INFO - found peak: 32.17
    2018-08-04 23:38:30,878 - mycodo.pid_autotune - INFO - peak count: 2
    2018-08-04 23:38:40,852 - mycodo.pid_autotune - INFO -
    2018-08-04 23:38:40,858 - mycodo.pid_autotune - INFO - Cycle: 77
    2018-08-04 23:38:40,860 - mycodo.pid_autotune - INFO - switched state: relay step down
    2018-08-04 23:38:40,861 - mycodo.pid_autotune - INFO - input: 32.85
    2018-08-04 23:40:50,834 - mycodo.pid_autotune - INFO -
    2018-08-04 23:40:50,835 - mycodo.pid_autotune - INFO - Cycle: 103
    2018-08-04 23:40:50,836 - mycodo.pid_autotune - INFO - found peak: 33.93
    2018-08-04 23:40:50,836 - mycodo.pid_autotune - INFO - peak count: 3
    2018-08-04 23:42:05,799 - mycodo.pid_autotune - INFO -
    2018-08-04 23:42:05,805 - mycodo.pid_autotune - INFO - Cycle: 118
    2018-08-04 23:42:05,806 - mycodo.pid_autotune - INFO - switched state: relay step up
    2018-08-04 23:42:05,807 - mycodo.pid_autotune - INFO - input: 31.27
    2018-08-04 23:43:15,816 - mycodo.pid_autotune - INFO -
    2018-08-04 23:43:15,822 - mycodo.pid_autotune - INFO - Cycle: 132
    2018-08-04 23:43:15,824 - mycodo.pid_autotune - INFO - found peak: 32.09
    2018-08-04 23:43:15,825 - mycodo.pid_autotune - INFO - peak count: 4
    2018-08-04 23:43:25,790 - mycodo.pid_autotune - INFO -
    2018-08-04 23:43:25,796 - mycodo.pid_autotune - INFO - Cycle: 134
    2018-08-04 23:43:25,797 - mycodo.pid_autotune - INFO - switched state: relay step down
    2018-08-04 23:43:25,798 - mycodo.pid_autotune - INFO - input: 32.76
    2018-08-04 23:45:30,802 - mycodo.pid_autotune - INFO -
    2018-08-04 23:45:30,808 - mycodo.pid_autotune - INFO - Cycle: 159
    2018-08-04 23:45:30,810 - mycodo.pid_autotune - INFO - found peak: 33.98
    2018-08-04 23:45:30,811 - mycodo.pid_autotune - INFO - peak count: 5
    2018-08-04 23:45:30,812 - mycodo.pid_autotune - INFO -
    2018-08-04 23:45:30,814 - mycodo.pid_autotune - INFO - amplitude: 0.9099999999999989
    2018-08-04 23:45:30,815 - mycodo.pid_autotune - INFO - amplitude deviation: 0.06593406593406595
    2018-08-04 23:46:40,851 - mycodo.pid_autotune - INFO -
    2018-08-04 23:46:40,857 - mycodo.pid_autotune - INFO - Cycle: 173
    2018-08-04 23:46:40,858 - mycodo.pid_autotune - INFO - switched state: relay step up
    2018-08-04 23:46:40,859 - mycodo.pid_autotune - INFO - input: 31.37
    2018-08-04 23:47:55,860 - mycodo.pid_autotune - INFO -
    2018-08-04 23:47:55,866 - mycodo.pid_autotune - INFO - Cycle: 188
    2018-08-04 23:47:55,868 - mycodo.pid_autotune - INFO - found peak: 32.36
    2018-08-04 23:47:55,869 - mycodo.pid_autotune - INFO - peak count: 6
    2018-08-04 23:47:55,870 - mycodo.pid_autotune - INFO -
    2018-08-04 23:47:55,871 - mycodo.pid_autotune - INFO - amplitude: 0.9149999999999979
    2018-08-04 23:47:55,872 - mycodo.pid_autotune - INFO - amplitude deviation: 0.032786885245900406
    2018-08-04 23:47:55,873 - mycodo.pid_3b533dff - INFO - time:  16 min
    2018-08-04 23:47:55,874 - mycodo.pid_3b533dff - INFO - state: succeeded
    2018-08-04 23:47:55,874 - mycodo.pid_3b533dff - INFO -
    2018-08-04 23:47:55,875 - mycodo.pid_3b533dff - INFO - rule: ziegler-nichols
    2018-08-04 23:47:55,876 - mycodo.pid_3b533dff - INFO - Kp: 0.40927018474290117
    2018-08-04 23:47:55,877 - mycodo.pid_3b533dff - INFO - Ki: 0.05846588600007114
    2018-08-04 23:47:55,879 - mycodo.pid_3b533dff - INFO - Kd: 0.7162385434443115
    2018-08-04 23:47:55,880 - mycodo.pid_3b533dff - INFO -
    2018-08-04 23:47:55,881 - mycodo.pid_3b533dff - INFO - rule: tyreus-luyben
    2018-08-04 23:47:55,887 - mycodo.pid_3b533dff - INFO - Kp: 0.3162542336649691
    2018-08-04 23:47:55,889 - mycodo.pid_3b533dff - INFO - Ki: 0.010165091543194185
    2018-08-04 23:47:55,890 - mycodo.pid_3b533dff - INFO - Kd: 0.7028026111719073
    2018-08-04 23:47:55,891 - mycodo.pid_3b533dff - INFO -
    2018-08-04 23:47:55,892 - mycodo.pid_3b533dff - INFO - rule: ciancone-marlin
    2018-08-04 23:47:55,892 - mycodo.pid_3b533dff - INFO - Kp: 0.21083615577664605
    2018-08-04 23:47:55,893 - mycodo.pid_3b533dff - INFO - Ki: 0.06626133746674728
    2018-08-04 23:47:55,893 - mycodo.pid_3b533dff - INFO - Kd: 0.3644161687558038
    2018-08-04 23:47:55,894 - mycodo.pid_3b533dff - INFO -
    2018-08-04 23:47:55,894 - mycodo.pid_3b533dff - INFO - rule: pessen-integral
    2018-08-04 23:47:55,895 - mycodo.pid_3b533dff - INFO - Kp: 0.49697093861638
    2018-08-04 23:47:55,895 - mycodo.pid_3b533dff - INFO - Ki: 0.0887428626786794
    2018-08-04 23:47:55,896 - mycodo.pid_3b533dff - INFO - Kd: 1.04627757151908
    2018-08-04 23:47:55,896 - mycodo.pid_3b533dff - INFO -
    2018-08-04 23:47:55,897 - mycodo.pid_3b533dff - INFO - rule: some-overshoot
    2018-08-04 23:47:55,898 - mycodo.pid_3b533dff - INFO - Kp: 0.23191977135431066
    2018-08-04 23:47:55,898 - mycodo.pid_3b533dff - INFO - Ki: 0.03313066873337365
    2018-08-04 23:47:55,899 - mycodo.pid_3b533dff - INFO - Kd: 1.0823160212047374
    2018-08-04 23:47:55,899 - mycodo.pid_3b533dff - INFO -
    2018-08-04 23:47:55,900 - mycodo.pid_3b533dff - INFO - rule: no-overshoot
    2018-08-04 23:47:55,900 - mycodo.pid_3b533dff - INFO - Kp: 0.1391518628125864
    2018-08-04 23:47:55,901 - mycodo.pid_3b533dff - INFO - Ki: 0.01987840124002419
    2018-08-04 23:47:55,901 - mycodo.pid_3b533dff - INFO - Kd: 0.6493896127228425
    2018-08-04 23:47:55,902 - mycodo.pid_3b533dff - INFO -
    2018-08-04 23:47:55,902 - mycodo.pid_3b533dff - INFO - rule: brewing
    2018-08-04 23:47:55,903 - mycodo.pid_3b533dff - INFO - Kp: 5.566074512503456
    2018-08-04 23:47:55,904 - mycodo.pid_3b533dff - INFO - Ki: 0.11927040744014512
    2018-08-04 23:47:55,904 - mycodo.pid_3b533dff - INFO - Kd: 4.101408080354794

## Conditional

Conditional controllers are used to perform certain actions based on whether a conditional statement is true, which is typically based on a measurement or GPIO state.

### Conditional Options

Check if the latest measurement is above or below the set value.

<table>
<col width="40%" />
<col width="59%" />
<thead>
<tr class="header">
<th align="left">Setting</th>
<th align="left">Description</th>
</tr>
</thead>
<tbody>
<tr class="odd">
<td align="left">Conditional Statement</td>
<td align="left">The text string that includes device IDs enclosed in curly brackets ({}) that will be converted to the actual measurement before being evaluated by python to determine if it is True or False. If True, the associated actions will be executed.</td>
</tr>
<tr class="even">
<td align="left">Period (seconds)</td>
<td align="left">The period (seconds) between conditional checks.</td>
</tr>
<tr class="odd">
<td align="left">Start Offset (seconds)</td>
<td align="left">The duration (seconds) to wait before executing the Conditional for the first after it is activated.</td>
</tr>
<tr class="even">
<td align="left">Log Level: Debug</td>
<td align="left">Show debug lines in the daemon log.</td>
</tr>
<tr class="odd">
<td align="left">Message Includes Code</td>
<td align="left">Include Conditional Statement code in the message that is passed to actions.</td>
</tr>
</tbody>
</table>

Conditions are variables that can be used within the Conditional Statement.

<table>
<col width="40%" />
<col width="59%" />
<thead>
<tr class="header">
<th align="left">Condition</th>
<th align="left">Description</th>
</tr>
</thead>
<tbody>
<tr class="odd">
<td align="left">Measurement (Single, Last)</td>
<td align="left">Acquires the latest measurement from an Input or device. Set Max Age (seconds) to restrict how long to accept values. If the latest value is older than this duration, &quot;None&quot; is returned.</td>
</tr>
<tr class="even">
<td align="left">Measurement (Single, Past, Average)</td>
<td align="left">Acquires the past measurements from an Input or device, then averages them. Set Max Age (seconds) to restrict how long to accept values. If all values are older than this duration, &quot;None&quot; is returned.</td>
</tr>
<tr class="odd">
<td align="left">Measurement (Single, Past, Sum)</td>
<td align="left">Acquires the past measurements from an Input or device, then sums them. Set Max Age (seconds) to restrict how long to accept values. If all values are older than this duration, &quot;None&quot; is returned.</td>
</tr>
<tr class="even">
<td align="left">Measurement (Multiple, Past)</td>
<td align="left">Acquires the past measurements from an Input or device. Set Max Age (seconds) to restrict how long to accept values. If no values are found in this duration, &quot;None&quot; is returned. This differs from the &quot;Measurement (Single)&quot; Condition because it returns a list of dictionaries with 'time' and 'value' key pairs.</td>
</tr>
<tr class="odd">
<td align="left">GPIO State</td>
<td align="left">Acquires the current GPIO state and returns 1 if HIGH or 0 if LOW. If the latest value is older than this duration, &quot;None&quot; is returned.</td>
</tr>
<tr class="even">
<td align="left">Output State</td>
<td align="left">Returns 'on' if the output is currently on, and 'off' if it's currently off.</td>
</tr>
<tr class="odd">
<td align="left">Output Duration On</td>
<td align="left">Returns how long the output has currently been on, in seconds. Returns 0 if off.</td>
</tr>
<tr class="even">
<td align="left">Controller Running</td>
<td align="left">Returns True if the controller is active, False if inactive.</td>
</tr>
<tr class="odd">
<td align="left">Max Age (seconds)</td>
<td align="left">The minimum age (seconds) the measurement can be. If the last measurement is older than this, &quot;None&quot; will be returned instead of a measurement.</td>
</tr>
</tbody>
</table>

### Conditional Setup Guide

Python 3 is the environment that these conditionals will be executed. The following functions can be used within your code.

Note: Indentation must use 4 spaces (not 2 spaces, tabs, or other).

<table>
<col width="40%" />
<col width="59%" />
<thead>
<tr class="header">
<th align="left">Function</th>
<th align="left">Description</th>
</tr>
</thead>
<tbody>
<tr class="odd">
<td align="left">self.condition(&quot;{ID}&quot;)</td>
<td align="left">Returns a measurement for the Condition with ID.</td>
</tr>
<tr class="even">
<td align="left">self.condition_dict(&quot;{ID }&quot;)</td>
<td align="left">Returns a dictionary of measurement for the Condition with ID.</td>
</tr>
<tr class="odd">
<td align="left">self.run_action(&quot;{ID}&quot;)</td>
<td align="left">Executes the Action with ID.</td>
</tr>
<tr class="even">
<td align="left">self.run_all_actions()</td>
<td align="left">Executes all actions.</td>
</tr>
<tr class="odd">
<td align="left">self.logger.info()</td>
<td align="left">Writes a log line to the daemon log. 'info' may also be changed to 'error' or 'debug'.</td>
</tr>
</tbody>
</table>

There are additional functions that can be used, but these must use the full UUID (not an abridged version as the functions above). See /home/pi/Mycodo/mycodo/mycodo_client.py for the functions available for use. These may be accessed via the 'control' object. An example, below, will return how long the output has been on (or 0 if it's currently off):

`output_on_seconds = control.output_sec_currently_on('1b6ada50-1e69-403a-9fa6-ec748b16dc23')`

Since the Python code contained in the Conditional Statement must be formatted properly, it's best to familiarize yourself with the [basics of Python](https://realpython.com/python-conditional-statements/).

Note that there are two different IDs in use here, one set of IDs are for the measurements, under the `Conditions` section of the Conditional, and one set of IDs are for the Actions, under the `Actions` section of the Conditional. Read all of this section, including the examples, below, to fully understand how to configure a conditional properly.

IMPORTANT: If a measurement hasn't been acquired within the Max Age that is set, "None" will be returned when self.condition("{ID}") is called in the code. It is very important that you account for this. All examples below incorporate a test for the measurement being None, and this should not be removed. If an error occurs (such as if the statement resolves to comparing None to a numerical value, such as "if None < 23"), then the code will stop there and an error will be logged in the daemon log. Accounting for None is useful for determining if an Input is no longer acquiring measurements (e.g. dead sensor, malfunction, etc.).

To create a basic conditional, follow these steps, using the numbers in the screenshots, below, that correspond to the numbers in parentheses:

-   Navigate to the `Setup -> Function` page.
-   Select "Controller: Conditional", then click `Add`.
-   Under Conditions (1), select a condition option, then click `Add Condition`.
-   Configure the newly-added Condition then click `Save`.
-   Under Actions (2), select an action option, then click `Add Action`.
-   Configure the newly-added Action then click `Save`.
-   Notice that each Condition and each Action has its own ID (underlined).
-   The default Conditional Statement (3) contains placeholder IDs that need to be changed to your Condition and Action IDs. Change the ID in self.condition("{asdf1234}") to your Condition ID. Change the ID in self.run_action("{qwer5678}", message=message) to your Action ID. Click `Save` at the top of the Conditional.
-   The logic used in the Conditional Statement will need to be adjusted to suit your particular needs. Additionally, you may add more Conditions or Actions. See the `Advanced Conditional Statement examples`, below, for usage examples.

If your `Conditional Statement` has been formatted correctly, your Conditional will save and it will be ready to activate. If an error is returned, your options will not have been saved. Inspect the error for which line is causing the issue and read the error message itself to try to understand what the problem is and how to fix it. There are an unfathomable number of ways to configure a Conditional, but this should hopefully get you started to developing one that suits your needs.

Note: Mycodo is constantly changing, so the screenshots below may not match what you see exactly. Be sure to read this entire section of the manual to understand how to use Conditionals.

![Figure-Mycodo-Conditional-Setup](manual_images/Figure-Mycodo-Conditional-Setup.png)

Simple `Conditional Statement` examples:

Each self.condition("{ID}") will return the most recent measurement obtained from that particular measurement under the `Conditions` section of the Conditional, as long as it's within the set Max Age.

```python
# Example 1, no measurement, useful to notify by email when an Input stops working
if self.condition("{asdf1234}") is None:
    self.run_all_actions()

# Example 2, test two measurements
measure_1 = self.condition("{asdf1234}")
measure_2 = self.condition("{hjkl5678}")
if None not in [measure_1, measure_2]:
    if measure_1 < 20 and measure_2 > 10:
        self.run_all_actions()

# Example 3, test two measurements and sum of measurements
measure_1 = self.condition("{asdf1234}")
measure_2 = self.condition("{hjkl5678}")
if None not in [measure_1, measure_2]:
    sum = measure_1 + measure_2
    if measure_1 > 2 and 10 < measure_2 < 23 and sum < 30.5:
        self.run_all_actions()

# Example 4, combine into one conditional
measurement = self.condition("{asdf1234}")
if measurement != None and 20 < measurement < 30:
    self.run_all_actions()

# Example 5, test two measurements and convert Edge Input from 0 or 1 to True or False
measure_1 = self.condition("{asdf1234}")
measure_2 = self.condition("{hjkl5678}")
if None not in [measure_1, measure_2]:
    if bool(measure_1) and measure_2 > 10:
        self.run_all_actions()

# Example 6, test measurement with "or" and a rounded measurement
measure_1 = self.condition("{asdf1234}")
measure_2 = self.condition("{hjkl5678}")
if None not in [measure_1, measure_2]:
    if measure_1 > 20 or int(round(measure_2)) in [20, 21, 22]:
        self.run_all_actions()

# Example 7, use self to store variables
measurement = self.condition("{asdf1234}")
if not hasattr(self, "stored_measurement"):  # Initialize variable
    self.stored_measurement = measurement
if measurement is not None:
    if abs(measurement - self.stored_measurement) > 10:
        self.run_all_actions()  # if difference is greater than 10
    self.stored_measurement = measurement  # Store measurement
```

"Measurement (Multiple)" is useful if you need to check if a particular value has been stored in any of the past measurements (within the set Max Age), not just the last measurement. This is useful if you have an alert system that each numerical value represents a different alert that you need to check each past value if it occurred. Here is an example that retrieves all measurements from the past 30 minutes and checks if each measurement value is equal to "119". If "119" exists, the Actions are executed and `break` is used to exit the `for` loop. each_measure['time'] may also be used to retrieve the timestamp for the particular measurement.

```python
# Example 1, find a particular measurement in the past 30 minutes (set Max Age to 1800 seconds)
measurements = self.condition_dict("{asdf1234}")
if measurements:
    for each_measure in measurements:
        if each_measure['value'] == 119:
            self.run_all_actions()
            break
```

Advanced `Conditional Statement` examples:

These examples expand on the simple examples, above, by activating specific actions. The following examples will reference actions with IDs that can be found under the `Actions` section of the Conditional. Two example action ID will be used: "qwer1234" and "uiop5678". Additionally, self.run_all_actions() is used here, which will run all actions in the order in which they appear in the Actions section of the Conditional.

```python
# Example 1
measurement = self.condition("{asdf1234}")
if measurement is None:
    self.run_action("{qwer1234}")
elif measurement > 23:
    self.run_action("{uiop5678}")
else:
    self.run_all_actions()

# Example 2, test two measurements
measure_1 = self.condition("{asdf1234}")
measure_2 = self.condition("{hjkl5678}")
if None not in [measure_1, measure_2]:
    if measure_1 < 20 and measure_2 > 10:
        self.run_action("{qwer1234}")
        self.run_action("{uiop5678}")

# Example 3, test two measurements and sum of measurements
measure_1 = self.condition("{asdf1234}")
measure_2 = self.condition("{hjkl5678}")
if None not in [measure_1, measure_2]:
    sum = measure_1 + measure_2
    if measure_1 > 2 and 10 < measure_2 < 23 and sum < 30.5:
        self.run_action("{qwer1234}")
    else:
        self.run_action("{uiop5678}")

# Example 4, combine into one conditional
measurement = self.condition("{asdf1234}")
if measurement != None and 20 < measurement < 30:
    self.run_action("{uiop5678}")

# Example 5, test two measurements and convert Edge Input from 0 or 1 to True or False
measure_1 = self.condition("{asdf1234}")
measure_2 = self.condition("{hjkl5678}")
if None not in [measure_1, measure_2]:
    if bool(measure_1) and measure_2 > 10:
        self.run_all_actions()

# Example 6, test measurement with "or" and a rounded measurement
measure_1 = self.measure("{asdf1234}")
measure_2 = self.measure("{hjkl5678}")
if None not in [measure_1, measure_2]:
    if measure_1 > 20 or int(round(measure_2)) in [20, 21, 22]:
        self.run_action("{qwer1234}")
        if measure_1 > 30:
            self.run_action("{uiop5678}")
```

If your action is a type that receives a message (E-Mail or Note), you can modify this message to include extra information before it is added to the Note or E-Mail. To do this, append a string to the variable `self.message` and add this to the `message` parameter of self.run_action() or self.run_all_actions(). Below are some examples. Note the use of "+=" instead of "=", which appends the string to the variable `self.message`.

```python
# Example 1
measurement = self.measure("{asdf1234}")
if measurement is None and measurement > 23:
    self.message += "Measurement was {}".format(measurement)
    self.run_action("{uiop5678}", message=self.message)

# Example 2
measure_1 = self.measure("{asdf1234}")
measure_2 = self.measure("{hjkl5678}")
if None not in [measure_1, measure_2]:
    if measure_1 < 20 and measure_2 > 10:
        self.message += "Measurement 1: {m1}, Measurement 2: {m2}".format(m1=measure_1, m2=measure_2)
        self.run_all_actions(message=self.message)
```

Logging can also be used to log messages to the daemon log using `self.logger`:

```python
# Example 1
measurement = self.measure("{asdf1234}")
if measurement is None and measurement > 23:
    self.logging.error("Warning, measurement was {}".format(measurement))
    self.message += "Measurement was {}".format(measurement)
    self.run_action("{uiop5678}", message=self.message)
```

Before activating any conditionals, it's advised to thoroughly explore all possible scenarios and plan a configuration that eliminates conflicts. Some devices or outputs may respond atypically or fail when switched on and off in rapid succession. Therefore, trial run your configuration before connecting devices to any outputs.

## Trigger

A Trigger Controller will execute actions when events are triggered, such as an output turning on or off, a GPIO pin changing it's voltage state, or timed events, including various timers (duration, time period, time point, etc), or the sunrise or sunset time at a specific latitude and longitude. One the trigger is defined, add any number of [Actions](#function-actions) to be executed when that event is triggered.

### Output (On/Off) Options

Monitor the state of an output.

<table>
<col width="40%" />
<col width="59%" />
<thead>
<tr class="header">
<th align="left">Setting</th>
<th align="left">Description</th>
</tr>
</thead>
<tbody>
<tr class="odd">
<td align="left">If Output</td>
<td align="left">The Output to monitor for a change of state.</td>
</tr>
<tr class="even">
<td align="left">If State</td>
<td align="left">If the state of the output changes to On or Off the conditional will trigger. If &quot;On (any duration) is selected, th trigger will occur no matter how long the output turns on for, whereas if only &quot;On&quot; is selected, the conditional will trigger only when the output turns on for a duration of time equal to the set &quot;Duration (seconds)&quot;.</td>
</tr>
<tr class="odd">
<td align="left">If Duration (seconds)</td>
<td align="left">If &quot;On&quot; is selected, an optional duration (seconds) may be set that will trigger the conditional only if the Output is turned on for this specific duration.</td>
</tr>
</tbody>
</table>

### Output (PWM) Options

Monitor the state of a PWM output.

<table>
<col width="40%" />
<col width="59%" />
<thead>
<tr class="header">
<th align="left">Setting</th>
<th align="left">Description</th>
</tr>
</thead>
<tbody>
<tr class="odd">
<td align="left">If Output</td>
<td align="left">The Output to monitor for a change of state.</td>
</tr>
<tr class="even">
<td align="left">If State</td>
<td align="left">If the duty cycle of the output is greater than,less than, or equal to the set value, trigger the Conditional Actions.</td>
</tr>
<tr class="odd">
<td align="left">If Duty Cycle (%)</td>
<td align="left">The duty cycle for the Output to be checked against.</td>
</tr>
</tbody>
</table>

### Edge Options

Monitor the state of a pin for a rising and/or falling edge.

<table>
<col width="40%" />
<col width="59%" />
<thead>
<tr class="header">
<th align="left">Setting</th>
<th align="left">Description</th>
</tr>
</thead>
<tbody>
<tr class="odd">
<td align="left">If Edge Detected</td>
<td align="left">The conditional will be triggered if a change in state is detected, either Rising when the state changes from LOW (0 volts) to HIGH (3.5 volts) or Falling when the state changes from HIGH (3.3 volts) to LOW (0 volts), or Both (Rising and Falling).</td>
</tr>
</tbody>
</table>

### Run PWM Method Options

Select a Duration Method and this will set the selected PWM Output to the duty cycle specified by the method.

<table>
<col width="40%" />
<col width="59%" />
<thead>
<tr class="header">
<th align="left">Setting</th>
<th align="left">Description</th>
</tr>
</thead>
<tbody>
<tr class="odd">
<td align="left">Duration Method</td>
<td align="left">Select which Method to use.</td>
</tr>
<tr class="even">
<td align="left">PWM Output</td>
<td align="left">Select which PWM Output to use.</td>
</tr>
<tr class="odd">
<td align="left">Period (seconds)</td>
<td align="left">Select the interval of time to calculate the duty cycle, then apply to the PWM Output.</td>
</tr>
<tr class="even">
<td align="left">Trigger Every Period</td>
<td align="left">Trigger Conditional Actions every period.</td>
</tr>
<tr class="odd">
<td align="left">Trigger when Activated</td>
<td align="left">Trigger Conditional Actions when the Conditional is activated.</td>
</tr>
</tbody>
</table>

### Infrared Remote Input Options

Mycodo uses lirc to detect Infrared signals. Follow the [lirc setup guide](#infrared-remote) before using this feature.

Note: Raspbian Buster broke this feature. Work is in progress to restore functionality.

<table>
<col width="40%" />
<col width="59%" />
<thead>
<tr class="header">
<th align="left">Setting</th>
<th align="left">Description</th>
</tr>
</thead>
<tbody>
<tr class="odd">
<td align="left">Program</td>
<td align="left">This is the variable 'program' in ~/.lircrc</td>
</tr>
<tr class="even">
<td align="left">Word</td>
<td align="left">This is the variable 'config' in ~/.lircrc</td>
</tr>
</tbody>
</table>

### Sunrise/Sunset Options

Trigger events at sunrise or sunset (or a time offset of those), based on latitude and longitude.

<table>
<col width="40%" />
<col width="59%" />
<thead>
<tr class="header">
<th align="left">Setting</th>
<th align="left">Description</th>
</tr>
</thead>
<tbody>
<tr class="odd">
<td align="left">Rise or Set</td>
<td align="left">Select which to trigger the conditional, at sunrise or sunset.</td>
</tr>
<tr class="even">
<td align="left">Latitude (decimal)</td>
<td align="left">Latitude of the sunrise/sunset, using decimal format.</td>
</tr>
<tr class="odd">
<td align="left">Longitude (decimal)</td>
<td align="left">Longitude of the sunrise/sunset, using decimal format.</td>
</tr>
<tr class="even">
<td align="left">Zenith</td>
<td align="left">The Zenith angle of the sun.</td>
</tr>
<tr class="odd">
<td align="left">Date Offset (days)</td>
<td align="left">Set a sunrise/sunset offset in days (positive or negative).</td>
</tr>
<tr class="even">
<td align="left">Time Offset (minutes)</td>
<td align="left">Set a sunrise/sunset offset in minutes (positive or negative).</td>
</tr>
</tbody>
</table>

### Timer (Duration) Options

Run a timer that triggers Conditional Actions every period.

<table>
<col width="40%" />
<col width="59%" />
<thead>
<tr class="header">
<th align="left">Setting</th>
<th align="left">Description</th>
</tr>
</thead>
<tbody>
<tr class="odd">
<td align="left">Period (seconds)</td>
<td align="left">The period of time between triggering Conditional Actions.</td>
</tr>
<tr class="even">
<td align="left">Start Offset (seconds)</td>
<td align="left">Set this to start the first trigger a number of seconds after the Conditional is activated.</td>
</tr>
</tbody>
</table>

### Timer (Daily Time Point) Options

Run a timer that triggers Conditional Actions at a specific time every day.

<table>
<col width="40%" />
<col width="59%" />
<thead>
<tr class="header">
<th align="left">Setting</th>
<th align="left">Description</th>
</tr>
</thead>
<tbody>
<tr class="odd">
<td align="left">Start Time (HH:MM)</td>
<td align="left">Set the time to trigger Conditional Actions, in the format &quot;HH:MM&quot;, with HH denoting hours, and MM denoting minutes. Time is in 24-hour format.</td>
</tr>
</tbody>
</table>

### Timer (Daily Time Span) Options

Run a timer that triggers Conditional Actions at a specific period if it's between the set start and end times. For example, if the Start Time is set to 10:00 and End Time set to 11:00 and Period set to 120 seconds, the Conditional Actions will trigger every 120 seconds when the time is between 10 AM and 11 AM.

This may be useful, for instance, if you desire an Output to remain on during a particular time period and you want to prevent power outages from interrupting the cycle (which a simple Time Point Timer could not prevent against because it only triggers once at the Start Time). By setting an Output to turn the lights on every few minutes during the Start -> End period, it ensured the Output remains on during this period.

<table>
<col width="40%" />
<col width="59%" />
<thead>
<tr class="header">
<th align="left">Setting</th>
<th align="left">Description</th>
</tr>
</thead>
<tbody>
<tr class="odd">
<td align="left">Start Time (HH:MM)</td>
<td align="left">Set the start time to trigger Conditional Actions, in the format &quot;HH:MM&quot;, with HH denoting hours, and MM denoting minutes. Time is in 24-hour format.</td>
</tr>
<tr class="even">
<td align="left">End Time (HH:MM)</td>
<td align="left">Set the end time to trigger Conditional Actions, in the format &quot;HH:MM&quot;, with HH denoting hours, and MM denoting minutes. Time is in 24-hour format.</td>
</tr>
<tr class="odd">
<td align="left">Period (seconds)</td>
<td align="left">The period of time between triggering Conditional Actions.</td>
</tr>
</tbody>
</table>

## Function Actions

These are the actions that can be added to Function controllers (i.e. Conditional, Trigger).

<table>
<col width="40%" />
<col width="59%" />
<thead>
<tr class="header">
<th align="left">Setting</th>
<th align="left">Description</th>
</tr>
</thead>
<tbody>
<tr class="odd">
<td align="left">Actions: Pause</td>
<td align="left">Pause executing actions for a duration of time (seconds).</td>
</tr>
<tr class="even">
<td align="left">Camera: Capture Photo</td>
<td align="left">Capture a photo with the selected camera.</td>
</tr>
<tr class="odd">
<td align="left">Create Note</td>
<td align="left">Create a note containing the conditional statement and actions, using a particular tag.</td>
</tr>
<tr class="even">
<td align="left">Controller: Activate</td>
<td align="left">Activate a particular controller.</td>
</tr>
<tr class="odd">
<td align="left">Controller: Deactivate</td>
<td align="left">Deactivate a particular controller.</td>
</tr>
<tr class="even">
<td align="left">E-Mail</td>
<td align="left">Send an email containing the conditional statement and actions.</td>
</tr>
<tr class="odd">
<td align="left">E-Mail with Photo Attachment</td>
<td align="left">Send an email containing the conditional statement, actions, and captured photo.</td>
</tr>
<tr class="even">
<td align="left">E-Mail with Video Attachment</td>
<td align="left">Send an email containing the conditional statement, actions, and captured video.</td>
</tr>
<tr class="odd">
<td align="left">Execute Command</td>
<td align="left">Execute a command in the linux shell (as user 'root').</td>
</tr>
<tr class="even">
<td align="left">Infrared Remote Send</td>
<td align="left">Send an infrared signal. See <a href="#infrared-remote">Infrared Remote</a> for details.</td>
</tr>
<tr class="odd">
<td align="left">LCD: Backlight</td>
<td align="left">Turn the LCD backlight on or off. Note: Only some LCDs are supported.</td>
</tr>
<tr class="even">
<td align="left">LCD: Flash</td>
<td align="left">Start of stop the LCD flashing to indicate an alert. Note: Only some LCDs are supported.</td>
</tr>
<tr class="odd">
<td align="left">Output: Duration</td>
<td align="left">Turn a output on, off, or on for a duration of time.</td>
</tr>
<tr class="even">
<td align="left">Output: Duty Cycle</td>
<td align="left">Turn a PWM output off or on for a duty cycle.</td>
</tr>
<tr class="odd">
<td align="left">PID: Pause</td>
<td align="left">Pause a particular PID controller.</td>
</tr>
<tr class="even">
<td align="left">PID: Hold</td>
<td align="left">Hold a particular PID controller.</td>
</tr>
<tr class="odd">
<td align="left">PID: Resume</td>
<td align="left">Resume a particular PID controller.</td>
</tr>
<tr class="even">
<td align="left">PID: Set Method</td>
<td align="left">Set the Method of a particular PID controller.</td>
</tr>
<tr class="odd">
<td align="left">PID: Set Setpoint</td>
<td align="left">Set the Setpoint of a particular PID controller.</td>
</tr>
<tr class="even">
<td align="left">System: Restart</td>
<td align="left">Restart the System.</td>
</tr>
<tr class="odd">
<td align="left">System: Shutdown</td>
<td align="left">Shutdown the System.</td>
</tr>
</tbody>
</table>
