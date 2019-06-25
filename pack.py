#!/usr/bin/python3
#
#               Multimedia Package Toolkit
# Copyright (c) 2019 by Kamil Pawlowski <kamilpe@gmail.com>

from mediapack.write import MpkWriter
import argparse

parser = argparse.ArgumentParser(description='Multimedia Package system')
parser.add_argument('filename')
parser.add_argument("-c", "--compress", help="use zlib to compress data", action="store_true")
parser.add_argument("-s", "--silent", help="remain silent", action="store_false")
args = parser.parse_args()

writer = MpkWriter(args.compress, args.silent)
writer.pack('.', args.filename)
