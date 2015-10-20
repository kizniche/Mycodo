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
$udb = new SQLite3($user_db);
$ndb = new SQLite3($note_db);


$results = $udb->query('SELECT user_name, user_email FROM users');
$i = 0;
while ($row = $results->fetchArray()) {
    $user_name[$i] = $row[0];
    $user_email[$i] = $row[1];
    $i++;
}


unset($relay_id);
$results = $db->query('SELECT Id, Name, Pin, Amps, Trigger, Start_State FROM Relays');
$i = 0;
while ($row = $results->fetchArray()) {
    $relay_id[$i] = $row[0];
    $relay_name[$i] = $row[1];
    $relay_pin[$i] = $row[2];
    $relay_amps[$i] = $row[3];
    $relay_trigger[$i] = $row[4];
    $relay_start_state[$i] = $row[5];
    $i++;
}
if (!isset($relay_id)) $relay_id = [];


// conditional statements
unset($conditional_relay_id);
$results = $db->query('SELECT Id, Name, If_Relay, If_Action, If_Duration, Sel_Relay, Do_Relay, Do_Action, Do_Duration, Sel_Command, Do_Command, Sel_Notify, Do_Notify FROM RelayConditional');
$i = 0;
while ($row = $results->fetchArray()) {
    $conditional_relay_id[$i] = $row[0];
    $conditional_relay_name[$i] = $row[1];
    $conditional_relay_ifrelay[$i] = $row[2];
    $conditional_relay_ifaction[$i] = $row[3];
    $conditional_relay_ifduration[$i] = $row[4];
    $conditional_relay_sel_relay[$i] = $row[5];
    $conditional_relay_dorelay[$i] = $row[6];
    $conditional_relay_doaction[$i] = $row[7];
    $conditional_relay_doduration[$i] = $row[8];
    $conditional_relay_sel_command[$i] = $row[9];
    $conditional_relay_command[$i] = str_replace("''","'",$row[10]);
    $conditional_relay_sel_notify[$i] = $row[11];
    $conditional_relay_notify[$i] = $row[12];
    $i++;
}
if (!isset($conditional_relay_id)) $conditional_relay_id = [];


unset($sensor_t_id);
$results = $db->query('SELECT Id, Name, Pin, Device, Period, Pre_Measure_Relay, Pre_Measure_Dur, Activated, Graph, YAxis_Relay_Min, YAxis_Relay_Max, YAxis_Relay_Tics, YAxis_Relay_MTics, YAxis_Temp_Min, YAxis_Temp_Max, YAxis_Temp_Tics, YAxis_Temp_MTics, Temp_Relays_Up, Temp_Relays_Down, Temp_Relay_High, Temp_Outmin_High, Temp_Outmax_High, Temp_Relay_Low, Temp_Outmin_Low, Temp_Outmax_Low, Temp_OR, Temp_Set, Temp_Set_Direction, Temp_Period, Temp_P, Temp_I, Temp_D FROM TSensor');
$i = 0;
while ($row = $results->fetchArray()) {
    $sensor_t_id[$i] = $row[0];
    $sensor_t_name[$i] = $row[1];
    $sensor_t_pin[$i] = $row[2];
    $sensor_t_device[$i] = $row[3];
    $sensor_t_period[$i] = $row[4];
    $sensor_t_premeasure_relay[$i] = $row[5];
    $sensor_t_premeasure_dur[$i] = $row[6];
    $sensor_t_activated[$i] = $row[7];
    $sensor_t_graph[$i] = $row[8];
    $sensor_t_yaxis_relay_min[$i] = $row[9];
    $sensor_t_yaxis_relay_max[$i] = $row[10];
    $sensor_t_yaxis_relay_tics[$i] = $row[11];
    $sensor_t_yaxis_relay_mtics[$i] = $row[12];
    $sensor_t_yaxis_temp_min[$i] = $row[13];
    $sensor_t_yaxis_temp_max[$i] = $row[14];
    $sensor_t_yaxis_temp_tics[$i] = $row[15];
    $sensor_t_yaxis_temp_mtics[$i] = $row[16];
    $sensor_t_temp_relays_up[$i] = $row[17];
    $sensor_t_temp_relays_down[$i] = $row[18];
    $pid_t_temp_relay_high[$i] = $row[19];
    $pid_t_temp_outmin_high[$i] = $row[20];
    $pid_t_temp_outmax_high[$i] = $row[21];
    $pid_t_temp_relay_low[$i] = $row[22];
    $pid_t_temp_outmin_low[$i] = $row[23];
    $pid_t_temp_outmax_low[$i] = $row[24];
    $pid_t_temp_or[$i] = $row[25];
    $pid_t_temp_set[$i] = $row[26];
    $pid_t_temp_set_dir[$i] = $row[27];
    $pid_t_temp_period[$i] = $row[28];
    $pid_t_temp_p[$i] = $row[29];
    $pid_t_temp_i[$i] = $row[30];
    $pid_t_temp_d[$i] = $row[31];
    $i++;
}
if (!isset($sensor_t_id)) $sensor_t_id = [];
if (!isset($sensor_t_graph)) $sensor_t_graph = [];


