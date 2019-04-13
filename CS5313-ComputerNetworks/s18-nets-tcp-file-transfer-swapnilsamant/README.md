# nets-tcp-file-transfer

The objective of this assignment is to define a file transfer protocol using TCP. The protocol is implemented in python 
using a client server model. This repositors has the following file structure: <br />
```
.
│   README.md                       This README file
│   TCP-FileTransferProtocol.pptx   Graphical representation of upload and download protocol
│
└───client
│   │   client_speech.txt           Test file
│   │   client.py                   Client program
│   │   params.py                   To parse command line arguments
│
└───server
│   │   declaration.txt             Test file
│   │   params.py                   To parse command line arguments
│   │   server.py                   Servre program
│   │   speech.txt                  Test file
│
└───proxy
    │   params.py                   To parse command line arguments
    │   stammerProxy.py             Stammering proxy for testing
```

Parts of server.py and client.py have been reproduced from https://github.com/robustUTEP/nets-tcp-proxy.git. <br />
params.py and stammerProxy.py are from the repository listed above.<br />

The file transfer protocol uses a state machine approach along with the "select" system call. <br />

### Download protocol
 
Upon parsing the command line arguments, the client enters into an 'init_download' state if download mode is specified.
In this mode the client creates a message with 256 bytes, the first byte specifies that the message is a download message. The remaining 
255 bytes are used to specify the file name. This message is written to the clients write buffer and the client enters the 'send_check_file_download' state. <br />

In the 'send_check_file_download' state, the client waits for write buffer to be sent out to the server. Upon sending the message, the client enters the 'check_download' state. In the 'check_download' state the client waits for a 9 byte response from the server. <br/>

Upon receiving the first message from client, the server enters the 'client_connect' state. In this state the server awaits a 256 byte message. If the first byte specifies that the message is a file download message, then the server parses the file name from the message 
and enters a 'check_download' state. In this state the server checks if the file requeted by the client exists on the server. If it exists, the server creates a 9 byte message, in which the first byte specifies that the file exists and the remaining 8 bytes specify the file size.
This message is written to the servers write buffer and the server enters the 'send_check_download' state. If the file does not exist on the server, then the message spcifies that the file does not exist. This message is written to the server write buffer and the and teh server entrers the 'download_complete' state.<br />

In the 'send_check_download' state, the server waits for the output buffer to be sent to the client. After the contents of write buffer are written out, the server enters the 'check_download_confirmation' state. In this state the server waits for a one byte message from the client.
<br />

When the clients receives a 9 byte message from the server in the 'check_download' state, it enters the 'prepare_download_confirmation' state. The first byteof the message specifies the file status on the server. If the status shows the file exists then the client check the remaining 8 bytes for the file size. If there is enough space on the client to store the file, then the client prepares a one byte message for the server to begin the file transfer. If the first byte of the message specifies an error on server or that the file does not exist on the server, then the client enters the 'download_complete' state. If the client does not have enough space to store the requested file, then the client creates a message for the server to stop the file transfer and enters the 'download_complete' state. The message to start or stop the file transfer is written to the clients write buffer. If the client wishes to continue the file transfer then the client enters the 'confirm_download' state. If the client wishes to stop the file transfer then the client enters the 'download_complete' state. <br />

In the 'confirm_download' state the client waits for the contents of write buffer to be sent out to the server. After the contents of the write buffer are written out to the server, the client enters the 'downloading' state. Upon receivng the confirmation to start the file download, the server enters the 'downloading' state. In the 'downloading' state, the server, writes out the contents of the requetsed file to the servers write buffer until the completed file as been written to the buffer. The client, in the 'downloading' state, read the contents of the file sent by the server, until all the bytes have been received. Upon sending all bytes, the server enters the 'download_complete' state. Upon receiving all bytes, the client enters the 'download_complete' state as well. <br />

In the 'download_complete' state, the server closes the client socket. In the 'download_complete' state, the client closes the server socket and exits. <br />


### Upload protocol
 
Upon parsing the command line arguments, the client enters into an 'init_upload' state if upload mode is specified.
In this mode the client creates a message with 256 bytes, the first byte specifies that the message is a upload message. The remaining 
255 bytes are used to specify the file name. This message is written to the clients write buffer and the client enters the 'send_check_file_upload' state. <br />

