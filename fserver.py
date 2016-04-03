#!/usr/bin/python

import socket
import thread

class Server:

	def get_id_from_pool(self):
		for x in xrange(0, self.POOL_SIZE):
			if (self.pool[x] == 0):
				return x+1
			pass
		return -1

	def broadcast_to_id_group(self, message, id):
		if id not in self.ADDR.keys():
			return
		for _conn in self.ADDR[id]:
			_conn[0].send(message)
		return

	def handle_new_client(self, s):
		while True:
			print "Waiting for client"
			conn, addr = s.accept()
			print "connected to client"
			data = conn.recv(self.BUFFER_SIZE)
			if not data:
				continue
			print "New client request:", data
			client = [_ for _ in data.split()]
			id = int(client[0])
			if (client[0] == '0'):
				id = self.get_id_from_pool()
				if (id == -1):
					conn.send("Server busy!!! :-( Visit again...\n")
					continue
				self.ADDR[id] = [[conn]]
				self.pool[id-1] = 1
				break
			else:
				if (self.ADDR[id] == None or len(self.ADDR[id]) == 0):
					conn.send("No such group present!!! :-( Try again...\n")
					continue
				self.ADDR[id].append([conn])
				break
		conn.send("SUCCESS Your id is"+str(id)+"\n")
		print "Client added\n"
		return conn, addr, id


	def waitForClient(self):
		conn, addr, id = self.handle_new_client(self.s)
		thread.start_new_thread(self.waitForClient, ())
		while True:
			while True:
				data = conn.recv(self.BUFFER_SIZE)
				if not data:
					break
				print "Data recieved:", data
				for a in self.ADDR[id]:
					a[0].send(data)
				pass
			pass
		pass

	def create_server(self):
		print self.TCP_IP, self.TCP_PORT
		self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self.s.bind((self.TCP_IP, self.TCP_PORT))
		self.s.listen(1)

		pass

	def __init__(self, IP, PORT, BUFFER, _POOL_SIZE):
		self.ADDR = {}
		self.TCP_IP = IP
		self.TCP_PORT = PORT
		self.BUFFER_SIZE = BUFFER
		self.pool = [0 for _ in range(_POOL_SIZE)]
		self.POOL_SIZE = _POOL_SIZE

		self.create_server()
		print "Server created"
		self.waitForClient()

		pass

port = int(input("Enter port: "))
serve = Server("127.0.0.1", port, 1024, 10)
