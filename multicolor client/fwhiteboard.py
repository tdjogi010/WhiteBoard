
from Tkinter import *
from ttk import Scrollbar, Sizegrip
import socket
import thread
from PIL import Image, ImageDraw
import tkFileDialog
from tkColorChooser import askcolor              

# Color button listener
color = "#000000"
def getColor():
    global color
    color = askcolor()[1] 
    print color

'''
    Clear button action handle function
'''
def clear():
    # Tell server to clear other client whiteboard
    global s
    s.sendall("clear\n")
    global drawing_area
    global image
    global imagedraw
    # Clear canvas
    drawing_area.delete("all")
    # Clear image
    image = Image.new("RGB", (root.winfo_screenwidth(), root.winfo_screenheight()), (255, 255, 255))
    imagedraw = ImageDraw.Draw(image)

'''
    Save current state of canvas as image button action handler
'''
def save_image():
    global image
    global root
    # Formats to save image in...
    myFormats = [
    ('Windows Bitmap','*.bmp'),
    ('Portable Network Graphics','*.png'),
    ('JPEG / JFIF','*.jpg'),
    ('CompuServer GIF','*.gif'),
    ]
    fileName = tkFileDialog.asksaveasfilename(parent=root,filetypes=myFormats ,title="Save the image as...")
    image.save(fileName)

'''
    Master thread
    Updates the whiteboard every second
'''
def main(master):
    global drawing_area
    drawing_area.pack()
    drawing_area.bind("<Motion>", motion)
    drawing_area.bind("<ButtonPress-1>", b1down)
    drawing_area.bind("<ButtonRelease-1>", b1up)
    def do_every_second(n):
        global draw
        global drawing_area
        global imagedraw
        global image
        while len(draw)>0:
            # Update the whiteboard
            x = draw.pop(0)
            if len(x)==1:
                if x[0] == "clear":
                    # Clear whiteboard, if clear command found
                    drawing_area.delete("all")
                    image = Image.new("RGB", (root.winfo_screenwidth(), root.winfo_screenheight()), (255, 255, 255))
                    imagedraw = ImageDraw.Draw(image)
                    continue
            # Draw the line on whiteboard
            drawing_area.create_line(x[0], x[1], x[2], x[3],smooth=TRUE, width=x[4], fill=x[5])
            # Draw the line on image
            imagedraw.line([(float(x[0]), float(x[1])), (float(x[2]), float(x[3]))], fill=x[5], width=int(float(x[4])))
        n += 1
        # Loop every 10ms
        master.after(100, do_every_second, n)
    do_every_second(n)

'''
    Mouse button up or down
'''
def b1down(event):
    global b1
    b1 = "down"           # you only want to draw when the button is down
                          # because "Motion" events happen -all the time-

def b1up(event):
    global b1, xold, yold
    b1 = "up"
    xold = None           # reset the line when you let go of the button
    yold = None

'''
    Motion listener for the canvas
    Draws a line on the canvas, and also alerts the server
'''
def motion(event):
    if b1 == "down":
        global xold, yold
        canvas = event.widget
        xn = canvas.canvasx(event.x)
        yn = canvas.canvasy(event.y)
        if xold is not None and yold is not None:
            event.widget.create_line(xold,yold,xn,yn,smooth=TRUE, width=thickness.get(), fill=color)
                          # here's where you draw it. smooth. neat.
            global s
            imagedraw.line([(float(xold), float(yold)), (float(xn), float(yn))], width=int(thickness.get()), fill=color)
            h=root.winfo_screenheight()
            w=root.winfo_screenwidth()
            # Scaling down
            s.sendall(str(xold/w)+" "+str(yold/h)+" "+str(xn/w)+" "+str(yn/h)+" "+str(thickness.get())+" "+str(color)+'\n')
        xold = xn
        yold = yn


'''
    Read a single line from the socket
'''
def readline(sock, recv_buffer=1, delim='\n'):
	buffer = ''
	data = True
	while data:
		data = sock.recv(recv_buffer)
		buffer += data

		while buffer.find(delim) != -1:
			line, buffer = buffer.split('\n', 1)
			return line
	return ''

'''
    Recieves the data from the server and adds the line to draw queue
'''
def receive():
    global s
    global drawing_area
    global image
    global root
    try:
        while True:
            data = readline(s)
            # if ping, just ignore, to check if client is alive
            if (data == "Ping"):
                continue
            # clear message, add clear action to queue
            if (data == "clear"):
                draw.append(["clear"])
                continue
            global Scaleheight
            global Scalewidth
            h = Scaleheight
            w = Scalewidth
            xold, yold, eventx, eventy, thick, col = map(str, data.split())
            xold, yold, eventx, eventy, thick = map(float, [xold, yold, eventx, eventy, thick])
            thick = int(thick)
            draw.append([int(xold*w), int(yold*h), int(eventx*w), int(eventy*h), thick, col])
        pass
    except Exception, e:
        print "Connection to server lost\nExiting...", e
        s.close()
        root.destroy()
        sys.exit(0)

TCP_IP = "127.0.0.1"
TCP_IP = raw_input("Enter IP: ")
TCP_PORT = int(input("Enter port number: "))
key = raw_input("Enter id(default is 0): ")

b1 = "up"
xold, yold = None, None
root = Tk()
root.title("WhiteBoard")
frame = Frame(root, width=200,height=100)
frame.pack(expand=YES, fill=BOTH)

# Scrollbars for canvas
hScroll = Scrollbar(frame, orient=HORIZONTAL)
vScroll = Scrollbar(frame, orient=VERTICAL)
hScroll.pack(side=BOTTOM, fill=X)
vScroll.pack(side=RIGHT, fill=Y)

# canvas
drawing_area = Canvas(frame, width=root.winfo_screenwidth()-800, height=root.winfo_screenheight()-400, scrollregion=(0, 0, root.winfo_screenwidth(), root.winfo_screenheight()), yscrollcommand=vScroll.set, xscrollcommand=hScroll.set)
Scalewidth=root.winfo_screenwidth()
Scaleheight=root.winfo_screenheight()
hScroll['command'] = drawing_area.xview
vScroll['command'] = drawing_area.yview

# Canvas background
drawing_area.pack(fill=BOTH, expand=YES)
drawing_area["background"]="white"
draw = []

# Line thickness scale
thickness = DoubleVar()
w = Scale(root, from_=1, to=10, orient=HORIZONTAL, resolution=1.0, variable=thickness)
w.pack(padx=0, pady=00, side=BOTTOM)

n = 0
UpdateQueueLen = 300
UpdateQueue = [[] for _ in range(UpdateQueueLen)]
UpdateQueueIndex = 0

# Select color button
Button(text='Select Color', command=getColor).pack(padx=0, pady=00, side=RIGHT, expand=YES)

# clear screen button
Button(text='Clear screen', command=clear).pack(padx=0, pady=00, side=RIGHT, expand=YES)

# Save as Image button
image = Image.new("RGB", (root.winfo_screenwidth(), root.winfo_screenheight()), (255, 255, 255))
imagedraw = ImageDraw.Draw(image)
Button(root, text="Save as image", command=save_image).pack(padx=10, pady=00, side=BOTTOM)

BUFFER_SIZE = 1024
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect((TCP_IP, TCP_PORT))
s.sendall(str(key)+'\n')
data = readline(s)
print data
if (data[:7]!="SUCCESS"):
    exit(0)
thread.start_new_thread(receive, ())
root.configure(background='black')
if __name__ == "__main__":
    main(root)
    root.mainloop()