<?php
/*
*  auth.php - Checks if a user is logged in
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

require_once(dirname(__FILE__) . '/../config.php');

$db_users = new SQLite3($config["db"]["users"]);

if (!isset($_COOKIE['login_user']) || !isset($_COOKIE['login_hash'])) {
	echo "Invalid username/password";
	return 0;
} else if (!preg_match('/^[a-z\d]{2,64}$/i', $_COOKIE['login_user'])) {
	echo "Invalid username/password";
	return 0;
}

$sql = "SELECT user_name, user_email, user_password_hash
        FROM users
        WHERE user_name = '" . $_COOKIE['login_user'] . "' OR user_email = '" . $_COOKIE['login_user'] . "'
        LIMIT 1";
$results = $db_users->query($sql);
while ($row = $results->fetchArray()) {
	$user_name = $row[1];
	$user_hash = $row[2];
}
