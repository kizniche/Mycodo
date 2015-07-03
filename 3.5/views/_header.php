<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="robots" content="noindex">
    <title>Mycodo</title>
    <link rel="stylesheet"  href="css/style.css" type="text/css" media="all" />
</head>
<body>
<?php
// show potential errors / feedback (from login object)
if (isset($login)) {
    if ($login->errors) {
        foreach ($login->errors as $error) {
            echo $error;
        }
    echo '<p>';
    }
    if ($login->messages) {
        foreach ($login->messages as $message) {
            echo $message;
        }
    echo '<p>';
    }
}
?>

<?php
// show potential errors / feedback (from registration object)
if (isset($registration)) {
    if ($registration->errors) {
        foreach ($registration->errors as $error) {
            echo $error;
        }
    echo '<p>';
    }
    if ($registration->messages) {
        foreach ($registration->messages as $message) {
            echo $message;
        }
    echo '<p>';
    }
}
?>
