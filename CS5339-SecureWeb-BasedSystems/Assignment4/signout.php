<?php
	// signin page for the website
	// accessible to all users
	session_start();
	// clear session variables
	$_SESSION = array();
	// set cookie to expire
	setcookie (session_id(), "", time() - 3600);
	// destroy session
	session_destroy();
	// to prevent session fixation
	session_regenerate_id();
	session_write_close();
	// redirect user to sigin in
	header("Location: signin.php"); 
?>