<?php
// Display Main tab graph-generation preset links
function menu_item($id, $title, $current) {
    global $page;
    $class = ($current == $id) ? "active" : "inactive";
    if ($current != $id) {
        echo '<a href="?tab=main&page=' . $id. '&Refresh=1';
        if (isset($_GET['r']) && ($_GET['r'] == 1)) echo '&r=1';
        echo '"><div class="inactive">' . $title . '</div></a>';
    } else echo '<div class="active">' . $title . '</div>';
}

// Display Log tab SQL database tables, names, and variables
function view_sql_db() {
    global $sqlite_db;

    $db = new SQLite3($sqlite_db);
    print "Table: Numbers<br>Relays HTSensors CO2Sensors Timers<br>";
    $results = $db->query('SELECT Relays, HTSensors, CO2Sensors, Timers FROM Numbers');
    while ($row = $results->fetchArray()) {
        print $row[0] . " " . $row[1] . " " . $row[2] . " " . $row[3] . "<br>";
    }

    print "<br>Table: Relays<br>Id Name Pin Trigger<br>";
    $results = $db->query('SELECT Id, Name, Pin, Trigger FROM Relays');
    while ($row = $results->fetchArray()) {
        print $row[0] . " " . $row[1] . " " . $row[2] . " " . $row[3] . "<br>";
    }

    print "<br>Table: HTSensor<br>Id Name Pin Device Period Activated Graph Temp_Relay Temp_OR Temp_Set Temp_P Temp_I Temp_D Hum_Relay Hum_OR Hum_Set Hum_P Hum_I Hum_D<br>";
    $results = $db->query('SELECT Id, Name, Pin, Device, Period, Activated, Graph, Temp_Relay, Temp_OR, Temp_Set, Temp_P, Temp_I, Temp_D, Hum_Relay, Hum_OR, Hum_Set, Hum_P, Hum_I, Hum_D FROM HTSensor');
    while ($row = $results->fetchArray()) {
        print $row[0] . " " . $row[1] . " " . $row[2] . " " . $row[3] . " " . $row[4] . " " . $row[5] . " " . $row[6] . " " . $row[7] . " " . $row[8] . " " . $row[9] . " " . $row[10] . " " . $row[11] . " " . $row[12] . " " . $row[13] . " " . $row[14] . " " . $row[15] . " " . $row[16] . " " . $row[17] . " " . $row[18] . "<br>";
    }

    print "<br>Table: CO2Sensor<br>Id Name Pin Device Period Activated Graph CO2_Relay CO2_OR CO2_Set CO2_P CO2_I CO2_D<br>";
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
        print $row[0] . " " . $row[1] . " " . $row[2] . " " . $row[3] . " " . $row[4] . " " . $row[5] . " " . $row[6] ."<br>";
    }

    print "<br>Table: Misc<br>";
    print "Camera_Relay<br>";
    $results = $db->query('SELECT Camera_Relay FROM Misc');
    while ($row = $results->fetchArray()) {
        print $row[0] . "<br>";
    }
}

// Display Graphs tab form
function displayform() { ?>
    <FORM action="?tab=graph<?php if (isset($_GET['page'])) echo "&page=" . $_GET['page']; ?>" method="POST">
    <div style="padding: 10px 0 0 15px;">
        <div style="display: inline-block;">
            <div style="padding-bottom: 5px; text-align: right;">START: <?php DateSelector("start"); ?></div>
            <div style="text-align: right;">END: <?php DateSelector("end"); ?></div>
        </div>
        <div style="display: inline-block;">
            <div style="display: inline-block;">
                <select name="MainType">
                    <option value="Separate" <?php
                        if (isset($_POST['MainType'])) {
                            if ($_POST['MainType'] == 'Separate') echo 'selected="selected"';
                        }
                        ?>>Separate</option>
                    <option value="Combined" <?php
                        if (isset($_POST['MainType'])) {
                            if ($_POST['MainType'] == 'Combined') echo 'selected="selected"';
                        }
                        ?>>Combined</option>
                </select>
                <input type="text" value="900" maxlength=4 size=4 name="graph-width" title="Width of the generated graph"> Width (pixels, max 4000)
            </div>
        </div>
        <div style="display: inline-block;">
            &nbsp;&nbsp;<input type="submit" name="SubmitDates" value="Submit">
        </div>
    </div>
    </FORM>
    <?php
}

// Graphs tab date selection inputs
function DateSelector($inName, $useDate=0) {
    /* create array to name months */
    $monthName = array(1=> "January", "February", "March",
    "April", "May", "June", "July", "August",
    "September", "October", "November", "December");
    /* if date invalid or not supplied, use current time */
    if($useDate == 0) $useDate = Time();

    echo "<SELECT NAME=" . $inName . "Month>\n";
	for($currentMonth = 1; $currentMonth <= 12; $currentMonth++) {
	    echo "<OPTION VALUE=\"" . intval($currentMonth) . "\"";
	    if(intval(date( "m", $useDate))==$currentMonth) echo " SELECTED";
	    echo ">" . $monthName[$currentMonth] . "\n";
	}
	echo "</SELECT> / ";

    echo "<SELECT NAME=" . $inName . "Day>\n";
	for($currentDay=1; $currentDay <= 31; $currentDay++) {
	    echo "<OPTION VALUE=\"$currentDay\"";
	    if(intval(date( "d", $useDate))==$currentDay) echo " SELECTED";
	    echo ">$currentDay\n";
	}
	echo "</SELECT> / ";

    echo "<SELECT NAME=" . $inName . "Year>\n";
	$startYear = date("Y", $useDate);
	for($currentYear = $startYear-5; $currentYear <= $startYear+5; $currentYear++) {
	    echo "<OPTION VALUE=\"$currentYear\"";
	    if(date("Y", $useDate) == $currentYear) echo " SELECTED";
	    echo ">$currentYear\n";
	}
	echo "</SELECT>&nbsp;&nbsp;&nbsp;";

    echo "<SELECT NAME=" . $inName . "Hour>\n";
	for($currentHour=0; $currentHour <= 23; $currentHour++) {
	    if($currentHour < 10) echo "<OPTION VALUE=\"0$currentHour\"";
	    else echo "<OPTION VALUE=\"$currentHour\"";
	    if(intval(date("H", $useDate)) == $currentHour) echo " SELECTED";
	    if($currentHour < 10) echo ">0$currentHour\n";
	    else echo ">$currentHour\n";
	}
	echo "</SELECT> : ";

    echo "<SELECT NAME=" . $inName . "Minute>\n";
	for($currentMinute=0; $currentMinute <= 59; $currentMinute++) {
	    if($currentMinute < 10) echo "<OPTION VALUE=\"0$currentMinute\"";
	    else echo "<OPTION VALUE=\"$currentMinute\"";
	    if(intval(date( "i", $useDate)) == $currentMinute) echo " SELECTED";
	    if($currentMinute < 10) echo ">0$currentMinute\n";
	    else echo ">$currentMinute\n";
	}
	echo "</SELECT>";
}

function is_positive_integer($str) {
    return (is_numeric($str) && $str > 0 && $str == round($str));
}
?>
