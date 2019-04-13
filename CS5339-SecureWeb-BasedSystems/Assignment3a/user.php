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
?>
<!DOCTYPE html>
<html>
<head>
	<title>CS5339 Assignemnt 3a - user page</title>
    <style>
        th {text-align: left;};
        td {text-align: left;};
    </style>
</head>
<body>
	<h1>CS5339 Assignemnt 3a - user page</h1>
<?php
// display user details from the session
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
?>    
</body>
</html>