unset($sensor_ht_id);
$results = $db->query('SELECT Id, Name, Pin, Device, Period, Pre_Measure_Relay, Pre_Measure_Dur, Activated, Graph, Verify_Pin, Verify_Temp, Verify_Temp_Notify, Verify_Temp_Stop, Verify_Hum, Verify_Hum_Notify, Verify_Hum_Stop, Verify_Notify_Email, YAxis_Relay_Min, YAxis_Relay_Max, YAxis_Relay_Tics, YAxis_Relay_MTics, YAxis_Temp_Min, YAxis_Temp_Max, YAxis_Temp_Tics, YAxis_Temp_MTics, YAxis_Hum_Min, YAxis_Hum_Max, YAxis_Hum_Tics, YAxis_Hum_MTics, Temp_Relays_Up, Temp_Relays_Down, Temp_Relay_High, Temp_Outmin_High, Temp_Outmax_High, Temp_Relay_Low, Temp_Outmin_Low, Temp_Outmax_Low, Temp_OR, Temp_Set, Temp_Set_Direction, Temp_Period, Temp_P, Temp_I, Temp_D, Hum_Relays_Up, Hum_Relays_Down, Hum_Relay_High, Hum_Outmin_High, Hum_Outmax_High, Hum_Relay_Low, Hum_Outmin_Low, Hum_Outmax_Low, Hum_OR, Hum_Set, Hum_Set_Direction, Hum_Period, Hum_P, Hum_I, Hum_D FROM HTSensor');
$i = 0;
while ($row = $results->fetchArray()) {
    $sensor_ht_id[$i] = $row[0];
    $sensor_ht_name[$i] = $row[1];
    $sensor_ht_pin[$i] = $row[2];
    $sensor_ht_device[$i] = $row[3];
    $sensor_ht_period[$i] = $row[4];
    $sensor_ht_premeasure_relay[$i] = $row[5];
    $sensor_ht_premeasure_dur[$i] = $row[6];
    $sensor_ht_activated[$i] = $row[7];
    $sensor_ht_graph[$i] = $row[8];
    $sensor_ht_verify_pin[$i] = $row[9];
    $sensor_ht_verify_temp[$i] = $row[10];
    $sensor_ht_verify_temp_notify[$i] = $row[11];
    $sensor_ht_verify_temp_stop[$i] = $row[12];
    $sensor_ht_verify_hum[$i] = $row[13];
    $sensor_ht_verify_hum_notify[$i] = $row[14];
    $sensor_ht_verify_hum_stop[$i] = $row[15];
    $sensor_ht_verify_email[$i] = $row[16];
    $sensor_ht_yaxis_relay_min[$i] = $row[17];
    $sensor_ht_yaxis_relay_max[$i] = $row[18];
    $sensor_ht_yaxis_relay_tics[$i] = $row[19];
    $sensor_ht_yaxis_relay_mtics[$i] = $row[20];
    $sensor_ht_yaxis_temp_min[$i] = $row[21];
    $sensor_ht_yaxis_temp_max[$i] = $row[22];
    $sensor_ht_yaxis_temp_tics[$i] = $row[23];
    $sensor_ht_yaxis_temp_mtics[$i] = $row[24];
    $sensor_ht_yaxis_hum_min[$i] = $row[25];
    $sensor_ht_yaxis_hum_max[$i] = $row[26];
    $sensor_ht_yaxis_hum_tics[$i] = $row[27];
    $sensor_ht_yaxis_hum_mtics[$i] = $row[28];
    $sensor_ht_temp_relays_up[$i] = $row[29];
    $sensor_ht_temp_relays_down[$i] = $row[30];
    $pid_ht_temp_relay_high[$i] = $row[31];
    $pid_ht_temp_outmin_high[$i] = $row[32];
    $pid_ht_temp_outmax_high[$i] = $row[33];
    $pid_ht_temp_relay_low[$i] = $row[34];
    $pid_ht_temp_outmin_low[$i] = $row[35];
    $pid_ht_temp_outmax_low[$i] = $row[36];
    $pid_ht_temp_or[$i] = $row[37];
    $pid_ht_temp_set[$i] = $row[38];
    $pid_ht_temp_set_dir[$i] = $row[39];
    $pid_ht_temp_period[$i] = $row[40];
    $pid_ht_temp_p[$i] = $row[41];
    $pid_ht_temp_i[$i] = $row[42];
    $pid_ht_temp_d[$i] = $row[43];
    $sensor_ht_hum_relays_up[$i] = $row[44];
    $sensor_ht_hum_relays_down[$i] = $row[45];
    $pid_ht_hum_relay_high[$i] = $row[46];
    $pid_ht_hum_outmin_high[$i] = $row[47];
    $pid_ht_hum_outmax_high[$i] = $row[48];
    $pid_ht_hum_relay_low[$i] = $row[49];
    $pid_ht_hum_outmin_low[$i] = $row[50];
    $pid_ht_hum_outmax_low[$i] = $row[51];
    $pid_ht_hum_or[$i] = $row[52];
    $pid_ht_hum_set[$i] = $row[53];
    $pid_ht_hum_set_dir[$i] = $row[54];
    $pid_ht_hum_period[$i] = $row[55];
    $pid_ht_hum_p[$i] = $row[56];
    $pid_ht_hum_i[$i] = $row[57];
    $pid_ht_hum_d[$i] = $row[58];
    $i++;
}
if (!isset($sensor_ht_id)) $sensor_ht_id = [];
if (!isset($sensor_ht_graph)) $sensor_ht_graph = [];


