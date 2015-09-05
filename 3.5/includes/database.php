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


unset($relay_id);
$results = $db->query('SELECT Id, Name, Pin, Trigger, Start_State FROM Relays');
$count = 0;
while ($row = $results->fetchArray()) {
    $relay_id[$count] = $row[0];
    $relay_name[$count] = $row[1];
    $relay_pin[$count] = $row[2];
    $relay_trigger[$count] = $row[3];
    $relay_start_state[$count] = $row[4];
    $count++;
}
if (!isset($relay_id)) $relay_id = [];


unset($sensor_t_id);
$results = $db->query('SELECT Id, Name, Pin, Device, Period, Pre_Measure_Relay, Pre_Measure_Dur, Activated, Graph, YAxis_Relay_Min, YAxis_Relay_Max, YAxis_Relay_Tics, YAxis_Relay_MTics, YAxis_Temp_Min, YAxis_Temp_Max, YAxis_Temp_Tics, YAxis_Temp_MTics, Temp_Relay_High, Temp_Outmax_High, Temp_Relay_Low, Temp_Outmax_Low, Temp_OR, Temp_Set, Temp_Set_Direction, Temp_Period, Temp_P, Temp_I, Temp_D FROM TSensor');
$count = 0;
while ($row = $results->fetchArray()) {
    $sensor_t_id[$count] = $row[0];
    $sensor_t_name[$count] = $row[1];
    $sensor_t_pin[$count] = $row[2];
    $sensor_t_device[$count] = $row[3];
    $sensor_t_period[$count] = $row[4];
    $sensor_t_premeasure_relay[$count] = $row[5];
    $sensor_t_premeasure_dur[$count] = $row[6];
    $sensor_t_activated[$count] = $row[7];
    $sensor_t_graph[$count] = $row[8];
    $sensor_t_yaxis_relay_min[$count] = $row[9];
    $sensor_t_yaxis_relay_max[$count] = $row[10];
    $sensor_t_yaxis_relay_tics[$count] = $row[11];
    $sensor_t_yaxis_relay_mtics[$count] = $row[12];
    $sensor_t_yaxis_temp_min[$count] = $row[13];
    $sensor_t_yaxis_temp_max[$count] = $row[14];
    $sensor_t_yaxis_temp_tics[$count] = $row[15];
    $sensor_t_yaxis_temp_mtics[$count] = $row[16];
    $pid_t_temp_relay_high[$count] = $row[17];
    $pid_t_temp_outmax_high[$count] = $row[18];
    $pid_t_temp_relay_low[$count] = $row[19];
    $pid_t_temp_outmax_low[$count] = $row[20];
    $pid_t_temp_or[$count] = $row[21];
    $pid_t_temp_set[$count] = $row[22];
    $pid_t_temp_set_dir[$count] = $row[23];
    $pid_t_temp_period[$count] = $row[24];
    $pid_t_temp_p[$count] = $row[25];
    $pid_t_temp_i[$count] = $row[26];
    $pid_t_temp_d[$count] = $row[27];
    $count++;
}
if (!isset($sensor_t_id)) $sensor_t_id = [];
if (!isset($sensor_t_graph)) $sensor_t_graph = [];


