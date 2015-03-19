<html>
<head>
<title>Register</title>
</head>
<body>
<?php
// Show potential errors
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

<form method="post" action="register.php" name="registerform">
<table>
    <tr>
        <td>
            <input id="login_input_username" class="login_input" type="text" pattern="[a-zA-Z0-9]{2,64}" name="user_name" required />
        </td>
        <td>
            <!-- the user name input field uses a HTML5 pattern check -->
            <label for="login_input_username">Username (letters/numbers, 2 to 64 characters)</label>
        </td>
    </tr>
    <tr>
        <td>
            <input id="login_input_email" class="login_input" type="email" name="user_email" required />
        </td>
        <td>
            <!-- the email input field uses a HTML5 email type check -->
            <label for="login_input_email">User's email</label>
        </td>
    </tr>
    <tr>
        <td>
            <input id="login_input_password_new" class="login_input" type="password" name="user_password_new" pattern=".{6,}" required autocomplete="off" />
        </td>
        <td>
            <label for="login_input_password_new">Password (min. 6 characters)</label>
        </td>
    </tr>
    <tr>
        <td>
            <input id="login_input_password_repeat" class="login_input" type="password" name="user_password_repeat" pattern=".{6,}" required autocomplete="off" />
        </td>
        <td>
            <label for="login_input_password_repeat">Repeat password</label>
        </td>
    </tr>
    <tr>
        <td>
            <input type="submit"  name="register" value="Register" />
        </td>
    </tr>
</table>
</form>
<p><a href="index.php">Back to Login Page</a></p>
</body>
</html>