unset($sensor_co2_id);
$results = $db->query('SELECT Id, Name, Pin, Device, Period, Pre_Measure_Relay, Pre_Measure_Dur, Activated, Graph,  YAxis_Relay_Min, YAxis_Relay_Max, YAxis_Relay_Tics, YAxis_Relay_MTics, YAxis_CO2_Min, YAxis_CO2_Max, YAxis_CO2_Tics, YAxis_CO2_MTics, CO2_Relays_Up, CO2_Relays_Down, CO2_Relay_High, CO2_Outmin_High, CO2_Outmax_High, CO2_Relay_Low, CO2_Outmin_Low, CO2_Outmax_Low, CO2_OR, CO2_Set, CO2_Set_Direction, CO2_Period, CO2_P, CO2_I, CO2_D FROM CO2Sensor');
$i = 0;
while ($row = $results->fetchArray()) {
    $sensor_co2_id[$i] = $row[0];
    $sensor_co2_name[$i] = $row[1];
    $sensor_co2_pin[$i] = $row[2];
    $sensor_co2_device[$i] = $row[3];
    $sensor_co2_period[$i] = $row[4];
    $sensor_co2_premeasure_relay[$i] = $row[5];
    $sensor_co2_premeasure_dur[$i] = $row[6];
    $sensor_co2_activated[$i] = $row[7];
    $sensor_co2_graph[$i] = $row[8];
    $sensor_co2_yaxis_relay_min[$i] = $row[9];
    $sensor_co2_yaxis_relay_max[$i] = $row[10];
    $sensor_co2_yaxis_relay_tics[$i] = $row[11];
    $sensor_co2_yaxis_relay_mtics[$i] = $row[12];
    $sensor_co2_yaxis_co2_min[$i] = $row[13];
    $sensor_co2_yaxis_co2_max[$i] = $row[14];
    $sensor_co2_yaxis_co2_tics[$i] = $row[15];
    $sensor_co2_yaxis_co2_mtics[$i] = $row[16];
    $sensor_co2_relays_up[$i] = $row[17];
    $sensor_co2_relays_down[$i] = $row[18];
    $pid_co2_relay_high[$i] = $row[19];
    $pid_co2_outmin_high[$i] = $row[20];
    $pid_co2_outmax_high[$i] = $row[21];
    $pid_co2_relay_low[$i] = $row[22];
    $pid_co2_outmin_low[$i] = $row[23];
    $pid_co2_outmax_low[$i] = $row[24];
    $pid_co2_or[$i] = $row[25];
    $pid_co2_set[$i] = $row[26];
    $pid_co2_set_dir[$i] = $row[27];
    $pid_co2_period[$i] = $row[28];
    $pid_co2_p[$i] = $row[29];
    $pid_co2_i[$i] = $row[30];
    $pid_co2_d[$i] = $row[31];
    $i++;
}
if (!isset($sensor_co2_id)) $sensor_co2_id = [];
if (!isset($sensor_co2_graph)) $sensor_co2_graph = [];

