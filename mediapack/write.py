#!/usr/bin/python3
#
#               Multimedia Package Toolkit
# Copyright (c) 2019 by Kamil Pawlowski <kamilpe@gmail.com>

import os
import sys
import re
import zlib
import tempfile
import json
import wave
from PIL import Image

def write_bytes(fd, data, size, s=False):
    fd.write(data.to_bytes(size, 'big', signed=s))

def write_str(fd, data, with_size=True):
    if (with_size):
        write_bytes(fd, len(data), 1)
    fd.write(data.encode())


class MpkWriter:
    def __init__(self, compression=True, progressbar=True):
        self.compression = compression
        self.progressbar = progressbar
        self.sprite_indexes = []
        self.sound_indexes = []
        self.font_indexes = []

    def pack(self, src_path, dst_filepath):
        # prepare
        self.src_path = src_path
        self.dst_filepath = dst_filepath
        self.dst_file = open(self.dst_filepath, "wb")
        self.data_file = tempfile.TemporaryFile()

        # action
        self.prepare_config()
        self.list_files()
        self.write_header()
        self.write_meta()
        self.write_sprites()
        self.write_sounds()
        self.write_indexes()
        self.compress_or_copy_data_file()

    def prepare_config(self):
        pre, ext = os.path.splitext(self.dst_filepath)
        json_file = pre + ".json"
        self.config = {}
        if (os.path.exists(json_file)):
            if (self.progressbar): print("found config:",json_file)
            with open(json_file, 'r') as f:
                self.config = json.load(f)

    def check_param(self,object_name, param_name, default):
        for pattern, content in self.config.items():
            p = re.compile(pattern)
            if (p.match(object_name)):
                for p, value in content.items():
                    if (p == param_name):
                        return value
        return default

    def list_files(self): # TODO: move outside of this
        self.sprites = {}
        self.sounds = {}
        self.fonts = {}
        sprite_exts = [".bmp", ".png", ".jpg"]
        wave_exts = [".wav"]

        for path, d, f in os.walk(self.src_path):
            for filename in f:
                splited = os.path.splitext(filename)
                name = splited[0]
                ext = splited[1].lower()
                fullFilePath = path + "/" + filename
                if ext in sprite_exts:
                    index = re.sub(r'\D','',name)
                    name = path.replace('./','') + "/" + re.sub(r'\d', '', name)
                    if (name not in self.sprites): self.sprites[name] = {}
                    self.sprites[name][index] = fullFilePath
                elif ext in wave_exts:
                    self.sounds[name] = fullFilePath

    def write_header(self):
        # signature
        write_str(self.dst_file, 'MPK', with_size=False)
        write_bytes(self.dst_file, self.compression, 1)

        # placeholder for header size
        placeholder = 0
        self.header_size_position = self.dst_file.tell()
        write_bytes(self.dst_file, placeholder, 2)

        # counters
        write_bytes(self.dst_file, len(self.sprites), 2)
        write_bytes(self.dst_file, len(self.sounds), 2)
        write_bytes(self.dst_file, len(self.fonts), 2)

        # indexes
        self.indexes_position = self.dst_file.tell()
        write_bytes(self.dst_file, placeholder, 4) # position of meta
        for i in range(0, len(self.sprites) + len(self.sounds) + len(self.fonts)):
            write_bytes(self.dst_file, placeholder, 4)

        # write header size
        self.header_size = self.dst_file.tell()
        self.dst_file.seek(self.header_size_position)
        write_bytes(self.dst_file, self.header_size, 2)
        self.dst_file.seek(self.header_size)

    def write_indexes(self):
        self.dst_file.seek(self.indexes_position)
        write_bytes(self.dst_file, self.header_size, 4) # meta index
        for index in self.sprite_indexes:
            write_bytes(self.dst_file, self.header_size + index, 4)
        for index in self.sound_indexes:
            write_bytes(self.dst_file, self.header_size + index, 4)

    def write_meta(self):
        write_bytes(self.data_file, 0, 4) # meta size

    def show_progress(self, title, index, count):
        percents = round(100.0 * index / float(count), 1)
        sys.stdout.write('\r%s %s%s' % (title, percents, '%'))
        sys.stdout.flush()

    def write_sprites(self):
        index = 0
        for name,imgfiles in self.sprites.items():
            if (self.progressbar):
                index+=1
                self.show_progress("sprites conversion:", index, len(self.sprites.items()))

            img = Image.open(next(iter(imgfiles.values())))

            alpha = self.check_param(name, 'alpha', True if img.mode == 'RGBA' else False)
            self.write_sprite_header(name, imgfiles, img, alpha = alpha)

            for key in sorted(imgfiles.keys()):
                imgfile = imgfiles[key]
                img = Image.open(imgfile)
                if (alpha):
                    if (img.mode == 'RGBA'):
                        self.write_sprite_data_rgba_raw(img)
                    elif (img.mode == 'RGB'):
                        self.write_sprite_data_rgb_generated_a(name, img)
                    else:
                        self.write_sprite_data_rgb_generated_a(name, img.convert('RGB'))
                else:
                    self.write_sprite_data_raw(img.convert('RGB'))
        if (self.progressbar and len(self.sprites)>0): print('')

    def write_sprite_header(self, name, imgfiles, img, alpha):
        self.sprite_indexes.append(self.data_file.tell())

        width, height = img.size
        frames = len(imgfiles)
        features = 0
        if (alpha): features = features | 0b001
        if (self.check_param(name,'loop',True)): features = features | 0b010
        ox = self.check_param(name, 'origin_x', int(width/2))
        oy = self.check_param(name, 'origin_y', height)
        fps = self.check_param(name, 'fps', 5 if len(imgfiles)>1 else 0)

        write_str(self.data_file, name)
        write_bytes(self.data_file, features, 2)
        write_bytes(self.data_file, width, 2)
        write_bytes(self.data_file, height, 2)
        write_bytes(self.data_file, ox, 2)
        write_bytes(self.data_file, oy, 2)
        write_bytes(self.data_file, frames, 2)
        write_bytes(self.data_file, fps, 1)

    def write_sprite_data_rgb_generated_a(self, name, img):
        ra,ga,ba = img.getpixel((0,0))
        ra = self.check_param(name, 'alpha_r', ra)
        ga = self.check_param(name, 'alpha_g', ga)
        ba = self.check_param(name, 'alpha_b', ba)

        imgbytes = bytearray(img.convert('RGBA').tobytes())

        for i in range(0,len(imgbytes),4):
            r = imgbytes[i]
            g = imgbytes[i+1]
            b = imgbytes[i+2]
            if (r == ra and g == ga and b == ba):
                imgbytes[i] = 0
                imgbytes[i+1] = 0
                imgbytes[i+2] = 0
                imgbytes[i+3] = 0

        self.data_file.write(imgbytes)

    def write_sprite_data_raw(self, img):
        self.data_file.write(img.tobytes())

    def write_sounds(self):
        index = 0
        for name,wave_file in self.sounds.items():
            if (self.progressbar):
                index+=1
                self.show_progress("wave conversion:", index, len(self.sounds.items()))

            wave_data = wave.open(wave_file, 'rb')
            self.sound_indexes.append(self.data_file.tell())
            write_str(self.data_file, name)
            write_bytes(self.data_file, wave_data.getnchannels(), 1)
            write_bytes(self.data_file, wave_data.getsampwidth(), 1)
            write_bytes(self.data_file, wave_data.getframerate(), 2)
            write_bytes(self.data_file, wave_data.getnframes(), 4)
            self.data_file.write(wave_data.readframes(wave_data.getnframes()))

        if (self.progressbar and len(self.sounds)>0): print('')

    def compress_or_copy_data_file(self):
        self.data_file.seek(0)
        self.dst_file.seek(self.header_size)
        if (self.compression):
            if (self.progressbar): print('compressing the', self.dst_filepath)
            self.dst_file.write(zlib.compress(self.data_file.read(),9))
        else:
            self.dst_file.write(self.data_file.read())
