
from Tkinter import *
import socket
import thread

"""paint.py: not exactly a paint program.. just a smooth line drawing demo."""

TCP_IP = "127.0.0.1"
TCP_PORT = int(input("Enter port number: "))
b1 = "up"
xold, yold = None, None
root = Tk()
drawing_area = Canvas(root)
draw = []
n = 0

def main(master):
    global drawing_area
    drawing_area.pack()
    drawing_area.bind("<Motion>", motion)
    drawing_area.bind("<ButtonPress-1>", b1down)
    drawing_area.bind("<ButtonRelease-1>", b1up)
    def do_every_second(n):
        global draw
        global drawing_area
        while len(draw)>0:
            x = draw.pop(0)
            drawing_area.create_line(x[0], x[1], x[2], x[3],smooth=TRUE)
        n += 1
        master.after(1000, do_every_second, n)
    do_every_second(n)

def b1down(event):
    global b1
    b1 = "down"           # you only want to draw when the button is down
                          # because "Motion" events happen -all the time-

def b1up(event):
    global b1, xold, yold
    b1 = "up"
    xold = None           # reset the line when you let go of the button
    yold = None

def motion(event):
    if b1 == "down":
        global xold, yold
        if xold is not None and yold is not None:
            event.widget.create_line(xold,yold,event.x,event.y,smooth=TRUE)
            global s
            s.send(str(xold)+" "+str(yold)+" "+str(event.x)+" "+str(event.y))
                          # here's where you draw it. smooth. neat.
        xold = event.x
        yold = event.y

def receive():
    global s
    global drawing_area
    while 1:
        data = s.recv(BUFFER_SIZE)
        xold, yold, eventx, eventy = data.split(" ")
        draw.append([xold, yold, eventx, eventy])

BUFFER_SIZE = 1024
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect((TCP_IP, TCP_PORT))
key = raw_input("Enter id(default is 0): ")
s.send(key)
data = s.recv(BUFFER_SIZE)
print data
thread.start_new_thread(receive, ())
if __name__ == "__main__":
    main(root)
    root.mainloop()