import time
import sys
import os
import struct 
from socket import *
import select


class Packet(object):
	def __init__(self, packet_id, packet_data):
		self.packet_id = packet_id
		self.packet_data = packet_data
		self.retransmit_count = 0
		self.epoch_time = time.time()
		

class Client(object):
	def __init__(self):
		self.max_retry_count = 60 # number of retires before giving up
		self.buffer_size = 2048 # maximum buffer size to read
		self.verbose_level = 1 # verbosity level 1 to 5, 1 - everything 5 - critical messages only
		self.retransmit_duration = 1 # timeout of select
		self.max_file_name_length = 255 # maximum file name length
		self.max_data_size = 75 # since largest header is aroubnd 21 bytes and max message size is 100 bytes
								# its safe to assume maximum data in a packet is around 75 bytes
		self.current_window_size = 1
		self.current_window_packets = {}

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
		self.file_size = 0 # total file size 
		self.file_size_transferred = 0 # file size that is transferred at any given time
		self.current_packet_number = 0 # current packet number
		self.file_id =0 # file if received from server
		self.client_file_handle = None #  file handle
		self.packet_dictionary = {} # for stats at the end of file transfer, each item is a tuple with sent time and received time for each packet
		self.start_time = time.time() # start time of file transfer

		# read command line arguments
		self.client_mode = self.get_client_mode() 
		self.server_file_name = self.get_server_file_name()
		self.client_file_name = self.get_client_file_name()
		self.server_ip = self.get_server_ip()
		self.server_port = self.get_server_port()

		# create a socket
		self.server_address = (self.server_ip, self.server_port)
		self.server_socket = socket(AF_INET, SOCK_DGRAM)

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

	# method to print RTT and Thoughput
	def get_stats(self, client_mode):
		self.print_information("File " + client_mode + " complete", 5)
		total_rtt = 0
		for each_pkt in self.packet_dictionary:
			total_rtt += self.packet_dictionary[each_pkt][1] - self.packet_dictionary[each_pkt][0]

		# average RTT is the average of all RTT
		print "Average RTT: %.3g s" % (total_rtt/len(self.packet_dictionary))
		
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

	# send a packet to the server
	def send_request(self, packet_data):
		try:
			self.server_socket.sendto(packet_data, self.server_address)
		except:
			self.print_information("Something went wrong...", 5)
			sys.exit(1)

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

	# indicate invliad response
	def invalid_response(self, custom_message):
		self.print_information("\n\nInvalid response received from server.", 3)
		self.print_information(custom_message + "\n\n", 3)
		return

	# update the received time for each packet
	def update_packet_dictionary(self, packet_name):
		tmp_lst = list(self.packet_dictionary[packet_name])
		tmp_lst[1] = time.time()
		tmp_tuple = tuple(tmp_lst)
		self.packet_dictionary[packet_name] = tmp_tuple
		return

	# read the socket to check for incoming data
	def check_socket_status(self, packet_data):
		data_received = None
		# initialize retransmit count to zero for each packet
		retransmit_count = 0

		while(retransmit_count < self.max_retry_count):
			#send data to the server
			self.send_request(packet_data)
			retransmit_count += 1

			read_socket_list = [self.server_socket]
			read_ready, write_ready, err_ready = select.select(read_socket_list, [], [], self.retransmit_duration)

			#if timer expires without input becoming ready, empty list is returned. In this case go to next iteration of loop (retransmit)
			if not read_ready:
				continue
			else:
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
					continue
				# if incoming packet is valid packet, then execute action
				elif (self.message_type_dictionary[response_type](received_payload)):
					# if action is successful, then break the retransmit loop
					break
				else:
					# if action is false, then packet must be out of order or malformed, retransmit
					self.invalid_response("Wrong packet format....")
					data_received = ""
					continue
	
		# if exceeded retransmit count, then exit with failure
		if (retransmit_count >= self.max_retry_count):
			self.print_information("No valid response from server after %d attempts. Giving up." % self.max_retry_count, 5)
			sys.exit(1)	

		# if action was successful then transition to next state.
		self.message_type_dictionary[self.current_client_status]()
		return

	# send the check file for download message to the server
	def send_check_file_download_request(self):
		self.print_information("Sending download request for file : %s" % self.server_file_name, 3)
		self.current_client_status = "check_download"
		packet_data = struct.pack("!c255s", 'A', self.server_file_name)
		self.packet_dictionary['check'] = (time.time(),None)
		self.check_socket_status(packet_data)


	# process the check file for download response received from the server
	def process_check_file_download_response(self, received_payload):
		self.print_information("Processing check download response", 3)

		# if the current is downloading, then the packet is a duplicate which has arrived out of order,
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
			self.update_packet_dictionary('check')
			self.file_id = file_id
			self.file_size = file_size
			self.print_information("Received check file download response. Server File ID: %d, File Size: %d\n" %(self.file_id, self.file_size), 1)
			self.current_client_status = "downloading"

			return True
		else:
			# if server responded with false, then terminate file transfer
			self.process_error_response(received_payload)

	# send the file download message to the server
	def send_file_download_request(self):
		# loop until all bytes have been received from the server
		while (self.file_size_transferred < self.file_size):
			self.print_information("\n\nSending file download request" ,3)
			self.print_information("File ID: %d" % self.file_id, 1)
			self.print_information("Packet Number: %d" % self.current_packet_number, 1)
			self.print_information("Start Position: %d" % self.file_size_transferred, 1)
			self.print_information("\n\n" ,3)
			self.packet_dictionary['pkt' + str(self.current_packet_number)] = (time.time(),None)
			packet_data = struct.pack("!cIQI", 'E', self.file_id, self.current_packet_number, self.file_size_transferred)
			self.check_socket_status(packet_data)

		
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

		# get data form the packet
		received_data = received_payload[21:]

		# check if received packet number matches the next expected packet number
		if ((self.current_packet_number != packet_number) or (self.file_id != file_id)):
			self.print_information("Incorrect packet number or Incorrect File ID.", 5)
			return False

		# append the packet data to the local file
		try:
			if (self.current_packet_number == 0) and os.path.exists(self.client_file_name):
				self.print_information("Client file: %s exists. Will overwrite." % self.client_file_name, 3)
				tmp_file = open(self.client_file_name,'w')
				tmp_file.close()
			self.update_packet_dictionary('pkt' + str(packet_number))

			self.client_file_handle = open(self.client_file_name, 'a+')
			self.client_file_handle.write(received_data)
			self.file_size_transferred += num_bytes
			self.client_file_handle.close()

			self.print_information("File ID: %d" % (file_id), 1)
			self.print_information("Packet number: %d" % (packet_number), 1)
			self.print_information("Start position: %d" % (start_pos), 1)
			self.print_information("Data length: %d" % (num_bytes), 1)
			self.print_information("\n\n", 3)
			self.current_packet_number += 1
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
		self.print_information("Server file name size: %s" % self.server_file_name, 1)
		self.print_information("File size: %d" % self.file_size, 1)
		
		packet_data = struct.pack("!cQ255s", "C", self.file_size, self.server_file_name)

		self.print_information("\n\n", 3)
		self.packet_dictionary['check'] = (time.time(),None)
		# send packet to the server
		self.check_socket_status(packet_data)
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
		self.update_packet_dictionary('check')
		self.print_information("Server returned file ID: %d" % (self.file_id), 3)
		self.current_client_status = "uploading"
		return True


	# send the file upload message to the server
   	def send_file_upload_request(self):
		# loop until the complete file has been sent and acknowledged by the server
		while (self.file_size_transferred < self.file_size):
			# open file and seek from the current location
			f_handle = open(self.client_file_name)
			f_handle.seek(self.file_size_transferred)
			data_read = f_handle.read(self.max_data_size)

			self.print_information("\n\nSending file upload request",3)
			self.print_information("File name: %s" % self.client_file_name, 1)
			self.print_information("Packet number: %d" % self.current_packet_number, 1)
			self.print_information("Start position: %d" % self.file_size_transferred, 1)
			self.print_information("Data length: %d" % len(data_read), 1)
			self.print_information("\n\n", 3)

			packet_data = struct.pack("!c2IQI", 'G', self.current_packet_number, self.file_id, self.file_size_transferred, len(data_read))
			packet_data = packet_data + data_read
			self.packet_dictionary['pkt' + str(self.current_packet_number)] = (time.time(),None)
			# send data and wait for response
			self.check_socket_status(packet_data)



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

		# if acknowledgement is for a different packet, the discard
		if (self.current_packet_number != packet_number or self.file_id != file_id):
			self.print_information("Incorrect packet number or Incorrect File ID.", 5)
			return False
		
		# if acknowdlegement is for the extecped packet number then 
		# move to the next packet
		self.update_packet_dictionary('pkt'+ str(self.current_packet_number))
		self.print_information("Packet Number: %d " %(self.current_packet_number), 3)
		self.current_packet_number += 1
		self.file_size_transferred += self.max_data_size
		
		return True


			

if __name__ == "__main__":
	client = Client()
	sys.exit(1)