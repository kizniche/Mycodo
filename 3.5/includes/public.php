<?php
/*
*  public.php - Code that can be executed by both users and guests
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

// Grab last entry for each sensor from the respective log file
for ($p = 0; $p < count($sensor_t_id); $p++) {
    if ($sensor_t_activated[$p]) {
        $last_t_sensor[$p] = `awk '$8 == $p {print}' /var/www/mycodo/log/sensor-t-tmp.log | tail -n 1`;
        if ($last_t_sensor[$p] != '') {
            $sensor_explode = preg_split('/[\s]+/', $last_t_sensor[$p]);
            $t_temp_c[$p] = $sensor_explode[6];
            $t_temp_f[$p] = round(($t_temp_c[$p]*(9/5) + 32), 1);
            $settemp_t_f[$p] = round($pid_t_temp_set[$p]*(9/5)+32, 1);
        }
    }
}

for ($p = 0; $p < count($sensor_ht_id); $p++) {
    if ($sensor_ht_activated[$p]) {
        $last_ht_sensor[$p] = `awk '$10 == $p {print}' /var/www/mycodo/log/sensor-ht-tmp.log | tail -n 1`;
        if ($last_ht_sensor[$p] != '') {
            $sensor_explode = preg_split('/[\s]+/', $last_ht_sensor[$p]);
            $ht_temp_c[$p] = floatval($sensor_explode[6]);
            $hum[$p] = $sensor_explode[7];
            $ht_temp_f[$p] = round(($ht_temp_c[$p]*(9/5) + 32), 1);
            $dp_c[$p] = substr($sensor_explode[8], 0, -1);
            $dp_f[$p] = round(($dp_c[$p]*(9/5) + 32), 1);
            $settemp_ht_f[$p] = round($pid_ht_temp_set[$p]*(9/5)+32, 1);
        }
    }
}

for ($p = 0; $p < count($sensor_co2_id); $p++) {
    if ($sensor_co2_activated[$p]) {
        $last_co2_sensor[$p] = `awk '$8 == $p {print}' /var/www/mycodo/log/sensor-co2-tmp.log | tail -n 1`;
        if ($last_co2_sensor[$p] != '') {
            $sensor_explode = preg_split('/[\s]+/', $last_co2_sensor[$p]);
            $co2[$p] = $sensor_explode[6];
        }
    }
}

for ($p = 0; $p < count($sensor_press_id); $p++) {
    if ($sensor_press_activated[$p]) {
        $last_press_sensor[$p] = `awk '$10 == $p {print}' /var/www/mycodo/log/sensor-press-tmp.log | tail -n 1`;
        if ($last_press_sensor[$p] != '') {
            $sensor_explode = preg_split('/[\s]+/', $last_press_sensor[$p]);
            $press_temp_c[$p] = floatval($sensor_explode[6]);
            $press[$p] = $sensor_explode[7];
            $press_temp_f[$p] = round(($press_temp_c[$p]*(9/5) + 32), 1);
            $settemp_press_f[$p] = round($pid_press_temp_set[$p]*(9/5)+32, 1);
        }
    }
}

$pi_temp_cpu_c = `cat /sys/class/thermal/thermal_zone0/temp`;
$pi_temp_cpu_c = round((float)($pi_temp_cpu_c / 1000), 1);
$pi_temp_cpu_f = round(($pi_temp_cpu_c*(9/5) + 32), 1);

$pi_temp_gpu_c = `/opt/vc/bin/vcgencmd measure_temp`;
$pi_temp_gpu_c = substr_replace($pi_temp_gpu_c,'',0,5);
$pi_temp_gpu_c = substr($pi_temp_gpu_c,0,-3);
$pi_temp_gpu_c = trim($pi_temp_gpu_c, "tempC=\'C");
$pi_temp_gpu_f = round(($pi_temp_gpu_c*(9/5) + 32), 1);

// Determine the time of the last sensor read
$time_now = `date +"%Y-%m-%d %H:%M:%S"`;

$time_last_t = `tail -n 1 /var/www/mycodo/log/sensor-t-tmp.log`;
if ($time_last_t != '') {
    $time_explode = preg_split('/[\s]+/', $time_last_t);
    $time_last_t = $time_explode[0] . '-' . $time_explode[1] . '-' . $time_explode[2] . ' ' .
                   $time_explode[3] . ':' . $time_explode[4] . ':' . $time_explode[5];
}

$time_last_ht = `tail -n 1 /var/www/mycodo/log/sensor-ht-tmp.log`;
if ($time_last_ht != '') {
    $time_explode = preg_split('/[\s]+/', $time_last_ht);
    $time_last_ht = $time_explode[0] . '-' . $time_explode[1] . '-' . $time_explode[2] . ' ' .
                    $time_explode[3] . ':' . $time_explode[4] . ':' . $time_explode[5];
}

$time_last_co2 = `tail -n 1 /var/www/mycodo/log/sensor-co2-tmp.log`;
if ($time_last_co2 != '') {
    $time_explode = preg_split('/[\s]+/', $time_last_co2);
    $time_last_co2 = $time_explode[0] . '-' . $time_explode[1] . '-' . $time_explode[2] . ' ' .
                     $time_explode[3] . ':' . $time_explode[4] . ':' . $time_explode[5];
}

$time_last_press = `tail -n 1 /var/www/mycodo/log/sensor-press-tmp.log`;
if ($time_last_press != '') {
    $time_explode = preg_split('/[\s]+/', $time_last_press);
    $time_last_press = $time_explode[0] . '-' . $time_explode[1] . '-' . $time_explode[2] . ' ' .
                     $time_explode[3] . ':' . $time_explode[4] . ':' . $time_explode[5];
}

$time_last = max($time_last_t, $time_last_ht, $time_last_co2, $time_last_press);


// Request to generate a graph
if (isset($_POST['Graph'])) {
    if (!isset($_POST['graph_type'])) {
        setcookie('graph_type', 'separate', time() + (86400 * 10), "/" );
        $_COOKIE['graph_type'] = 'separate';
    } else {
        setcookie('graph_type', $_POST['graph_type'], time() + (86400 * 10), "/" );
        $_COOKIE['graph_type'] = $_POST['graph_type'];
    }
    setcookie('graph_span', $_POST['graph_time_span'], time() + (86400 * 10), "/" );
    $_COOKIE['graph_span'] = $_POST['graph_time_span'];
    set_new_graph_id();
}
