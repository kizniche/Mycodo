Page\: `Setup -> Input` (Previously `Setup -> Data`)

!!! warning
    Math controllers have been deprecated since Mycodo version 8.9.0. All Math controller functionality has been ported to [Functions](Functions.md). No new Math controllers can be created in Mycodo 8.9.0 and beyond, but already-existing Math controllers are permitted to operate until further notice. If you are using Mycodo version 8.9.0 or beyond, it is advised to create Functions for all your current Math controllers, because at some point in the future Math controllers will be completely removed. This manual page only serves as reference material for those still using Math controllers.

!!! note
    "Last" means the controller will only acquire the last (latest) measurement in the database for performing math with. "Past" means the controller will acquire all measurements from the present until the "Max Age (seconds)" set by the user (e.g. if measurements are acquired every 10 seconds, and a Max Age is set to 60 seconds, there will on average be 6 measurements returned to have math performed).

### Math Options

Types of math controllers.

<table>
<thead>
<tr class="header">
<th>Type</th>
<th>Description</th>
</tr>
</thead>
<tbody>
<tr>
<td>Average (Last, Multiple Channels)</td>
<td>Stores the statistical mean of the last measurement of multiple selected measurement channels.</td>
</tr>
<tr>
<td>Average (Past, Single Channel)</td>
<td>Stores the statistical mean of one selected measurement channel over a duration of time determined by the Max Age (seconds) option.</td>
</tr>
<tr>
<td>Sum (Last, Multiple Channels)</td>
<td>Stores the sum of multiple selected measurement channels.</td>
</tr>
<tr>
<td>Sum (Past, Single Channel)</td>
<td>Stores the sum of one selected measurement channel over a duration of time determined by the Max Age(seconds) option.</td>
</tr>
<tr>
<td>Difference</td>
<td>Stores the mathematical difference (value_1 - value_2).</td>
</tr>
<tr>
<td>Equation</td>
<td>Stores the calculated value of an equation.</td>
</tr>
<tr>
<td>Redundancy</td>
<td>Select multiple Inputs and if one input isn't available, the next measurement will be used. For example, this is useful if an Input stops but you don't want a PID controller to stop working if there is another measurement that can be used. More than one Input can be and the preferred Order of Use can be defined.</td>
</tr>
<tr>
<td>Verification</td>
<td>Ensures the greatest difference between any selected Inputs is less than Max Difference, and if so, stores the average of the selected measurements.</td>
</tr>
<tr>
<td>Statistics</td>
<td>Calculates mean, median, minimum, maximum, standard deviation (SD), SD upper, and SD lower for a set of measurements.</td>
</tr>
<tr>
<td>Humidity (Wet/Dry-Bulb)</td>
<td>Calculates and stores the percent relative humidity from the dry-bulb and wet-bulb temperatures, and optional pressure.</td>
</tr>
</tbody>
</table>

Math controller options.

<table>
<thead>
<tr class="header">
<th>Setting</th>
<th>Description</th>
</tr>
</thead>
<tbody>
<tr>
<td>Input</td>
<td>Select the Inputs to use with the particular Math controller</td>
</tr>
<tr>
<td>Period (seconds)</td>
<td>The duration of time between calculating and storing a new value</td>
</tr>
<tr>
<td>Max Age (seconds)</td>
<td>The maximum allowed age of the Input measurements. If an Input measurement is older than this period, the calculation is cancelled and the new value is not stored in the database. Consequently, if another controller has a Max Age set and cannot retrieve a current Math value, it will cease functioning. A PID controller, for instance, may stop regulating if there is no new Math value created, preventing the PID controller from continuing to run when it should not.</td>
</tr>
<tr>
<td>Start Offset (seconds)</td>
<td>Wait this duration before attempting the first calculation/measurement.</td>
</tr>
<tr>
<td>Measurement</td>
<td>This is the condition being measured. For instance, if all of the selected measurements are temperature, this should also be temperature. A list of the pre-defined measurements that may be used is below.</td>
</tr>
<tr>
<td>Units</td>
<td>This is the units to display along with the measurement, on Graphs. If a pre-defined measurement is used, this field will default to the units associated with that measurement.</td>
</tr>
<tr>
<td>Reverse Equation</td>
<td>For Difference calculations, this will reverse the equation order, from <code>value_1 - value_2</code> to <code>value_2 - value_1</code>.</td>
</tr>
<tr>
<td>Absolute Value</td>
<td>For Difference calculations, this will yield an absolute value (positive number).</td>
</tr>
<tr>
<td>Max Difference</td>
<td>If the difference between any selected Input is greater than this value, no new value will be stored in the database.</td>
</tr>
<tr>
<td>Dry-Bulb Temperature</td>
<td>The measurement that will serve as the dry-bulb temperature (this is the warmer of the two temperature measurements)</td>
</tr>
<tr>
<td>Wet-Bulb Temperature</td>
<td>The measurement that will serve as the wet-bulb temperature (this is the colder of the two temperature measurements)</td>
</tr>
<tr>
<td>Pressure</td>
<td>This is an optional pressure measurement that can be used to calculate the percent relative humidity. If disabled, a default 101325 Pa will be used in the calculation.</td>
</tr>
<tr>
<td>Equation</td>
<td>An equation that will be solved with Python's eval() function. Let &quot;x&quot; represent the input value. Valid equation symbols include: + - * / ^</td>
</tr>
<tr>
<td>Order of Use</td>
<td>This is the order in which the selected Inputs will be used. This must be a comma separated list of Input IDs (integers, not UUIDs).</td>
</tr>
</tbody>
</table>
