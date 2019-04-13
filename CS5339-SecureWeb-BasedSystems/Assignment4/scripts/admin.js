// client side javascript validation function
// Learning PHP, MySQL & JavaScript_ With jQuery, CSS & HTML5 (2014, O’Reilly Media) - Robin Nixon
function validate(form)
{
	fail = validateUsername(form.txtUserName.value)
	fail += validatePassword(form.txtPassword.value)
	
	if (form.cmbUserType.options[cmbUserType.selectedIndex].value == "admin")
	{
		fail += validateFirstName(form.txtFirstName.value.trim())
		fail += validateLastName(form.txtLastName.value.trim())	
	}

	if (fail == "")     return true
	else { alert(fail); return false }
}

// client side function to validate first name  
// checks for empty string and string length 
// max length is 255
// Learning PHP, MySQL & JavaScript_ With jQuery, CSS & HTML5 (2014, O’Reilly Media) - Robin Nixon
function validateFirstName(field)
{
	if (field == "") return "No first name was entered.\n"
	else if (field.length > 255) 
		return "First name must be less than 255 characters.\n"	
	return ""
}

// client side function to validate last name  
// checks for empty string and string length 
// max length is 255
// Learning PHP, MySQL & JavaScript_ With jQuery, CSS & HTML5 (2014, O’Reilly Media) - Robin Nixon
function validateLastName(field)
{
	if (field == "") return "No Last Name was entered.\n"
	else if (field.length > 255) 
		return "Last name must be less than 255 characters.\n"	
	return ""
}

// client side function to validate username  
// checks for empty string, string lenght
// valid characters for username are a-z, A-Z, 0-9, "_" and "-"
// min length is 5, max length is 64
// Learning PHP, MySQL & JavaScript_ With jQuery, CSS & HTML5 (2014, O’Reilly Media) - Robin Nixon
function validateUsername(field)
{
	if (field == "") return "No Username was entered.\n"
	else if (field.length < 5)
		return "Username must be at least 5 characters.\n"
	else if (field.length > 64)
		return "Username must be less than 64 characters.\n"		
	else if (/[^a-zA-Z0-9_\-]/.test(field))
		return "Only a-z, A-Z, 0-9, - and _ allowed in Usernames.\n"
	return ""
}

// client side function to validate password  
// checks for empty string, string lenght
// valid characters for password are a-z, 0-9
// min length is 6, max length is 64
// Learning PHP, MySQL & JavaScript_ With jQuery, CSS & HTML5 (2014, O’Reilly Media) - Robin Nixon
function validatePassword(field)
{
	if (field == "") return "No Password was entered.\n"
	else if (field.length < 6)
		return "Password must be at least 6 characters.\n"
	else if (field.length > 64)
		return "Password must be less than 64 characters.\n"		
	else if (!/[a-z]/.test(field) || !/[0-9]/.test(field))
		return "Password requires one each of a-z and 0-9.\n"
	return ""
}

function onUserTypeChange(cmbUserType)
{
	if (cmbUserType.options[cmbUserType.selectedIndex].value == "admin")
	{
		document.getElementById("txtFirstName").disabled = false;
		document.getElementById("txtLastName").disabled = false;
		document.getElementById("cmbUserProfile").disabled = true;
	}
	else
	{
		document.getElementById("txtFirstName").disabled = true;
		document.getElementById("txtLastName").disabled = true;
		document.getElementById("cmbUserProfile").disabled = false;
	}
}

window.onload = function() 
{
	onUserTypeChange(document.getElementById("cmbUserType"));
};