unset($sensor_press_id);
$results = $db->query('SELECT Id, Name, Pin, Device, Period, Pre_Measure_Relay, Pre_Measure_Dur, Activated, Graph, YAxis_Relay_Min, YAxis_Relay_Max, YAxis_Relay_Tics, YAxis_Relay_MTics, YAxis_Temp_Min, YAxis_Temp_Max, YAxis_Temp_Tics, YAxis_Temp_MTics, YAxis_Press_Min, YAxis_Press_Max, YAxis_Press_Tics, YAxis_Press_MTics, Temp_Relays_Up, Temp_Relays_Down, Temp_Relay_High, Temp_Outmin_High, Temp_Outmax_High, Temp_Relay_Low, Temp_Outmin_Low, Temp_Outmax_Low, Temp_OR, Temp_Set, Temp_Set_Direction, Temp_Period, Temp_P, Temp_I, Temp_D, Press_Relays_Up, Press_Relays_Down, Press_Relay_High, Press_Outmin_High, Press_Outmax_High, Press_Relay_Low, Press_Outmin_Low, Press_Outmax_Low, Press_OR, Press_Set, Press_Set_Direction, Press_Period, Press_P, Press_I, Press_D FROM PressSensor');
$i = 0;
while ($row = $results->fetchArray()) {
    $sensor_press_id[$i] = $row[0];
    $sensor_press_name[$i] = $row[1];
    $sensor_press_pin[$i] = $row[2];
    $sensor_press_device[$i] = $row[3];
    $sensor_press_period[$i] = $row[4];
    $sensor_press_premeasure_relay[$i] = $row[5];
    $sensor_press_premeasure_dur[$i] = $row[6];
    $sensor_press_activated[$i] = $row[7];
    $sensor_press_graph[$i] = $row[8];
    $sensor_press_yaxis_relay_min[$i] = $row[9];
    $sensor_press_yaxis_relay_max[$i] = $row[10];
    $sensor_press_yaxis_relay_tics[$i] = $row[11];
    $sensor_press_yaxis_relay_mtics[$i] = $row[12];
    $sensor_press_yaxis_temp_min[$i] = $row[13];
    $sensor_press_yaxis_temp_max[$i] = $row[14];
    $sensor_press_yaxis_temp_tics[$i] = $row[15];
    $sensor_press_yaxis_temp_mtics[$i] = $row[16];
    $sensor_press_yaxis_press_min[$i] = $row[17];
    $sensor_press_yaxis_press_max[$i] = $row[18];
    $sensor_press_yaxis_press_tics[$i] = $row[19];
    $sensor_press_yaxis_press_mtics[$i] = $row[20];
    $sensor_press_temp_relays_up[$i] = $row[21];
    $sensor_press_temp_relays_down[$i] = $row[22];
    $pid_press_temp_relay_high[$i] = $row[23];
    $pid_press_temp_outmin_high[$i] = $row[24];
    $pid_press_temp_outmax_high[$i] = $row[25];
    $pid_press_temp_relay_low[$i] = $row[26];
    $pid_press_temp_outmin_low[$i] = $row[27];
    $pid_press_temp_outmax_low[$i] = $row[28];
    $pid_press_temp_or[$i] = $row[29];
    $pid_press_temp_set[$i] = $row[30];
    $pid_press_temp_set_dir[$i] = $row[31];
    $pid_press_temp_period[$i] = $row[32];
    $pid_press_temp_p[$i] = $row[33];
    $pid_press_temp_i[$i] = $row[34];
    $pid_press_temp_d[$i] = $row[35];
    $sensor_press_press_relays_up[$i] = $row[36];
    $sensor_press_press_relays_down[$i] = $row[37];
    $pid_press_press_relay_high[$i] = $row[38];
    $pid_press_press_outmin_high[$i] = $row[39];
    $pid_press_press_outmax_high[$i] = $row[40];
    $pid_press_press_relay_low[$i] = $row[41];
    $pid_press_press_outmin_low[$i] = $row[42];
    $pid_press_press_outmax_low[$i] = $row[43];
    $pid_press_press_or[$i] = $row[44];
    $pid_press_press_set[$i] = $row[45];
    $pid_press_press_set_dir[$i] = $row[46];
    $pid_press_press_period[$i] = $row[47];
    $pid_press_press_p[$i] = $row[48];
    $pid_press_press_i[$i] = $row[49];
    $pid_press_press_d[$i] = $row[50];
    $i++;
}
if (!isset($sensor_press_id)) $sensor_press_id = [];
if (!isset($sensor_press_graph)) $sensor_press_graph = [];


