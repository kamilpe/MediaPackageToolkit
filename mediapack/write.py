#!/usr/bin/python3
#
#               Multimedia Package System
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
        self.write_sprites()
        self.compress_or_copy_data_file()

    def prepare_config(self):
        pre, ext = os.path.splitext(self.dst_filepath)
        json_file = pre + ".json"
        self.config = {}
        if (os.path.exists(json_file)):
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
                index = re.sub(r'\D','',name)
                name = path.replace('./','') + "/" + re.sub(r'\d', '', name)
                fullFilePath = path + "/" + filename
                if ext in sprite_exts:
                    if (name not in self.sprites):
                        self.sprites[name] = {}
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

    def write_sprites(self):
        self.sprite_indexes = []

        index = 0
        for name,imgfiles in self.sprites.items():
            if (self.progressbar):
                index+=1
                percents = round(100.0 * index / float(len(self.sprites.items())), 1)
                sys.stdout.write('\rsprites conversion: %s%s' % (percents, '%'))
                sys.stdout.flush()

            self.sprite_indexes.append(self.data_file.tell())
            img = Image.open(next(iter(imgfiles.values())))
            alpha = self.check_param(name, 'alpha', True if img.mode == 'RGBA' else False)
            self.write_sprite_header(name, imgfiles, img, alpha = alpha, sound = False)

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
        print('')

    def write_sprite_header(self, name, imgfiles, img, alpha, sound):
        width, height = img.size
        frames = len(imgfiles)

        features = 0
        if (alpha): features = features | 0b001
        if (sound): features = features | 0b010
        if (self.check_param(name,'loop',True)): features = features | 0b100
        ox = self.check_param(name, 'origin_x', int(width/2))
        oy = self.check_param(name, 'origin_y', height)
        fps = self.check_param(name, 'fps', 5 if len(imgfiles)>0 else 0)

        write_str(self.data_file, name)
        write_bytes(self.data_file, features, 2)
        write_bytes(self.data_file, width, 2)
        write_bytes(self.data_file, height, 2)
        write_bytes(self.data_file, ox, 2)
        write_bytes(self.data_file, oy, 2)
        write_bytes(self.data_file, frames, 2)
        write_bytes(self.data_file, fps, 1)

    def write_sprite_data_raw(self, img):
        self.data_file.write(img.tobytes())


    def write_sprite_data_rgb_generated_a(self, name, img):
        ra,ga,ba = img.getpixel((0,0))
        ra = check_param(name, 'alpha_r', ra)
        ga = check_param(name, 'alpha_g', ga)
        ba = check_param(name, 'alpha_b', ba)

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

    def compress_or_copy_data_file(self):
        self.data_file.seek(0)
        self.dst_file.seek(self.header_size)
        if (self.compression):
            print('compressing the', self.dst_filepath)
            self.dst_file.write(zlib.compress(self.data_file.read(),9))
        else:
            self.dst_file.write(self.data_file.read())
