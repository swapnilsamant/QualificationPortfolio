<?php
// page to display list of all registered users
// accessible only to users with "admin" access level
session_start();

// inclulde common functions
require_once("includes/common.php");

// check if user has credentials to access page
check_page_access("admin");

// display top navigation based on session state
require_once("includes/topnav.php");

// include database connection module
require_once("includes/conn.php");
?>
<!DOCTYPE html>
<html>
<head>
	<title>CS5339 Assignemnt 3a - list of registered users</title>
</head>
<body>
<h1>CS5339 Assignemnt 3a - list of registered users</h1>
<?php
// init statement
$select_stmt = $link->stmt_init();
// prepare statement
$select_stmt = $link->prepare("SELECT user_id, user_name, first_name, last_name, creation_time, last_login_time, access_level FROM user order by first_name");
// execute statement
$select_stmt->execute();
// store results from the statement
$select_stmt->store_result();
// if no rows are returned, display message
// dont show table headers
if ($select_stmt->num_rows === 0) 
{
	echo "No rows.";
}
else
{
	// if rows are returned, bind the results to array variables
	$select_stmt->bind_result($user_id_rows, $user_name_rows, $first_name_rows, $last_name_rows, $creation_time_rows, $last_login_time_rows, $access_level_rows);
	// fetch results in one array per column
	while($select_stmt->fetch())
	{
		$user_id[] = $user_id_rows;
		$user_name[] = $user_name_rows;
		$first_name[] = $first_name_rows;
		$last_name[] = $last_name_rows;
		$creation_time[] = $creation_time_rows;
		$last_login_time[] = $last_login_time_rows;
		$access_level[] = $access_level_rows;
	}
	$select_stmt->close();
	$link->close();

// display table headers
	echo  <<<HTML
<table border="1">
<tr>
<th>User Name</th>
<th>First Name</th>
<th>Last Name</th>
<th>Account Creation Time</th>
<th>Last Login Time</th>
<th>Access level</th>
</tr>
HTML;
// iterate over array to display list of users
	for ($i = 0; $i < count($user_id); $i++)
	{
		echo "<tr>";
		echo "<td>$user_name[$i]</td>";
		echo "<td>$first_name[$i]</td>";
		echo "<td>$last_name[$i]</td>";
		echo "<td>$creation_time[$i]</td>";
		echo "<td>$last_login_time[$i]</td>";
		echo "<td>$access_level[$i]</td>";
		echo "</tr>";
	}
	echo "</table>";
}
?>
</body>
</html>