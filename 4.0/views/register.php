<?php include('_header.php'); ?>

<!-- show registration form, but only if we didn't submit already -->
<p><h1>Register a new user</h1></p>

<?php if (!$registration->registration_successful && !$registration->verification_successful) { ?>
<form method="post" action="register.php" name="registerform">
    <input id="user_name" type="text" pattern="[a-zA-Z0-9]{2,64}" name="user_name" required />
    <label for="user_name"><?php echo WORDING_REGISTRATION_USERNAME; ?></label>
    <p>
    <input id="user_email" type="email" name="user_email" required />
    <label for="user_email"><?php echo WORDING_REGISTRATION_EMAIL; ?></label>
    <p>
    <input id="user_password_new" type="password" name="user_password_new" pattern=".{6,}" required autocomplete="off" />
    <label for="user_password_new"><?php echo WORDING_REGISTRATION_PASSWORD; ?></label>
    <p>
    <input id="user_password_repeat" type="password" name="user_password_repeat" pattern=".{6,}" required autocomplete="off" />
    <label for="user_password_repeat"><?php echo WORDING_REGISTRATION_PASSWORD_REPEAT; ?></label>
    <p>
    <img src="tools/showCaptcha.php" alt="captcha" />
    <p>
    <label><?php echo WORDING_REGISTRATION_CAPTCHA; ?></label>
    <br><input type="text" name="captcha" required />

    <input type="submit" name="register" value="<?php echo WORDING_REGISTER; ?>" />
</form>
<?php } ?>

    <a href="index.php"><?php echo WORDING_BACK_TO_LOGIN; ?></a>

<?php include('_footer.php'); ?>
