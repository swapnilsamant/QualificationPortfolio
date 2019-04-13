<?php
require_once("includes/common.php");
require_once("includes/conn.php");

$col_list = json_decode($_POST["col_list"]);
$filter_list = json_decode($_POST["filter_list"]);
$sort_field = fix_string($_POST["sort_field"]);
$sort_dir = fix_string($_POST["sort_dir"]);
$page_size = fix_string($_POST["page_size"]);
$page_offset = fix_string($_POST["page_offset"]);

$sql_select = "SELECT SQL_CALC_FOUND_ROWS alum_pk AS id,";
foreach ($col_list as $col_val)
{
	switch($col_val)
	{
		case 'GradYear':
			$sql_select .= ' TRIM(graduation_academic_year) AS '.$col_val.',';
			break;
		case 'Semester':
			$sql_select .= ' TRIM(graduation_semester) AS '.$col_val.',';
			break;
		case 'LastName':
			$sql_select .= ' TRIM(alum_last_name) AS '.$col_val.',';
			break;
		case 'FirstName':
			$sql_select .= ' TRIM(alum_first_name) AS '.$col_val.',';
			break;	
		case 'Major':
			$sql_select .= ' TRIM(alum_major) AS '.$col_val.',';
			break;	
		case 'Classification':
			$sql_select .= ' TRIM(alum_classification) AS '.$col_val.',';
			break;															
		case 'Degree':
			$sql_select .= ' TRIM(alum_degree) AS '.$col_val.',';
			break;	
	}
}

$sql_select = substr($sql_select, 0, -1);

if (count($filter_list) > 0)
{
	$conditions = [];
	$parameters = [];
	$parameter_data_type = [];
	foreach ($filter_list as $key => $value)
	{
		switch($key)
		{
			case 'GradYear':
				$conditions[] = 'TRIM(graduation_academic_year) LIKE ?';
				$parameters[] = $link->real_escape_string($value)."%";
				$parameter_data_type[] = 's';
				break;
			case 'Semester':
				$conditions[] = 'TRIM(graduation_semester) LIKE ?';
				$parameters[] = $link->real_escape_string($value)."%";
				$parameter_data_type[] = 's';
				break;
			case 'LastName':
				$conditions[] = 'TRIM(alum_last_name) LIKE ?';
				$parameters[] = $link->real_escape_string($value)."%";
				$parameter_data_type[] = 's';
				break;
			case 'FirstName':
				$conditions[] = 'TRIM(alum_first_name) LIKE ?';
				$parameters[] = $link->real_escape_string($value)."%";
				$parameter_data_type[] = 's';
				break;	
			case 'Major':
				$conditions[] = 'TRIM(alum_major) LIKE ?';
				$parameters[] = $link->real_escape_string($value)."%";
				$parameter_data_type[] = 's';
				break;	
			case 'Classification':
				$conditions[] = 'TRIM(alum_classification) LIKE ?';
				$parameters[] = $link->real_escape_string($value)."%";
				$parameter_data_type[] = 's';
				break;															
			case 'Degree':
				$conditions[] = 'TRIM(alum_degree) LIKE ?';
				$parameters[] = $link->real_escape_string($value)."%";
				$parameter_data_type[] = 's';
				break;	
		}
	}
	
	if ($conditions)
	{
		$sql_where = " WHERE ".implode(" AND ", $conditions);
		$bind_data_types = "".implode($parameter_data_type);;
	}
}

$sort_direction = ' ASC ';
$sql_sort = '';
switch ($sort_dir)
{
	case 'asc':
		$sort_direction = ' ASC ';
		break;
	case 'desc':
		$sort_direction = ' DESC ';
		break;
}

switch($sort_field)
{
	case 'GradYear':
		$sql_sort .= ' ORDER BY graduation_academic_year' . $sort_direction;
		break;
	case 'Semester':
		$sql_sort .= ' ORDER BY graduation_semester'. $sort_direction;
		break;
	case 'LastName':
		$sql_sort .= ' ORDER BY alum_last_name'. $sort_direction;
		break;
	case 'FirstName':
		$sql_sort .= ' ORDER BY alum_first_name'. $sort_direction;
		break;	
	case 'Major':
		$sql_sort .= ' ORDER BY alum_major'. $sort_direction;
		break;	
	case 'Classification':
		$sql_sort .= ' ORDER BY alum_classification'. $sort_direction;
		break;															
	case 'Degree':
		$sql_sort .= ' ORDER BY alum_degree'. $sort_direction;
		break;	
}

if ($page_size <> 'all')
	$sql_pagination = " LIMIT ". $page_offset . ", ". $page_size;
else
	$sql_pagination = "";

$sql = $sql_select;
$sql .= " FROM alumni_profile ";
if (strlen($sql_where) > 0)
	$sql .= $sql_where;

$sql .= $sql_sort;
$sql .= $sql_pagination;


$select_stmt = $link->stmt_init();
$select_stmt = $link->prepare($sql);
DynamicBindVariables($select_stmt, $parameters, $parameter_data_type);
$select_stmt->execute();
$select_stmt->store_result();

// Get metadata for field names
$meta = $select_stmt->result_metadata();

// This is the tricky bit dynamically creating an array of variables to use
// to bind the results
while ($field = $meta->fetch_field()) { 
	$var = $field->name; 
	$$var = null; 
	$fields[$var] = &$$var;
}

// Bind Results
call_user_func_array(array($select_stmt,'bind_result'),$fields);

// Fetch Results
$i = 0;
while ($select_stmt->fetch()) {
	$results[$i] = array();
	foreach($fields as $k => $v)
		$results[$i][$k] = $v;
	$i++;
}

//get total number of rows.
$query="SELECT FOUND_ROWS()";
$stmt = $link->prepare($query);
$stmt->execute();
$stmt->bind_result($num);
while($stmt->fetch()){
	$count=$num;
}
$results_encode = array('rec_count' => $count, 
		  'records' => $results
		  );
echo json_encode($results_encode);


//http://dev.flauschig.ch/wordpress/?p=213
function DynamicBindVariables($stmt, $params, $parameter_data_type)
{
	if ($params != null)
	{
		// Generate the Type String (eg: 'issisd')
		$types = '';
		foreach($parameter_data_type as $param_type)
		{
			$types .= $param_type;
		}
	
		// Add the Type String as the first Parameter
		$bind_names[] = $types;
	
		// Loop thru the given Parameters
		for ($i=0; $i<count($params);$i++)
		{
			// Create a variable Name
			$bind_name = 'bind' . $i;
			// Add the Parameter to the variable Variable
			$$bind_name = $params[$i];
			// Associate the Variable as an Element in the Array
			$bind_names[] = &$$bind_name;
		}
			
		// Call the Function bind_param with dynamic Parameters
		call_user_func_array(array($stmt,'bind_param'), $bind_names);
	}
	return $stmt;
}

?>