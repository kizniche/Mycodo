<?php include('_header.php'); 

if ($_SESSION['user_name'] != guest) {
?>
<img style="float: left; padding-right: 10px;" src="<?php echo $login->user_gravatar_image_tag; ?>">
<div style="font-size: 20px; font-weight: bold;">
    <?php echo 'Editing ' . $_SESSION['user_name'] . '\'s Profile'; ?>
</div>
<div style="">
    Image can be changed at gravatar.com
</div>
<div style="clear: both; padding: 0 0 5px 0;"></div>
<div style="padding: 1em 0 1em 0;">
<form method="post" action="edit.php" name="user_edit_form_name">
    <div class="edit-title">
        <label for="user_name">
            <?php echo WORDING_CHANGE_USERNAME; ?> (<?php echo WORDING_CURRENTLY; ?>: <?php echo $_SESSION['user_name']; ?>)
        </label>
    </div>
    <input id="user_name" type="text" name="user_name" pattern="[a-zA-Z0-9]{2,64}" required />
    <input type="submit" name="user_edit_submit_name" value="<?php echo WORDING_CHANGE_USERNAME; ?> " /> <?php echo WORDING_NEW_USERNAME; ?>
</form>
</div>
<div style="padding: 0 0 1em 0;">
<form method="post" action="edit.php" name="user_edit_form_email">
    <div class="edit-title">
        <label for="user_email">
            <?php echo WORDING_NEW_EMAIL; ?> (<?php echo WORDING_CURRENTLY; ?>: <?php echo $_SESSION['user_email']; ?>)
        </label>
    </div>
    <input id="user_email" type="email" name="user_email" required /> 
    <input type="submit" name="user_edit_submit_email" value="<?php echo WORDING_CHANGE_EMAIL; ?>" />
</form>
</div>
<form method="post" action="edit.php" name="user_edit_form_password">
    <div class="edit-title">
        <label for="user_password_new">
            <?php echo WORDING_CHANGE_PASSWORD; ?>
        </label>
    </div>
    <input id="user_password_old" type="password" name="user_password_old" autocomplete="off" />
    <label for="user_password_old"><?php echo WORDING_OLD_PASSWORD; ?></label>
    <br>
    <input id="user_password_new" type="password" name="user_password_new" autocomplete="off" />
    <label for="user_password_new"><?php echo WORDING_NEW_PASSWORD; ?></label>
    <br>
    <input id="user_password_repeat" type="password" name="user_password_repeat" autocomplete="off" />
    <label for="user_password_repeat"><?php echo WORDING_NEW_PASSWORD_REPEAT; ?></label>
    <br>
    <div style="padding: 5px 0 20px 0;">
        <input type="submit" name="user_edit_submit_password" value="<?php echo WORDING_CHANGE_PASSWORD; ?>" />
    </div>
</form>
<?php } else { ?>
<p>Profile editing disabled for guest.<p/>
<?php } ?>
<a href="index.php"><?php echo WORDING_BACK_TO_LOGIN; ?></a>

<?php include('_footer.php'); ?>
