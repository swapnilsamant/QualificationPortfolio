<html>
  <head>
    <title>CS 4339/5339 PHP assignment</title>
  </head>
  <body>
    <pre>
<?php
require_once 'Tokenizer.php';
require_once 'EvalSectionException.php';

// Global variables
$map = array();
$oneIndent = "   ";

// Check if Request method is GET or POST
// If Request method if GET, then use hardcoded file location
// If Request method is POST, then use the file location is txtFileURL POST variable
if ($_SERVER['REQUEST_METHOD'] === 'POST') 
{
	if(isset($_POST["submit"])) 
	{
		$url = htmlspecialchars($_POST["txtFileURL"]);
	}
}
else
{
	$url = "http://cs5339.cs.utep.edu/longpre/assignment1/fall18Testing.txt";
}

// Check for valid URL: https://www.w3schools.com/php/filter_validate_url.asp
// Remove all illegal characters from a url
$url = filter_var($url, FILTER_SANITIZE_URL);

// Validate url
if (!(filter_var($url, FILTER_VALIDATE_URL))) 
{
	die("$url is not a valid URL.");
} 

// Check if URL exists
$file_headers = @get_headers($url);

if(!$file_headers || $file_headers[0] == 'HTTP/1.1 404 Not Found') 
{
	die("File doesn't exist. Please check URL.");
}

// Read file from URL
$inputFile = file_get_contents($url);

$t = new Tokenizer($inputFile);

$currentToken = $t->nextToken();

$section = 0;
$result = "";
while ($currentToken->type != TokenType::EOF) 
{
	echo "section ". ++$section . PHP_EOL;
	try 
	{
		evalSection();
		echo "Section result:" . PHP_EOL;
		echo $result . PHP_EOL;
	}
	//catch exception
	catch(Exception $e) 
	{
		// skip to the end of section
		while ($currentToken->type != TokenType::RSQUAREBRACKET
					&& $currentToken->type != TokenType::EOF) 
		{
			$currentToken = $t->nextToken();
		}
		$currentToken = $t->nextToken();
	}
}


function evalSection() 
{
	// <section> ::= [ <statement>* ]
	global $result;
	global $currentToken;
	global $map;
	global $t;
	global $oneIndent;

	$result = "";
	$map = array();

	if ($currentToken->type != TokenType::LSQUAREBRACKET) 
	{
		throw new EvalSectionException("A section must start with \"[\"");
	}

	echo "[" . PHP_EOL;
	$currentToken = $t->nextToken();
	while ($currentToken->type != TokenType::RSQUAREBRACKET
			&& $currentToken->type != TokenType::EOF) 
	{
		evalStatement($oneIndent, true);
	}
	echo "]" . PHP_EOL;
	$currentToken = $t->nextToken();	
}


function evalStatement($indent, $exec)
{
	// exec it true if we are executing the statements in addition to parsing
	// <statement> ::= STRING | <assignment> | <conditional>
	global $currentToken;
	global $result;
	global $t;

	//echo $currentToken->type . PHP_EOL;

	switch ($currentToken->type) 
	{
		case TokenType::ID:
			evalAssignment($indent, $exec);
			break;
		case TokenType::IF_TOKEN:
			evalConditional($indent, $exec);
			break;
		case TokenType::STRING_TOKEN:
			if ($exec)
			{
				$result = $result . $currentToken->value . PHP_EOL;
			}
			echo $indent . "\"" . $currentToken->value . "\"" . PHP_EOL;
			$currentToken = $t->nextToken();
			break;
		default:
			throw new EvalSectionException("invalid statement");
	}
}


function evalAssignment($indent, $exec) 
{
	// <assignment> ::= ID '=' INT
	// we know currentToken is ID 

	global $currentToken;
	global $result;
	global $map;
	global $t;

	$key = $currentToken->value;
	echo $indent . $key;
	$currentToken = $t->nextToken();
	if ($currentToken->type != TokenType::EQUAL) 
	{
		throw new EvalSectionException("equal sign expected");
	}
	echo "=";
	$currentToken = $t->nextToken();

	if ($currentToken->type != TokenType::INT_TOKEN) 
	{
		throw new EvalSectionException("integer expected");
	}

	$value = intval($currentToken->value);
	echo $value . PHP_EOL;
	$currentToken = $t->nextToken();
	if ($exec)
	{
		$map[$key] = $value;
	}
}

