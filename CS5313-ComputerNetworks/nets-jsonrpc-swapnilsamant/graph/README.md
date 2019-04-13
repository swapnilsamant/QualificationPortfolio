The object of this assignment is to implement a function call uusing JSON-RPC. The file structure of this folder is as follows: <br />
```
.
└─  README.md               This README file
└─  client.py               An implementation of the client which makes the JSON-RPC call 
└─  graphFunctions.py       Common functions which convert a graph to a dictionary and a dictionary back to the graph
└─  localDemo.py            Original file provided which does graph increment locally
└─  node.py                 A node object which implements the show function and an increment function 
└─  request.json            An example of the serialed data as passed between the client and the server
└─  server.py               An implementation of the server which accepts a JSON-RPC call and returns the results.

```

The server listens on port 50001 for incoming connections. The server provides a server_increment method for the clients using JSON-PRC. <br />

The node.py file provides a node class. It also provides an increment function which increments the values of a graph created using the nodes.  <br />

The flow for this program can be summarized as follows: <br />


The client creates a DAG using the node objects. <br />
This DAG is serialized using the object_to_dictionary function in graphFunctions.py.  <br />
Serialized graph is sent to the server_increment function in server.py using JSON-RPC. <br />
The server deseralizes(converts the dictionary back to a graph with node objects) using the dictionary_to_object function in graphFunctions.py. <br />
Server executes the increment method of the node class on the root of the graph. <br />
Server serializes the resulting graph using the object_to_dictionary function in graphFunctions.py. <br />
Dictionary object created after serialization is sent back to the client as a result of the JSON-RPC function call. <br />
Client in turn converts the dictionary back to a graph with node objects using dictionary_to_object function in graphFunctions.py. <br />

Usage: <br />

`python server.py`<br />
`python client.py`