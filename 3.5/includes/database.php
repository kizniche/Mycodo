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


$results = $db->query('SELECT Id, Name, Pin, Trigger, Start_State FROM Relays');
while ($row = $results->fetchArray()) {
    $relay_name[$row[0]] = $row[1];
    $relay_pin[$row[0]] = $row[2];
    $relay_trigger[$row[0]] = $row[3];
    $relay_start_state[$row[0]] = $row[4];
}


// Sensor/PID Presets
$sensor_t_preset = [];
$results = $db->query('SELECT Preset FROM TSensorPreset');
while ($row = $results->fetchArray()) {
    $sensor_t_preset[] = $row[0];
}
sort($sensor_t_preset, SORT_NATURAL | SORT_FLAG_CASE);

$sensor_ht_preset = [];
$results = $db->query('SELECT Preset FROM HTSensorPreset');
while ($row = $results->fetchArray()) {
    $sensor_ht_preset[] = $row[0];
}
sort($sensor_ht_preset, SORT_NATURAL | SORT_FLAG_CASE);

$sensor_co2_preset = [];
$results = $db->query('SELECT Preset FROM CO2SensorPreset');
while ($row = $results->fetchArray()) {
    $sensor_co2_preset[] = $row[0];
}
sort($sensor_co2_preset, SORT_NATURAL | SORT_FLAG_CASE);





$sensor_ht = [];
$results = $db->query('SELECT Name FROM HTSensor');
while ($row = $results->fetchArray()) {
    $sensor_ht[] = $row[0];
}
//sort($sensor_ht, SORT_NATURAL | SORT_FLAG_CASE);





$results = $db->query('SELECT Id, Name, Pin, Device, Period, Activated, Graph, Temp_Relay_High, Temp_Relay_Low, Temp_OR, Temp_Set, Temp_Set_Direction, Temp_Set_Buffer, Temp_Period, Temp_P_High, Temp_I_High, Temp_D_High, Temp_P_Low, Temp_I_Low, Temp_D_Low FROM TSensor');
while ($row = $results->fetchArray()) {
    $sensor_t_name[$row[0]] = $row[1];
    $sensor_t_pin[$row[0]] = $row[2];
    $sensor_t_device[$row[0]] = $row[3];
    $sensor_t_period[$row[0]] = $row[4];
    $sensor_t_activated[$row[0]] = $row[5];
    $sensor_t_graph[$row[0]] = $row[6];
    $pid_t_temp_relay_high[$row[0]] = $row[7];
    $pid_t_temp_relay_low[$row[0]] = $row[8];
    $pid_t_temp_or[$row[0]] = $row[9];
    $pid_t_temp_set[$row[0]] = $row[10];
    $pid_t_temp_set_dir[$row[0]] = $row[11];
    $pid_t_temp_set_buf[$row[0]] = $row[12];
    $pid_t_temp_period[$row[0]] = $row[13];
    $pid_t_temp_p_high[$row[0]] = $row[14];
    $pid_t_temp_i_high[$row[0]] = $row[15];
    $pid_t_temp_d_high[$row[0]] = $row[16];
    $pid_t_temp_p_low[$row[0]] = $row[17];
    $pid_t_temp_i_low[$row[0]] = $row[18];
    $pid_t_temp_d_low[$row[0]] = $row[19];
}


