import sys
import traceback
from select import *
from socket import *
import struct
import re
import params
import os
import statvfs

# defaults for command line arguments for the program 
# format ((short switch, long switch), variable name, default value)
switches_var_defaults = (
	(('-l', '--listen-port') ,'listen_port', 50001), # port to listen for connections
	(('-d', '--debug'), 'debug', False), # run script in debig mode. boolean (set if present)
	(('-?', '--usage'), 'usage', False) # displays command line arguments. boolean (set if present)
	)

# send passed command line arguments to the parser
param_map = params.parseParams(switches_var_defaults)

# assign command line agruments to variables
listen_port = param_map["listen_port"]
usage = param_map["usage"]
debug = param_map["debug"]

# print usage
if usage:
	params.usage()

# cast listen port to integer
try:
	listen_port = int(listen_port)
except:
	print "Can't parse listen port from %s" % listen_port
	sys.exit(1)

ongoing_file_transfers = {} # dictionary to keep track of all ongoing file transfers
#all_sock_names = {}               # from socket to name
next_connection_number = 0     # each connection is assigned a unique id


# class connection
# each client connection results in a new object of class Conn
class Conn:
	def __init__(self, client_sock, client_addr):
		global next_connection_number
		
		# all possible states for the file transfer connection
		self.server_state_map = {'client_connect': self.process_client_connect,
									'check_download': self.prepare_check_file_download_response,
									'send_check_download': self.send_check_file_download_response,
									'check_download_confirmation': self.check_download_confirmation,
									'downloading': self.send_file,
									'download_complete': self.check_done,
									'check_upload': self.prepare_check_file_upload_response,
									'send_check_upload': self.send_check_file_upload_response,
									'check_file_upload_size': self.process_file_upload_size,
									'prepare_file_upload_size_response': self.prepare_file_upload_size_response,
									'send_file_upload_size_response': self.send_file_upload_size_response,
									'uploading': self.receive_file,
									'upload_complete': self.check_done}
									#'error': self.send_error_response}

		# dictionary for forward progress of a file transfer connection
		self.state_transition_map = {'check_download': 'send_check_download',
										'send_check_download': 'check_download_confirmation',
										'check_download_confirmation': 'downloading',
										'downloading': 'download_complete',
										'check_upload': 'send_check_upload',
										'send_check_upload': 'check_file_upload_size',
										'check_file_upload_size': 'prepare_file_upload_size_response', 
										'prepare_file_upload_size_response': 'send_file_upload_size_response',
										'send_file_upload_size_response': 'uploading',
										'uploading': 'upload_complete'}

		# max size of message for a connection state
		self.state_message_length = {'client_connect': 256,
										'check_download_confirmation': 1,
										'check_file_upload_size': 8}

		self.client_sock = client_sock      # client socket
		self.client_addr = client_addr		# client address
		self.client_connection_mode = None
		self.file_transfer_state = 'client_connect' # current state of the client. client_connect for a new connection from client
		self.conn_index = next_connection_number	#unique id for each connection
		next_connection_number += 1			
		self.buffer_capacity = 2048			# maximum capacity for read and write buffer
		self.read_buffer = ""				# read buffer
		self.write_buffer = ""				# write buffer
		self.server_file_name = None		# file name requested for download or upload by server
		self.file_size = 0					# file size of file uploaded by downloaded by client
		self.number_of_bytes_transferred = 0	# number of bytes uploaded or download at any given point
		print "New connection #%d from %s" % (self.conn_index, repr(client_addr))
		if debug: print "changed status to: " + self.file_transfer_state  
		self.sock_name = "C%d:ToClient" % self.conn_index # creat a socket name for the client socket
		self.done = False					# check if the current upload or download is finished
		
		# add the newly created connection to the list of all current connections
		all_connections.add(self)			 
		

	# get free space on disk for file upload from client
	def get_free_space_on_disk(self):
		f = os.statvfs(".")
		return  f[statvfs.F_FRSIZE] * f[statvfs.F_BLOCKS]

	# check if there is another file transfer for the same file
	# in upload mode
	def check_ongoing_transfers_in_upload(self):
		existing_file_transfer_in_upload_mode = False
		for each_transfer in ongoing_file_transfers:
			if each_transfer != self.conn_index \
				and ongoing_file_transfers[each_transfer][1] == 'upload' \
				and ongoing_file_transfers[each_transfer][0] == self.server_file_name:

				existing_file_transfer_in_upload_mode = True

		return existing_file_transfer_in_upload_mode

	# check if there is another file transfer for the same file
	# in any mode
	def check_ongoing_transfers_in_upload_download(self):
		existing_file_transfer = False
		for each_transfer in ongoing_file_transfers:
			if  ongoing_file_transfers[each_transfer][0] == self.server_file_name \
				and each_transfer != self.conn_index:
				
				existing_file_transfer = True

		return existing_file_transfer


	# on conneection the clients sends a message which identifies 
	# if the clint wants to upload or download a file
	# and the file name for upload ot download

	def process_client_connect(self):
		# message length is always 256 bytes
		# wait until the read buffer receives
		# 256 bytes
		if (len(self.read_buffer) == self.state_message_length[self.file_transfer_state]):
			# extract the operation and file name from the message
			# first character is which operation followed by 255 bytes of file name
			(msg_type, file_name) = struct.unpack('!c255s', self.read_buffer)
			file_name = file_name.replace('\x00', "").strip()
			self.server_file_name = file_name.strip()
			# U: upload
			# D: download
			if msg_type == "D":
				# change the state of the connection to check_download
				self.client_connection_mode = 'download'
				self.file_transfer_state = "check_download"
				if debug: print "changed status to: " + self.file_transfer_state 
				ongoing_file_transfers[self.conn_index] = (self.server_file_name, 'download')
			elif msg_type == "U":
				# change the state of the connection to check_upload
				self.client_connection_mode = 'upload'
				self.file_transfer_state = "check_upload"
				if debug: print "changed status to: " + self.file_transfer_state 
				ongoing_file_transfers[self.conn_index] = (self.server_file_name, 'upload')

			self.read_buffer = ""

	# If the connection is in check_download state
	# then check if the file exists 
	# and writes appropriate response to write buffer
	def prepare_check_file_download_response(self):
		# if the file does not exist 
		# then write "F" with a zero for file size
		
		if not os.path.exists(self.server_file_name):
			packet_data = struct.pack("!cQ", 'F', 0)
			self.write_buffer = packet_data
			self.done = True
			# change state so that the contents of write buffer are sent out 
			self.file_transfer_state = 'download_complete'
			print "File does not exist on server for connection #%d" % self.conn_index
			return

		# reject file download is same file is being uploaded by another client
		if self.check_ongoing_transfers_in_upload():
			packet_data = struct.pack("!cQ", 'F', 0)
			self.write_buffer = packet_data
			self.done = True
			# change state so that the contents of write buffer are sent out 
			self.file_transfer_state = 'download_complete'
			print "File being uploaded by another client for connection #%d" % self.conn_index
			return

		# if the file exists 
		# then write "T" with the file size
		try: 
			file_size = os.path.getsize(self.server_file_name)
			self.file_size = file_size
			packet_data = struct.pack("!cQ", 'T', file_size)
			self.write_buffer = packet_data
			# change state so that the contents of write buffer are sent out
			self.file_transfer_state = self.state_transition_map[self.file_transfer_state]
			
			if debug: print "changed status to: " + self.file_transfer_state 

		# incase of error change connection state to error 
		# write error state write buffer
		except:
			packet_data = struct.pack("!cQ", 'E', 0)
			self.write_buffer = packet_data
			self.done = True
			# change state so that the contents of write buffer are sent out
			self.file_transfer_state = 'download_complete'
			print "Error on file transfer for connection #%d" % self.conn_index

	# wait contents of write buffer have been sent out
	def send_check_file_download_response(self):
		if len(self.write_buffer) <= 0:
			# change state to wait for response from client to begin download
			self.file_transfer_state = self.state_transition_map[self.file_transfer_state]
			if debug: print "changed status to: " + self.file_transfer_state 

	# wait for client response 
	def check_download_confirmation(self):
		if (len(self.read_buffer) == self.state_message_length[self.file_transfer_state]):
			download_confirmation = self.read_buffer[0]
			# client response with a "T" to begin file download
			if download_confirmation == 'T':
				self.file_transfer_state = self.state_transition_map[self.file_transfer_state]
				if debug: print "changed status to: " + self.file_transfer_state 
				# empty out read buffer
				self.read_buffer = ""
			# clients rejects file transfer with "F" response
			elif download_confirmation == 'F':
				print 'Download request cancelled by client.'
				self.done = True
				self.read_buffer = ""
				# change the file transfer statew to complete
				self.file_transfer_state = 'download_complete'
				print "File transfer rejected by client for connection #%d" % self.conn_index
			# if client response is not "T" or "F" then its an error
			else:
				print 'Error encountered during file transfer.'
				self.done = True
				self.read_buffer = ""
				self.file_transfer_state = 'download_complete'
				print "Error reported by client for connection #%d" % self.conn_index

	# if client responded with confirmation to begin file download then 
	# start to send file to the client
	def send_file(self):
		if self.number_of_bytes_transferred < self.file_size:
			if len(self.write_buffer) < self.buffer_capacity:
				# if the number of bytes sent is less than the file size 
				# then read new bytes from the file to fill the write buffer
				f_handle = open(self.server_file_name)
				f_handle.seek(self.number_of_bytes_transferred)
				data_read = f_handle.read(self.buffer_capacity - len(self.write_buffer))
				self.write_buffer = self.write_buffer + data_read
				self.number_of_bytes_transferred = self.number_of_bytes_transferred + len(data_read)
		# if the file has been transferred then change state to download complete
		else:
			self.done = True
			self.file_transfer_state = self.state_transition_map[self.file_transfer_state]
			if debug: print "changed status to: " + self.file_transfer_state 
			print "File transfer complete."

	# If the connection is in check_upload state
	# then check if the file exists 
	# and writes appropriate response to write buffer
	def prepare_check_file_upload_response(self):
		# if file name exists then reject file transfer
		# with an "F" response
		# and close client connection
		if os.path.exists(self.server_file_name):
			self.write_buffer = 'F'
			self.done = True
			self.file_transfer_state = 'upload_complete'
			print "File exists on server. Client on connection #%d will be disconnected." % self.conn_index
			return

		# reject file upload if another client is uploading or downloading the same file
		if self.check_ongoing_transfers_in_upload_download():
			self.write_buffer = 'F'
			self.done = True
			self.file_transfer_state = 'upload_complete'
			print "File in use by another client. Client on connection #%d will be disconnected." % self.conn_index
			return
		# if file name exists then go to the next step
		# with an "T" response		
		try: 
			self.write_buffer = 'T'
			self.file_transfer_state = self.state_transition_map[self.file_transfer_state]
			if debug: print "changed status to: " + self.file_transfer_state 

		# if error is encountered 
		# send an "E" response
		except Exception as thrown_exception:
			self.write_buffer = 'E'
			self.done = True
			self.file_transfer_state = 'upload_complete'
			print "Error in file transfer. Client on connection #%d will be disconnected." % self.conn_index

	# wait contents of write buffer have been sent out
	def send_check_file_upload_response(self):
		if len(self.write_buffer) <= 0:
			self.file_transfer_state = self.state_transition_map[self.file_transfer_state]
			if debug: print "changed status to: " + self.file_transfer_state 

	# receive the file size of the file to be uploaded
	def process_file_upload_size(self):
		if (len(self.read_buffer) == self.state_message_length[self.file_transfer_state]):
			(file_size,) = struct.unpack('!Q', self.read_buffer)
			# if disk has engouh space for the file then proceed with next step
			if self.get_free_space_on_disk() > file_size:
				self.file_size = file_size
				self.file_transfer_state = self.state_transition_map[self.file_transfer_state]
				if debug: print "changed status to: " + self.file_transfer_state 
				self.read_buffer = ""
			else:
				self.write_buffer = 'F'
				self.done = True
				self.file_transfer_state = 'upload_complete'
				print "Upload file size too big. Client on connection #%d will be disconnected." % self.conn_index

	# write a "T" response to output buffer to proceed with file upload
	def prepare_file_upload_size_response(self):
		self.write_buffer = 'T'
		self.file_transfer_state = self.state_transition_map[self.file_transfer_state]
		if debug: print "changed status to: " + self.file_transfer_state 

	# wait contents of write buffer have been sent out
	def send_file_upload_size_response(self):
		if len(self.write_buffer) <= 0:
			self.file_transfer_state = self.state_transition_map[self.file_transfer_state]
			if debug: print "changed status to: " + self.file_transfer_state 

	# receieve the uploaded file
	def receive_file(self):
		if self.number_of_bytes_transferred < self.file_size:
			server_file_handle = open(self.server_file_name, 'a+')
			server_file_handle.write(self.read_buffer)
			self.number_of_bytes_transferred += len(self.read_buffer)
			self.read_buffer = ""
			server_file_handle.close()
		# change status to done after the complete file has been received
		else:
			self.done = True
			self.file_transfer_state = self.state_transition_map[self.file_transfer_state]
			if debug: print "changed status to: " + self.file_transfer_state 
			print "File upload complete."

	# check if the read buffer has space to read new content
	# if it does then return the client socket
	def check_read(self):
		if len(self.read_buffer) < self.buffer_capacity:
			return self.client_sock
		else:
			return None

	# check if the write buffer has content to be sent out
	# if it does then return the client socket
	def check_write(self):
		if len(self.write_buffer) > 0:
			return self.client_sock
		else:
			return None

	# if the socket is in error state
	def check_error(self):
		return self.client_sock

	# receive from the socket and save the received data to the read buffer
	def do_receive(self):
		received_data = ""
		try:
			received_data = self.client_sock.recv(self.buffer_capacity - len(self.read_buffer))
		except:
			self.die()

		if len(received_data):
			self.read_buffer += received_data


	# send out data in the write buffer
	def do_send(self):
		try:
			n = self.client_sock.send(self.write_buffer)
			self.write_buffer = self.write_buffer[n:]
		except:
			self.die()

	# close the client connection
	def die(self):
		print "Closing connection #%d" % self.conn_index
		try:
			self.client_sock.close()
		except Exception as e:
			pass
			#print e 

	# before closing the client socket 
	# check if the read and write buffers are empty
	def check_done(self):
		if len(self.read_buffer) == 0 and len(self.write_buffer) ==0 and self.done:
			try:
				del ongoing_file_transfers[self.conn_index]
				self.client_sock.shutdown(SHUT_RDWR)
				print "Shutting down connection #%d" % self.conn_index
			except Exception as e:
				pass
				#print e

			self.die()

	# close the connection in case of an error
	def do_error(self):
		print "File transfer from client %s failing due to error." % repr(self.client_addr)
		self.die()

