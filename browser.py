#!/usr/bin/python3

import reader
import sys

if (len(sys.argv) < 2):
    print("Provide a file")
    exit()

pack = reader.mpk(sys.argv[1])

def play_sprite(ind):
    pack.sprites[ind].frames[0].show()

if (len(sys.argv) > 4):
    if (sys.argv[2] == 'play'):
        if (sys.argv[3] == 'sprite'):
            play_sprite(int(sys.argv[4]))
else:
    pack.printout()