// conditional statements
unset($conditional_t_id);
for ($n = 0; $n < count($sensor_t_id); $n++) {
    $results = $db->query('SELECT Id, Name, State, Sensor, Direction, Setpoint, Period, Sel_Relay, Relay, Relay_State, Relay_Seconds_On, Sel_Command, Do_Command, Sel_Notify, Do_Notify FROM TSensorConditional WHERE Sensor=' . $n);
    $i = 0;
    while ($row = $results->fetchArray()) {
        $conditional_t_id[$n][$i] = $row[0];
        $conditional_t_name[$n][$i] = $row[1];
        $conditional_t_state[$n][$i] = $row[2];
        $conditional_t_sensor[$n][$i] = $row[3];
        $conditional_t_direction[$n][$i] = $row[4];
        $conditional_t_setpoint[$n][$i] = $row[5];
        $conditional_t_period[$n][$i] = $row[6];
        $conditional_t_sel_relay[$n][$i] = $row[7];
        $conditional_t_relay[$n][$i] = $row[8];
        $conditional_t_relay_state[$n][$i] = $row[9];
        $conditional_t_relay_seconds_on[$n][$i] = $row[10];
        $conditional_t_sel_command[$n][$i] = $row[11];
        $conditional_t_command[$n][$i] = str_replace("''","'",$row[12]);
        $conditional_t_sel_notify[$n][$i] = $row[13];
        $conditional_t_notify[$n][$i] = $row[14];
        $i++;
    }
}