# listener class to listen for incoming connections
class Listener:
	def __init__(self, bind_addr, addr_family=AF_INET, sock_type=SOCK_STREAM): 
		self.bind_addr = bind_addr
		self.addr_family = addr_family,
		self.socktype = sock_type
		# create a new TCP listening socket for internet address family
		self.listning_sock = socket(addr_family, sock_type)
		# set socket options to reuse socket addrrres
		self.listning_sock.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
		# bind the socket to the port number
		self.listning_sock.bind(bind_addr)
		# non-blocking socket
		self.listning_sock.setblocking(False)
		# start listening, max 4 outstanding connections
		self.listning_sock.listen(4)

	# check for new connections on the listening socket
	def do_receive(self):
		try:
			# accept new connection on the listening socket
			client_sock, client_addr = self.listning_sock.accept() # socket connected to client
			# create a new connection object for the new client 
			conn = Conn(client_sock, client_addr)
		except:
			print "weird.  listener readable but can't accept!"
			traceback.print_exc(file=sys.stdout)

	# exit the program if there is an error on the listening socket
	def do_error(self):
		print "listener socket failed!!!!!"
		sys.exit(2)

	# function to check for incoming connections on the listening socket
	def check_read(self):
		return self.listning_sock

	def check_write(self):
		return None

	# function to check for errors on the listening socket
	def check_err(self):
		return self.listning_sock
		
