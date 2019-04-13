This folder contains the client script for the UDP file transfer lab.

Usage:

`python client.py <mode> <server_file_name> <client_file_name> <server_ip_address> <server_port_number>`

Where:<br />
mode: upload or download<br />
server_file_name: name of the file on the server to be uploaded to the server or downloaded from the server<br />
client_file_name: name of the file on the client to be uploaded to the server or downloaded from the server<br />
server_ip_address: IP address of the server<br />
server_port_number: Port number the server is listening on<br />

Example:<br />

`python client.py download server_file.txt client_file.txt 127.0.0.1 5001`