<?php

$mycodo_install_path = realpath(__DIR__ . '/..');

$config = array(
    "db" => array(
        "mycodo" => "$mycodo_install_path/config/mycodo.db",
        "users" => "$mycodo_install_path/config/users.db",
        "notes" => "$mycodo_install_path/config/notes.db"
    ),
    "paths" => array(
        "install" => $mycodo_install_path,
        "lock" => "/var/lock"
    )
);

/*
    Consider creating constants for heavily used paths.
    ex. require_once(LIBRARY_PATH . "password_compatibility_library.php")
*/

// defined("LOG_PATH")
//     or define("LIBRARY_PATH", realpath(dirname(__FILE__) . '/libraries/'));

?>