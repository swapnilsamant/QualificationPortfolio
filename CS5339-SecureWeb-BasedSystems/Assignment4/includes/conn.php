<?php
// File contains database connection module
$cssrvlab = "cssrvlab01"; //UTEP CS Server

$referer = $_SERVER['HTTP_REFERER'];

// get referrer from browser
$domain = parse_url($referer); 

// check if referrer is UTEP CS Server
if(strpos($domain['host'], $cssrvlab) !== false)
{
    $db_hostname="cssrvlab01.utep.edu";
    $db_username="sssamant";
    $db_password="cs5339pass";
    $db_name="sssamant_db";
} 
else 
{
    // otherwise its localhost
    $db_hostname="localhost";
    $db_username="root";
    $db_password="mysql";
    $db_name="sssamant_db";
}

$link = mysqli_connect($db_hostname, $db_username, $db_password, $db_name);

if (!$link) 
{
    echo "Error: Unable to connect to MySQL." . PHP_EOL;
    echo "Debugging errno: " . mysqli_connect_errno() . PHP_EOL;
    echo "Debugging error: " . mysqli_connect_error() . PHP_EOL;
    die('Connection Error');
    exit;
}
?>