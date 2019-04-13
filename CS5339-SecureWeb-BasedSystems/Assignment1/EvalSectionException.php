<?php

class EvalSectionException extends Exception 
{
	public function __construct($m)
	{
		echo PHP_EOL . "Parsing or execution Exception: ". $m . PHP_EOL . PHP_EOL;
  	}
}

?>