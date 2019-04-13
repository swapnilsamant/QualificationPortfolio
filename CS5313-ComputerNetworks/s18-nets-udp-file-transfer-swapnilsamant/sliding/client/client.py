import time
import sys
import os
import struct 
from socket import *
import select
import random
import string
import operator

# class to represent a typical packet
class Packet(object):
	def __init__(self, seq_num, packet_data):
		self.seq_num = seq_num 				# sequence number for the packet
		self.packet_data = packet_data 		# contents of the packet
		self.retransmit_count = 0 			# how many times the packet has been sent
		self.epoch_time = None 				# creating time for the packet
		self.response_received_time = None 	# acknowledgment time of the packet
		self.last_sent = None				# last time the packet was sent
	
	# update the acked time for a packet
	def update_received_time(self):
		self.response_received_time = time.time()
		return

	# send the packet to the server
	def send_packet(self, socket, server_addr):
		try:
			
			current_time = time.time()

			socket.sendto(self.packet_data, server_addr)

			# update the first sent time for packet
			if self.epoch_time is None:
				self.epoch_time = current_time

			# how many times the packet is transmitted
			self.retransmit_count += 1

			# what time the packet was last sent
			self.last_sent = current_time

		except:
			print "Something went wrong..."
			sys.exit(1)
		return


