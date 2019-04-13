<?php

require_once 'Token.php';

class Tokenizer 
{ 
	private $e; 
	private $i;
	private $currentChar;
	
	public function __construct($s) 
	{ 
		$this->e = $s;
		$this->i = 0;
	}

	public function nextToken()
	{
		// skip blank like characters

		while ($this->i < strlen($this->e) 
				&& strpos(" \n\t\r", $this->e[$this->i]) !== FALSE)
		{
			$this->i++;
		}

		if ($this->i >= strlen($this->e)) 
		{
			return new Token(TokenType::EOF);
		}

		 // check for INT
		$inputString = "";

		while ($this->i < strlen($this->e) 
				&& strpos("0123456789", $this->e[$this->i]) !== FALSE) 
		{
			$inputString .= $this->e[$this->i++];
		}
		
		if (strlen($inputString) > 0)
		{
			return new Token(TokenType::INT_TOKEN, $inputString);
		}

		// check for ID or reserved word    
		while ($this->i < strlen($this->e) 
				&& strpos("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ_", $this->e[$this->i])  !== FALSE) 
		{
			$inputString .= $this->e[$this->i++];
		}
		
		if (strlen($inputString) > 0)
		{
			if ($inputString == "if")
			{
				return new Token(TokenType::IF_TOKEN);
			}
			if ($inputString == "else") 
			{
				return new Token(TokenType::ELSE_TOKEN);
			}
			return new Token(TokenType::ID, $inputString);
		}

		

		 // We're left with strings or one character tokens
		 switch ($this->e[$this->i++]) 
		 {
			case "{":
				return new Token(TokenType::LBRACKET, "{");
			case "}":
				return new Token(TokenType::RBRACKET, "}");
			case "[":
				return new Token(TokenType::LSQUAREBRACKET, "[");
			case "]":
				return new Token(TokenType::RSQUAREBRACKET, "]");
			case "<":
				return new Token(TokenType::LESS, "<");
			case ">":
				return new Token(TokenType::GREATER, ">");
			case "=":
				return new Token(TokenType::EQUAL, "=");
			case '"':
				$value = "";
				while ($this->i < strlen($this->e) && $this->e[$this->i] != '"')
				{
					$c = $this->e[$this->i++];
					
					if ($this->i >= strlen($this->e))
					{
						return new Token(TokenType::OTHER);
					}
					// check for escaped double quote
					if ($c == '\\' && $this->e[$this->i] == '"')
					{
						$c='"';
						$this->i++;
					}
					$value .= $c;
				} 
				$this->i++;
				return new Token(TokenType::STRING_TOKEN, $value);
			default:
				//echo "Other: " . $this->i . PHP_EOL;
				// OTHER should result in exception
				return new Token(TokenType::OTHER);
		}

	}

}

?>