Page\: `Setup -> Method`

Methods enable Setpoint Tracking in PIDs and time-based duty cycle changes in timers. Normally, a PID controller will regulate an environmental condition to a specific setpoint. If you would like the setpoint to change over time, this is called setpoint tracking. Setpoint Tracking is useful for applications such as reflow ovens, thermal cyclers (DNA replication), mimicking natural daily cycles, and more. Methods may also be used to change a duty cycle over time when used with a Run PWM Method Conditional.

## Method Options

These options are shared with several method types.

<table>
<thead>
<tr class="header">
<th>Setting</th>
<th>Description</th>
</tr>
</thead>
<tbody>
<tr>
<td>Start Time/Date</td>
<td>This is the start time of a range of time.</td>
</tr>
<tr>
<td>End Time/Date</td>
<td>This is the end time of a range of time.</td>
</tr>
<tr>
<td>Start Setpoint</td>
<td>This is the start setpoint of a range of setpoints.</td>
</tr>
<tr>
<td>End Setpoint</td>
<td>This is the end setpoint of a range of setpoints.</td>
</tr>
</tbody>
</table>

## Time/Date Method

A time/date method allows a specific time/date span to dictate the setpoint. This is useful for long-running methods, that may take place over the period of days, weeks, or months.

## Duration Method

A Duration Method allows a **Setpoint** (for PIDs) or **Duty Cycle** (for Conditional) to be set after specific durations of time. Each new duration added will stack, meaning it will come after the previous duration, meaning a newly-added **Start Setpoint** will begin after the previous entry's **End Setpoint**.

If the "Repeat Method" option is used, this will cause the method to repeat once it has reached the end. If this option is used, no more durations may be added to the method. If the repeat option is deleted then more durations may be added. For instance, if your method is 200 seconds total, if the Repeat Duration is set to 600 seconds, the method will repeat 3 times and then automatically turn off the PID or Conditional.

## Daily (Time-Based) Method

The daily time-based method is similar to the time/date method, however it will repeat every day. Therefore, it is essential that only the span of one day be set in this method. Begin with the start time at 00:00:00 and end at 23:59:59 (or 00:00:00, which would be 24 hours from the start). The start time must be equal or greater than the previous end time.

## Daily (Sine Wave) Method

The daily sine wave method defines the setpoint over the day based on a sinusoidal wave. The sine wave is defined by y = [A \* sin(B \* x + C)] + D, where A is amplitude, B is frequency, C is the angle shift, and D is the y-axis shift. This method will repeat daily.

## Daily (Bezier Curve) Method

A daily Bezier curve method define the setpoint over the day based on a cubic Bezier curve. If unfamiliar with a Bezier curve, it is recommended you use the [graphical Bezier curve generator](https://www.desmos.com/calculator/cahqdxeshd) and use the 8 variables it creates for 4 points (each a set of x and y). The x-axis start (x3) and end (x0) will be automatically stretched or skewed to fit within a 24-hour period and this method will repeat daily.

## Cascade Method

This method combines multiple methods and outputs the average of the methods. For examples, let's combine a Duration method set to 100 for 60 seconds and 0 for 60 seconds (and set to repeat forever) with a Daily Method that rises from 0 at 00:00:00 to 50 at 12:00:00, and falls back to 0 at 23:59:59. At 00:00:00, the combined methods would produce an output that oscillates from 0 ((0 / 100) * (0 / 100) = 0) to 0 ((100 / 100) * (0 / 100) = 0) every 60 seconds, and gradually increase until at 12:00:00 the output would be oscillating from 0 ((0 / 100) * (50 / 100)) to 50 ((100 / 100) * (50 / 100)) every 60 seconds. This is a simple example, but combinations can become very complex.
