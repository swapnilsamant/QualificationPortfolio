var columnList = {
	'GradYear' : 'Graduation Year',
	'Semester' : 'Semester',
	'LastName':'Last Name',
	'FirstName':'First Name',
	'Major': 'Major',
	'Classification': 'Classification',
	'Degree':'Degree'	
};

var columnSelectionDivId = 'divColumnSelection';
var columnFilterDivId = 'divColumnFilters';
var dataTable = 'dataTable';
var selectedColCount = 0;
var page_offset = 0;

function tableColumn(colName, colDisplayText){
	this.column_name = colName;
	this.display_text = colDisplayText;
	this.checkbox_name = 'chk' + colName;
	this.filter_input = 'txt' + colName;
	this.option_value = colName;
}

//https://siongui.github.io/2012/10/05/javascript-http-post-request/

HTTPPOST = function(url, keyValuePairs, callback, failCallback) 
{
	var xmlhttp;
  
	if (window.XMLHttpRequest) {
	  // code for IE7+, Firefox, Chrome, Opera, Safari
	  xmlhttp=new XMLHttpRequest();
	} else {
	  // code for IE6, IE5
	  xmlhttp=new ActiveXObject("Microsoft.XMLHTTP");
	}
  
	xmlhttp.onreadystatechange = function() {
	  if (xmlhttp.readyState == 4) {
		if (xmlhttp.status == 200)
		  callback(xmlhttp.responseText, url);
		else
		  failCallback(url);
	  }
	};
  
	xmlhttp.open("POST", url, true);
	xmlhttp.setRequestHeader("Content-type", "application/x-www-form-urlencoded");
  
	var kvpairs = '';
	for (var key in keyValuePairs) {
	  if (kvpairs == '')
		kvpairs = encodeURIComponent(key) + '=' +
				  encodeURIComponent(keyValuePairs[key]);
	  else
		kvpairs = kvpairs + '&' + encodeURIComponent(key) + '=' +
				  encodeURIComponent(keyValuePairs[key]);
	}
  
	xmlhttp.send(kvpairs);
};

var callback = function(responseText, url) {
	// write your own handler for success of HTTP POST

	if (!(responseText) || responseText == "null"){
		document.getElementById(dataTable).innerHTML = "No data for selected criteria.";
		return false;
	}

	var json_response = JSON.parse(responseText);
	var row_count = parseInt(json_response['rec_count']);
	if (row_count <= 0)
	{
		document.getElementById(dataTable).innerHTML = "No data for selected criteria.";
		return false;
	}
	var json_rows = json_response['records'];
	
	//alert('responseText from url ' + url + ':\n'
	//	  + json_rows.length);
	
	var table_head = [];
	var table_head_id = [];


	var jsonObj = json_rows[0];
	Object.keys(jsonObj).forEach(function(colName) {
		if (colName in columnList){
			table_head.push(columnList[colName]);
			table_head_id.push(colName);
		}
	});
	//alert(table_head);

	var tbl = document.createElement('table');

	tbl.style.width = '100%';
	tbl.style.tableLayout = 'fixed';
	tbl.setAttribute('border', '1');

	var thead = document.createElement('thead');
	var tr = document.createElement('tr');
	for (var i = 0; i < table_head.length; i++) {
		var th = document.createElement('th');
		th.appendChild(document.createTextNode(table_head[i]));
		tr.appendChild(th);	
	}
	if (session_flag.length > 0)
	{	
		var th = document.createElement('th');
		th.appendChild(document.createTextNode('Profile Link'));
		tr.appendChild(th);	
	}


	thead.appendChild(tr);
	tbl.appendChild(thead);

	var tbdy = document.createElement('tbody');
	for (var i = 0; i < json_rows.length; i++) {
	  var tr = document.createElement('tr');
	  var json_row = json_rows[i];
	  for (var j = 0; j < table_head.length; j++) {
		  var td = document.createElement('td');
		  td.appendChild(document.createTextNode(json_row[table_head_id[j]]))
		  tr.appendChild(td)
		}
		
		if (session_flag.length > 0)
		{
			var td = document.createElement('td');
			var a = document.createElement('a');
			var linkText = document.createTextNode('Profile');
			a.appendChild(linkText);
			a.title = "Go to users profile";
			a.href = "user.php?profile_id=" + json_row['id'];
			a.style.margin = "5px";
			
			td.appendChild(a);	
		}
	
		tr.appendChild(td);	

		tbdy.appendChild(tr);
	  }
	tbl.appendChild(tbdy);

	var pageSize = document.getElementById('cmbPageSize')[document.getElementById('cmbPageSize').selectedIndex].value;
	var pageCount = row_count/parseInt(pageSize);
	var currentPageNumber = (page_offset/pageSize) + 1;

	//alert(currentPageNumber);

	if (pageCount > 1)
	{
		var tfoot = document.createElement('tfoot');
		var tr = document.createElement('tr');
		var tf = document.createElement('td');
		if (session_flag.length > 0)
		{	
			tf.colSpan = table_head.length + 1;
		}
		else{
			tf.colSpan = table_head.length;
		}
		tf.style.wordWrap = 'break-word';

		for (var pageIndex =1; pageIndex <= pageCount; pageIndex++){
			if (currentPageNumber != pageIndex){
				var a = document.createElement('a');
				var linkText = document.createTextNode(pageIndex);
				a.appendChild(linkText);
				a.title = "Go to page " + pageIndex;
				a.href = "#";
				a.style.margin = "5px";
				
				a.onclick = function(pageIndex) {
					return(function() { 
						filterData((pageIndex-1) * pageSize); 
					});
				}(pageIndex);
				tf.appendChild(a);
			}
			else
			{
				var pageNumSpan = document.createElement('span')
				pageNumSpan.innerHTML = pageIndex;
				pageNumSpan.style.margin = "5px";
				tf.appendChild(pageNumSpan);
			}

			//document.body.appendChild(a);
		}
		
		tr.appendChild(tf);	
		tfoot.appendChild(tr);
		tbl.appendChild(tfoot);
	}

	document.getElementById(dataTable).appendChild(tbl);
  };


  var failCallback = function(url) {
	// write your own handler for failure of HTTP POST
	alert('fail to post ' + url);
  };


