This repository contains the code for the UDP file trasnfer lab. The
purpose is to develop a protocol between the client and server
to achieve a reliable file transfer between client and server over the 
network using UDP. The protocol accounts for dropped packets, delayed packets,
and duplicate packets.


Each packet has a message type which is 1 byte in lenght. The message type is
represented by a character. 

The protocol relies and the following types of messages which are exchanged 
between the client and the server:

Message types are specified by a 1 char packet header.
----------------------------------------------------------------------------
(commas are only for reference.)<br />
A - Check File Download Request (Client -> Server)<br />
Packet format:<br />
A, FileName<br />

B - Check File Download Response (Server -> Client)<br />
Packet format:<br />
B, FileStatus, FileId, FileSize<br />
In case of error, FileStatus is False and FileId is the Error Code<br />

C - Check File Upload Request (Client -> Server)<br />
Packet format:<br />
C, FileSize, FileName<br />

D - Check File Upload Response (Server  -> Client)<br />
Packet format:<br />
D, FileStatus, FileId<br />
In case of error, FileStatus is False and FileId is the Error Code<br />

E - Download File Request (Client -> Server)<br />
Packet format:<br />
E, FileId, CurrentPacketNumber, FileStartPosition<br />

F - Download File Response (Server  -> Client)<br />
Packet format:<br />
F, ReadStatus, RequestedPacketNumber, FileId, FileStartPosition, LengthOfData<br />
In case of error, ReadStatus is False and RequestedPacketNumber is the Error Code<br />

G - Upload File Request (Client -> Server)<br />
Packet format:<br />
G, CurrentPacketNumber, FileId, FileStartPosition, LengthOfData<br />

H - Upload File Response (Server  -> Client)<br />
Packet format:<br />
H, WriteStatus, ReceivedPacketNumber, FileId<br />
In case of error, WriteStatus is False and ReceivedPacketNumber is the Error Code<br />

We are using the python struct library to construct the packet and to decode the received 
packet.

Struct Pack/Unpack Reference
----------------------------------------------------------------------------
! - network (= big-endian)<br />
File Id - Unsigned Integer - I - 4 Bytes<br />
File Size - Unsigned Long Long - Q - 8 Bytes<br />
Status - Boolean - ? - 1 Byte<br />
File Start Position - Unsigned Long Long - Q - 8 Bytes<br />
Bytes Read - Unsigned Integer - I - 4 Bytes<br />
Packet Header - Char - c - 1 Byte<br />
Packet Number - Unsigned Integer - I - 4 Bytes<br />


The server and client scripts can communicate throughr a proxy. At the end of the file transfer the
client prints out an average RTT and the throughput of file transfer.


Statistics for proxy configs using speech.txt are as follows:<br />

Download<br />
p1 : Average RTT = 0.121 s, Throughput = 813 B/s<br />
p2 : Average RTT = 0.371 s, Throughput = 267 B/s<br />
p3 : Average RTT = 0.193 s, Throughput = 498 B/s<br />
<br />
Upload<br />
p1 : Average RTT = 0.119 s, Throughput = 625 B/s<br />
p2 : Average RTT = 0.301 s, Throughput = 247 B/s<br />
p3 : Average RTT = 0.182 s, Throughput = 409 B/s<br />

Usage instruction are specified in readme files of server and client folders.<br />

Timing diagrams are specified in UDP-FileTransferProtocol-v4.pptx<br />

Protocol dissector added : stop-wait-file-transfer.lua