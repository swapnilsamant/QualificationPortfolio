// client side javascript validation function
// Learning PHP, MySQL & JavaScript_ With jQuery, CSS & HTML5 (2014, O’Reilly Media) - Robin Nixon
function validate(form)
{
	fail = validateEmail(form.txtEmailAddress.value)
	fail += validateEmployerName(form.txtEmployerName.value)
	
	if (fail == "")
	{
		return true;
	}
	else 
	{ 
		alert(fail); 
		return false; 
	}
}

// client side function to validate email address  
// checks for empty string and string length 
// max length is 255
// Learning PHP, MySQL & JavaScript_ With jQuery, CSS & HTML5 (2014, O’Reilly Media) - Robin Nixon
function validateEmail(field)
{
    if (field.length > 200) 
		return "First name must be less than 200 characters.\n"	
	var re = /^(([^<>()\[\]\\.,;:\s@"]+(\.[^<>()\[\]\\.,;:\s@"]+)*)|(".+"))@((\[[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\])|(([a-zA-Z\-0-9]+\.)+[a-zA-Z]{2,}))$/;
	if (!(re.test(String(field).toLowerCase())))
	{
		return "Invalid email address.\n"	
	}

	return ""
}

// client side function to validate last name  
// checks for empty string and string length 
// max length is 255
// Learning PHP, MySQL & JavaScript_ With jQuery, CSS & HTML5 (2014, O’Reilly Media) - Robin Nixon
function validateEmployerName(field)
{
    if (field.length > 500) 
		return "Employer name must be less than 500 characters.\n";
	else if (/[^a-zA-Z0-9_\-&,#@* ]/.test(field))
		return "Only a-z, A-Z, 0-9, -, _, *, @, #, &, comma and space allowed in employer name.\n"
	return ""
}