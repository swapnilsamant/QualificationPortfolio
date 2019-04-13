import sys
import os
import re
import params
from select import *
from socket import *
import struct 
import statvfs

# valid modes for the client
valid_client_modes = ['upload','download']

# defaults for command line arguments for the program 
# format ((short switch, long switch), variable name, default value)
switchesVarDefaults = (
	(('-s', '--server'), 'server', "127.0.0.1:50000"),
	(('-m', '--mode'), 'mode', "download"), # client mode, valid modes are upload or download, default is download
	(('-v', '--server-file-name'), 'server_file_name', "server-test.txt"), # server file name to upload or download
	(('-l', '--client-file-name'), 'client_file_name', "client-test.txt"), # client file name to upload or download
	(('-d', '--debug'), "debug", False), # boolean (set if present)
	(('-?', '--usage'), "usage", False) # boolean (set if present)
	)

# send passed command line arguments to the parser
param_map = params.parseParams(switchesVarDefaults)

# assign command line agruments to variables
server = param_map["server"]
usage = param_map["usage"]
debug = param_map["debug"]
mode = param_map["mode"]
server_file_name = param_map["server_file_name"]
client_file_name = param_map["client_file_name"]

# print usage
if usage:
	params.usage()

# parse server address and port number
try:
	server_host, server_port = re.split(":", server)
	server_port = int(server_port)
except:
	print "Can't parse server:port from '%s'" % server
	sys.exit(1)

# check for valid client mode from command line
if mode not in valid_client_modes:
	print "Invalid client mode: '%s'" % mode
	sys.exit(1)

# check lenght of server file name passed from commadline
if len(server_file_name) <= 0 or len(server_file_name) > 255:
	print "Invalid server file name: '%s'" % server_file_name
	sys.exit(1) 

# check lenght of client file name passed from commadline
if len(client_file_name) <= 0 or len(client_file_name) > 255:
	print "Invalid client file name: '%s'" % server_file_name
	sys.exit(1) 

# if client mode is upload then check if the client file exists
if mode == 'upload' and not os.path.exists(client_file_name):
	print  "Client file '%s' does not exist." % client_file_name
	sys.exit(1)

