<?php

abstract class TokenType
{
	const LBRACKET = 0;
	const RBRACKET = 1;
	const LSQUAREBRACKET = 2;
	const RSQUAREBRACKET = 3;
	const STRING_TOKEN = 4;
	const EQUAL = 5;
	const LESS = 6;
	const GREATER = 7;
	const IF_TOKEN = 8;
	const ELSE_TOKEN = 9;
	const ID = 10;
	const INT_TOKEN = 11;
	const EOF = 12;
	const OTHER = 13;
}
?>