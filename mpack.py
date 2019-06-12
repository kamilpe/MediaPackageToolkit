#!/usr/bin/python3
#
# Multimedia Package System
# Copyright (c) 2019 by Kamil Pawlowski <kamilpe@gmail.com>
#
# It is a tool to create integrated packaged files with multimedia data.
# Especially usefull for internet assets to easy convert for your game usage
#
# Example of usage:
# ./mpack.py myfile.json
#
# JSON file is used to provide meta data, like coordinates of origin, or sound file.
# You can also override the names without changing physical names
#
# MPK file format:
# ==============================================================
# 3 bytes                  - MPK
# 1 byte                   - 0x1 for compressed or 0x0 for uncompressed
# 2 bytes                  - Header size
# 2 bytes                  - Sprites count
# 2 bytes                  - Sounds count
# 2 bytes                  - Fonts count
# 4 bytes                  - Position of meta data
# 4 bytes*num of sprites   - Position of sprites in file
# 4 bytes*num of sounds    - Position of sounds in file
# 4 bytes*num of sounds    - Position of fonts in file
#
# --- gzip compression for the rest of the file ---
#
# X bytes                  - Mapping data, application layer
#
# Sprite format:
# ==============================================================
# 1 byte                   - Length of the name
# 1-255 bytes              - Name
# 2 bytes                  - Feature flags: 0x1 for alpha 0x3 for sound
# 2 bytes                  - Width
# 2 bytes                  - Heihgt
# 2 bytes                  - Origin X
# 2 bytes                  - Origin Y
# 2 bytes                  - Number of frames
# 1 byte                   - Frames per second
# 4 bytes * width * length * num of frames
#                          - RGBA of sprites
# extra bytes              - Only if has sound. Sound format after name section
#
# Sound format:
# ==============================================================
# 1 byte                   - Length of the name
# 1-255 bytes              - Name
# 1 byte                   - Resolution
# 2 bytes                  - Frequency
# 2 bytes                  - Length in miliseconds
# length*frequency*resolution
#                          - Samples
#
# Font format:
# ==============================================================
# todo

import os
import sys
import re
import io
import zlib
import tempfile
import json
import re
from PIL import Image

if (len(sys.argv) < 2):
    print("mpack.py filename [ds]")
    print("d - for uncompressed")
    print("s - for no progress")
    quit()

out_name = sys.argv[1]
params = '' if len(sys.argv) < 3 else sys.argv[2]
is_compression = (params.find('d') == -1)
is_silent = (params.find('s') != -1)
df = open(out_name, "wb")
df_temp = tempfile.TemporaryFile()

pre, ext = os.path.splitext(out_name)
with open( pre + ".json", 'r') as f:
    config = json.load(f)

def check_param(iname, pname):
    global config
    for pattern,content in config.items():
        p = re.compile(pattern)
        if (p.match(iname)):
            for p,value in content.items():
                if (p == pname):
                    return value
    return None


def read_sprites(source):
    sprites = {}
    for path,d,f in os.walk(source):
        exts = [".bmp", ".png", ".jpg"]
        for filename in f:
            splited = os.path.splitext(filename)
            name = splited[0]
            ext = splited[1].lower()
            if ext in exts:
                name = re.sub(r'\d*', '', name)
                fullFilePath = path + "/" + filename;
                if (name not in sprites):
                    sprites[name] = []
                sprites[name].append(fullFilePath)
    return sprites