unset($sensor_ht_id);
$results = $db->query('SELECT Id, Name, Pin, Device, Period, Pre_Measure_Relay, Pre_Measure_Dur, Activated, Graph,  YAxis_Relay_Min, YAxis_Relay_Max, YAxis_Relay_Tics, YAxis_Relay_MTics, YAxis_Temp_Min, YAxis_Temp_Max, YAxis_Temp_Tics, YAxis_Temp_MTics, YAxis_Hum_Min, YAxis_Hum_Max, YAxis_Hum_Tics, YAxis_Hum_MTics, Temp_Relay_High, Temp_Outmax_High, Temp_Relay_Low, Temp_Outmax_Low, Temp_OR, Temp_Set, Temp_Set_Direction, Temp_Period, Temp_P, Temp_I, Temp_D, Hum_Relay_High, Hum_Outmax_High, Hum_Relay_Low, Hum_Outmax_Low, Hum_OR, Hum_Set, Hum_Set_Direction, Hum_Period, Hum_P, Hum_I, Hum_D FROM HTSensor');
$count = 0;
while ($row = $results->fetchArray()) {
    $sensor_ht_id[$count] = $row[0];
    $sensor_ht_name[$count] = $row[1];
    $sensor_ht_pin[$count] = $row[2];
    $sensor_ht_device[$count] = $row[3];
    $sensor_ht_period[$count] = $row[4];
    $sensor_ht_premeasure_relay[$count] = $row[5];
    $sensor_ht_premeasure_dur[$count] = $row[6];
    $sensor_ht_activated[$count] = $row[7];
    $sensor_ht_graph[$count] = $row[8];
    $sensor_ht_yaxis_relay_min[$count] = $row[9];
    $sensor_ht_yaxis_relay_max[$count] = $row[10];
    $sensor_ht_yaxis_relay_tics[$count] = $row[11];
    $sensor_ht_yaxis_relay_mtics[$count] = $row[12];
    $sensor_ht_yaxis_temp_min[$count] = $row[13];
    $sensor_ht_yaxis_temp_max[$count] = $row[14];
    $sensor_ht_yaxis_temp_tics[$count] = $row[15];
    $sensor_ht_yaxis_temp_mtics[$count] = $row[16];
    $sensor_ht_yaxis_hum_min[$count] = $row[17];
    $sensor_ht_yaxis_hum_max[$count] = $row[18];
    $sensor_ht_yaxis_hum_tics[$count] = $row[19];
    $sensor_ht_yaxis_hum_mtics[$count] = $row[20];
    $pid_ht_temp_relay_high[$count] = $row[21];
    $pid_ht_temp_outmax_high[$count] = $row[22];
    $pid_ht_temp_relay_low[$count] = $row[23];
    $pid_ht_temp_outmax_low[$count] = $row[24];
    $pid_ht_temp_or[$count] = $row[25];
    $pid_ht_temp_set[$count] = $row[26];
    $pid_ht_temp_set_dir[$count] = $row[27];
    $pid_ht_temp_period[$count] = $row[28];
    $pid_ht_temp_p[$count] = $row[29];
    $pid_ht_temp_i[$count] = $row[30];
    $pid_ht_temp_d[$count] = $row[31];
    $pid_ht_hum_relay_high[$count] = $row[32];
    $pid_ht_hum_outmax_high[$count] = $row[33];
    $pid_ht_hum_relay_low[$count] = $row[34];
    $pid_ht_hum_outmax_low[$count] = $row[35];
    $pid_ht_hum_or[$count] = $row[36];
    $pid_ht_hum_set[$count] = $row[37];
    $pid_ht_hum_set_dir[$count] = $row[38];
    $pid_ht_hum_period[$count] = $row[39];
    $pid_ht_hum_p[$count] = $row[40];
    $pid_ht_hum_i[$count] = $row[41];
    $pid_ht_hum_d[$count] = $row[42];
    $count++;
}
if (!isset($sensor_ht_id)) $sensor_ht_id = [];
if (!isset($sensor_ht_graph)) $sensor_ht_graph = [];


