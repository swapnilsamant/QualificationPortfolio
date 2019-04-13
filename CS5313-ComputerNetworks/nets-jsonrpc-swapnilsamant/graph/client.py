import socket
from bsonrpc import JSONRpc
from node import *				# for node class
from graphFunctions import *	# for object to dictionary conversion functions

# method for Remote Procedure Call 
def increment_using_rpc(current_node):
	# create a server socket
	s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	# connect to the server socket
	s.connect(('localhost', 50001))

	# Connects via socket to RPC peer node
	rpc = JSONRpc(s)

	# Get a RPC peer proxy object
	server = rpc.get_peer_proxy()

	# Serialize the graph as a dictionary
	# Dictionary structure 
	# {"root_object_id": {"name": "root",
	# 						"level": 0,
	# 						"value": 0,
	# 						"children":["leaf1_object_id", "leaf1_object_id", "leaf2_object_id"]
	# 						},
	# 	"leaf1_object_id": {.....
	# }
	ser_graph = object_to_dictionary(current_node)
	
	# Remote procedure call using the serialized tree and the root node name
	result = server.server_increment(ser_graph)

	# Close thr RPC. 
	# Closes the socket 's' also
	rpc.close() 

	# construct the tree using objects 
	# from the serialized output received from the RPC
	current_node = dictionary_to_object(result)

	# return the root node
	return current_node

# create first leaf node
leaf1 = node("leaf1")
# create first leaf node
leaf2 = node("leaf2")

# create root node, add two children
root = node("root", [leaf1, leaf1, leaf2])

print "graph before increment"
root.show()

# do this increment remotely
root = increment_using_rpc(root)

print "graph after increment"
root.show()
