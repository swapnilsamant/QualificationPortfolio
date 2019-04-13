<?php
// signin page for the website
// accessible to all users
// display top navigation based on session state
session_start();
require_once("includes/topnav.php");
// inclulde common PHP functions
require_once("includes/common.php");
require_once("includes/config.php");
// check if user is already logged in
// if user is already logged in, then redirect the user
// to appropriate homepage
if(isset($_SESSION['loggedinflag'])) 
{
	redirect_to_home_page();
}
// if user is not logged in then
// display the login page
?>
<!DOCTYPE html>
<html>
<head>
	<title>CS5339 Assignment 4 - signin</title>
</head>
<body>
<?php
$user_name = $password = "";

// if the form is submitted
if(isset($_POST["cmdSubmit"])) 
{
	// check CSRF token
	$csrf_token = $_SESSION['csrf_token'];
	unset($_SESSION['csrf_token']);
	if (!($csrf_token) || ($_POST['csrf_token']!==$csrf_token))
	{
		die("Invalid token.");
	}

	// include database connection module
	require_once("includes/conn.php");

	// get username and password from the form
	if (isset($_POST['txtUserName']))
		$user_name = fix_string($_POST['txtUserName']);
	if (isset($_POST['txtPassword']))
		$password = fix_string($_POST['txtPassword']);

	$password_hash = hash('sha256', $random_salt.$user_name.$password);
	// prepare statement to select the user details
	$select_stmt = $link->stmt_init();
	$select_stmt = $link->prepare("SELECT user_id, user_name, first_name, 
									last_name, creation_time, last_login_time, 
									access_level, alum_profile_id 
									FROM user 
									WHERE user_name = ?
									AND user_password = ?");
	$select_stmt->bind_param("ss", $user_name, $password_hash);
	$select_stmt->execute();
	$select_stmt->store_result();

	// if no rows are returned display error and show from again
	if ($select_stmt->num_rows === 0) 
	{
		$message = "Invalid username or password. Please try again.";
	}
	else
	{
		// if rows are returned, then bind results
		$select_stmt->bind_result($user_id, $user_name, $first_name, 
									$last_name, $creation_time, $last_login_time, $access_level, $profileid); 
		// fetch first row, because usernames are unique
		$select_stmt->fetch();
		$select_stmt->close();

		date_default_timezone_set('America/Denver');
		$last_login_time = date('Y-m-d H:i:s');
		$update_stmt = $link->prepare("UPDATE user SET last_login_time = ? WHERE user_id = ? ");
		$update_stmt->bind_param("si", $last_login_time, $user_id);
		$update_stmt->execute();
		if ($update_stmt->affected_rows === 0) exit('Sorry, the website is experiencing problems.');
		$update_stmt->close();

			// to prevent session fixation
		session_regenerate_id();

		// set session variables
		// with user details
		$_SESSION["username"] = $user_name;
		$_SESSION["accesslevel"] = $access_level;
		$_SESSION["firstname"] = $first_name;
		$_SESSION["lastname"] = $last_name;
		$_SESSION["lastlogin"] = $last_login_time;
		$_SESSION["accountcreated"] = $creation_time;
		$_SESSION["loggedinflag"] = true;
		$_SESSION["profileid"] = $profileid;
		
		// redirect user to correct home page
		redirect_to_home_page();
	}
	$link->close();
}
?>
	<!-- display form-->
	<h1>CS5339 Assignemnt 4 - signin</h1>
	<?php
		// display a message if there is a validation or success message
		if (($message) && ($message !== ""))
		{
			echo $message; 
		}
	?>
	<form name="frmLogin" method="post">
		<label for="txtUserName">User Name</label>
		<br/>
		<input type="text" name="txtUserName" id="txtUserName" value="<?php echo $user_name?>"/>
		<br/>
		<label for="txtPassword">Password</label>
		<br/>
		<input type="password" name="txtPassword" id="txtPassword"/>
		<br/>
		<!-- CSRF token-->
		<?php
			$csrf_token= md5(uniqid());
			$_SESSION['csrf_token']= $csrf_token;
		?>
		<input type="hidden" name="csrf_token" value="<?php echo $csrf_token; ?>"/>
		<button type="submit" name="cmdSubmit" id="cmdSubmit" value="Login">Login</button>
	</form>
</body>
</html>