# Client class
class Client(object):
	def __init__(self, sock_addr, client_mode, server_file_name, client_file_name, addr_family = AF_INET, sock_type = SOCK_STREAM):
		# all possible states for the client
		self.client_state_map = {'init_download':self.prepare_check_file_download_request,
									'send_check_file_download': self.send_check_file_download_request,
									'check_download': self.process_check_file_download_response,
									'prepare_download_confirmation':self.send_download_confirmation,
									'confirm_download': self.process_confirm_download_state,
									'downloading': self.download_file,
									'download_complete' : self.check_done,
									'init_upload': self.prepare_check_file_upload_request,
									'send_check_file_upload': self.send_check_file_upload_request,
									'check_upload': self.process_check_file_upload_response,
									'prepare_upload_file_size':self.prepare_upload_file_size,
									'send_upload_file_size': self.send_upload_file_size,
									'process_upload_file_size_response': self.process_upload_file_size_response,
									'uploading': self.send_file,
									'upload_complete' : self.check_done}

		# dictionary for forward progress of a file transfer for the client
		self.state_transition_map = {'init_download': 'send_check_file_download',
										'send_check_file_download': 'check_download',
										'check_download': 'prepare_download_confirmation',
										'prepare_download_confirmation': 'confirm_download',
										'confirm_download': 'downloading',
										'downloading': 'download_complete',
										'init_upload':'send_check_file_upload',
										'send_check_file_upload': 'check_upload',
										'check_upload': 'prepare_upload_file_size',
										'prepare_upload_file_size': 'send_upload_file_size',
										'send_upload_file_size':'process_upload_file_size_response',
										'process_upload_file_size_response': 'uploading',
										'uploading': 'upload_complete'}

		# create a server socket
		self.server_sock = socket(addr_family, sock_type)
		# set the socket to non-blocking
		self.server_sock.setblocking(False)
		# connect to the server 
		self.server_sock.connect_ex(sock_addr)
		self.client_mode = client_mode
		self.server_file_name = server_file_name
		self.client_file_name = client_file_name
		self.client_state = None
		self.client_done = False
		# initialize the read and write buffers
		self.read_buffer = ""
		self.write_buffer = ""
		# set buffer capacity
		self.buffer_capacity = 2048
		# size of file to be transferred
		self.file_size = 0
		# number of ytes transferred at any given point in time
		self.number_of_bytes_transferred = 0

		# start the client in the selected mode
		if (self.client_mode == 'download'):
			self.client_state = 'init_download'

		elif (self.client_mode == 'upload'): 
			self.client_state = 'init_upload'

		if debug: print "changed status to: " + self.client_state 

	# get free space on disk for file upload from client
	def get_free_space_on_disk(self):
		f = os.statvfs(".")
		return  f[statvfs.F_FRSIZE] * f[statvfs.F_BLOCKS]

	# if the client is in download mode 
	# then create the download message and 
	# append it to the write buffer
	def prepare_check_file_download_request(self):
		# message is character "D" followed by a 255 byte file name
		packet_data = struct.pack("!c255s", 'D', self.server_file_name)
		self.write_buffer = packet_data
		# transition to the next step after the message 
		# is appended to the write buffer
		self.client_state = self.state_transition_map[self.client_state]
		if debug: print "changed status to: " + self.client_state 

	# wait until the contents of write buffer are sent out
	def send_check_file_download_request(self):
		if (len(self.write_buffer) == 0):
			# transition to the next step after the contents of
			# write buffer are written out 
			self.client_state = self.state_transition_map[self.client_state]
			if debug: print "changed status to: " + self.client_state 

	# After the check check file for download message 
	# has been sent out
	# wait for the response from the server.
	# The response is:
	# One character (T: for file transfer possible, 
	# 					F: File does not exists or 
	# 					E: File transfer not possible due to unknown error)
	# followed by 8 bytes of file size
	def process_check_file_download_response(self):
		# Check if the read buffer has 9 bytes
		if len(self.read_buffer) == 9:
			# extract file transfer flag and file size from the message
			(file_status, file_size) = struct.unpack("!cQ", self.read_buffer)
			# if file transfer is possible 
			# then extract file size
			# and transition to the next step
			if (file_status == 'T'):
				self.file_size = int(file_size)
				self.read_buffer = ""
				self.client_state = self.state_transition_map[self.client_state]
				if debug: print "changed status to: " + self.client_state 
			# if file transfer is not possible then close connection 
			# and exit client
			elif (file_status == 'F'):
				print "file not found on server"
				self.client_done = True
				self.read_buffer = ""
				self.write_buffer = ""
				self.client_state = 'download_complete'
				#sys.exit(1)
			elif (file_status == 'E'):
				print "unknown error on server"
				self.client_done = True
				self.read_buffer = ""
				self.write_buffer = ""
				self.client_state = 'download_complete'
				#sys.exit(1)

	# if file transfer is possible
	# check if the client has enough space on disk
	# for the file download
	def send_download_confirmation(self):
		# if there is not enough disk space then
		# send reponse to server and exit file transfer
		if self.file_size > self.get_free_space_on_disk():
			self.write_buffer ="F"
			self.client_done = True
			self.client_state = 'download_complete'
			return

		# check if file exists on client
		# if it does then delete the existing file
		if os.path.exists(self.client_file_name):
			print "Client file exists. Will overwrite."
			os.remove(self.client_file_name)

		# if there is enough space 
		# and existing file has been deleted
		# then write a message to the write buffer to proceed with the file transfer 
		self.write_buffer ="T"
		# transition to the next step
		self.client_state = self.state_transition_map[self.client_state]
		if debug: print "changed status to: " + self.client_state 

	# wait for the message to proceed with file transfer to be 
	# written to the srever socket
	def process_confirm_download_state(self):
		if (len(self.write_buffer) == 0):
			# after the message has been writeen out
			# empty out the rtead buffer and transition to the next step
			self.read_buffer = ""
			self.client_state = self.state_transition_map[self.client_state]
			if debug: print "changed status to: " + self.client_state 

	# after the message to proceeed with file transfer has been 
	# sent to the server
	# wait for the file download from server
	def download_file(self):
		# check if the whole file has been downloaded from the server
		if self.number_of_bytes_transferred < self.file_size:
			client_file_handle = open(self.client_file_name, 'a+')
			client_file_handle.write(self.read_buffer)
			self.number_of_bytes_transferred += len(self.read_buffer)
			self.read_buffer = ""
			client_file_handle.close()
		else:
		# after file transfer is complete
		# set the client status to done 
		# and transition to the file state
			self.read_buffer = ""
			self.client_done = True
			self.client_state = self.state_transition_map[self.client_state]
			if debug: print "changed status to: " + self.client_state 
			print "File transfer complete."

	# if the client is in upload mode 
	# then create the upload message and 
	# append it to the write buffer
	def prepare_check_file_upload_request(self):
		# Upload message is character "U" followed by a 255 byte file name
		packet_data = struct.pack("!c255s", 'U', self.server_file_name)
		self.write_buffer = packet_data
		# transition to the next step after the message 
		# is appended to the write buffer
		self.client_state = self.state_transition_map[self.client_state]
		if debug: print "changed status to: " + self.client_state 

	# wait until the contents of write buffer are sent out
	def send_check_file_upload_request(self):
		if (len(self.write_buffer) == 0):
			# transition to the next step after the contents of
			# write buffer are written out 
			self.client_state = self.state_transition_map[self.client_state]
			if debug: print "changed status to: " + self.client_state 

	# parse the response received from server from the read buffer
	def process_check_file_upload_response(self):
		# response length expected is 1 byte
		if len(self.read_buffer) == 1:
			file_status = self.read_buffer
			# if the server responded with "T"
			# then transition to the next step
			if (file_status == 'T'):
				self.read_buffer = ""
				self.client_state = self.state_transition_map[self.client_state]
				if debug: print "changed status to: " + self.client_state 
			# if the server responded with "F", False
			# then exit file transfer
			elif (file_status == 'F'):
				self.read_buffer = ""
				print "file found on server. use a different file name."
				self.client_done = True
				self.client_state = 'upload_complete'
			# if the server responded with "E", error
			# then exit file transfer
			elif (file_status == 'E'):
				self.read_buffer = ""
				print "unknown error on server. please retry."
				self.client_done = True
				self.client_state = 'upload_complete'
				#sys.exit(1)

	# Send the file size to the server if the server has responded 
	# to proceed with file transfer
	def prepare_upload_file_size(self):
		self.file_size = os.path.getsize(self.client_file_name)
		packet_data = struct.pack("!Q", self.file_size)
		self.write_buffer = packet_data
		self.client_state = self.state_transition_map[self.client_state]
		if debug: print "changed status to: " + self.client_state 

	# wait until the socket has finished sending file size
	# to the server
	def send_upload_file_size(self):
		if (len(self.write_buffer) == 0):
			self.client_state = self.state_transition_map[self.client_state]
			if debug: print "changed status to: " + self.client_state 

	# check the servers response for
	# file size that was sent to the server
	def process_upload_file_size_response(self):
		# response lenght expected is 1 byte
		if len(self.read_buffer) == 1:
			download_confirmation = self.read_buffer
			if download_confirmation == 'T':
				#print "status changed to download"
				self.client_state = self.state_transition_map[self.client_state]
				if debug: print "changed status to: " + self.client_state 
				self.read_buffer = ""
			else:
				print "Server rejected file upload."
				self.read_buffer = ""
				self.client_done = True
				self.client_state = 'upload_complete'
				#sys.exit(1)

	# if the server accepted file upload
	# then start sending the file
	def send_file(self):
		# continue sending until the complete file has been sent
		if self.number_of_bytes_transferred != self.file_size:
			if len(self.write_buffer) < self.buffer_capacity:
				f_handle = open(self.client_file_name)
				f_handle.seek(self.number_of_bytes_transferred)
				data_read = f_handle.read(self.buffer_capacity - len(self.write_buffer))
				self.write_buffer = self.write_buffer + data_read
				self.number_of_bytes_transferred = self.number_of_bytes_transferred + len(data_read)
		# transition to the next step  
		# after complete file has been sent
		else:
			self.client_done = True
			self.client_state = self.state_transition_map[self.client_state]
			if debug: print "changed status to: " + self.client_state 
			print "File transfer complete."

	# check if the read buffer has space to read new content
	# if it does then return the server socket
	def check_read(self):
		if len(self.read_buffer) < self.buffer_capacity:
			return self.server_sock
		else:
			return None

	# check if the write buffer has content to be sent out
	# if it does then return the server socket
	def check_write(self):
		if len(self.write_buffer) > 0:
			return self.server_sock
		else:
			return None

	# if the socket is in error state
	def check_error(self):
		return self.server_sock

	# receive from the socket and save the received data to the read buffer
	def do_receive(self):
		received_data = ""
		try:
			received_data = self.server_sock.recv(self.buffer_capacity - len(self.read_buffer))
		except:
			self.die()
		
		if len(received_data):
			self.read_buffer += received_data
		else:
			self.check_done()

		
	# close the socket
	def die(self):
		print "connection to server closing"
		try:
			self.server_sock.close()
			sys.exit(1)
		except:
			pass 

	# send out data in the write buffer
	def do_send(self):
		try:
			n = self.server_sock.send(self.write_buffer)
			self.write_buffer = self.write_buffer[n:]
		except Exception as e:
			pass

	# before closing the client socket 
	# check if the read and write buffers are empty
	def check_done(self):
		if len(self.read_buffer) == 0 and len(self.write_buffer) == 0 and self.client_done:
			try:
				self.server_sock.shutdown(SHUT_RDWR)
				print "Shutting down connection to server"
				self.die()
			except Exception as e:
				pass

	# close the connection in case of an error
	def do_error(self):
		print "File transfer failed due to error."
		self.die()

# create a new Client object with the command line arguments received	
current_client = Client((server_host, server_port), mode, server_file_name, client_file_name)

# cotinue until the client status is not done
while (not (current_client.client_done)):
	# check for client state transitions
	current_client.client_state_map[current_client.client_state]()

	read_map = {}
	write_map = {}
	error_map = {}

	# check if the read buffer has space of new data
	read_sock = current_client.check_read()
	if (read_sock):
		read_map[read_sock] = current_client

	# check if the write buffer has anything to be written
	write_sock = current_client.check_write()
	if (write_sock):
		write_map[write_sock] = current_client

	# to check for error state on the socket
	error_map[current_client.server_sock] = current_client

	# select to check which sockets have data to read, write or are in error state
	read_sock_set, write_sock_set, error_sock_set = select(read_map.keys(), write_map.keys(), error_map.keys(),1)

	for sock in error_sock_set:
		error_map[sock].do_error()
	for sock in read_sock_set:
		read_map[sock].do_receive()
	for sock in write_sock_set:
		write_map[sock].do_send()