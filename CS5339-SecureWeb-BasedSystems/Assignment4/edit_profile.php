<?php
// user page for the website
// accessible only to users with "admin" or "user" access level

session_start();

require_once("includes/config.php");
// inclulde common functions
require_once("includes/common.php");

// check if user has credentials to access page
check_page_access("user");


// display top navigation based on session state
require_once("includes/topnav.php");

// include database connection module
require_once("includes/conn.php");
?>
<!DOCTYPE html>
<html>
<head>
	<title>CS5339 Assignemnt 4 - Edit Profile</title>
	<style>
		th {text-align: left;};
		td {text-align: left;};
	</style>
	<script type="text/javascript" src="scripts/edit_profile.js"></script>
</head>
<body>
	<h1>CS5339 Assignemnt 4 - Edit Profile</h1>
<?php
$email_address = $employer_name = $employer_type = $profile_id = $fail = $message = "";
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

	// get form varaibles
	if (isset($_POST['txtEmailAddress']))
		$email_address = fix_string($_POST['txtEmailAddress']);
	if (isset($_POST['txtEmployerName']))
		$employer_name = fix_string($_POST['txtEmployerName']);
	if (isset($_POST['cmbEmployerType']))
		$employer_type = fix_string($_POST['cmbEmployerType']);
	if (isset($_POST['hidProfileId']))
		$profile_id = fix_string($_POST['hidProfileId']);    

	if ($profile_id != $_SESSION["profileid"])
	{
		die("invalid profile id");
	}


	//Validate email, employer name and employer type
	$fail = validate_email($email_address);
	$fail .= validate_employer_name($employer_name);
	$fail .= validate_employer_type($employer_type);


	// if there are no errors in input
	if ($fail == "")
	{
		$update_stmt = $link->prepare("UPDATE alumni_profile 
										SET `alum_email` = ?, 
											`alum_employer_name` = ?,
											`alum_employer_type` = ?
										WHERE alum_pk = ?");
		$update_stmt->bind_param("sssi", $email_address, $employer_name, $employer_type, $profile_id);
		$update_stmt->execute();
		//if ($update_stmt->affected_rows === 0) exit('Sorry, the website is experiencing problems.');
		$update_stmt->close();
		// set success message
		header("Location: user.php?profile_id=". $profile_id);
	}
	else
	{
		// if errors are found, set the message to display errors
		$message = "<br/>Error(s) found on form:<br/>" . $fail; 
	}
}

if (isset($_GET['profile_id']))
{
	$profile_id = fix_string($_GET['profile_id']);

	if (!(check_integer($profile_id)))
	{
		die("invalid profile id");
	}

	if ($profile_id != $_SESSION["profileid"])
	{
		die("invalid profile id");
	}
	$select_stmt = $link->stmt_init();
	$select_stmt = $link->prepare("SELECT alum_pk, graduation_academic_year, graduation_semester, alum_last_name, 
									alum_first_name, alum_major, alum_classification, 
									alum_degree, alum_email, alum_employer_name, alum_employer_type 
									FROM alumni_profile 
									WHERE alum_pk = ?");
	$select_stmt->bind_param("i", $profile_id);
	$select_stmt->execute();
	$select_stmt->store_result();

	if ($select_stmt->num_rows === 0) 
	{
		die("invalid profile id");
	}
	else
	{
		// if rows are returned, then bind results
		$select_stmt->bind_result($alum_pk, $graduation_academic_year, $graduation_semester, $alum_last_name, 
									$alum_first_name, $alum_major, $alum_classification, 
									$alum_degree, $alum_email, $alum_employer_name, $alum_employer_type); 
		// fetch first row, because usernames are unique
		$select_stmt->fetch();
		$select_stmt->close();

		// display a message if there is a validation or success message
		if (($message) && ($message !== ""))
		{
			echo $message; 
		}
		// display user details from the session
		echo '<form name="frmEditProfile" id ="frmEditProfile" method="post" onsubmit="return validate(this)">';
		echo '<table border="0">';
		echo "<tr><th>Last Name: </th>";
		echo "<td>" . $alum_last_name . "</td></tr>";
		echo "<tr><th>First Name: </th>";
		echo "<td>" . $alum_first_name . "</td></tr>";
		echo "<tr><th>Graduation Year: </th>";
		echo "<td>" . $graduation_academic_year . "</td></tr>";
		echo "<tr><th>Graduation Semester: </th>";
		echo "<td>" . $graduation_semester . "</td></tr>";
		echo "<tr><th>Major: </th>";
		echo "<td>" . $alum_major . "</td></tr>";
		echo "<tr><th>Classification: </th>";
		echo "<td>" . $alum_classification . "</td></tr>";
		echo "<tr><th>Degree: </th>";
		echo "<td>" . $alum_degree . "</td></tr>";
		echo "<tr><th>e-mail: </th>";
		echo '<td><input type="text" name="txtEmailAddress" id="txtEmailAddress" value="' . $alum_email . '"/></td></tr>';
		echo "<tr><th>Employer Name: </th>";
		echo '<td><input type="text" name="txtEmployerName" id="txtEmployerName" value="' . $alum_employer_name . '"/></td></tr>';
		echo "<tr><th>Employer Type: </th>";
?>
		<td><select name="cmbEmployerType" id="cmbEmployerType">
					<option value="Private Sector" <?php if ($alum_employer_type == "Private Sector") echo "selected";?>>Private Sector</option>
					<option value="Government" <?php if ($alum_employer_type == "Government") echo "selected";?>>Government</option>
					<option value="Higher Education" <?php if ($alum_employer_type == "Higher Education") echo "selected"?>>Higher Education</option>
					<option value="Research" <?php if ($alum_employer_type == "Research") echo "selected"?>>Research</option>
				</select> </td></tr>
<?php
		// CSRF token
		$csrf_token= md5(uniqid());
		$_SESSION['csrf_token']= $csrf_token;
		echo  '<input type="hidden" name="csrf_token" value="' . $csrf_token . '"/>';
		echo  '<input type="hidden" name="hidProfileId" value="' . $alum_pk . '"/>';
		echo '<tr><td colspan="2"><input type ="submit" value="Save" name="cmdSubmit" id="cmdSubmit"></td></tr>';

		echo "</table>";
		echo "</form>";
	}
}
else
{
	die("invalid profile id");
}

?>    
</body>
</html>