Page\: `[Gear Icon] -> System Information`

This page serves to provide information about the Mycodo frontend and backend as well as the linux system it's running on. Several commands and their output are listed to give the user information about how their system is running.

<table>
<thead>
<tr class="header">
<th>Command</th>
<th>Description</th>
</tr>
</thead>
<tbody>
<tr>
<td>Mycodo Version</td>
<td>The current version of Mycodo, reported by the configuration file.</td>
</tr>
<tr>
<td>Python Version</td>
<td>The version of python currently running the web user interface.</td>
</tr>
<tr>
<td>Database Version</td>
<td>The current version of the settings database. If the current version is different from what it should be, an error will appear indicating the issue and a link to find out more information about the issue.</td>
</tr>
<tr>
<td>Daemon Status</td>
<td>This will be a green &quot;Running&quot; or a red &quot;Stopped&quot;. Additionally, the Mycodo version and hostname text at the top-left of the screen May be Green, Yellow, or Red to indicate the status. Green = daemon running, yellow = unable to connect, and red = daemon not running.</td>
</tr>
<tr>
<td>...</td>
<td>Several other status indicators and commands are listed to provide information about the health of the system. Use these in addition to others to investigate software or hardware issues.</td>
</tr>
</tbody>
</table>