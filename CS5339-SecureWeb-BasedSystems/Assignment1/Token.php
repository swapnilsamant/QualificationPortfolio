<?php

require_once 'TokenType.php';

class Token 
{ 
	public $type;
	public $value;

	// multiple constructors from http://php.net/manual/en/language.oop5.decon.php

	public function __construct()
	{
		$a = func_get_args(); 
		$i = func_num_args(); 
		if (method_exists($this,$f='__construct'.$i)) { 
			call_user_func_array(array($this,$f),$a); 
		} 
	}

	public function __construct1($theType) 
	{
		$this->type = $theType;

	}

	public function __construct2($theType, $theValue) 
	{
		$this->type = $theType;
		$this->value = $theValue;
	}

	public function printToken()
	{
		switch($this->type)
		{
			case TokenType::LBRACKET:
				return "LBRACKET";
				break;
			case TokenType::RBRACKET:
				return "RBRACKET";
				break;
			case TokenType::LSQUAREBRACKET:
				return "LSQUAREBRACKET";
				break;
			case TokenType::RSQUAREBRACKET:
				return "RSQUAREBRACKET";
				break;
			case TokenType::STRING_TOKEN:
				return "STRING " . $this->value;
				break;
			case TokenType::EQUAL:
				return "EQUAL";
				break;
			case TokenType::LESS:
				return "LESS";
				break;
			case TokenType::GREATER:
				return "GREATER";
				break;
			case TokenType::IF_TOKEN:
				return "IF";
				break;
			case TokenType::ELSE_TOKEN:
				return "ELSE";
				break;
			case TokenType::ID:
				return "ID " . $this->value;
				break;
			case TokenType::INT_TOKEN:
				return "INT " . $this->value;
				break;
			case TokenType::EOF:
				return "EOF";
				break;
			default:
				return "OTHER";
				break;
		}
	}
}
?>