unset($sensor_co2_id);
$results = $db->query('SELECT Id, Name, Pin, Device, Period, Pre_Measure_Relay, Pre_Measure_Dur, Activated, Graph,  YAxis_Relay_Min, YAxis_Relay_Max, YAxis_Relay_Tics, YAxis_Relay_MTics, YAxis_CO2_Min, YAxis_CO2_Max, YAxis_CO2_Tics, YAxis_CO2_MTics, CO2_Relay_High, CO2_Outmax_High, CO2_Relay_Low, CO2_Outmax_Low, CO2_OR, CO2_Set, CO2_Set_Direction, CO2_Period, CO2_P, CO2_I, CO2_D FROM CO2Sensor');
$count = 0;
while ($row = $results->fetchArray()) {
    $sensor_co2_id[$count] = $row[0];
    $sensor_co2_name[$count] = $row[1];
    $sensor_co2_pin[$count] = $row[2];
    $sensor_co2_device[$count] = $row[3];
    $sensor_co2_period[$count] = $row[4];
    $sensor_co2_premeasure_relay[$count] = $row[5];
    $sensor_co2_premeasure_dur[$count] = $row[6];
    $sensor_co2_activated[$count] = $row[7];
    $sensor_co2_graph[$count] = $row[8];
    $sensor_co2_yaxis_relay_min[$count] = $row[9];
    $sensor_co2_yaxis_relay_max[$count] = $row[10];
    $sensor_co2_yaxis_relay_tics[$count] = $row[11];
    $sensor_co2_yaxis_relay_mtics[$count] = $row[12];
    $sensor_co2_yaxis_co2_min[$count] = $row[13];
    $sensor_co2_yaxis_co2_max[$count] = $row[14];
    $sensor_co2_yaxis_co2_tics[$count] = $row[15];
    $sensor_co2_yaxis_co2_mtics[$count] = $row[16];
    $pid_co2_relay_high[$count] = $row[17];
    $pid_co2_outmax_high[$count] = $row[18];
    $pid_co2_relay_low[$count] = $row[19];
    $pid_co2_outmax_low[$count] = $row[20];
    $pid_co2_or[$count] = $row[21];
    $pid_co2_set[$count] = $row[22];
    $pid_co2_set_dir[$count] = $row[23];
    $pid_co2_period[$count] = $row[24];
    $pid_co2_p[$count] = $row[25];
    $pid_co2_i[$count] = $row[26];
    $pid_co2_d[$count] = $row[27];
    $count++;
}
if (!isset($sensor_co2_id)) $sensor_co2_id = [];
if (!isset($sensor_co2_graph)) $sensor_co2_graph = [];

unset($sensor_press_id);
$results = $db->query('SELECT Id, Name, Pin, Device, Period, Pre_Measure_Relay, Pre_Measure_Dur, Activated, Graph, YAxis_Relay_Min, YAxis_Relay_Max, YAxis_Relay_Tics, YAxis_Relay_MTics, YAxis_Temp_Min, YAxis_Temp_Max, YAxis_Temp_Tics, YAxis_Temp_MTics, YAxis_Press_Min, YAxis_Press_Max, YAxis_Press_Tics, YAxis_Press_MTics, Temp_Relay_High, Temp_Outmax_High, Temp_Relay_Low, Temp_Outmax_Low, Temp_OR, Temp_Set, Temp_Set_Direction, Temp_Period, Temp_P, Temp_I, Temp_D, Press_Relay_High, Press_Outmax_High, Press_Relay_Low, Press_Outmax_Low, Press_OR, Press_Set, Press_Set_Direction, Press_Period, Press_P, Press_I, Press_D FROM PressSensor');
$count = 0;
while ($row = $results->fetchArray()) {
    $sensor_press_id[$count] = $row[0];
    $sensor_press_name[$count] = $row[1];
    $sensor_press_pin[$count] = $row[2];
    $sensor_press_device[$count] = $row[3];
    $sensor_press_period[$count] = $row[4];
    $sensor_press_premeasure_relay[$count] = $row[5];
    $sensor_press_premeasure_dur[$count] = $row[6];
    $sensor_press_activated[$count] = $row[7];
    $sensor_press_graph[$count] = $row[8];
    $sensor_press_yaxis_relay_min[$count] = $row[9];
    $sensor_press_yaxis_relay_max[$count] = $row[10];
    $sensor_press_yaxis_relay_tics[$count] = $row[11];
    $sensor_press_yaxis_relay_mtics[$count] = $row[12];
    $sensor_press_yaxis_temp_min[$count] = $row[13];
    $sensor_press_yaxis_temp_max[$count] = $row[14];
    $sensor_press_yaxis_temp_tics[$count] = $row[15];
    $sensor_press_yaxis_temp_mtics[$count] = $row[16];
    $sensor_press_yaxis_press_min[$count] = $row[17];
    $sensor_press_yaxis_press_max[$count] = $row[18];
    $sensor_press_yaxis_press_tics[$count] = $row[19];
    $sensor_press_yaxis_press_mtics[$count] = $row[20];
    $pid_press_temp_relay_high[$count] = $row[21];
    $pid_press_temp_outmax_high[$count] = $row[22];
    $pid_press_temp_relay_low[$count] = $row[23];
    $pid_press_temp_outmax_low[$count] = $row[24];
    $pid_press_temp_or[$count] = $row[25];
    $pid_press_temp_set[$count] = $row[26];
    $pid_press_temp_set_dir[$count] = $row[27];
    $pid_press_temp_period[$count] = $row[28];
    $pid_press_temp_p[$count] = $row[29];
    $pid_press_temp_i[$count] = $row[30];
    $pid_press_temp_d[$count] = $row[31];
    $pid_press_press_relay_high[$count] = $row[32];
    $pid_press_press_outmax_high[$count] = $row[33];
    $pid_press_press_relay_low[$count] = $row[34];
    $pid_press_press_outmax_low[$count] = $row[35];
    $pid_press_press_or[$count] = $row[36];
    $pid_press_press_set[$count] = $row[37];
    $pid_press_press_set_dir[$count] = $row[38];
    $pid_press_press_period[$count] = $row[39];
    $pid_press_press_p[$count] = $row[40];
    $pid_press_press_i[$count] = $row[41];
    $pid_press_press_d[$count] = $row[42];
    $count++;
}
if (!isset($sensor_press_id)) $sensor_press_id = [];
if (!isset($sensor_press_graph)) $sensor_press_graph = [];


