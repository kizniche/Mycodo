<?php

$errors = array();  // array to hold validation errors
$data = array();  // array to pass back data

	if (empty($_POST['name']))
		$errors['name'] = 'Name is required.';

	if (empty($_POST['email']))
		$errors['email'] = 'Email is required.';

	if (empty($_POST['superheroAlias']))
		$errors['superheroAlias'] = 'Superhero alias is required.';

	if (!empty($errors)) {
		$data['success'] = false;
		$data['errors']  = $errors;
	} else {
		// DO ALL YOUR FORM PROCESSING HERE
		// THIS CAN BE WHATEVER YOU WANT TO DO (LOGIN, SAVE, UPDATE, WHATEVER)
		$today = date("Y-m-d H:i:s");
		$data['success'] = true;
		$data['message'] = 'Settings Successfully Saved (at ' . $today . ' server time)';
	}

	echo json_encode($data);
