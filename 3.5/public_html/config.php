<?php

// $image_path = '../log/';
// echo shell_exec("ls $image_path");

/*
    The important thing to realize is that the config file should be included in every
    page of your project, or at least any page you want access to these settings.
    This allows you to confidently use these settings throughout a project because
    if something changes such as your database credentials, or a path to a specific resource,
    you'll only need to update it here.
*/

$config = array(
    "db" => array(
        "mycodo" => "../config/mycodo.db",
        "users" => "../config/users.db",
        "notes" => "../config/notes.db"
    ),
    "paths" => array(
        "lock" => "/var/lock"
    )
);

/*
    I will usually place the following in a bootstrap file or some type of environment
    setup file (code that is run at the start of every page request), but they work 
    just as well in your config file if it's in php (some alternatives to php are xml or ini files).
*/

/*
    Creating constants for heavily used paths makes things a lot easier.
    ex. require_once(LIBRARY_PATH . "Paginator.php")
*/

// defined("LOG_PATH")
//     or define("LIBRARY_PATH", realpath(dirname(__FILE__) . '../logs'));
    
// defined("TEMPLATES_PATH")
//     or define("TEMPLATES_PATH", realpath(dirname(__FILE__) . '/templates'));

?>