unset($conditional_ht_id);
for ($n = 0; $n < count($sensor_ht_id); $n++) {
    $results = $db->query('SELECT Id, Name, State, Sensor, Condition, Direction, Setpoint, Period, Sel_Relay, Relay, Relay_State, Relay_Seconds_On, Sel_Command, Do_Command, Sel_Notify, Do_Notify FROM HTSensorConditional WHERE Sensor=' . $n);
    $i = 0;
    while ($row = $results->fetchArray()) {
        $conditional_ht_id[$n][$i] = $row[0];
        $conditional_ht_name[$n][$i] = $row[1];
        $conditional_ht_state[$n][$i] = $row[2];
        $conditional_ht_sensor[$n][$i] = $row[3];
        $conditional_ht_condition[$n][$i] = $row[4];
        $conditional_ht_direction[$n][$i] = $row[5];
        $conditional_ht_setpoint[$n][$i] = $row[6];
        $conditional_ht_period[$n][$i] = $row[7];
        $conditional_ht_sel_relay[$n][$i] = $row[8];
        $conditional_ht_relay[$n][$i] = $row[9];
        $conditional_ht_relay_state[$n][$i] = $row[10];
        $conditional_ht_relay_seconds_on[$n][$i] = $row[11];
        $conditional_ht_sel_command[$n][$i] = $row[12];
        $conditional_ht_command[$n][$i] = str_replace("''","'",$row[13]);
        $conditional_ht_sel_notify[$n][$i] = $row[14];
        $conditional_ht_notify[$n][$i] = $row[15];
        $i++;
    }
}

unset($conditional_co2_id);
for ($n = 0; $n < count($sensor_co2_id); $n++) {
    $results = $db->query('SELECT Id, Name, State, Sensor, Direction, Setpoint, Period, Sel_Relay, Relay, Relay_State, Relay_Seconds_On, Sel_Command, Do_Command, Sel_Notify, Do_Notify FROM CO2SensorConditional WHERE Sensor=' . $n);
    $i = 0;
    while ($row = $results->fetchArray()) {
        $conditional_co2_id[$n][$i] = $row[0];
        $conditional_co2_name[$n][$i] = $row[1];
        $conditional_co2_state[$n][$i] = $row[2];
        $conditional_co2_sensor[$n][$i] = $row[3];
        $conditional_co2_direction[$n][$i] = $row[4];
        $conditional_co2_setpoint[$n][$i] = $row[5];
        $conditional_co2_period[$n][$i] = $row[6];
        $conditional_co2_sel_relay[$n][$i] = $row[7];
        $conditional_co2_relay[$n][$i] = $row[8];
        $conditional_co2_relay_state[$n][$i] = $row[9];
        $conditional_co2_relay_seconds_on[$n][$i] = $row[10];
        $conditional_co2_sel_command[$n][$i] = $row[11];
        $conditional_co2_command[$n][$i] = str_replace("''","'",$row[12]);
        $conditional_co2_sel_notify[$n][$i] = $row[13];
        $conditional_co2_notify[$n][$i] = $row[14];
        $i++;
    }
}