In the 'send_check_file_upload' state, the client waits for write buffer to be sent out to the server. Upon sending the message, the client enters the 'check_upload' state. In the 'check_upload' state the client waits for a one byte response from the server. <br/>

Upon receiving the first message from client, the server enters the 'client_connect' state. In this state the server awaits a 256 byte message. If the first byte specifies that the message is a file upload message, then the server parses the file name from the message 
and enters a 'check_upload' state. In this state the server checks if the file requeted by the client exists on the server. If it does not exist, the server creates a one byte message, which specifies that the file does not. This message is written to the servers write buffer and the server enters the 'send_check_upload' state. If the file does exist on the server or if the server encounters an error, then the message spcifies that the file transfer cannot proceed and the server enters the 'upload_complete' state. <br />

In the 'send_check_upload' state, the server waits for the output buffer to be sent to the client. After the contents of write buffer are written out, the server enters the 'check_file_upload_size' state. In this state the server waits for a 8 byte message from the client.<br />

When the clients receives a one byte message from the server in the 'check_upload' state, it check if the server wishes to proceed with the file transfer. If it determines that the file transfer shold proceed, the the client enters the 'prepare_upload_file_size' state. If the client determines that the file transfer should not proceed, the the client enters the 'upload_complete' state. In the 'prepare_upload_file_size' state, the client prepares a 8 byte message with the size of the file to be uploaded. This message is written to the clients write buffer and the client enters the 'send_file_upload_size_response' in the 'send_file_upload_size_response' state, the client waits for the write buffer to be written out to the server. After the write buffer is written out to the server, the client enters the 'process_upload_file_size_response' state. In this state, the client waits for a one byte response from the server. <br />

When the server receives a 8 byte message from the client in the 'check_file_upload_size' state, it determines the size of the file to be uploaded from the message. If the server has enough space for the file, then the server prepares a message to proceed with the file transfer. This message is written to the servers write buffer and the server enters the 'uploading' state. In the uploading state the server waits for the client to start uploading the file. If the server determines that the file transfer should not proceed, the the server creates a message to stop the file transfer, this message is written to the servers write buffer and the server enters the 'upload_complete' state.<br />

When the client receives a one byte message to proceed with the file transfer while in the 'process_upload_file_size_response' state, the client enters the 'uploading' state. If the one byte message received in this state signifies that the file transfer should not proceed, then the client enters the 'upload_complete' state. In the 'uploading' state, the client writes the contents of the file to the clients write buffer until the complete file has been written. In the 'uploading' state, the server receives the contents of the file from its read buffer until all bytes have been read. After all bytes have been written by the client to its write buffer, the client enters the 'upload_complete' state. After all bytes have been read by the server it enters the 'upload_complete' state.<br />

In the 'upload_complete' state, the client closes the connection to the server and exits. The server in 'upload_complete' state closes the client socket.<br />

### Usage

#### Server
`python server.py [options]`<br />

options:<br />
`-l, --listen-port listening port for the server (default = 50001)`<br />
`-d, --debug show debug messages if option is specified`<br />
`-?, --usage displays the usage if specified`<br />

#### Client
`python client.py [options]`<br />

options:<br />
`-m, --mode mode for the client, valid options are upload and download (default = download)`<br />
`-s, --server specify the server address. specified as ip address:port. (default = 127.0.0.1:50000)`<br />
`-v, --server-file-name specifiy the file name on the server to upload or download from the server. (default = server.txt)`<br />
`-l, --client-file-name specify the file name on the client to upload or download from the server. (default = client.txt)`<br />
`-d, --debug show debug messages if option is specified`<br />
`-?, --usage displays the usage if specified`<br />

### Example
These examples use a stammering proxy running with the following configuration:<br />
`python stammerProxy.py -l 50000 -s 127.0.0.1:50001` <br />
`python server.py -l 50001`<br />

Download:<br />
`python client.py -m download -s 127.0.0.1:50000 -l client_speech.txt -v speech.txt`<br />

Upload:<br />
`python client.py -m upload -s 127.0.0.1:50000 -l client_speech.txt -v server_speech.txt`<br />

