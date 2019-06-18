#!/usr/bin/python3
#
#               Multimedia Package System
# Copyright (c) 2019 by Kamil Pawlowski <kamilpe@gmail.com>

from mediapack.write import MpkWriter

writer = MpkWriter(compression=False)
writer.pack('/Users/kamil/projects/samples/T_queen', 'test.mpk')
