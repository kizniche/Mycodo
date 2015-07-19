<?php
/*
*  database.php - Load database values as variables
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

$db = new SQLite3($mycodo_db);

$results = $db->query('SELECT Relays, TSensors, HTSensors, CO2Sensors, Timers FROM Numbers');
while ($row = $results->fetchArray()) {
    $relay_num = $row[0];
    $sensor_t_num = $row[1];
    $sensor_ht_num = $row[2];
    $sensor_co2_num = $row[3];
    $timer_num = $row[4];
}

$results = $db->query('SELECT Id, Name, Pin, Trigger FROM Relays');
while ($row = $results->fetchArray()) {
    $relay_name[$row[0]] = $row[1];
    $relay_pin[$row[0]] = $row[2];
    $relay_trigger[$row[0]] = $row[3];
}

$results = $db->query('SELECT Id, Name, Pin, Device, Period, Activated, Graph, Temp_Relay, Temp_OR, Temp_Set, Temp_Period, Temp_P, Temp_I, Temp_D FROM TSensor');
while ($row = $results->fetchArray()) {
    $sensor_t_name[$row[0]] = $row[1];
    $sensor_t_pin[$row[0]] = $row[2];
    $sensor_t_device[$row[0]] = $row[3];
    $sensor_t_period[$row[0]] = $row[4];
    $sensor_t_activated[$row[0]] = $row[5];
    $sensor_t_graph[$row[0]] = $row[6];
    $pid_t_temp_relay[$row[0]] = $row[7];
    $pid_t_temp_or[$row[0]] = $row[8];
    $pid_t_temp_set[$row[0]] = $row[9];
    $pid_t_temp_period[$row[0]] = $row[10];
    $pid_t_temp_p[$row[0]] = $row[11];
    $pid_t_temp_i[$row[0]] = $row[12];
    $pid_t_temp_d[$row[0]] = $row[13];
}

$results = $db->query('SELECT Id, Name, Pin, Device, Period, Activated, Graph, Temp_Relay, Temp_OR, Temp_Set, Temp_Period, Temp_P, Temp_I, Temp_D, Hum_Relay, Hum_OR, Hum_Set, Hum_Period, Hum_P, Hum_I, Hum_D FROM HTSensor');
while ($row = $results->fetchArray()) {
    $sensor_ht_name[$row[0]] = $row[1];
    $sensor_ht_pin[$row[0]] = $row[2];
    $sensor_ht_device[$row[0]] = $row[3];
    $sensor_ht_period[$row[0]] = $row[4];
    $sensor_ht_activated[$row[0]] = $row[5];
    $sensor_ht_graph[$row[0]] = $row[6];
    $pid_ht_temp_relay[$row[0]] = $row[7];
    $pid_ht_temp_or[$row[0]] = $row[8];
    $pid_ht_temp_set[$row[0]] = $row[9];
    $pid_ht_temp_period[$row[0]] = $row[10];
    $pid_ht_temp_p[$row[0]] = $row[11];
    $pid_ht_temp_i[$row[0]] = $row[12];
    $pid_ht_temp_d[$row[0]] = $row[13];
    $pid_ht_hum_relay[$row[0]] = $row[14];
    $pid_ht_hum_or[$row[0]] = $row[15];
    $pid_ht_hum_set[$row[0]] = $row[16];
    $pid_ht_hum_period[$row[0]] = $row[17];
    $pid_ht_hum_p[$row[0]] = $row[18];
    $pid_ht_hum_i[$row[0]] = $row[19];
    $pid_ht_hum_d[$row[0]] = $row[20];
}

$results = $db->query('SELECT Id, Name, Pin, Device, Period, Activated, Graph, CO2_Relay, CO2_OR, CO2_Set, CO2_Period, CO2_P, CO2_I, CO2_D FROM CO2Sensor');
while ($row = $results->fetchArray()) {
    $sensor_co2_name[$row[0]] = $row[1];
    $sensor_co2_pin[$row[0]] = $row[2];
    $sensor_co2_device[$row[0]] = $row[3];
    $sensor_co2_period[$row[0]] = $row[4];
    $sensor_co2_activated[$row[0]] = $row[5];
    $sensor_co2_graph[$row[0]] = $row[6];
    $pid_co2_relay[$row[0]] = $row[7];
    $pid_co2_or[$row[0]] = $row[8];
    $pid_co2_set[$row[0]] = $row[9];
    $pid_co2_period[$row[0]] = $row[10];
    $pid_co2_p[$row[0]] = $row[11];
    $pid_co2_i[$row[0]] = $row[12];
    $pid_co2_d[$row[0]] = $row[13];
}

$results = $db->query('SELECT Id, Name, State, Relay, DurationOn, DurationOff FROM Timers');
while ($row = $results->fetchArray()) {
    $timer_name[$row[0]] = $row[1];
    $timer_state[$row[0]] = $row[2];
    $timer_relay[$row[0]] = $row[3];
    $timer_duration_on[$row[0]] = $row[4];
    $timer_duration_off[$row[0]] = $row[5];
}

$results = $db->query('SELECT Host, SSL, Port, User, Pass, Email_From, Email_To FROM SMTP');
while ($row = $results->fetchArray()) {
    $smtp_host = $row[0];
    $smtp_ssl = $row[1];
    $smtp_port = $row[2];
    $smtp_user = $row[3];
    $smtp_pass = $row[4];
    $smtp_email_to = $row[5];
    $smtp_email_from = $row[6];
}

$results = $db->query('SELECT Camera_Relay, Display_Last, Display_Timestamp FROM Misc');
while ($row = $results->fetchArray()) {
    $camera_relay = $row[0];
    $display_last = $row[1];
    $display_timestamp = $row[2];
}
