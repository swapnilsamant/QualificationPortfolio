<?php
// page to display list of all registered users
// accessible only to users with "admin" access level
session_start();

// inclulde common functions
require_once("includes/common.php");

// display top navigation based on session state
require_once("includes/topnav.php");

?>
<!DOCTYPE html>
<html>
<head>
	<title>CS5339 Assignemnt 4 - list of alumni</title>
	<script type="text/javascript">
    	var session_flag='<?php echo $_SESSION['loggedinflag'];?>';
    </script>
	<script type="text/javascript" src="scripts/mainpage.js"></script>
</head>
<body>
<h1>CS5339 Assignemnt 4 - list of alumni</h1>


<div style="width: 100%; overflow: hidden;">
	<div style="width: 300px; float: left;" id ="divColumnSelection">
		Select Columns: <br/>
	</div>
    <div style="margin-left: 320px;" id ="divColumnFilters">
		Enter Filters: <br/>
	</div>
</div>
<div id="divSortField">
	Sort by : 
	<select name="cmbSortBy" id="cmbSortBy">
	</select>
	<select name="cmbSortDir" id="cmbSortDir">
		<option value="asc">Ascending</option>
		<option value="desc">Descending</option>
	</select>
</div>
<div id="divPageSize">
Page size: 	
<select name="cmbPageSize" id="cmbPageSize">
	<option value="10" selected>10</option>
	<option value="50">50</option>
	<option value="100">100</option>
	<option value="all">All</option>
</select>
</div>
<br/>
<input type="button" id="cmdGetData" value="Filter Data" onclick="filterData();"/>
<br/>
<div id="dataTable">

</div>
</body>
</html>