import time
import sys
import os
import struct 
from socket import *
import select
import statvfs
import random
import string

# class to keep track of ongoing file transfers
class FileTransfer(object):
	def __init__(self, file_id, file_name, ttl, file_size):
		self.file_id = file_id			# file id assigned by the server
		self.file_name =  file_name		# server file name
		self.init_time = time.time()	# start time for the file transfer
		self.ttl = ttl					# time until file transfer stays active without any communication from client
		self.last_acked = 0				# seq number last acked by server
		self.file_size = file_size		# file size for the file transfer
		self.acked_lst = []				# list of seq numbers acked by the server

	# update the next packet number for a client 
	# on receiving communication from the client
	# update the continous seq number that was
	# acknowledged by the server 
	def update_file_transfer(self, pkt_id):
		self.acked_lst.append(pkt_id)
		max_acked_id = max(self.acked_lst)
		
		for acked_id in range(0, max_acked_id + 1):
			if acked_id in self.acked_lst:
				self.last_acked = acked_id
			else:
				break

		return

	# update the ttl if no communication from client
	# reset the ttl if there is communication from client 
	def update_ttl(self, default_ttl, reset_flag):
		if reset_flag:
			self.ttl = default_ttl
		else:
			self.ttl -= 1 

		return self.ttl

class Server(object):
	def __init__(self):
		self.timeout = 1 				# timeout for select
		self.ttl = 60 					# time until the file transfer will stay active on the server, without any communication from client
		self.verbose_level = 1 			# verbosity level 1 to 5, 1 - everything 5 - critical messages only
		self.max_data_size = 75 		# since largest header is aroubnd 21 bytes and max message size is 100 bytes
										# its safe to assume maximum data in a packet is around 75 bytes
		self.buffer_size = 2048 		# maximum buffer size to read

		# use a random file name for the temp file
		# temp file is used to join the incoming packets
		# for creating the server file
		self.tmp_file_name = ''.join(random.choice(string.ascii_lowercase + string.digits) for _ in range(8))

		# method to call based on type of message received
		self.message_type_dictionary = {'A': self.send_check_file_download_response,
										'C': self.send_check_file_upload_response,
										'E': self.send_file_download_response,
										'G': self.send_file_upload_response}

		# error codes sent by the server. only or reference in this file
		self.error_codes = {0: "Unknonwn error on server, please try again.",
							1: "File does not exist on server. Please check download file name.",
							2: "File name already exists on server. Please use a different server file name.",
							3: "Error while reading file.",
							4: "Error while writing file.",
							5: "Upload file size exceeds available free space."}

		# read command line arguments
		self.port_number = self.get_listen_port_number()
		self.address = ("", self.port_number)
		
		# get the listening socket
		self.listening_socket = self.get_udp_socket()

		# dictionary to maintain list if connected clients
		# each item is an object of class FileTransfer
		self.ongoing_file_transfers = {}

		# file ID assiged to clients
		self.current_file_id = 0
		
		# start listening to port for messages
		self.listen_to_port()

	# create UDP socket and bind it to the port and address
	def get_udp_socket(self):
		udp_socket = socket(AF_INET, SOCK_DGRAM)
		udp_socket.bind(self.address)
		udp_socket.setblocking(False)
		
		return udp_socket

	# print usage in case of incorrect usage
	def print_usage(self):
		sys.exit("Usage:\npython server.py  <server_listen_port_number>\n\nExample:\npython server.py 5001\n")

	# get listening port from command line arguments
	def get_listen_port_number(self):
		try:
			arg = int(sys.argv[1])
		except IndexError:
			self.print_information("Please provide a valid server port number.", 5)
			self.print_usage()
		except ValueError:
			self.print_information("Port number must be an integer.", 5)
			self.print_usage()
		if (arg < 1024 or arg > 65535):
			self.print_information("Port number must be between 1025 and 65535.", 5)
			self.print_usage()
		else:
			return arg

	# print general trace and debug messages
	def print_information(self, message, verbose_level):
		if verbose_level >= self.verbose_level:
			print message
		return

	# send reposne to the client
	def send_response(self, response_packet, client_address):
		self.listening_socket.sendto(response_packet, client_address)
		return

	# get free space on disk for file upload from client
	def get_free_space_on_disk(self):
		f = os.statvfs(".")
		return  f[statvfs.F_FRSIZE] * f[statvfs.F_BLOCKS]

	# indicate invlid request from client
	def send_invalid_request_response(self, received_data, client_address):
		self.print_information("Invalid request received from client.", 5)
		return

	# parse the received message and call the action for the message type
	def parse_received_data(self, received_data, client_address):
		packet_type = received_data[0:1]
		packet_payload = received_data[1:]
		
		if (packet_type in self.message_type_dictionary):
			self.message_type_dictionary[packet_type](packet_payload, client_address)
		else:
			self.send_invalid_request_response(received_data, client_address)


	# construct the file using received packets
	def assemble_file(self, client_addr, start_pos, received_data):
		file_name = self.ongoing_file_transfers[client_addr].file_name

		#(file_id, file_name, init_time, self.ttl, current_packet_number) = self.ongoing_file_transfers[client_addr]
		with open(file_name, 'r') as old_buffer, open(self.tmp_file_name, 'w') as new_buffer:
			# copy until start position of the received packet
			new_buffer.write(old_buffer.read(start_pos))
			# insert data from the current packet
			new_buffer.write(received_data)
			# copy the rest of the file
			old_buffer.seek(start_pos + len(received_data))
			new_buffer.write(old_buffer.read())

		# delete existing file
		os.remove(file_name)
		# rename temp file to the server file
		os.rename(self.tmp_file_name, file_name)
		return
	
	# create empty file
	def initialize_empty_file(self, client_addr):
		# create an empty file having a file size
		# that was returned by the server
		file_name = self.ongoing_file_transfers[client_addr].file_name
		file_size = self.ongoing_file_transfers[client_addr].file_size
		f = open(file_name, "wb")
		f.seek(file_size - 1)
		f.write("\0")
		f.close()
		return

	# send a reponse for a check file for download message received from client
	def send_check_file_download_response(self, payload_data, client_address):
		# extract file name
		(file_name,) = struct.unpack('!255s', payload_data)
		file_name = file_name.replace('\x00', "").strip()
		self.print_information("\n\nReceived check file download request:", 3)
		self.print_information("Client address: %s" % repr(client_address), 1)
		self.print_information("File name: %s" % file_name, 1)
		self.print_information("\n\n", 3)

		# check if file exists
		if not os.path.exists(file_name):
			response_packet = struct.pack("!c?IQ", 'B', False, 1, 0)
			self.send_response(response_packet, client_address)
			self.print_information("\n\nFile does not exist on server.\n\n", 5)
			return
	   
		try: 
			self.print_information("Opening file: %s" % file_name, 3)

			# assign a file id for the file transfer
			self.current_file_id += 1
			file_id = self.current_file_id
			file_size = os.path.getsize(file_name)

			# add the file trasnfer for the main dictionary of file transfers
			self.ongoing_file_transfers[client_address] = FileTransfer(file_id, file_name, self.ttl, file_size)
			status = True
			response_packet = struct.pack("!c?IQ", 'B', status, file_id, file_size)
			# send a response to the client
			self.send_response(response_packet, client_address)
			self.print_information("Sent check file download response.\n\n", 3)
			
			if file_id > 0:
				self.print_information("Client %s given handle %d" % (repr(client_address), file_id), 3)

		except Exception as thrown_exception:
			# if there was an error then send a error response to the client
			self.print_information("Open response error: %s" %(thrown_exception), 5)
			status = False
			file_size = 0
			file_id = 0
			response_packet = struct.pack("!c?IQ", 'B', False, 0, 0)
			self.send_response(response_packet, client_address)

		return
		

	 # send a reponse for a file download message received from client
	def send_file_download_response(self, payload_data, client_address):

		self.print_information("\n\nReceived file download request.", 3)
		# unpack all message headers
		try:
			(client_file_id, current_requested_packet_number, file_start_pos) = struct.unpack("!IQI", payload_data)
			file_name = self.ongoing_file_transfers[client_address].file_name
		except:
			self.print_information("Error parsing received packet.", 5)
			return

		try:
			
			self.print_information("Client Address: %s" % repr(client_address), 1)
			self.print_information("File ID: %d" % client_file_id, 1)
			self.print_information("File name: %s" % file_name, 1)
			self.print_information("Packet number: %d" % current_requested_packet_number, 1)
			self.print_information("Start Position: %d" % file_start_pos, 1)
			
			# open the file and seek to the requested position 
			f_handle = open(file_name)
			f_handle.seek(file_start_pos)
			
			# read the max number of bytes
			data_read = f_handle.read(self.max_data_size)
			read_status = True
			response_packet = struct.pack("!c?2IQI", "F", read_status, current_requested_packet_number, client_file_id, file_start_pos, len(data_read))
			response_packet = response_packet + data_read
			
			# send response packet to client
			self.send_response(response_packet, client_address)
			self.ongoing_file_transfers[client_address].update_file_transfer(current_requested_packet_number)

			self.print_information("\n\nResponse sent to client:", 3)
			self.print_information("Client Address: %s" % repr(client_address), 1)
			self.print_information("File ID: %d" % client_file_id, 1)
			self.print_information("File name: %s" % file_name, 1)
			self.print_information("Packet number: %d" % current_requested_packet_number, 1)
			self.print_information("Start Position: %d" % file_start_pos, 1)
			self.print_information("Data: %s" % data_read, 1)

		except:
			# if any errors were encountered then send an error response
			self.print_information("Error reading file.", 5)
			response_packet = struct.pack("!c?2IQI", "F", False, 3, 0, 0, 0)
			self.send_response(response_packet, client_address)

		self.print_information("\n\n", 3)

		return

	# send a reponse for check file for upload message received from client
	def send_check_file_upload_response(self, payload_data, client_address):

		self.print_information("\n\nReceived check file upload request.", 3)
		# check if there is a file transfer in progress
		if (client_address in self.ongoing_file_transfers):
			self.print_information("File upload in progress", 5)
			file_id = self.ongoing_file_transfers[client_address].file_id
			response_packet = struct.pack("!c?I", "D", True, file_id)
			# if there is one then send acknowledgement, probably the earlier ACK was lost
			self.send_response(response_packet, client_address)
			return

		# if there is no prior file trasnfer, the initialize file upload to server
		try:
			(file_size, client_file_name) = struct.unpack("!Q255s", payload_data)
		except:
			self.print_information("\n\nError parsing received packet.\n\n", 5)
			return

		client_file_name = client_file_name.replace('\x00', "").strip()
		
		self.print_information("Client address: %s" % repr(client_address), 1)
		self.print_information("File name: %s" % client_file_name, 1)
		self.print_information("File size: %d" % file_size, 1)
		
		# check if there is enough free disk space on server
		if file_size > self.get_free_space_on_disk():
			self.print_information("Upload file size exceeds free space. Can't proceeed.", 3)
			response_packet = struct.pack("!c?I", "D", False, 5)
			self.send_response(response_packet, client_address)
			return
			
		# check if the file already exists on server
		if os.path.exists(client_file_name):
			self.print_information("Upload file name already exists. Will not overwrite.", 3)
			response_packet = struct.pack("!c?I", "D", False, 2)
			self.send_response(response_packet, client_address)
			return

		# if all conditions are met the setup a new file upload from the client
		self.current_file_id += 1
		file_id = self.current_file_id
		self.ongoing_file_transfers[client_address] = FileTransfer(file_id, client_file_name, self.ttl, file_size)
		self.initialize_empty_file(client_address)
		response_packet = struct.pack("!c?I", "D", True, file_id)
		self.send_response(response_packet, client_address)
		self.print_information("Check upload file request processed successfully.", 1)
		self.print_information("\n\n", 3)

		return


	# send a reponse for file upload message received from client
	def send_file_upload_response(self, payload_data, client_address):

		self.print_information("\n\nReceived file upload request:", 3)
		# try to unpack the message headers
		try:
			(received_packet_number, received_file_id, start_pos, data_size) = struct.unpack("!2IQI", payload_data[:20])
			server_file_id = self.ongoing_file_transfers[client_address].file_id
			file_name = self.ongoing_file_transfers[client_address].file_name
			last_acked = self.ongoing_file_transfers[client_address].last_acked
			file_data = payload_data[20:]
		except:
			self.print_information("\n\nError parsing received packet.\n\n", 5)
			return

		self.print_information("Client address: %s" % repr(client_address), 1)
		self.print_information("File name: %s" % file_name, 1)
		self.print_information("Requested file id: %d" % received_file_id, 1)
		self.print_information("Requested packet number: %d" % received_packet_number, 1)
		self.print_information("Server file id: %d" % server_file_id, 1)
		self.print_information("Last ACKed packet number: %d" % last_acked, 1) 
		self.print_information("Requested start position: %d" % start_pos, 1) 
		

		if (received_file_id != server_file_id):
			self.send_invalid_request_response(payload_data, client_address)
			return

		response_packet = struct.pack("!c?2I", "H", True, received_packet_number, received_file_id)
		# check if the ereceived packet number has already been acknowledged
		# if it has not been already acknowledged 
		# then append data to the local file
		# and send an acknowledgement
		if (received_packet_number not in self.ongoing_file_transfers[client_address].acked_lst):
			self.assemble_file(client_address, start_pos, file_data)
			
			self.send_response(response_packet, client_address)
			self.ongoing_file_transfers[client_address].update_file_transfer(received_packet_number)
			self.print_information("Packet upload request completed successfully.", 3)

		# if its an old packet then ackowledge but dont append data to file
		elif(received_packet_number in self.ongoing_file_transfers[client_address].acked_lst):
			self.send_response(response_packet, client_address)
			self.print_information("Unable to process packet upload request.", 3)
			
		
		self.print_information("\n\n", 3)

		return 

	# listent to server port
	def listen_to_port(self):
		self.print_information("Listening to localhost on port %d." %  self.port_number, 5)
		listening_socket_list = [self.listening_socket]

		# continue listening for ever
		while (True):
			read_ready, write_ready, err_ready = select.select(listening_socket_list, [], [], self.timeout )

			# check for inactive clients
			inactive_client_list = []
			for each_file_transfer in self.ongoing_file_transfers:
				current_ttl = self.ongoing_file_transfers[each_file_transfer].update_ttl(self.ttl, False)
				if current_ttl <=0:
					inactive_client_list.append(each_file_transfer)

			# remove inactive clients
			for each_inactive_client in inactive_client_list:
				del(self.ongoing_file_transfers[each_inactive_client])
				self.print_information("Client %s inactive for more than %d seconds. File transfer removed." %(repr(each_inactive_client), self.ttl), 5)

			if not read_ready and not write_ready and not err_ready:
				self.print_information("Server running: no events", 5)

			# if data available on read sockets, parse data and call action
			# also reset ttl for client
			for sock in read_ready:
				(received_data, client_address) = self.listening_socket.recvfrom(self.buffer_size)
				self.parse_received_data(received_data, client_address)
				
				if client_address in self.ongoing_file_transfers:
					self.ongoing_file_transfers[client_address].update_ttl(self.ttl, True)

				

if __name__ == "__main__":
	server_process = Server()
