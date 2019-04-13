<?php
// File contains common functions used across the website

// This function checks the users access level and redirects the user
// to the appropriate default homepage
function redirect_to_home_page()
{
	switch ($_SESSION["accesslevel"]) 
	{
		case "admin":
			header("Location: admin.php");
			break;
		case "user":
			header("Location: user.php");
			break;
	}
}

// This function check the users access level and decides whether the user 
// has acceess to the page
function check_page_access($page_name)
{
	switch ($page_name) 
	{
		case "admin":
			if ($_SESSION["accesslevel"] !== "admin") 
			{
				echo "you need to be logged in as an administrator to access this page";
				die();
			}
			break;
		case "user":
			if (!(($_SESSION["accesslevel"] === "admin") || ($_SESSION["accesslevel"] === "user")))
			{
				echo "you need to be logged in as an administrator or a user to access this page";
				die();
			}
			break;
	}
}

// Input sanitazation function  
// Learning PHP, MySQL & JavaScript_ With jQuery, CSS & HTML5 (2014, O’Reilly Media) - Robin Nixon
function fix_string($string)
{
  if (get_magic_quotes_gpc()) $string = stripslashes(trim($string));
  return htmlentities($string);
}

// function to validate first name  
// checks for empty string and string length 
// max length is 255
// Learning PHP, MySQL & JavaScript_ With jQuery, CSS & HTML5 (2014, O’Reilly Media) - Robin Nixon
function validate_firstname($field)
{
	if ($field == "") return "No first name was entered<br>";
	else if (strlen($field) > 255)
		return "First name must be less than 255 characters<br>";
	return "";
}

// function to validate last name  
// checks for empty string and string length 
// max length is 255
// Learning PHP, MySQL & JavaScript_ With jQuery, CSS & HTML5 (2014, O’Reilly Media) - Robin Nixon
function validate_lastname($field)
{
	if ($field == "") return "No last name was entered<br>";
	else if (strlen($field) > 255)
		return "Last name must be less than 255 characters<br>";
	return "";
}
  
// function to validate username  
// checks for empty string, string lenght
// valid characters for username are a-z, A-Z, 0-9, "_" and "-"
// min length is 5, max length is 64
// Learning PHP, MySQL & JavaScript_ With jQuery, CSS & HTML5 (2014, O’Reilly Media) - Robin Nixon
function validate_username($field)
{
	if ($field == "") return "No Username was entered<br>";
	else if (strlen($field) < 5)
		return "Usernames must be at least 5 characters<br>";
	else if (strlen($field) > 64)
		return "Usernames must be less than 64 characters<br>";        
	else if (preg_match("/[^a-zA-Z0-9_-]/", $field))
		return "Only letters, numbers, - and _ in usernames<br>";
	return "";		
}

// function to validate password  
// checks for empty string, string lenght
// valid characters for password are a-z, 0-9
// min length is 6, max length is 64
// Learning PHP, MySQL & JavaScript_ With jQuery, CSS & HTML5 (2014, O’Reilly Media) - Robin Nixon
function validate_password($field)
{
	if ($field == "") return "No Password was entered<br>";
	else if (strlen($field) < 6)
		return "Passwords must be at least 6 characters<br>";
	else if (strlen($field) > 64)
		return "Passwords must be less than 64 characters<br>";        
	else if (!preg_match("/[a-z]/", $field) ||
				!preg_match("/[0-9]/", $field))
		return "Passwords require 1 each of a-z and 0-9<br>";
	return "";
}
?>