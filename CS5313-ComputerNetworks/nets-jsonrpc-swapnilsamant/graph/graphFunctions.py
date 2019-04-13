from node import *

# create a dictionary from the tree composed of node objects
def object_to_dictionary(current_node, level=0, serialized_graph={}):
	# get the current objects id. 
	# unique across scope
	curr_obj_id = str(id(current_node))
	# check if the node is already in the dictionary
	# node can be in dictionary only once
	if curr_obj_id not in serialized_graph:
		# if node is not in dictionary then add it
		serialized_graph[curr_obj_id] = {}
		# assign the name of the node
		serialized_graph[curr_obj_id]['name'] = current_node.name		
		# assign a level to the node, root is level 0
		serialized_graph[curr_obj_id]['level'] = level
		# assign the current value of the node
		serialized_graph[curr_obj_id]['value'] = current_node.val
		# create an empty list as children for the node
		serialized_graph[curr_obj_id]['children'] = []
		# add all children to the list of children
		for each_child in current_node.children:
			serialized_graph[curr_obj_id]['children'].append(str(id(each_child)))

	# recursively call serialize to process all children
	for c in current_node.children: 
		object_to_dictionary(c, level+1, serialized_graph)
	
	# return serialized graph
	return serialized_graph

# create a tree of node objects from the dictionary
def dictionary_to_object(serialized_graph):
	# initialize root node to None
	root_node = None
	# iterate through all nodes in the dictionary
	for each_node in serialized_graph:
		# create node objects for each node in the dictionary
		# and assign a new dictionary item in the existing
		# dictionary to hold the object
		serialized_graph[each_node]['node_object'] = node(serialized_graph[each_node]['name'])
		# get the value of node from the dictionary
		serialized_graph[each_node]['node_object'].val = serialized_graph[each_node]['value']
		# empty list of childrem
		serialized_graph[each_node]['node_object'].children = []

		# if the level of this node is 0, then assign root node to the current node object
		if serialized_graph[each_node]['level'] == 0:
			root_node = serialized_graph[each_node]['node_object']
	
	# after creating all nodes,
	# iterate through each node to assign the 
	# children node object pointer to the correct parent 
	for each_node in serialized_graph:
		# iterate through all children 
		for each_child in serialized_graph[each_node]['children']:
			serialized_graph[each_node]['node_object'].children.append(serialized_graph[each_child]['node_object'])

	# return the root node
	return root_node