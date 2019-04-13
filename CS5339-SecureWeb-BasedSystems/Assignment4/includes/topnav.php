<?php
// File displays navigation links at the top based on
// session state

// set session time to 30 minutes
if (isset($_SESSION['LAST_ACTIVITY']) && (time() - $_SESSION['LAST_ACTIVITY'] > 1800)) 
{
	header("Location: signout.php"); 
}
$_SESSION['LAST_ACTIVITY'] = time(); // update last activity time stamp
// always display main page link
echo '<a href="mainpage.php">main page</a> ';

if(isset( $_SESSION['loggedinflag'])) 
{
	// if user is logged in then display user page link
	if (strlen($_SESSION["profileid"]) > 0)
	{
		echo '<a href="user.php?profile_id=' . $_SESSION["profileid"] . '">user page</a> ';
	}
	else
	{
		echo '<a href="user.php">user page</a> ';
	}

	// if user's access level is admin then display admin page link
	if ($_SESSION["accesslevel"] === "admin")
	{
		echo '<a href="admin.php">admin page</a> ';
	}

	// if user is logged in then display signout link
	echo '<a href="signout.php">signout</a> ';
}
else
{
	// if user is not logged in then display signin link
	echo '<a href="signin.php">signin</a> ';
}
echo "<br/>";
?>