$results = $db->query('SELECT Id, Name, Pin, Device, Period, Activated, Graph, Temp_Relay_High, Temp_Relay_Low, Temp_OR, Temp_Set, Temp_Set_Direction, Temp_Set_Buffer, Temp_Period, Temp_P_High, Temp_I_High, Temp_D_High, Temp_P_Low, Temp_I_Low, Temp_D_Low, Hum_Relay_High, Hum_Relay_Low, Hum_OR, Hum_Set, Hum_Set_Direction, Hum_Set_Buffer, Hum_Period, Hum_P_High, Hum_I_High, Hum_D_High, Hum_P_Low, Hum_I_Low, Hum_D_low FROM HTSensor');
$count = 0;
while ($row = $results->fetchArray()) {
    $sensor_ht_id[$count] = $row[0];
    $sensor_ht_name[$count] = $row[1];
    $sensor_ht_pin[$count] = $row[2];
    $sensor_ht_device[$count] = $row[3];
    $sensor_ht_period[$count] = $row[4];
    $sensor_ht_activated[$count] = $row[5];
    $sensor_ht_graph[$count] = $row[6];
    $pid_ht_temp_relay_high[$count] = $row[7];
    $pid_ht_temp_relay_low[$count] = $row[8];
    $pid_ht_temp_or[$count] = $row[9];
    $pid_ht_temp_set[$count] = $row[10];
    $pid_ht_temp_set_dir[$count] = $row[11];
    $pid_ht_temp_set_buf[$count] = $row[12];
    $pid_ht_temp_period[$count] = $row[13];
    $pid_ht_temp_p_high[$count] = $row[14];
    $pid_ht_temp_i_high[$count] = $row[15];
    $pid_ht_temp_d_high[$count] = $row[16];
    $pid_ht_temp_p_low[$count] = $row[17];
    $pid_ht_temp_i_low[$count] = $row[18];
    $pid_ht_temp_d_low[$count] = $row[19];
    $pid_ht_hum_relay_high[$count] = $row[20];
    $pid_ht_hum_relay_low[$count] = $row[21];
    $pid_ht_hum_or[$count] = $row[22];
    $pid_ht_hum_set[$count] = $row[23];
    $pid_ht_hum_set_dir[$count] = $row[24];
    $pid_ht_hum_set_buf[$count] = $row[25];
    $pid_ht_hum_period[$count] = $row[26];
    $pid_ht_hum_p_high[$count] = $row[27];
    $pid_ht_hum_i_high[$count] = $row[28];
    $pid_ht_hum_d_high[$count] = $row[29];
    $pid_ht_hum_p_low[$count] = $row[30];
    $pid_ht_hum_i_low[$count] = $row[31];
    $pid_ht_hum_d_low[$count] = $row[32];
    $count++;
}


$results = $db->query('SELECT Id, Name, Pin, Device, Period, Activated, Graph, CO2_Relay_High, CO2_Relay_Low, CO2_OR, CO2_Set, CO2_Set_Direction, CO2_Set_Buffer, CO2_Period, CO2_P_High, CO2_I_High, CO2_D_High, CO2_P_Low, CO2_I_Low, CO2_D_Low FROM CO2Sensor');
while ($row = $results->fetchArray()) {
    $sensor_co2_name[$row[0]] = $row[1];
    $sensor_co2_pin[$row[0]] = $row[2];
    $sensor_co2_device[$row[0]] = $row[3];
    $sensor_co2_period[$row[0]] = $row[4];
    $sensor_co2_activated[$row[0]] = $row[5];
    $sensor_co2_graph[$row[0]] = $row[6];
    $pid_co2_relay_high[$row[0]] = $row[7];
    $pid_co2_relay_low[$row[0]] = $row[8];
    $pid_co2_or[$row[0]] = $row[9];
    $pid_co2_set[$row[0]] = $row[10];
    $pid_co2_set_dir[$row[0]] = $row[11];
    $pid_co2_set_buf[$row[0]] = $row[12];
    $pid_co2_period[$row[0]] = $row[13];
    $pid_co2_p_high[$row[0]] = $row[14];
    $pid_co2_i_high[$row[0]] = $row[15];
    $pid_co2_d_high[$row[0]] = $row[16];
    $pid_co2_p_low[$row[0]] = $row[17];
    $pid_co2_i_low[$row[0]] = $row[18];
    $pid_co2_d_low[$row[0]] = $row[19];
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


$results = $db->query('SELECT Relay, Timestamp, Display_Last, Extra_Parameters FROM CameraStill');
while ($row = $results->fetchArray()) {
    $still_relay = $row[0];
    $still_timestamp = $row[1];
    $still_display_last = $row[2];
    $still_extra_parameters = $row[3];
}


$results = $db->query('SELECT Relay, Extra_Parameters FROM CameraStream');
while ($row = $results->fetchArray()) {
    $stream_relay = $row[0];
    $stream_extra_parameters = $row[1];
}


$results = $db->query('SELECT Relay, Path, Prefix, File_Timestamp, Display_Last, Extra_Parameters FROM CameraTimelapse');
while ($row = $results->fetchArray()) {
    $timelapse_relay = $row[0];
    $timelapse_path = $row[1];
    $timelapse_prefix = $row[2];
    $timelapse_timestamp = $row[3];
    $timelapse_display_last = $row[4];
    $timelapse_extra_parameters = $row[5];
}


$results = $db->query('SELECT Refresh_Time FROM Misc');
while ($row = $results->fetchArray()) {
    $refresh_time = $row[0];
}
