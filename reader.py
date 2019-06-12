#!/usr/bin/python3

class mpk:
    def __init__(self, filename):
        self.name = filename
        self.fd = open(filename, 'rb')
        if (not self.check_sign()): raise Exception("Wrong signature")
        self.read_header()
        self.printout()

    def check_sign(self):
        signature = self.fd.read(3)
        if (signature == 'MPK'.encode()): return True
        return False

    def read_header(self):
        self.is_compressed = bool(self.fd.read(1))
        self.header_size = int.from_bytes(self.fd.read(2), 'big')
        self.sprites_count = int.from_bytes(self.fd.read(2), 'big')
        self.sounds_count = int.from_bytes(self.fd.read(2), 'big')
        self.fonts_count = int.from_bytes(self.fd.read(2), 'big')
        self.meta_position = int.from_bytes(self.fd.read(4), 'big')
        self.sprite_indexes = self.read_indexes(self.sprites_count)
        self.sound_indexes = self.read_indexes(self.sounds_count)
        self.font_indexes = self.read_indexes(self.fonts_count)

    def read_indexes(self, count):
        indexes = []
        for i in range(1, count):
            indexes.append(int.from_bytes(self.fd.read(4), 'big'))
        return indexes

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
        print ('Header ends at:', self.fd.tell())

    def print_indexes(self, name, indexes, count):
        print (name+':', count)
        for i in range(0, count-1):
            print (str(i+1)+':',indexes[i], end=' ')
        if (count > 0):
            print('')
