import socket
from bsonrpc import JSONRpc
from bsonrpc import request, service_class
from graphFunctions import *				# for object to dictionary conversion functions
from node import *							# for node class

# Class providing functions for the client to use:
@service_class
class ServerServices(object):

	# decorator to expose server_increment method
	@request
	def server_increment(self, ser_graph):
		# convert the received dictionary to
		# a tree with node objects
		root = dictionary_to_object(ser_graph)
		print "graph before increment"
		# show the tree using node class show method
		root.show()
		# call the increment method on the node module
		increment(root)
		print "graph after increment"
		# show the tree using node class show method
		root.show()
		# serialize the tree to a dictionary and return
		return object_to_dictionary(root)

# create a TCP socket
ss = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
# bind the socket to port 50001
ss.bind(('localhost', 50001))
# listen for incoming connections
# upto 10 connections in backlog
ss.listen(10)

# continue forever
while True:
	# acceopt incoming connections
	s, _ = ss.accept()
	# JSONRpc object spawns internal thread to serve the connection.
	JSONRpc(s, ServerServices())