// conditional statements
unset($conditional_t_id);
for ($n = 0; $n < count($sensor_t_id); $n++) {
    $results = $db->query('SELECT Id, Name, State, Sensor, Direction, Setpoint, Period, Relay, Relay_State, Relay_Seconds_On FROM TSensorConditional WHERE Sensor=' . $n);
    $count = 0;
    while ($row = $results->fetchArray()) {
        $conditional_t_id[$n][$count] = $row[0];
        $conditional_t_name[$n][$count] = $row[1];
        $conditional_t_state[$n][$count] = $row[2];
        $conditional_t_sensor[$n][$count] = $row[3];
        $conditional_t_direction[$n][$count] = $row[4];
        $conditional_t_setpoint[$n][$count] = $row[5];
        $conditional_t_period[$n][$count] = $row[6];
        $conditional_t_relay[$n][$count] = $row[7];
        $conditional_t_relay_state[$n][$count] = $row[8];
        $conditional_t_relay_seconds_on[$n][$count] = $row[9];
        $count++;
    }
}

unset($conditional_ht_id);
for ($n = 0; $n < count($sensor_ht_id); $n++) {
    $results = $db->query('SELECT Id, Name, State, Sensor, Condition, Direction, Setpoint, Period, Relay, Relay_State, Relay_Seconds_On FROM HTSensorConditional WHERE Sensor=' . $n);
    $count = 0;
    while ($row = $results->fetchArray()) {
        $conditional_ht_id[$n][$count] = $row[0];
        $conditional_ht_name[$n][$count] = $row[1];
        $conditional_ht_state[$n][$count] = $row[2];
        $conditional_ht_sensor[$n][$count] = $row[3];
        $conditional_ht_condition[$n][$count] = $row[4];
        $conditional_ht_direction[$n][$count] = $row[5];
        $conditional_ht_setpoint[$n][$count] = $row[6];
        $conditional_ht_period[$n][$count] = $row[7];
        $conditional_ht_relay[$n][$count] = $row[8];
        $conditional_ht_relay_state[$n][$count] = $row[9];
        $conditional_ht_relay_seconds_on[$n][$count] = $row[10];
        $count++;
    }
}

unset($conditional_co2_id);
for ($n = 0; $n < count($sensor_co2_id); $n++) {
    $results = $db->query('SELECT Id, Name, State, Sensor, Direction, Setpoint, Period, Relay, Relay_State, Relay_Seconds_On FROM CO2SensorConditional WHERE Sensor=' . $n);
    $count = 0;
    while ($row = $results->fetchArray()) {
        $conditional_co2_id[$n][$count] = $row[0];
        $conditional_co2_name[$n][$count] = $row[1];
        $conditional_co2_state[$n][$count] = $row[2];
        $conditional_co2_sensor[$n][$count] = $row[3];
        $conditional_co2_direction[$n][$count] = $row[4];
        $conditional_co2_setpoint[$n][$count] = $row[5];
        $conditional_co2_period[$n][$count] = $row[6];
        $conditional_co2_relay[$n][$count] = $row[7];
        $conditional_co2_relay_state[$n][$count] = $row[8];
        $conditional_co2_relay_seconds_on[$n][$count] = $row[9];
        $count++;
    }
}

