<?php
/*
 * The following code can be executed by both users and guests
 */

// Grab last entry for each sensor from the respective log file
$last_ht_sensor = array();
$last_co2_sensor = array();
for ($p = 1; $p <= $sensor_ht_num; $p++) {
    if ($sensor_ht_activated[$p]) {
        $last_ht_sensor[$p] = `awk '($10 == 1){exit}END{print}' /var/www/mycodo/log/sensor-ht-tmp.log`;
        $sensor_explode = explode(" ", $last_ht_sensor[$p]);
        $t_c[$p] = $sensor_explode[6];
        $hum[$p] = $sensor_explode[7];
        $t_f[$p] = round(($t_c[$p]*(9/5) + 32), 1);
        $dp_c[$p] = substr($sensor_explode[8], 0, -1);
        $dp_f[$p] = round(($dp_c[$p]*(9/5) + 32), 1);
        $settemp_f[$p] = round($pid_temp_set[$p]*(9/5)+32, 1);
    }
}
for ($p = 1; $p <= $sensor_co2_num; $p++) {
    if ($sensor_co2_activated[$p]) {
        $last_co2_sensor[$p] = `awk '($8 == 1){exit}END{print}' /var/www/mycodo/log/sensor-co2-tmp.log`;
        $sensor_explode = explode(" ", $last_co2_sensor[$p]);
        $co2[$p] = $sensor_explode[6];
    }
}


// Grab the time of the last sensor read
$time_now = `date +"%Y-%m-%d %H:%M:%S"`;
$time_last = `tail -n 1 /var/www/mycodo/log/sensor-ht-tmp.log`;
$time_explode = explode(" ", $time_last);
$time_last = $time_explode[0] . '-' . $time_explode[1] . '-' . 
            $time_explode[2] . ' ' . $time_explode[3] . ':' . 
            $time_explode[4] . ':' . $time_explode[5];


// Request to generate a graph
if (isset($_POST['Graph'])) {
	if (!isset($_POST['graph_type'])) {
		setcookie('graph_type', 'separate', time() + (86400 * 10), "/" );
		$_COOKIE['graph_type'] = 'separate';
	} else {
		setcookie('graph_type', $_POST['graph_type'], time() + (86400 * 10), "/" );
		$_COOKIE['graph_type'] = $_POST['graph_type'];
	}
    setcookie('graph_span', $_POST['graph_span'], time() + (86400 * 10), "/" );
    $_COOKIE['graph_span'] = $_POST['graph_span'];
    set_new_graph_id();
}
?>
