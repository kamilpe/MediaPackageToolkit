#!/usr/bin/python3

import reader
import sys

if (len(sys.argv) < 2):
    print("Provide a file")
    exit()

data = reader.mpk(sys.argv[1])