def write_header(df, nsprites, nsounds, nfonts, is_compression):
    # signature
    df.write('MPK'.encode())
    df.write(is_compression.to_bytes(1, 'big'))

    # placeholder for header size
    placeholder = 0
    header_size_position = df.tell()
    df.write(placeholder.to_bytes(2, 'big'))

    # counters
    df.write(nsprites.to_bytes(2, 'big', signed=False))
    df.write(nsounds.to_bytes(2, 'big', signed=False))
    df.write(nfonts.to_bytes(2, 'big', signed=False))

    # indexes
    indexes = df.tell()
    df.write(placeholder.to_bytes(4, 'big', signed=False))
    for i in range(1, nsprites + nsounds + nfonts):
        df.write(placeholder.to_bytes(4, 'big', signed=False))

    # write header size
    header_size = df.tell()
    df.seek(header_size_position)
    df.write(header_size.to_bytes(2, 'big', signed=False))
    df.seek(header_size)

    return indexes, header_size


def write_indexes(df, header_size, indexes_position, sprite_indexes):
    df.seek(indexes_position)
    for index in sprite_indexes:
        index_with_offset = header_size + index
        df.write(index_with_offset.to_bytes(4, 'big', signed=False))


def compress_into(df, header_size, df_temp):
    df.seek(header_size)
    df_temp.seek(0)
    buf = df_temp.read();
    df.write(zlib.compress(buf,9))


def write_sprite_header(df_temp, name, imgfiles, img, alpha = True, sound = False):
    global sprite_offsets
    width, height = img.size

    ox = check_param(name, 'origin_x')
    if (ox is None): ox = int(width/2)
    oy = check_param(name, 'origin_y')
    if (oy is None): oy = height

    features = 0
    if (alpha): features = features | 0x1
    if (sound): features = features | 0x3
    frames = len(imgfiles)
    fps = 0

    df_temp.write(len(name).to_bytes(1, 'big', signed=False))
    df_temp.write(name[:255].encode())
    df_temp.write(features.to_bytes(2, 'big'))
    df_temp.write(width.to_bytes(2, 'big'))
    df_temp.write(height.to_bytes(2, 'big'))
    df_temp.write(ox.to_bytes(2, 'big'))
    df_temp.write(oy.to_bytes(2, 'big'))
    df_temp.write(frames.to_bytes(2, 'big'))
    df_temp.write(fps.to_bytes(1, 'big'))


def write_sprite_data_raw(df_temp, img):
    df_temp.write(img.tobytes())


def write_sprite_data_rgb_generated_a(df_temp, img):
    ra,ga,ba = img.getpixel((0,0))
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

    df_temp.write(imgbytes)

def write_sprites(df_temp, sprites):
    sprite_indexes = []

    t = 0
    for name,imgfiles in sprites.items():
        global is_silent
        if (not is_silent):
            t+=1
            percents = round(100.0 * t / float(len(sprites.items())), 1)
            sys.stdout.write('\rsprites conversion: %s%s' % (percents, '%'))
            sys.stdout.flush()

        img = Image.open(imgfiles[0])
        alpha = check_param(name, 'alpha')
        if (alpha is None): alpha = True if img.mode == 'RGBA' else False

        sprite_indexes.append(df_temp.tell())
        write_sprite_header(df_temp, name, imgfiles, img, alpha = alpha)

        for imgfile in imgfiles:
            img = Image.open(imgfile)
            if (alpha):
                if (img.mode == 'RGBA'):
                    write_sprite_data_rgba_raw(df_temp, img)
                elif (img.mode == 'RGB'):
                    write_sprite_data_rgb_generated_a(df_temp, img)
                else:
                    write_sprite_data_rgb_generated_a(df_temp, img.convert('RGB'))
            else:
                write_sprite_data_raw(df_temp, img.convert('RGB'))
    if (not is_silent): print('')
    return sprite_indexes


sprites = read_sprites(".")
indexes_position, header_size = write_header(df, len(sprites), 0, 0, is_compression)
sprite_indexes = write_sprites(df_temp, sprites)
assert len(sprites) == len(sprite_indexes)
write_indexes(df, header_size, indexes_position, sprite_indexes)

if (is_compression):
    if (not is_silent):
        print('compressing...')
    compress_into(df, header_size, df_temp)
else:
    df_temp.seek(0)
    df.write(df_temp.read())

print(out_name, 'completed')
