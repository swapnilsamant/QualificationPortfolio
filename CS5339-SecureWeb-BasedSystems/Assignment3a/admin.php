<?php
// admin page for the website
// accessible only to users with "admin" access level

session_start();

// inclulde common functions
require_once("includes/common.php");

// check if user has credentials to access page
check_page_access("admin");

// configuration file for random salt
require_once("includes/config.php");

// display top navigation based on session state
require_once("includes/topnav.php");
$message = ""; // to display validation and success messages
?>

<!DOCTYPE html>
<html>
<head>
	<title>CS5339 Assignemnt 3a - admin page</title>
	<script type="text/javascript" src="scripts/admin.js"></script>
</head>
<body>

<?php

// function to check if username is already in database
function check_existing_username($user_name)
{
	try 
	{
		global $link;
		$select_stmt = $link->prepare("SELECT user_id FROM user WHERE user_name = ?");
		$select_stmt->bind_param("s", $user_name);
		$select_stmt->execute();
		$select_stmt->store_result();
		if ($select_stmt->num_rows == 0)
		{
			$select_stmt->close();
			return "";
		}
		$select_stmt->close();
		return "Username already exists<br>";
	}
	catch(Exception $e) 
	{
		echo 'Message: ' .$e->getMessage();
	}
}


$firstname = $lastname = $user_name = $password = $usertype = "";

// if the form is posted 
if(isset($_POST["cmdSubmit"])) 
{
	// check CSRF token
	$csrf_token = $_SESSION['csrf_token'];
	unset($_SESSION['csrf_token']);
	if (!($csrf_token) || ($_POST['csrf_token']!==$csrf_token))
	{
		die("Invalid token.");
	}
	
	// input validation
	if (isset($_POST['txtFirstName']))
		$firstname = fix_string($_POST['txtFirstName']);
  	if (isset($_POST['txtLastName']))
		$lastname  = fix_string($_POST['txtLastName']);
  	if (isset($_POST['txtUserName']))
		$user_name = fix_string($_POST['txtUserName']);
  	if (isset($_POST['txtPassword']))
		$password = fix_string($_POST['txtPassword']);
  	if (isset($_POST['cmbUserType']))
		$usertype = fix_string($_POST['cmbUserType']);
	
	$fail  = validate_firstname($firstname);
	$fail .= validate_lastname($lastname);
	$fail .= validate_username($user_name);
	$fail .= validate_password($password);
	
	// include database connection module
	require_once("includes/conn.php");	
	$fail .= check_existing_username($user_name);
	
	// if there are no errors in input
	if ($fail == "")
	{
		// hash the password string with PHP function
		// and salt created above
		$password_hash = hash('sha256', $random_salt.$user_name.$password);
		// insert new user in database
		$insert_stmt = $link->prepare("INSERT INTO user (`first_name`, `last_name`, `user_name`, `user_password`, `access_level`) VALUES (?,?,?,?,?)");
		$insert_stmt->bind_param("sssss", $firstname, $lastname, $user_name, $password_hash, $usertype);
		$insert_stmt->execute();
		if ($insert_stmt->affected_rows === 0) exit('Sorry, the website is experiencing problems.');
		$insert_stmt->close();
		// set success message
		$message = "<br/>New user created successfully<br/>";
		
		// close database connection
		$link->close();
	}
	else
	{
		// if errors are found, set the message to display errors
		$message = "<br/>Error(s) found on form:<br/>" . $fail; 
	}
}    
?>
	<h1>CS5339 Assignemnt 3a - admin page</h1>
	<!-- link to display list of all registered users -->
	<a href="list_users.php">List all registered users</a>

	<?php
		// display a message if there is a validation or success message
		if (($message) && ($message !== ""))
		{
			echo $message; 
		}
	?>
	<!-- display form-->
	<form name="frmAddUser" id="frmAddUser" method="post" onsubmit="return validate(this)">
		<label for="txtFirstName">First Name</label> <input type="text" name="txtFirstName" id="txtFirstName" value="<?php echo $firstname?>"/>
		<br/>
		<label for="txtLastName">Last Name</label> <input type="text" name="txtLastName" id="txtLastName"value="<?php echo $lastname?>"/>
		<br/>        
		<label for="txtUserName">User Name</label> <input type="text" name="txtUserName" id="txtUserName" value="<?php echo $user_name?>"/>
		<br/>
		<label for="cmbUserType">User Type</label> 
		<select name="cmbUserType" id="cmbUserType">
			<option value="admin" <?php if ($usertype === "admin") echo "selected"; ?>>Admin</option>
			<option value="user" <?php if ($usertype !== "admin") echo "selected"; ?>>User</option>
		</select>
		<br/>        
		<label for="txtPassword">Password</label><input type="password" name="txtPassword" id="txtPassword"/>
		<br/>
		<!-- CSRF token-->
		<?php
			$csrf_token= md5(uniqid());
			$_SESSION['csrf_token']= $csrf_token;
		?>
		<input type="hidden" name="csrf_token" value="<?php echo $csrf_token; ?>"/>
		<button type="submit" name="cmdSubmit" id="cmdSubmit" value="Create">Create</button>        
	</form>
</body>
</html>