unset($conditional_press_id);
for ($n = 0; $n < count($sensor_press_id); $n++) {
    $results = $db->query('SELECT Id, Name, State, Sensor, Condition, Direction, Setpoint, Period, Sel_Relay, Relay, Relay_State, Relay_Seconds_On, Sel_Command, Do_Command, Sel_Notify, Do_Notify FROM PressSensorConditional WHERE Sensor=' . $n);
    $i = 0;
    while ($row = $results->fetchArray()) {
        $conditional_press_id[$n][$i] = $row[0];
        $conditional_press_name[$n][$i] = $row[1];
        $conditional_press_state[$n][$i] = $row[2];
        $conditional_press_sensor[$n][$i] = $row[3];
        $conditional_press_condition[$n][$i] = $row[4];
        $conditional_press_direction[$n][$i] = $row[5];
        $conditional_press_setpoint[$n][$i] = $row[6];
        $conditional_press_period[$n][$i] = $row[7];
        $conditional_press_sel_relay[$n][$i] = $row[8];
        $conditional_press_relay[$n][$i] = $row[9];
        $conditional_press_relay_state[$n][$i] = $row[10];
        $conditional_press_relay_seconds_on[$n][$i] = $row[11];
        $conditional_press_sel_command[$n][$i] = $row[12];
        $conditional_press_command[$n][$i] = str_replace("''","'",$row[13]);
        $conditional_press_sel_notify[$n][$i] = $row[14];
        $conditional_press_notify[$n][$i] = $row[15];
        $i++;
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
$i = 0;
while ($row = $results->fetchArray()) {
    $timer_id[$i] = $row[0];
    $timer_name[$i] = $row[1];
    $timer_state[$i] = $row[2];
    $timer_relay[$i] = $row[3];
    $timer_duration_on[$i] = $row[4];
    $timer_duration_off[$i] = $row[5];
    $i++;
}
if (!isset($timer_id)) $timer_id = [];


$results = $db->query('SELECT Host, SSL, Port, User, Pass, Email_From, Wait_Time FROM SMTP');
while ($row = $results->fetchArray()) {
    $smtp_host = $row[0];
    $smtp_ssl = $row[1];
    $smtp_port = $row[2];
    $smtp_user = $row[3];
    $smtp_pass = $row[4];
    $smtp_email_from = $row[5];
    $smtp_wait_time = $row[6];
}


$results = $db->query('SELECT Relay, Timestamp, Display_Last, Cmd_Pre, Cmd_Post, Extra_Parameters FROM CameraStill');
while ($row = $results->fetchArray()) {
    $still_relay = $row[0];
    $still_timestamp = $row[1];
    $still_display_last = $row[2];
    $still_cmd_pre = str_replace("''","'",$row[3]);
    $still_cmd_post = str_replace("''","'",$row[4]);
    $still_extra_parameters = str_replace("''","'",$row[5]);
}

$results = $db->query('SELECT Relay, Cmd_Pre, Cmd_Post, Extra_Parameters FROM CameraStream');
while ($row = $results->fetchArray()) {
    $stream_relay = $row[0];
    $stream_cmd_pre = str_replace("''","'",$row[1]);
    $stream_cmd_post = str_replace("''","'",$row[2]);
    $stream_extra_parameters = str_replace("''","'",$row[3]);
}

$results = $db->query('SELECT Relay, Path, Prefix, File_Timestamp, Display_Last, Cmd_Pre, Cmd_Post, Extra_Parameters FROM CameraTimelapse');
while ($row = $results->fetchArray()) {
    $timelapse_relay = $row[0];
    $timelapse_path = $row[1];
    $timelapse_prefix = $row[2];
    $timelapse_timestamp = $row[3];
    $timelapse_display_last = $row[4];
    $timelapse_cmd_pre = str_replace("''","'",$row[5]);
    $timelapse_cmd_post = str_replace("''","'",$row[6]);
    $timelapse_extra_parameters = str_replace("''","'",$row[7]);
}

$results = $db->query('SELECT Login_Message, Refresh_Time, Enable_Max_Amps, Max_Amps FROM Misc');
while ($row = $results->fetchArray()) {
    $login_message = $row[0];
    $refresh_time = $row[1];
    $enable_max_amps = $row[2];
    $max_amps = $row[3];
}