unset($conditional_press_id);
for ($n = 0; $n < count($sensor_press_id); $n++) {
    $results = $db->query('SELECT Id, Name, State, Sensor, Condition, Direction, Setpoint, Period, Relay, Relay_State, Relay_Seconds_On FROM PressSensorConditional WHERE Sensor=' . $n);
    $count = 0;
    while ($row = $results->fetchArray()) {
        $conditional_press_id[$n][$count] = $row[0];
        $conditional_press_name[$n][$count] = $row[1];
        $conditional_press_state[$n][$count] = $row[2];
        $conditional_press_sensor[$n][$count] = $row[3];
        $conditional_press_condition[$n][$count] = $row[4];
        $conditional_press_direction[$n][$count] = $row[5];
        $conditional_press_setpoint[$n][$count] = $row[6];
        $conditional_press_period[$n][$count] = $row[7];
        $conditional_press_relay[$n][$count] = $row[8];
        $conditional_press_relay_state[$n][$count] = $row[9];
        $conditional_press_relay_seconds_on[$n][$count] = $row[10];
        $count++;
    }
}


// Sort sensor Presets
$sensor_t_preset = [];
$results = $db->query('SELECT Id FROM TSensorPreset');
while ($row = $results->fetchArray()) {
    $sensor_t_preset[] = $row[0];
}
sort($sensor_t_preset, SORT_NATURAL | SORT_FLAG_CASE);

$sensor_ht_preset = [];
$results = $db->query('SELECT Id FROM HTSensorPreset');
while ($row = $results->fetchArray()) {
    $sensor_ht_preset[] = $row[0];
}
sort($sensor_ht_preset, SORT_NATURAL | SORT_FLAG_CASE);

$sensor_co2_preset = [];
$results = $db->query('SELECT Id FROM CO2SensorPreset');
while ($row = $results->fetchArray()) {
    $sensor_co2_preset[] = $row[0];
}
sort($sensor_co2_preset, SORT_NATURAL | SORT_FLAG_CASE);

$sensor_press_preset = [];
$results = $db->query('SELECT Id FROM CO2SensorPreset');
while ($row = $results->fetchArray()) {
    $sensor_press_preset[] = $row[0];
}
sort($sensor_press_preset, SORT_NATURAL | SORT_FLAG_CASE);

unset($timer_id);
$results = $db->query('SELECT Id, Name, State, Relay, DurationOn, DurationOff FROM Timers');
$count = 0;
while ($row = $results->fetchArray()) {
    $timer_id[$count] = $row[0];
    $timer_name[$count] = $row[1];
    $timer_state[$count] = $row[2];
    $timer_relay[$count] = $row[3];
    $timer_duration_on[$count] = $row[4];
    $timer_duration_off[$count] = $row[5];
    $count++;
}
if (!isset($timer_id)) $timer_id = [];


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


$results = $db->query('SELECT Relay, Timestamp, Display_Last, Cmd_Pre, Cmd_Post, Extra_Parameters FROM CameraStill');
while ($row = $results->fetchArray()) {
    $still_relay = $row[0];
    $still_timestamp = $row[1];
    $still_display_last = $row[2];
    $still_cmd_pre = $row[3];
    $still_cmd_post = $row[4];
    $still_extra_parameters = $row[5];
}

$results = $db->query('SELECT Relay, Cmd_Pre, Cmd_Post, Extra_Parameters FROM CameraStream');
while ($row = $results->fetchArray()) {
    $stream_relay = $row[0];
    $stream_cmd_pre = $row[1];
    $stream_cmd_post = $row[2];
    $stream_extra_parameters = $row[3];
}

$results = $db->query('SELECT Relay, Path, Prefix, File_Timestamp, Display_Last, Cmd_Pre, Cmd_Post, Extra_Parameters FROM CameraTimelapse');
while ($row = $results->fetchArray()) {
    $timelapse_relay = $row[0];
    $timelapse_path = $row[1];
    $timelapse_prefix = $row[2];
    $timelapse_timestamp = $row[3];
    $timelapse_display_last = $row[4];
    $timelapse_cmd_pre = $row[5];
    $timelapse_cmd_post = $row[6];
    $timelapse_extra_parameters = $row[7];
}

$results = $db->query('SELECT Refresh_Time FROM Misc');
while ($row = $results->fetchArray()) {
    $refresh_time = $row[0];
}
