#!/usr/bin/python3
#
#               Multimedia Package System
# Copyright (c) 2019 by Kamil Pawlowski <kamilpe@gmail.com>

import sys
import time
import argparse
import pyaudio
import tkinter
from mediapack.read import MpkReader
from PIL import ImageTk

parser = argparse.ArgumentParser(description='Multimedia Package system')
parser.add_argument('filename')
parser.add_argument("--sprite", help="show sprite form the index", type=int)
parser.add_argument("--sound", help="play sound from the index", type=int)
args = parser.parse_args()

class Sound:
    def __init__(self,pack,index):
        self.pack = pack
        self.sound = self.pack.sounds[index]
        self.pack.print_sound(index)
        p = pyaudio.PyAudio
        stream = p.open(p, format=p.get_format_from_width(p, width = self.sound.sample),
                        channels=self.sound.channels,
                        rate=self.sound.channels,
                        output=True,
                        output_device_index=1)

        for i in range(0,self.sound.frame_count):
            start = i * self.sound.channels * self.sound.sample
            stop = start + self.sound_channel * self.sound_sample
            stream.write(self.sound.data[start:stop])

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


pack = MpkReader(args.filename)
if (args.sprite is not None):
    Animation(pack, args.sprite)
elif (args.sound is not None):
    Sound(pack, args.sound)
else:
    pack.printout()
