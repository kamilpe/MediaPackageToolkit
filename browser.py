#!/usr/bin/python3

import reader
import sys
import tkinter
import time
from PIL import ImageTk

if (len(sys.argv) < 2):
    print("Provide a file")
    exit()

class Animation:
    def __init__(self,pack,index):
        self.root = tkinter.Tk()
        self.pack = pack
        self.setup_sprite(index)
        self.tk_frame = tkinter.Frame(self.root)
        self.tk_frame.bind('<Left>', self.left)
        self.tk_frame.bind('<Right>', self.right)
        self.tk_frame.bind('<Escape>', self.tk_quit)
        self.tk_frame.pack()
        self.panel = tkinter.Label(self.tk_frame, image = self.frames[0])
        self.panel.pack(side='bottom',fill='both',expand='yes')
        self.tk_frame.focus_set()
        self.direction = 1
        self.change_image()
        self.center()
        self.root.mainloop()

    def setup_sprite(self, index):
        self.pack.print_sprite(index)
        self.index = index
        self.cur = 0
        self.fps =  self.pack.sprites[self.index].fps
        self.frames = []
        for frame in self.pack.sprites[self.index].frames:
            self.frames.append(ImageTk.PhotoImage(frame))

    def tk_quit(self, event):
        self.root.quit()

    def left(self, event):
        if (self.index > 0):
            self.setup_sprite(self.index-1)

    def right(self, event):
        if (self.index < len(pack.sprites)-1):
            self.setup_sprite(self.index+1)

    def change_image(self):
        self.panel.config(image = self.frames[self.cur])
        if (len(self.frames)==1):
            return
        self.cur+=1

        if (self.cur >= len(self.frames)):
            self.cur=0
            if ('loop' not in self.pack.sprites[self.index].features):
                self.root.after(int(2000), self.change_image)
                return

        self.root.after(int(1000/self.fps), self.change_image)

    def center(self):
        windowWidth = self.root.winfo_reqwidth()
        windowHeight = self.root.winfo_reqheight()
        positionRight = int(self.root.winfo_screenwidth()/2 - windowWidth/2)
        positionDown = int(self.root.winfo_screenheight()/2 - windowHeight/2)
        self.root.geometry("+{}+{}".format(positionRight, positionDown))


pack = reader.mpk(sys.argv[1])
if (len(sys.argv) > 2):
    if (len(sys.argv) > 3 and sys.argv[2] == 'sprite'):
        Animation(pack, int(sys.argv[3]))
    elif (len(pack.sprites) > 0):
        Animation(pack, 0)

else:
    pack.printout()