function evalConditional($indent, $exec) 
{
	// <conditional> ::= 'if' <condition> '{' <statement>* '}' [ 'else' '{'
	// We know currentToken is "if"
	global $currentToken;
	global $result;
	global $map;
	global $t;
	global $oneIndent;

	echo $indent . "if ";
	$currentToken = $t->nextToken();
	$trueCondition = evalCondition($exec);

	if ($currentToken->type != TokenType::LBRACKET) 
	{
		throw new EvalSectionException("left bracket extected");
	}
	echo " {" . PHP_EOL;
	$currentToken = $t->nextToken();
	while ($currentToken->type != TokenType::RBRACKET
			&& $currentToken->type != TokenType::EOF) 
	{
		if ($trueCondition) 
		{
			evalStatement($indent . $oneIndent, $exec);
		} 
		else 
		{
			evalStatement($indent . $oneIndent, false);
		}
	}

	if ($currentToken->type == TokenType::RBRACKET) 
	{
		echo $indent . "}" . PHP_EOL;
		$currentToken = $t->nextToken();
	} 
	else
	{
		throw new EvalSectionException("right bracket expected");
	}
		
	if ($currentToken->type == TokenType::ELSE_TOKEN) 
	{
		echo $indent . "else " ;
		$currentToken = $t->nextToken();

		if ($currentToken->type != TokenType::LBRACKET) 
		{
			throw new EvalSectionException("left bracket expected");
		}
		echo "{" . PHP_EOL;

		$currentToken = $t->nextToken();

		while ($currentToken->type != TokenType::RBRACKET
				&& $currentToken->type != TokenType::EOF) 
		{
			if ($trueCondition) 
			{
				evalStatement($indent . $oneIndent, false);
			} 
			else 
			{
				evalStatement($indent . $oneIndent, $exec);
			}
		}

		if ($currentToken->type == TokenType::RBRACKET) 
		{
			echo $indent . "}" . PHP_EOL;
			$currentToken = $t->nextToken();
		} 
		else
		{
			throw new EvalSectionException("right bracket expected");
		} 
	}
}

function evalCondition($exec) 
{ 
	// <condition> ::= ID ('<' | '>' | '=') INT
	global $currentToken;
	global $result;
	global $map;
	global $t;

	$v1=NULL; // value associated with ID
	if ($currentToken->type != TokenType::ID) 
	{
		throw new EvalSectionException("identifier expected");
	}

	$key = $currentToken->value;

	echo $key;
	
	if ($exec) 
	{
		$v1 = $map[$key];
		if ($v1 == NULL) 
		{
			throw new EvalSectionException("undefined variable");
		}
	} 
	$currentToken = $t->nextToken();
	$operator = $currentToken->type;

	if ($currentToken->type != TokenType::EQUAL
			&& $currentToken->type != TokenType::LESS
			&& $currentToken->type != TokenType::GREATER) 
	{
		throw new EvalSectionException("comparison operator expected");
	}

	echo $currentToken->value;
	$currentToken = $t->nextToken();

	if ($currentToken->type != TokenType::INT_TOKEN) 
	{
		throw new EvalSectionException("integer expected");
	}
	$value = intval($currentToken->value);

	echo $value . " ";

	$currentToken = $t->nextToken();

	// compute return value
	if (!$exec)
	{
		return false;
	}
		
	$trueResult = false;

	switch ($operator) 
	{
		case TokenType::LESS:
			$trueResult = $v1 < $value;
			break;
		case TokenType::GREATER:
			$trueResult = $v1 > $value;
			break;
		case TokenType::EQUAL:
			$trueResult = $v1 == $value;
	}
	return $trueResult;
}


?>
    </pre>
  </body>
</html>
