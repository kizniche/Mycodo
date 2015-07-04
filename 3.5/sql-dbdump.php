<?php
/*
*  sql-test.php - Development code for Mycodo SQL database use
*
*  Copyright (C) 2015  Kyle T. Gabriel
*
*  This file is part of Mycodo
*
*  Mycodo is free software: you can redistribute it and/or modify
*  it under the terms of the GNU General Public License as published by
*  the Free Software Foundation, either version 3 of the License, or
*  (at your option) any later version.
*
*  Mycodo is distributed in the hope that it will be useful,
*  but WITHOUT ANY WARRANTY; without even the implied warranty of
*  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
*  GNU General Public License for more details.
*
*  You should have received a copy of the GNU General Public License
*  along with Mycodo. If not, see <http://www.gnu.org/licenses/>.
*
*  Contact at kylegabriel.com
*/

$sqlite_db = "/var/www/mycodo/config/mycodo.sqlite3";

$db = new SQLite3($sqlite_db);

print "Table: Numbers<br>";
$results = $db->query('SELECT Relays, HTSensors, CO2Sensors, Timers FROM Numbers');
while ($row = $results->fetchArray()) {
    print $row[0] . " " . $row[1] . " " . $row[2] . " " . $row[3] . "<br>";
}

print "<br>Table: Relays<br>";
$results = $db->query('SELECT Id, Name, Pin, Trigger FROM Relays');
while ($row = $results->fetchArray()) {
    print $row[0] . " " . $row[1] . " " . $row[2] . " " . $row[3] . "<br>";
}

print "<br>Table: HTSensor<br>";
$results = $db->query('SELECT Id, Name, Pin, Device, Relay, Period, Activated, Graph, Temp_OR, Temp_Set, Temp_P, Temp_I, Temp_D, Hum_OR, Hum_Set, Hum_P, Hum_I, Hum_D FROM HTSensor');
while ($row = $results->fetchArray()) {
    print $row[0] . " " . $row[1] . " " . $row[2] . " " . $row[3] . " " . $row[4] . " " . $row[5] . " " . $row[6] . " " . $row[7] . " " . $row[8] . " " . $row[9] . " " . $row[10] . " " . $row[11] . " " . $row[12] . " " . $row[13] . " " . $row[14] . " " . $row[15] . " " . $row[16] . " " . $row[17] . "<br>";
}

print "<br>Table: CO2Sensor<br>";
$results = $db->query('SELECT Id, Name, Pin, Device, Relay, Period, Activated, Graph, CO2_OR, CO2_Set, CO2_P, CO2_I, CO2_D FROM CO2Sensor');
while ($row = $results->fetchArray()) {
    print $row[0] . " " . $row[1] . " " . $row[2] . " " . $row[3] . " " . $row[4] . " " . $row[5] . " " . $row[6] . " " . $row[7] . " " . $row[8] . " " . $row[9] . " " . $row[10] . " " . $row[11] . " " . $row[12] . "<br>";
}

print "<br>Table: Timers<br>";
$results = $db->query('SELECT Id, Name, State, Relay, DurationOn, DurationOff FROM Timers');
while ($row = $results->fetchArray()) {
    print $row[0] . " " . $row[1] . " " . $row[2] . " " . $row[3] . " " . $row[4] . " " . $row[5] . "<br>";
}
/*
print "<br>Table: Strings<br>";
$results = $db->query('SELECT row, column FROM Strings');
while ($row = $results->fetchArray()) {
    print $row[0] . " = " . $row[1] . "<br>";
}

print "<br>Table: Integers<br>";
$results = $db->query('SELECT row, column FROM Integers');
while ($row = $results->fetchArray()) {
    print $row[0] . " = " . $row[1] . "<br>";
}

print "<br>Table: Floats<br>";
$results = $db->query('SELECT row, column FROM Floats');
while ($row = $results->fetchArray()) {
    print $row[0] . " = " . number_format($row[1],1) . "<br>";
}
*/
?>