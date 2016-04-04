#!/usr/bin/python

import socket
import select
import thread
from time import sleep
from concurrent.futures import Future

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
			while True:
				print "Waiting for client"
				conn, addr = s.accept()
				print "connected to client"
				data = conn.recv(self.BUFFER_SIZE)
				if not data:
					continue
				print "New client request:", data
				client = [_ for _ in data.split()]
				if (len(client)==0):
					print "[Error 101] Invalid id supplied"
					conn.send("No such group present!!! :-( Try again...\n")
					continue
				id = int(client[0])
				if (client[0] == '0'):
					id = self.get_id_from_pool()
					if (id == -1):
						print "[Error 100] Maximum pool limit exceeded"
						conn.send("Server busy!!! :-( Visit again...\n")
						continue
					self.ADDR[id] = [[conn]]
					self.pool[id-1] = 1
					break
				else:
					if (id not in self.ADDR or self.ADDR[id] == None or len(self.ADDR[id]) == 0):
						print "[Error 101] Invalid id supplied"
						conn.send("No such group present!!! :-( Try again...\n")
						continue
					self.ADDR[id].append([conn])
					break
			conn.send("SUCCESS Your id is "+str(id)+"\n")
			print "Client added"
			print self.ADDR
			thread.start_new_thread( self.waitForClient, (conn, addr, id))

	def waitForClient(self, conn, addr, id):
		try:
			conn.setblocking(0)
			while True:
				nullData = 0
				while True:
					data = ""
					ready = select.select([conn], [], [], 5)
					if (ready[0]):
						data = conn.recv(self.BUFFER_SIZE)
						if len(data)==0:
							nullData=1
						if (nullData==1):
							raise ValueError("Client disconnected")
						print data
					else:
						conn.send("Ping")
						continue
					if not data:
						break
					print "Data recieved:", data
					for a in self.ADDR[id]:
						try:
							a[0].send(data)
						except Exception as e:
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

	def create_server(self):
		print "IP:",self.TCP_IP,"PORT:", self.TCP_PORT
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

		self.future = Future()
		self.create_server()
		print "Server created"
		self.handle_new_client(self.s)

		pass

port = int(input("Enter port: "))
serve = Server("127.0.0.1", port, 1024, 1)
