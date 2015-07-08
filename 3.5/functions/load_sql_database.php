<?php
$db = new SQLite3($sqlite_db);
$results = $db->query('SELECT Relays, HTSensors, CO2Sensors, Timers FROM Numbers');
while ($row = $results->fetchArray()) {
    $relay_num = $row[0];
    $sensor_ht_num = $row[1];
    $sensor_co2_num = $row[2];
    $timer_num = $row[3];
}

$results = $db->query('SELECT Id, Name, Pin, Trigger FROM Relays');
while ($row = $results->fetchArray()) {
    //print $row[0] . " " . $row[1] . " " . $row[2] . " " . $row[3] . "<br>";
    $relay_name[$row[0]] = $row[1];
    $relay_pin[$row[0]] = $row[2];
    $relay_trigger[$row[0]] = $row[3];
}

$results = $db->query('SELECT Id, Name, Pin, Device, Period, Activated, Graph, Temp_Relay, Temp_OR, Temp_Set, Temp_Period, Temp_P, Temp_I, Temp_D, Hum_Relay, Hum_OR, Hum_Set, Hum_Period, Hum_P, Hum_I, Hum_D FROM HTSensor');
while ($row = $results->fetchArray()) {
    //print $row[0] . " " . $row[1] . " " . $row[2] . " " . $row[3] . " " . $row[4] . " " . $row[5] . " " . $row[6] . " " . $row[7] . " " . $row[8] . " " . $row[9] . " " . $row[10] . " " . $row[11] . " " . $row[12] . " " . $row[13] . " " . $row[14] . " " . $row[15] . " " . $row[16] . " " . $row[17] . " " . $row[18] . "<br>";
    $sensor_ht_name[$row[0]] = $row[1];
    $sensor_ht_pin[$row[0]] = $row[2];
    $sensor_ht_device[$row[0]] = $row[3];
    $sensor_ht_period[$row[0]] = $row[4];
    $sensor_ht_activated[$row[0]] = $row[5];
    $sensor_ht_graph[$row[0]] = $row[6];
    $pid_temp_relay[$row[0]] = $row[7];
    $pid_temp_or[$row[0]] = $row[8];
    $pid_temp_set[$row[0]] = $row[9];
    $pid_temp_period[$row[0]] = $row[10];
    $pid_temp_p[$row[0]] = $row[11];
    $pid_temp_i[$row[0]] = $row[12];
    $pid_temp_d[$row[0]] = $row[13];
    $pid_hum_relay[$row[0]] = $row[14];
    $pid_hum_or[$row[0]] = $row[15];
    $pid_hum_set[$row[0]] = $row[16];
    $pid_hum_period[$row[0]] = $row[17];
    $pid_hum_p[$row[0]] = $row[18];
    $pid_hum_i[$row[0]] = $row[19];
    $pid_hum_d[$row[0]] = $row[20];
}

$results = $db->query('SELECT Id, Name, Pin, Device, Period, Activated, Graph, CO2_Relay, CO2_OR, CO2_Set, CO2_Period, CO2_P, CO2_I, CO2_D FROM CO2Sensor');
while ($row = $results->fetchArray()) {
    //print $row[0] . " " . $row[1] . " " . $row[2] . " " . $row[3] . " " . $row[4] . " " . $row[5] . " " . $row[6] . " " . $row[7] . " " . $row[8] . " " . $row[9] . " " . $row[10] . " " . $row[11] . " " . $row[12] . "<br>";
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
    //print $row[0] . " " . $row[1] . " " . $row[2] . " " . $row[3] . " " . $row[4] . " " . $row[5] . "<br>";
    $timer_name[$row[0]] = $row[1];
    $timer_state[$row[0]] = $row[2];
    $timer_relay[$row[0]] = $row[3];
    $timer_duration_on[$row[0]] = $row[4];
    $timer_duration_off[$row[0]] = $row[5];
}

$results = $db->query('SELECT Host, SSL, Port, User, Pass, Email_From, Email_To FROM SMTP');
while ($row = $results->fetchArray()) {
    //print $row[0] . " " . $row[1] . " " . $row[2] . " " . $row[3] . " " . $row[4] . " " . $row[5] . " " . $row[6] ."<br>";
    $smtp_host = $row[0];
    $smtp_ssl = $row[1];
    $smtp_port = $row[2];
    $smtp_user = $row[3];
    $smtp_pass = $row[4];
    $smtp_email_to = $row[5];
    $smtp_email_from = $row[6];
}

$results = $db->query('SELECT Camera_Relay FROM Misc');
while ($row = $results->fetchArray()) {
    //print $row[0] . "<br>";
    $camera_relay = $row[0];
}
?>
