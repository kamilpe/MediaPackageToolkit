#!/usr/bin/python3

import zlib
import tempfile
from PIL import Image

def read_bytes_bool(fd):
    return bool.from_bytes(fd.read(1), 'big')

def read_bytes_int(fd, size, s=False):
    return int.from_bytes(fd.read(size), 'big', signed=s)

def read_bytes_str(fd, size):
    return fd.read(size).decode()

def decode_features(fbits):
    features = []
    if (fbits & 0b01): features.append('alpha')
    if (fbits & 0b10): features.append('sound')
    return features

class sprite:
    def __init__(self, datafd):
        name_len = read_bytes_int(datafd, 1)
        self.name = read_bytes_str(datafd, name_len)
        self.features = decode_features(read_bytes_int(datafd, 2))
        self.width = read_bytes_int(datafd, 2)
        self.height = read_bytes_int(datafd, 2)
        self.origin_x = read_bytes_int(datafd, 2)
        self.origin_y = read_bytes_int(datafd, 2)
        self.frames_count = read_bytes_int(datafd, 2)
        self.fps = read_bytes_int(datafd, 1)

        self.frames = []
        for i in range(0,self.frames_count):
            if ('alpha' in self.features):
                mode = 'RGBA'
                pixel_size = 4
            else:
                mode = 'RGB'
                pixel_size = 3

            data = datafd.read(self.width*self.height*pixel_size)
            self.frames.append(Image.frombytes(mode,(self.width,self.height),data))

class mpk:
    def __init__(self, filename):
        self.name = filename
        self.fd = open(filename, 'rb')
        if (not self.check_sign()): raise Exception("Wrong signature")
        self.read_header()
        self.unpack()

        self.sprites = []
        while (True):
            if not self.read_next_data():
                break;

        print('loading ok')

    def check_sign(self):
        signature = self.fd.read(3)
        if (signature == 'MPK'.encode()): return True
        return False

    def read_header(self):
        self.is_compressed = read_bytes_bool(self.fd)
        self.header_size = read_bytes_int(self.fd, 2)
        self.sprites_count = read_bytes_int(self.fd, 2)
        self.sounds_count = read_bytes_int(self.fd, 2)
        self.fonts_count = read_bytes_int(self.fd, 2)
        self.meta_position = read_bytes_int(self.fd, 4)
        self.sprite_indexes = self.read_indexes(self.sprites_count)
        self.sound_indexes = self.read_indexes(self.sounds_count)
        self.font_indexes = self.read_indexes(self.fonts_count)

    def read_indexes(self, count):
        indexes = []
        for i in range(0, count):
            indexes.append(read_bytes_int(self.fd, 4))
        return indexes

    def unpack(self):
        #self.datafd = tempfile.TemporaryFile()
        self.datafd = open('temp.tmp','w+b')
        if (self.is_compressed):
            print('decompressing...')
            self.datafd.write(zlib.decompress(self.fd.read()))
        else:
            self.datafd.write(self.fd.read())
        self.datafd.seek(0)

    def read_next_data(self):
        position = self.datafd.tell() + self.header_size
        if position in self.sprite_indexes:
            self.sprites.append(sprite(self.datafd))
            return True
        elif position in self.sound_indexes:
            self.read_sound()
            return True
        elif position in self.font_indexes:
            self.read_font()
            return True
        elif position == self.meta_position:
            self.read_meta()
            return True
        return False


    def read_sound(self):
        print('found sound')

    def read_font(self):
        print('found font')

    def read_meta(self):
        size = read_bytes_int(self.datafd, 4)
        self.meta = self.datafd.read(size)

    def printout(self):
        print ('MPK file:', self.name)
        print ('')
        print ('Header dump:')
        print ('------------------------------------------------------------------')
        print ('Header size:', self.header_size)
        print ('Compression:', ('yes' if self.is_compressed else 'no'))
        print ('Meta position:', self.meta_position)
        self.print_indexes('Sprites', self.sprite_indexes, self.sprites_count)
        self.print_indexes('Sounds', self.sound_indexes, self.sounds_count)
        self.print_indexes('Fonts', self.font_indexes, self.fonts_count)
        print ('')
        print ('Sprites:')
        print ('------------------------------------------------------------------')
        i = 0
        for s in self.sprites:
            i+=1
            print(i, ': "'+s.name+'" -- width:', s.width, 'height:', s.height,
                  'origin x:', s.origin_x, 'origin_y:',s.origin_y,
                  'frames:', s.frames_count, 'fps:', s.fps,
                  'features:', s.features)

    def print_indexes(self, name, indexes, count):
        print (name+':', count)
        for i in range(0, count):
            print (str(i+1)+':',indexes[i], end=' ')
        if (count > 0):
            print('')
