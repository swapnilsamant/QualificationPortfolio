<?php
// user page for the website
// accessible only to users with "admin" or "user" access level

session_start();

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
	<title>CS5339 Assignemnt 4 - profile page</title>
	<style>
		th {text-align: left;};
		td {text-align: left;};
	</style>
</head>
<body>
	<h1>CS5339 Assignemnt 4 - profile page</h1>
<?php
if (isset($_GET['profile_id']))
{
	$profile_id = fix_string($_GET['profile_id']);
	if (!(check_integer($profile_id)))
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

		// display user details from the session
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
		echo "<td>" . $alum_email . "</td></tr>";
		echo "<tr><th>Employer Name: </th>";
		echo "<td>" . $alum_employer_name . "</td></tr>";
		echo "<tr><th>Employer Type: </th>";
		echo "<td>" . $alum_employer_type . "</td></tr>";


		if ($_SESSION["profileid"] == $alum_pk)
		{
			echo '<tr><td colspan="2"><a href="edit_profile.php?profile_id=' . $alum_pk . '">Edit Profile</a></td></tr>';
		}

		echo "</table>";        
	}
}
else if ($_SESSION["accesslevel"] == "admin")
{
	echo '<table border="0">';
	echo "<tr><th>User Name: </th>";
	echo "<td>" . $_SESSION['username'] . "</td></tr>";
	echo "<tr><th>First Name: </th>";
	echo "<td>" . $_SESSION['firstname'] . "</td></tr>";
	echo "<tr><th>Last Name: </th>";
	echo "<td>" . $_SESSION['lastname'] . "</td></tr>";
	echo "<tr><th>Account Created: </th>";
	echo "<td>" . $_SESSION['accountcreated'] . "</td></tr>";
	echo "<tr><th>Last Login: </th>";
	echo "<td>" . $_SESSION['lastlogin'] . "</td></tr>";
	echo "<tr><th>Access Level: </th>";
	echo "<td>" . $_SESSION['accesslevel'] . "</td></tr>";
	echo "</table>";
}
else
{
	die("invalid profile id");
}

?>    
</body>
</html>