class Client(object):
	def __init__(self):
		self.max_retry_count = 60 			# number of retires before giving up
		self.buffer_size = 2048 			# maximum buffer size to read
		self.verbose_level = 1 				# verbosity level 1 to 5, 1 - everything 5 - critical messages only
		self.retransmit_duration = 1 		# timeout of select
		self.max_file_name_length = 255 	# maximum file name length
		self.max_data_size = 75 			# since largest header is aroubnd 21 bytes and max message size is 100 bytes
											# its safe to assume maximum data in a packet is around 75 bytes
		
		self.dynamic_window_size = True		# flag to modify the window size based on lost packets
		self.current_window_size = 1 		# starting window size
		self.current_window_packets = [] 	# current packet ids in send window
											# packets that have been sent but not acknowledged

		self.last_acked = None					# sequence number of last acknowledged packet

		# use a random file name for the temp file
		# temp file is used to join the incoming packets
		# for creating the client file
		self.tmp_file_name = ''.join(random.choice(string.ascii_lowercase + string.digits) for _ in range(8))

		# client can be ran in upload or download mode
		self.valid_modes = ['upload', 'download']

		# method to call based on type of message received
		self.message_type_dictionary = {'B': self.process_check_file_download_response,
										'F': self.process_file_download_response,
										'D': self.process_check_file_upload_response,
										'H': self.process_file_upload_response,
										'I': self.process_error_response,
										'downloading': self.send_file_download_request,
										'uploading':self.send_file_upload_request}

		# error codes sent by the server
		self.error_codes = {0: "Unknonwn error on server, please try again.",
							1: "File does not exist on server. Please check download file name.",
							2: "File name already exists on server. Please use a different server file name.",
							3: "Error while reading file on server.",
							4: "Error while writing file on server.",
							5: "Upload file size exceeds available free space."}

		# initialize file transfer
		self.file_size = 0 				# total file size 
		self.file_size_transferred = 0 	# file size that is transferred at any given time
		self.current_packet_number = 0 	# current packet number
		self.file_id = 0 				# file if received from server
		self.client_file_handle = None 	# ile handle
		self.packet_stats_dictionary = {} # for statistics at the end of file transfer, 
										# items are objects of class Packet
		self.start_time = time.time() 	# start time of file transfer

		# read command line arguments
		self.client_mode = self.get_client_mode() 
		self.server_file_name = self.get_server_file_name()
		self.client_file_name = self.get_client_file_name()
		self.server_ip = self.get_server_ip()
		self.server_port = self.get_server_port()

		# create a socket
		self.server_address = (self.server_ip, self.server_port)
		self.server_socket = socket(AF_INET, SOCK_DGRAM)
		self.server_socket.setblocking(0)

		# client can be in check-download, downloading status in download mode
		# and check-upload and uploading status in upload mode
		self.current_client_status = None

		# start the client in the selected mode
		if (self.client_mode == 'download'): 
			# protocol starts by sending a check download file message to the server in download mode
			self.send_check_file_download_request()
			self.get_stats("download")

		elif (self.client_mode == 'upload'): 
			# protocol starts by sending a check upload file message to the server in upload mode
			self.send_check_file_upload_request()
			self.get_stats("upload")

	# function to print RTT and Thoughput
	def get_stats(self, client_mode):
		self.print_information("File " + client_mode + " complete", 5)
		total_rtt = 0
		total_packets = 0

		# consider only the packets which were not retransmitted
		for each_pkt in self.packet_stats_dictionary:
			if self.packet_stats_dictionary[each_pkt].retransmit_count < 2:
				total_rtt += self.packet_stats_dictionary[each_pkt].response_received_time - self.packet_stats_dictionary[each_pkt].epoch_time
				total_packets += 1

		# average RTT is the average of all RTT where retransmit count was zero
		print "Average RTT: %.3g s" % (total_rtt/total_packets)
		
		# Throughput is the number of bytes transferred per second
		print "Throughput: %.3g B/s" % (self.file_size / (time.time() - self.start_time))

	# print usage in case of incorrect usage
	def print_usage(self):
		self.print_information("Usage:\npython client.py <mode> <server_file_name> <client_file_name> <server_ip_address> <server_port_number>", 5)
		sys.exit("Example:\npython client.py download server_file.txt client_file.txt 127.0.0.1 5001\n")	

	# get client mode from command line argument
	def get_client_mode(self):
		try:
			arg = str(sys.argv[1])
		except IndexError:
			self.print_information("Please provide a valid client mode.", 5)
			self.print_usage()
		if (arg not in self.valid_modes):
			err_str =  "\nInvalid client mode.\nValid client mode values are: %s \n" % (', '.join(self.valid_modes))
			self.print_information(err_str, 5)
			self.print_usage()
		else:
			return arg

	# get server ip address from command line argument
	def get_server_ip(self):
		try:
			arg = str(sys.argv[4])
		except IndexError:
			self.print_information("Please provide a valid server IP address.", 5)
			self.print_usage()
		else:
			return arg

	# get server port number from command line argument
	def get_server_port(self):
		try:
			arg = int(sys.argv[5])
		except ValueError:
			self.print_information("Invalid port number.", 5)
			self.print_usage()
		except IndexError:
			self.print_information("Please provide a valid server port number.", 5)
			self.print_usage()
		if (arg <=1024 or arg >= 65535):
			self.print_information("Port number must be between 1025 and 65535.", 5)
			self.print_usage()
		else:
			return arg

	# get server file name from command line argument
	def get_server_file_name(self):
		try:
			arg = str(sys.argv[2])
		except IndexError:
			self.print_information("Please provide a valid server file name.", 5)
			self.print_usage()

		if (len(arg) > self.max_file_name_length):
			self.print_information("Server file name too long. Max file name length is %s characters." % self.max_file_name_length, 5)
			self.print_usage()
		else:
			return arg

	# get client file name from command line argument
	def get_client_file_name(self):
		try:
			arg = str(sys.argv[3])
		except IndexError:
			self.print_information("Please provide a valid local file name.", 5)
			self.print_usage()

		if (len(arg) > self.max_file_name_length):
			self.print_information("Client file name too long. Max file name length is %s characters." % self.max_file_name_length, 5)
			self.print_usage()
		else:
			return arg

	# print packet ids of all packets in flight
	# for debug purpose only
	def print_current_window(self):
		print 'Current packets in flight:'
		print self.current_window_packets
		return

	# print the error response received from the server
	def process_error_response(self, received_payload):
		(error_code,) = struct.unpack("!I", received_payload[1:5])
		self.print_information(self.error_codes[error_code], 5)
		sys.exit(1)

	# print general trace and debug messages
	def print_information(self, message, verbose_level):
		if verbose_level >= self.verbose_level:
			print message
		return

	# indicate invalid response
	def invalid_response(self, custom_message):
		self.print_information("\n\nInvalid response received from server.", 3)
		self.print_information(custom_message + "\n\n", 3)
		return

	# create empty file
	def initialize_empty_file(self):
		# create an empty file having a file size
		# that was returned by the server
		f = open(self.client_file_name, "wb")
		f.seek(self.file_size - 1)
		f.write("\0")
		f.close()
		return

	# delete the partially downloaded file 
	# in case of unsucessful file transfer
	def delete_partial_file(self):
		try:
			os.remove(self.client_file_name)
			print 'Partial file deleted.'
		except:
			pass
		
		return

	# construct the file using received packets
	def assemble_file(self, start_pos, received_data):
		with open(self.client_file_name, 'r') as old_buffer, open(self.tmp_file_name, 'w') as new_buffer:
			# copy until start position of the received packet
			new_buffer.write(old_buffer.read(start_pos))
			# insert data from the current packet
			new_buffer.write(received_data)
			# copy the rest of the file
			old_buffer.seek(start_pos + len(received_data))
			new_buffer.write(old_buffer.read())

		# delete existing file
		os.remove(self.client_file_name)
		# rename new file to the client file
		os.rename(self.tmp_file_name, self.client_file_name)
		return
	
	# update the last acked packet number
	def update_last_acked(self):
		# check packet number of last continuous packet acked by server
		for pkt_id in sorted(self.packet_stats_dictionary, key = lambda p: self.packet_stats_dictionary[p].seq_num):
			# exclude the check packet
			if pkt_id != "check":
				if self.packet_stats_dictionary[pkt_id].response_received_time != None:
					self.last_acked = self.packet_stats_dictionary[pkt_id].seq_num 
				else:
					return
		return

	# function to dynamically change the window size
	def update_window_size(self):
		if not self.dynamic_window_size:
			return

		window_has_retransmits = False # to check if the current packet window has any retransmits

		for each_pkt in self.current_window_packets:
			if self.packet_stats_dictionary[each_pkt].retransmit_count > 1:
				window_has_retransmits = True
				break

		# if the current window does not have any retransmits then
		# increase the window size by one
		# otherwise reduce the window size by half.
		if not window_has_retransmits:
			self.current_window_size += 1
			self.print_information("Increasing window size to: %d"  % (self.current_window_size), 3)
		else:
			self.current_window_size = int(self.current_window_size/2) if int(self.current_window_size/2) > 0 else 1
			self.print_information("Decreasing window size to: %d"  % (self.current_window_size), 3)

		return

	# read the socket to check for incoming data
	def check_socket_status(self):
		status_flag = False
		read_socket_list = [self.server_socket]
		read_ready, write_ready, err_ready = select.select(read_socket_list, [], [], self.retransmit_duration)

		# if timer expires without input becoming ready, empty list is returned. 
		# In this case go to next iteration of loop (retransmit)
		if not (read_ready or write_ready or err_ready):
			return

		elif read_ready:
			try:
				# read data from the socket
				data_received = self.server_socket.recv(self.buffer_size)
			except:
				self.print_information("Something went wrong while receiving data from socket", 4)
				sys.exit(1)

			# check incoming packet type
			response_type = data_received[0:1]

			# get packet payload
			received_payload = data_received[1:]
			
			# if incoming packet is not a valid packet, then discard
			if response_type not in self.message_type_dictionary: 
				self.invalid_response("Incorrect type of packet or no packet header.")
				data_received = ""
			# if incoming packet is valid packet, then execute action
			elif (self.message_type_dictionary[response_type](received_payload)):
				# if action is successful, then break the retransmit loop
				status_flag = True
			else:
				# if action is false, then packet must be out of order or malformed, retransmit
				self.invalid_response("Wrong packet format....")
				data_received = ""
	
			# if action was successful then transition to next state.
			if status_flag:
				self.message_type_dictionary[self.current_client_status]()
		else:
			return
		
		return

	# send the check file for download message to the server
	def send_check_file_download_request(self):
		self.print_information("Sending download request for file : %s" % self.server_file_name, 3)
		self.current_client_status = "check_download"
		# construct the packet with file name for download
		packet_data = struct.pack("!c255s", 'A', self.server_file_name)
		# add the packet to the packet stats and current window
		current_pkt = Packet(self.current_packet_number, packet_data)
		self.current_window_packets.append('check')
		self.packet_stats_dictionary['check'] = current_pkt

		# response for the check download request is needed to proceed to the 
		# next step i.e. request to download the file
		while 'check' in self.current_window_packets:
			# send the packet
			self.packet_stats_dictionary['check'].send_packet(self.server_socket, self.server_address)

			# if the packet is sent more than max number of tries
			# then exit with failure	
			if self.packet_stats_dictionary['check'].retransmit_count > self.max_retry_count:
				print "No response from server"
				sys.exit(1)

			# check for response
			self.check_socket_status()

	# process the check file for download response received from the server
	def process_check_file_download_response(self, received_payload):
		self.print_information("Processing check download response", 3)

		# if the current status is downloading, then the packet is a duplicate which has arrived out of order,
		# discard this packet
		if (self.current_client_status != "check_download"):
			self.invalid_response("Downloading packet received while in check download file state.")
			return True

		# try to extract fields from the packet payload
		try:
			(file_status, file_id, file_size) = struct.unpack("!?IQ", received_payload)
		except:
			self.invalid_response("Invalid packet format.")
			return False

		# if server reported true for check message then proceed to next step
		if (file_status):
			# update packet received time
			self.packet_stats_dictionary['check'].update_received_time()

			self.file_id = file_id
			self.file_size = file_size

			# remove check packet from the send packet window
			self.current_window_packets.remove('check')
			
			# initialize an empty file with the file size received
			# from the server
			self.initialize_empty_file()

			self.print_information("Received check file download response. Server File ID: %d, File Size: %d\n" %(self.file_id, self.file_size), 1)
			self.current_client_status = "downloading"

			return True
		else:
			# if server responded with false, then terminate file transfer
			self.process_error_response(received_payload)

	# send the file download message to the server
	def send_file_download_request(self):
		# loop until the request window has pending packets
		# or all packets have not been requested
		while (self.file_size_transferred < self.file_size) or (len(self.current_window_packets) > 0):
			# if current window has less packets than max window size
			# then request more packets
			if (self.current_window_size > len(self.current_window_packets)):
				# request packets starting from current last acked sequence number 
				# to last acked seq num + current max window size

				if self.last_acked is None:
					window_lower_bound = 0
					window_upper_bound = self.current_window_size
				else:
					window_lower_bound = self.last_acked + 1
					window_upper_bound = self.last_acked + self.current_window_size + 1

				for seq_num in range(window_lower_bound, window_upper_bound):
					# if all packets have been added to the requets window then break
					if (self.file_size_transferred >= self.file_size):
						break
					# current packet id
					pkt_id = 'pkt' + str(seq_num)

					# if the packet has not been requested yet
					# then add it to the request window
					if pkt_id not in self.packet_stats_dictionary:
						self.print_information("\n\nSending file download request" ,3)
						self.print_information("File ID: %d" % self.file_id, 1)
						self.print_information("Packet Number: %d" % seq_num, 1)
						self.print_information("Start Position: %d" % self.file_size_transferred, 1)
						self.print_information("\n\n" ,3)
					
						packet_data = struct.pack("!cIQI", 'E', self.file_id, seq_num, self.file_size_transferred)
						current_pkt = Packet(seq_num, packet_data)

						self.packet_stats_dictionary[pkt_id] = current_pkt
						self.current_window_packets.append(pkt_id)
						self.file_size_transferred = self.file_size_transferred + self.max_data_size
						self.current_packet_number = seq_num


			# itertate through all packets in the request window
			for each_pkt in sorted(self.current_window_packets):
				# if the retransmit count for a packet has exceeded the max retransmit count
				# then report failure
				if self.packet_stats_dictionary[each_pkt].retransmit_count > self.max_retry_count:
					self.print_information("No valid response from server after %d attempts. Giving up." % self.max_retry_count, 5)
					self.delete_partial_file()
					sys.exit(1)	

				# send a request for the packet
				# if it has not been requested yet
				# or if the packet has not been acknowledged after timeout
				if self.packet_stats_dictionary[each_pkt].epoch_time is None:
					self.packet_stats_dictionary[each_pkt].send_packet(self.server_socket, self.server_address)

				elif (time.time() - self.packet_stats_dictionary[each_pkt].last_sent > self.retransmit_duration):
					self.packet_stats_dictionary[each_pkt].send_packet(self.server_socket, self.server_address)


			# check for arriving packets
			self.check_socket_status()

	# process the file download response received from the server
	def process_file_download_response(self, received_payload):
		self.print_information("\n\nProcessing file download response", 3)

		# if current state is not downloading then the packet has arrived out of order
		if (self.current_client_status != "downloading"):
			return True

		# try to extract fields from the packet payload
		try:
			(file_status, packet_number, file_id, start_pos, num_bytes) = struct.unpack("!?2IQI", received_payload[:21])
		except:
			self.invalid_response("Invalid packet format.")
			return False

		# if the server responded with false for download message, then terminate file transfer
		if not file_status:
			self.process_error_response(received_payload)

		# if the packet payload size is smaller than equal to the total header size then there is no data,
		# discard packet
		if len(received_payload) <= 17:
			self.invalid_response("Packet with no data.... :-(")
			return False

		# get data from the packet
		received_data = received_payload[21:]

		pkt_id = 'pkt' + str(packet_number)

		# check if received packet sequence number
		# is in the pending window
		if ((pkt_id not in self.current_window_packets) or (self.file_id != file_id)):
			self.print_information("Incorrect packet number or Incorrect File ID.", 5)
			return False
		
		try:
			# append the packet data to the local file
			self.assemble_file(start_pos, received_data)

			# update statistics for the received packet
			self.packet_stats_dictionary[pkt_id].update_received_time()
			
			# get the last continuous packed acked by the server
			self.update_last_acked()

			# update the window size based on the recently received packet
			self.update_window_size()

			# remove received packet from the current window
			self.current_window_packets.remove(pkt_id)

			# print information about the received packet
			self.print_information("File ID: %d" % (file_id), 1)
			self.print_information("Packet number: %d" % (packet_number), 1)
			self.print_information("Start position: %d" % (start_pos), 1)
			self.print_information("Data length: %d" % (num_bytes), 1)
			self.print_information("ReTX Count: %d" % (self.packet_stats_dictionary[pkt_id].retransmit_count), 1)
			self.print_information("\n\n", 3)
			
			

			return True

		except:
			self.print_information("Something went wrong...", 5)
			return False

	# send the check file for upload message to the server
	def send_check_file_upload_request(self):

		self.print_information("\n\nSending check file upload request",3)
		
		# check if the file exists on the client
		if not os.path.exists(self.client_file_name):
			self.print_information("Client file does not exist.", 5)
			sys.exit(1)

		self.current_client_status = "check_upload"
		# get local file size
		self.file_size = os.path.getsize(self.client_file_name)
		self.print_information("Server file name: %s" % self.server_file_name, 1)
		self.print_information("File size: %d" % self.file_size, 1)
		
		packet_data = struct.pack("!cQ255s", "C", self.file_size, self.server_file_name)

		self.print_information("\n\n", 3)
		pkt_id = 'check'
		
		# send packet to the server

		current_pkt = Packet(self.current_packet_number, packet_data)
		self.current_window_packets.append(pkt_id)
		self.packet_stats_dictionary[pkt_id] = current_pkt
		
		while 'check' in self.current_window_packets:
			self.packet_stats_dictionary['check'].send_packet(self.server_socket, self.server_address)
			if self.packet_stats_dictionary['check'].retransmit_count > self.max_retry_count:
				print "No response from server"
				sys.exit(1)

			self.check_socket_status()

		return

	# process the check file for upload response received from the server
	def process_check_file_upload_response(self, received_payload):
		self.print_information("Processing check file upload response", 3)

		# check if the program is in correct state
		if (self.current_client_status != "check_upload"):
			return True

		# try to extract fields from the packet payload
		try:
			(file_status, file_id) = struct.unpack("!?I", received_payload)
		except:
			self.invalid_response("Invalid packet format.")
			return False

		# if server responded with false, then terminate file transfer
		if not file_status:
			self.process_error_response(received_payload)

		self.file_id = file_id
		self.packet_stats_dictionary['check'].update_received_time()

		# remove check packet from the window
		self.current_window_packets.remove('check')

		self.print_information("Server returned file ID: %d" % (self.file_id), 3)
		self.current_client_status = "uploading"
		return True

	# send the file upload message to the server
   	def send_file_upload_request(self):
		# loop until the complete file has been sent and acknowledged by the server
		# loop until the request window has pending packets
		# or all packets have not been requested
		while (self.file_size_transferred < self.file_size) or (len(self.current_window_packets) > 0):
			if (self.current_window_size > len(self.current_window_packets)):
				if self.last_acked is None:
					window_lower_bound = 0
					window_upper_bound = self.current_window_size
				else:
					window_lower_bound = self.last_acked + 1
					window_upper_bound = self.last_acked + self.current_window_size + 1

				for seq_num in range(window_lower_bound, window_upper_bound):
					# if all packets have been added to the requets window then break
					if (self.file_size_transferred >= self.file_size):
						break
					
					pkt_id = 'pkt' + str(seq_num)

					# if the packet is not requetsed yet
					# then add it to the request window
					if pkt_id not in self.packet_stats_dictionary:
						# open file and seek from the current location
						f_handle = open(self.client_file_name)
						f_handle.seek(self.file_size_transferred)
						data_read = f_handle.read(self.max_data_size)

						self.print_information("\n\nSending file upload request",3)
						self.print_information("File name: %s" % self.client_file_name, 1)
						self.print_information("Packet number: %d" % seq_num, 1)
						self.print_information("Start position: %d" % self.file_size_transferred, 1)
						self.print_information("Data length: %d" % len(data_read), 1)
						self.print_information("\n\n", 3)

						packet_data = struct.pack("!c2IQI", 'G', seq_num, self.file_id, self.file_size_transferred, len(data_read))
						packet_data = packet_data + data_read
						current_pkt = Packet(seq_num, packet_data)
						self.current_window_packets.append(pkt_id)
						self.packet_stats_dictionary[pkt_id] = current_pkt
						
						self.file_size_transferred += self.max_data_size
						self.current_packet_number = seq_num
						
			# itertate through all packets in the request window
			for each_pkt in sorted(self.current_window_packets):
				# if the retransmit count for a packet has exceeded the max retransmit count
				# then report failure
				if self.packet_stats_dictionary[each_pkt].retransmit_count > self.max_retry_count:
					self.print_information("No valid response from server after %d attempts. Giving up." % self.max_retry_count, 5)
					sys.exit(1)	
				# send a request for the packet
				# if it has not been requested yet
				# or if the acknowledgement has not arrived after timeout

				if self.packet_stats_dictionary[each_pkt].epoch_time is None:
					self.packet_stats_dictionary[each_pkt].send_packet(self.server_socket, self.server_address)

				elif (time.time() - self.packet_stats_dictionary[each_pkt].last_sent > self.retransmit_duration):
					self.packet_stats_dictionary[each_pkt].send_packet(self.server_socket, self.server_address)
				
			# check for arriving packets
			self.check_socket_status()

	# process the file upload response received from the server
	def process_file_upload_response(self, received_payload):
		self.print_information("Processing file upload response", 3)

		if (self.current_client_status != "uploading"):
			return True

		try:
			(file_status, packet_number, file_id) = struct.unpack("!?2I", received_payload)
		except:
			self.invalid_response("Invalid packet format.")
			return False


		if not file_status:
			self.process_error_response(received_payload)

		pkt_id = 'pkt' + str(packet_number)

		# if acknowledgement is for a different packet, the discard
		if ((pkt_id not in self.current_window_packets) or (self.file_id != file_id)):
			self.print_information("Incorrect packet number or Incorrect File ID.", 5)
			return False
		
		# update packet stats for the received packet
		# self.update_packet_dictionary(pkt_id)
		self.packet_stats_dictionary[pkt_id].update_received_time()

		# update last acked based on the received packet
		self.update_last_acked()

		# update window size based on the received packet
		self.update_window_size()

		# remove the received packet from the send window
		self.current_window_packets.remove(pkt_id)

		self.print_information("Packet Number: %d " %(self.current_packet_number), 3)
		
		return True




if __name__ == "__main__":
	client = Client()
	sys.exit(1)