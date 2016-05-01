#!/usr/bin/python

import socket
import select
import thread
from time import sleep
from concurrent.futures import Future

'''
	Contains all the implementation for the shared witeboard server
'''
class Server:
	'''
		Reads a line from the conn socket
	'''
	def readline(self, conn, recv_buffer=1, delim='\n'):
		buffer = ''
		data = True
		while data:
			data = conn.recv(recv_buffer)
			buffer += data

			while buffer.find(delim) != -1:
				line, buffer = buffer.split('\n', 1)
				return line
		return ''

	'''
		Returns a group id for new group request
		-1 if maximum group numbers reached
	'''
	def get_id_from_pool(self):
		for x in xrange(0, self.POOL_SIZE):
			if (self.pool[x] == 0):
				return x+1
			pass
		return -1

	'''
		Broadcast message to all members of id group
	'''
	def broadcast_to_id_group(self, message, id):
		if id not in self.ADDR.keys():
			return
		for _conn in self.ADDR[id]:
			_conn[0].sendall(message)
		return

	'''
		Waits for a new client
		Adds it to some group, or rejects if invalid group id supplied
	'''
	def handle_new_client(self, s):
		while True:
			while True:
				print "Waiting for client"
				conn, addr = s.accept()
				print "connected to client"
				data = self.readline(conn)
				if not data:
					continue
				print "New client request:", data
				client = [_ for _ in data.split()]
				if (len(client)==0):
					print "[Error 101] Invalid id supplied"
					conn.sendall("No such group present!!! :-( Try again...\n")
					continue
				id = int(client[0])
				if (client[0] == '0'):
					# If new group request, get a new group id if available
					# and add the client to the group
					id = self.get_id_from_pool()
					if (id == -1):
						print "[Error 100] Maximum pool limit exceeded"
						conn.sendall("Server busy!!! :-( Visit again...\n")
						continue
					self.ADDR[id] = [[conn]]
					self.pool[id-1] = 1
					break
				else:
					# If client wants to join an already existing group,
					# Check if group id is present
					if (id not in self.ADDR or self.ADDR[id] == None or len(self.ADDR[id]) == 0):
						print "[Error 101] Invalid id supplied"
						conn.sendall("No such group present!!! :-( Try again...\n")
						continue
					self.ADDR[id].append([conn])
					break
			# send success message to client
			conn.sendall("SUCCESS Your id is "+str(id)+"\n")
			print "Client added"
			print self.ADDR
			# handle client and server communication
			thread.start_new_thread( self.waitForClient, (conn, addr, id))

	'''
		Handles the client server communication
		Called from handle_new_client when a new client is added
	'''
	def waitForClient(self, conn, addr, id):
		try:
			# set connection to non blocking
			# otherwise server keeps waiting in case of connection problems
			conn.setblocking(0)
			while True:
				nullData = 0
				while True:
					data = ""
					# wait for communication from client for 5s
					ready = select.select([conn], [], [], 5)
					if (ready[0]):
						# if any kind of data recieved from client, read data
						data = self.readline(conn)
						if len(data)==0:
							nullData=1
						# if an empty line recieved, connection broken, raise exception
						if (nullData==1):
							raise ValueError("Client disconnected")
						print data
					else:
						# if no data recieved within given time period
						# check if client is alive, ping the client
						conn.sendall("Ping\n")
						continue
					if not data:
						# if no data recieved, no need to do anything, wait again
						break
					data = data+'\n'
					print "Data recieved:", data
					# Transmit data to all clients
					for a in self.ADDR[id]:
						# send only to other clients, not self
						if a[0] == conn:
							continue
						try:
							a[0].sendall(data)
						except Exception as e:
							# If unable to communicate with a client, disconnect that client
							# Check group size, if 0 then delete the group 
							print "[ERROR 001]Connection lost with a client. Removing...."
							self.ADDR[id].remove(a)
							if (len(self.ADDR[id]) == 0):
								print "All members of group",id,"left. Removing group...."
								del self.ADDR[id]
								self.pool[id-1] = 0
					pass
				pass
			pass
		except Exception as e:
			# if any error occurs, remove client, check group size
			# if 0 delete the group
			print "[ERROR 002]Connection lost with the client. Removing...."
			x = 0
			print e
			for a in self.ADDR[id]:
				if a[0] == conn:
					del self.ADDR[id][x]
					if len(self.ADDR[id]) == 0:
						print "All members of group",id,"left. Removing group...."
						del self.ADDR[id]
						self.pool[id-1] = 0
					print self.ADDR
				x += 1

	'''
		Create the server
	'''
	def create_server(self):
		print "IP:",self.TCP_IP,"PORT:", self.TCP_PORT
		self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self.s.bind((self.TCP_IP, self.TCP_PORT))
		self.s.listen(1)

		pass

	'''
		Initialize parameters for the server
		IP: TCP IP
		PORT: TCP Port
		BUFFER: Read buffer size
		_POOL_SIZE: Maximum number of different groups that can be created
	'''
	def __init__(self, IP, PORT, BUFFER, _POOL_SIZE):
		self.ADDR = {}
		self.TCP_IP = IP
		self.TCP_PORT = PORT
		self.BUFFER_SIZE = BUFFER
		self.pool = [0 for _ in range(_POOL_SIZE)]
		self.POOL_SIZE = _POOL_SIZE

		self.future = Future()
		self.create_server()
		print "Server created"
		self.handle_new_client(self.s)

		pass

IP = raw_input("Enter IP: ")
port = int(input("Enter port: "))
capacity = int(raw_input("Enter pool capacity: "))
serve = Server(IP, port, 1024, capacity)