function filterData()
{
	document.getElementById(dataTable).innerHTML = "";

	var col_list = [];
	var filter_list = {};
	var sort_field = '';
	var sort_dir = '';
	var page_size = '';
	page_offset = 0;
	if (arguments.length > 0){
		page_offset = arguments[0];	
	}

	for (var key in columnList) 
	{
		if (document.getElementById('chk' + key).checked){
			col_list.push(key);
			if ((document.getElementById('txt' + key).value.trim().length) > 0){
				filter_list[key] = document.getElementById('txt' + key).value;
			}
		}
	}	
	sort_field = document.getElementById('cmbSortBy')[document.getElementById('cmbSortBy').selectedIndex].value;
	sort_dir = document.getElementById('cmbSortDir')[document.getElementById('cmbSortDir').selectedIndex].value;
	page_size = document.getElementById('cmbPageSize')[document.getElementById('cmbPageSize').selectedIndex].value;

	//var col_list_str = encodeURIComponent(JSON.stringify(col_list));
	//var filter_list_str = encodeURIComponent(JSON.stringify(filter_list));

	var req_url = 'get_alumni_data.php';

	keyValuePairs = {'col_list': JSON.stringify(col_list),
					'filter_list': JSON.stringify(filter_list),
					'sort_field': sort_field,
					'sort_dir': sort_dir,
					'page_size': page_size,
					'page_offset': page_offset};

	HTTPPOST(req_url, keyValuePairs, callback, failCallback);
}

window.onload = function(){
	displayColumnSelection();
	filterData();
}

function displayColumnSelection()
{
	
	var columnContainer = document.getElementById(columnSelectionDivId);
	var filterContainer = document.getElementById(columnFilterDivId);
	var selectSortItems = document.getElementById('cmbSortBy');

	for (var key in columnList) 
	{
		selectSortItems.options[selectSortItems.options.length] = new Option(columnList[key], key);

		var txtFilter = document.createElement('input');
		txtFilter.type = "text";
		txtFilter.name = "txt" + key;
		txtFilter.id = "txt" + key;

		var textboxLabel = document.createElement('label')
		textboxLabel.htmlFor = 'txt' + key;
		textboxLabel.appendChild(document.createTextNode(columnList[key] + ": "));	
		
		var txtLinebreak = document.createElement("br");

		filterContainer.appendChild(textboxLabel);
		filterContainer.appendChild(txtFilter);
		filterContainer.appendChild(txtLinebreak);

		var chkCol = document.createElement('input');
		chkCol.type = "checkbox";
		chkCol.name = 'chk' + key;
		chkCol.value = key;
		chkCol.id = 'chk' + key;
		chkCol.data = key;
		chkCol.checked = "checked";

		chkCol.onclick = function onCheckboxChange(){
			if (this.checked){
				document.getElementById('txt'+ this.data).disabled = false;
				//selectSortItems.options.add(new Option(columnList[this.data], this.data), selectSortItems.options[2]);
				selectSortItems.style.display = 'none';
				for (i = 0; i < selectSortItems.length; i++ ){
					if (selectSortItems.options[i].value == this.data){
						selectSortItems.options[i].style.display = 'block';
						//selectSortItems.remove(i);
					}
				}
				selectSortItems.style.display = 'inline';
				selectedColCount++;
			}
			else{
				if (selectedColCount <= 1){
					alert ('At least one column should be selected.');
					return false;
				}

				document.getElementById('txt'+ this.data).disabled = true;
				selectSortItems.style.display = 'none';
				for (i = 0; i < selectSortItems.length; i++ ){
					if (selectSortItems.options[i].value == this.data){
						selectSortItems.options[i].style.display = 'none';
						//selectSortItems.remove(i);
						if (selectSortItems.selectedIndex == i){
							selectSortItems.selectedIndex = -1;
						}
					}
				}
				selectSortItems.style.display = 'inline';
				selectedColCount--;				
			}
		};


		var label = document.createElement('label');
		label.htmlFor = 'chk' + key;
		label.appendChild(document.createTextNode(columnList[key]));

		var chkLinebreak = document.createElement("br");

		columnContainer.appendChild(chkCol);
		columnContainer.appendChild(label);
		columnContainer.appendChild(chkLinebreak);

		selectedColCount++;
	}
}