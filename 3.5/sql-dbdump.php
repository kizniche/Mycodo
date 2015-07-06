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
print "Relays HTSensors CO2Sensors Timers<br>";
$results = $db->query('SELECT Relays, HTSensors, CO2Sensors, Timers FROM Numbers');
while ($row = $results->fetchArray()) {
    print $row[0] . " " . $row[1] . " " . $row[2] . " " . $row[3] . "<br>";
}

print "<br>Table: Relays<br>";
print "Id Name Pin Trigger<br>";
$results = $db->query('SELECT Id, Name, Pin, Trigger FROM Relays');
while ($row = $results->fetchArray()) {
    print $row[0] . " " . $row[1] . " " . $row[2] . " " . $row[3] . "<br>";
}

print "<br>Table: HTSensor<br>";
print "Id Name Pin Device Period Activated Graph Temp_Relay Temp_OR Temp_Set Temp_P Temp_I Temp_D Hum_Relay Hum_OR Hum_Set Hum_P Hum_I Hum_D<br>";
$results = $db->query('SELECT Id, Name, Pin, Device, Period, Activated, Graph, Temp_Relay, Temp_OR, Temp_Set, Temp_P, Temp_I, Temp_D, Hum_Relay, Hum_OR, Hum_Set, Hum_P, Hum_I, Hum_D FROM HTSensor');
while ($row = $results->fetchArray()) {
    print $row[0] . " " . $row[1] . " " . $row[2] . " " . $row[3] . " " . $row[4] . " " . $row[5] . " " . $row[6] . " " . $row[7] . " " . $row[8] . " " . $row[9] . " " . $row[10] . " " . $row[11] . " " . $row[12] . " " . $row[13] . " " . $row[14] . " " . $row[15] . " " . $row[16] . " " . $row[17] . $row[18] . "<br>";
}

print "<br>Table: CO2Sensor<br>";
print "Id Name Pin Device Period Activated Graph CO2_Relay CO2_OR CO2_Set CO2_P CO2_I CO2_D<br>";
$results = $db->query('SELECT Id, Name, Pin, Device, Period, Activated, Graph, CO2_Relay, CO2_OR, CO2_Set, CO2_P, CO2_I, CO2_D FROM CO2Sensor');
while ($row = $results->fetchArray()) {
    print $row[0] . " " . $row[1] . " " . $row[2] . " " . $row[3] . " " . $row[4] . " " . $row[5] . " " . $row[6] . " " . $row[7] . " " . $row[8] . " " . $row[9] . " " . $row[10] . " " . $row[11] . " " . $row[12] . "<br>";
}

print "<br>Table: Timers<br>";
print "Id Name State Relay DurationOn DurationOff<br>";
$results = $db->query('SELECT Id, Name, State, Relay, DurationOn, DurationOff FROM Timers');
while ($row = $results->fetchArray()) {
    print $row[0] . " " . $row[1] . " " . $row[2] . " " . $row[3] . " " . $row[4] . " " . $row[5] . "<br>";
}

print "<br>Table: SMTP<br>";
print "Host SSL Port User Pass Email_From Email_To<br>";
$results = $db->query('SELECT Host, SSL, Port, User, Pass, Email_From, Email_To FROM SMTP');
while ($row = $results->fetchArray()) {
    print $row[0] . " " . $row[1] . " " . $row[2] . " " . $row[3] . " " . $row[4] . " " . $row[5] . $row[6] ."<br>";
}
?>