# set for all client connections 
all_connections = set()
current_listener = Listener(("0.0.0.0", listen_port))

# run for ever...
while 1:
	read_map = {}
	write_map = {}
	error_map = {}   # socket:object mappings for select
	# add listening socket to the reader map
	# to check for errors on the listening socket
	error_map[current_listener.check_err()] = current_listener
	# add listening socket to reader map
	# to check for reads on the listening socket
	read_map[current_listener.check_read()] = current_listener
	# to remove dead client connections
	remove_list = []
	# iterate over all client connections
	for each_connection in all_connections:
		# if the done attribute is set on the 
		# connection then remove it from the 
		# connections list
		if each_connection.done:
			each_connection.check_done()
			remove_list.append(each_connection)
			break

		# check for state transitions on the client connection
		each_connection.server_state_map[each_connection.file_transfer_state]()
		# add check for error on each client to the error map
		error_map[each_connection.client_sock] = each_connection
		# check if the client connection has 
		# space in read buffer for new data
		read_sock = each_connection.check_read()
		if (read_sock): 
			read_map[read_sock] = each_connection

		# check if the client connection has 
		# data in write buffer
		write_sock = each_connection.check_write()
		if (write_sock): 
			write_map[write_sock] = each_connection

	# select to return a set of read, write and error sockets for all connections
	rset, wset, xset = select(read_map.keys(), write_map.keys(), error_map.keys(),1)

	# if there are sockets in read set, then recieve data
	for sock in rset:
		read_map[sock].do_receive()
	# if there are sockets in write set, then write data
	for sock in wset:
		write_map[sock].do_send()
	# if there are sockets in erroe set, then perform error response
	for sock in xset:
		error_map[sock].do_error()

	# remove dead sockets from all connections set
	for each_conn in remove_list:
		all_connections.remove(each_conn)