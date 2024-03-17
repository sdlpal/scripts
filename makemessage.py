#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import with_statement

import argparse
import os
import traceback
import struct
import sys
import binascii
import re

def crc32(buf):
    return hex(binascii.crc32(buf) & 0xFFFFFFFF)
    
def get_msg(msg_bytes,index_bytes,p,encoding):
    msg_begin, msg_end = struct.unpack("<II",index_bytes[p * 4 : (p + 2) * 4])
    msg =  msg_bytes[msg_begin : msg_end].decode(encoding, 'replace')
    if not sys.version_info.major >= 3:
        msg = msg.encode('utf-8')
    return msg

def main():

    parser = argparse.ArgumentParser(description = 'Generate a translatable language file that can be used by SDLPAL.')
    parser.add_argument('gamepath', help = 'Game path where SSS.MKF & M.MSG & WORD.DAT are located.')
    parser.add_argument('outputfile', help = 'Path of the output message file.')
    parser.add_argument('encoding', choices = ['gbk', 'big5'], help = 'Text encoding name, should be either gbk or big5.')
    parser.add_argument('-w', '--width', dest = 'wordwidth', default = 10, type = int, help = 'Word width in bytes, default is 10')
    parser.add_argument("-c", "--comment", action = 'store_true', help = 'Automatically generate comments')
    parser.add_argument("-d", "--description", action = 'store_true', help = 'Generate description section from desc.dat for DOS version.')
    parser.add_argument("--compact", dest='is_compact', action='store_true', default=False, help = 'Generate SLF that works with index-compacted resources.')
    options = parser.parse_args()

    if options.gamepath[-1] != '/' and options.gamepath[-1] != '\\':
        options.gamepath += '/'

    script_bytes = []
    index_bytes = []
    msg_bytes = []
    word_bytes = []
    description_bytes = []
    sss_bytes = []

    is_msg_group = 0    #是否正在处理文字组的标示。
    msg_count = 0
    last_index = -1
    continue_msgs = 0
    temp = ""
    comment = ""
    message = ""

    version = "2024.03"
    slf_version = "3.1"

    cmd_extstr = ""

    if options.comment: cmd_extstr += "-c"
    if options.description: cmd_extstr += " -d"

    output = "# SDLPAL localization file\n"
    output += "# Version %s\n" % (slf_version)
    output += "# This document is generated with MakeMessage Utility ver. %s\n" % (version)
    output += "# Please visit https://github.com/sdlpal/sdlpal/ for more information.\n\n"
	
    output += "# Command line: makemessage.py PATH/TO/THE/GAME/DIRECTORY/ PATH/OF/THE/GENERATED/FILE %s -w %d %s\n\n" % (options.encoding, options.wordwidth, cmd_extstr)
	
    for file_ in os.listdir(options.gamepath):
        if file_.lower() == 'sss.mkf':
            try:
                with open(options.gamepath + file_, 'rb') as f:
                    f.seek(12, os.SEEK_SET)
                    offset_begin, script_begin, file_end = struct.unpack('<III', f.read(12))
                    f.seek(offset_begin, os.SEEK_SET)
                    index_bytes = f.read(script_begin - offset_begin)
                    script_bytes = f.read(file_end - script_begin)

                    f.seek(0, os.SEEK_SET)
                    sss_bytes = f.read()
            except:
                traceback.print_exc()
                return
        elif file_.lower() == 'm.msg':
            try:
                with open(options.gamepath + file_, 'rb') as f:
                    msg_bytes = f.read()
            except:
                traceback.print_exc()
                return
        elif file_.lower() == 'word.dat':
            try:
                with open(options.gamepath + file_, 'rb') as f:
                    data_bytes=f.read()
            except:
                traceback.print_exc()
                return
        elif file_.lower() == 'desc.dat':
            try:
                with open(options.gamepath + file_, 'rb') as f:
                    description_bytes=f.read()
            except:
                traceback.print_exc()
                return

    output += "# CRC32 of the resource files:\n"
    output += "# SSS.MKF:  %s\n" % (crc32(sss_bytes))
    output += "# M.MSG:    %s\n" % (crc32(msg_bytes))
    output += "# WORD.DAT: %s\n" % (crc32(data_bytes))
    if options.description and description_bytes != []: output += "# DESC.DAT: %s" % (crc32(description_bytes))
    output += "\n"
	
    if len(data_bytes) % options.wordwidth != 0:
        data_bytes += [0x20 for i in range(0, options.wordwidth - len(data_bytes) % options.wordwidth)]

    output += "# All lines, except those inside [BEIGN MESSAGE] and [END MESSAGE], can be commented by adding the sharp '#' mark at the first of the line.\n\n"

    output += "# This section contains the information that will be displayed when a user finishes the game.\n"
    output += "# Only the keys listed here are valid. Other keys will be ignored.\n"
    output += "[BEGIN CREDITS]\n"
    output += "# Place the translated text of 'Classical special build' here in no more than 24 half-wide characters.\n"
    output += "1= Classical special build\n"
    output += "# Place the translated porting information template at the following two lines. Be aware that each replaced line will be truncated into at most 40 half-wide characters.\n"
    output += "6= ${platform} port by ${author}, ${year}.\n"
    output += "7=\n"
    output += "# Place the translated GNU licensing information at the following three lines. Be aware that each line will be truncated into at most 40 half-wide characters.\n"
    output += "8=   This is a free software and it is\n"
    output += "9=   published under GNU General Public\n"
    output += "10=    License v3.\n"
    output += "# Place the translated text at the following line. Be aware that each line will be truncated into at most 40 half-wide characters.\n"
    output += "11=    ...Press Enter to continue\n"
    output += "[END CREDITS]\n\n"

    output += "# Each line controls one position value.\n"
    output += "# For each line, the format is 'idx=x,y,flag', while the flag is optional\n"
    output += "# If bit 0 of flag is 1, then use 8x8 font; and while bit 1 of flag is 1, then disable shadow\n"
    output += "# Lines from 1 to 26 are for equipping screen, lines from 27 to 80 are for status screen.\n"
    output += "[BEGIN LAYOUT]\n"
    output += "# 1 is the position of image box in equipping screen\n"
    output += "1=8,8\n"
    output += "# 2 is the position of role list box in equipping screen\n"
    output += "2=2,95\n"
    output += "# 3 is the position of current equipment's name in equipping screen\n"
    output += "3=5,70\n"
    output += "# 4 is the position of current equipment's amount in equipping screen\n"
    output += "4=51,57\n"
    output += "# 5 .. 10 are the positions of words 600 ... 605 in equipping screen\n"
    output += "5=92,11\n"
    output += "6=92,33\n"
    output += "7=92,55\n"
    output += "8=92,77\n"
    output += "9=92,99\n"
    output += "10=92,121\n"
    output += "# 11 .. 16 are the positions of equipped equipments in equipping screen\n"
    output += "11=130,11\n"
    output += "12=130,33\n"
    output += "13=130,55\n"
    output += "14=130,77\n"
    output += "15=130,99\n"
    output += "16=130,121\n"
    output += "# 17 .. 21 are the positions of words 51 ... 55 in equipping screen\n"
    output += "17=226,10\n"
    output += "18=226,32\n"
    output += "19=226,54\n"
    output += "20=226,76\n"
    output += "21=226,98\n"
    output += "# 22 .. 26 are the positions of status values in equipping screen\n"
    output += "22=260,14\n"
    output += "23=260,36\n"
    output += "24=260,58\n"
    output += "25=260,80\n"
    output += "26=260,102\n"
    output += "# 27 is the position of role name in status screen\n"
    output += "27=110,8\n"
    output += "# 28 is the position of role image in status screen\n"
    output += "28=110,30\n"
    output += "# 29 is the position of EXP label in status screen\n"
    output += "29=6,6\n"
    output += "# 30 is the position of LEVEL label in status screen\n"
    output += "30=6,32\n"
    output += "# 31 is the position of HP label in status screen\n"
    output += "31=6,54\n"
    output += "# 32 is the position of MP label in status screen\n"
    output += "32=6,76\n"
    output += "# 33 .. 37 are the positions of words 51 ... 55 in equipping screen\n"
    output += "33=6,98\n"
    output += "34=6,118\n"
    output += "35=6,138\n"
    output += "36=6,158\n"
    output += "37=6,178\n"
    output += "# 38 is the position of current EXP in status screen\n"
    output += "38=58,6\n"
    output += "# 39 is the position of required EXP to level up in status screen\n"
    output += "39=58,15\n"
    output += "# 40 is the position of slash between EXPs in status screen, if set to (0,0), then do not show the slash\n"
    output += "40=0,0\n"
    output += "# 41 is the position of LEVEL in status screen\n"
    output += "41=54,35\n"
    output += "# 42 is the position of current HP in status screen\n"
    output += "42=42,56\n"
    output += "# 43 is the position of max HP in status screen\n"
    output += "43=63,61\n"
    output += "# 44 is the position of slash between cur & max HPs in status screen, if set to (0,0), then do not show the slash\n"
    output += "44=65,58\n"
    output += "# 45 is the position of current MP in status screen\n"
    output += "45=42,78\n"
    output += "# 46 is the position of max MP in status screen\n"
    output += "46=63,83\n"
    output += "# 47 is the position of slash between cur & max MPs in status screen, if set to (0,0), then do not show the slash\n"
    output += "47=65,80\n"
    output += "# 48 .. 52 are the positions of status values in status screen\n"
    output += "48=42,102\n"
    output += "49=42,122\n"
    output += "50=42,142\n"
    output += "51=42,162\n"
    output += "52=42,182\n"
    output += "# 53 .. 58 are the positions of image boxes for equipped equipments in status screen\n"
    output += "53=189,-1\n"
    output += "54=247,39\n"
    output += "55=251,101\n"
    output += "56=201,133\n"
    output += "57=141,141\n"
    output += "58=81,125\n"
    output += "# 59 .. 64 are the positions of names for equipped equipments in status screen\n"
    output += "59=195,38\n"
    output += "60=253,78\n"
    output += "61=257,140\n"
    output += "62=207,172\n"
    output += "63=147,180\n"
    output += "64=87,164\n"
    output += "# 65 .. 80 are the positions of poison names in status screen, note that currently there are no more than 8 poisons can be simulatenously displayed\n"
    output += "65=185,58\n"
    output += "66=185,76\n"
    output += "67=185,94\n"
    output += "68=185,112\n"
    output += "69=185,130\n"
    output += "70=185,148\n"
    output += "71=185,166\n"
    output += "72=185,184\n"
    output += "73=185,184\n"
    output += "74=185,184\n"
    output += "75=185,184\n"
    output += "76=185,184\n"
    output += "77=185,184\n"
    output += "78=185,184\n"
    output += "79=185,184\n"
    output += "80=185,184\n"
    output += "# 81 .. 82 are extra description lines in the item (81) & magic (82) menu, where the first value specifies the lines and the second value should be zero.\n"
    output += "81=2,0\n"
    output += "82=1,0\n"
    output += "# 83 .. 87 customize the layout of MP information and description message in the magic menu.\n"
    output += "# 83 customizes the width of the MP column with its first value. The default value is 5. Use 3 for a narrower one. The second value should be zero.\n"
    output += "83=5,0\n"
    output += "# 84 .. 86 are the coordinates of the slash mark, required MP and current player MP.\n"
    output += "84=45,14\n"
    output += "85=15,14\n"
    output += "86=50,14\n"
    output += "# 87 customizes the X coordinate of the description message with its first value and the second value should be zero.\n"
    output += "87=102,0\n"
    output += "[END LAYOUT]\n\n"

    output += "# This section contains the words used by the game.\n"
    output += "[BEGIN WORDS]\n"
    output += "# Each line is a pattern of 'key=value', where key is an integer and value is a string.\n"

    for i in range(0, len(data_bytes) // options.wordwidth):
        if sys.version_info.major >= 3:
            temp = data_bytes[i * options.wordwidth: (i + 1) * options.wordwidth].rstrip(str.encode('\x20\x00')).decode(options.encoding)
        else:
            temp = data_bytes[i * options.wordwidth: (i + 1) * options.wordwidth].rstrip('\x20\x00').decode(options.encoding).encode('utf-8')
        if options.comment: output += "# Original word: %d=%s\n" % (i, temp)
        output += "%d=%s\n" % (i, temp)
    output += "# 600 .. 605 are extra description lines in the equipments menu: Headgear, Body Gear, Clothing, Weapon, Footwear, Accessory.\n"
    output += "600=頭戴\n"
    output += "601=披掛\n"
    output += "602=身穿\n"
    output += "603=手持\n"
    output += "604=脚穿\n"
    output += "605=佩帶\n"
    output += "# The following six words are for ATB only: Battle Speed, 1, 2, 3, 4, 5. They are not used in classical mode.\n"
    if options.encoding == "gbk":
        output += "606=战斗速度\n"
    else:
        output += "606=戰鬥速度\n"
    output += "# The following five words are for ATB battle speed. It is not used in classical mode.\n"
    output += "607=1\n"
    output += "608=2\n"
    output += "609=3\n"
    output += "610=4\n"
    output += "611=5\n"
    output += "# The following word is used to ask user whether to launch setting interface on next game start.\n"
    if options.encoding == "gbk":
        output += "612=返回设定\n"
    else:
        output += "612=返回設定\n"
    output += "[END WORDS]\n\n"

    output += "# The following sections contain dialog/description texts used by the game.\n\n"

    if sys.version_info.major >= 3:
        print ("MakeMessage Utility by SDLPal Team ver. %s" % (version))
        print ("Python 3 adaption by PalAlexx, OPL3ChipFan and Palxex")
        print ("Now Processing. Please wait...")
    else:
        print ("MakeMessage Utility by SDLPal Team ver. %s" % (version))
        print ("Python 3 adaption by PalAlexx, OPL3ChipFan and Palxex")
        print ("Running in Python 2 compatibility mode. Python 3 is recommended.")
        print ("Now Processing. Please wait...")

    for i in range(0, len(script_bytes) // 8):
        op, w1, w2, w3 = struct.unpack('<HHHH', script_bytes[i * 8 : (i + 1) * 8])
        if op == 0xFFFF:
            msg = get_msg(msg_bytes, index_bytes, w1, options.encoding)
            if is_msg_group == 1 and (last_index + 1 != w1 or (options.is_compact and continue_msgs == 1 and (get_msg(msg_bytes, index_bytes, last_index, options.encoding).endswith('：') or get_msg(msg_bytes, index_bytes, last_index, options.encoding).endswith(':')))):
                is_msg_group = 0
                temp = "%s %d\n\n" % ('[END MESSAGE]', last_index)
                message += temp
                output += comment + message

            if is_msg_group == 0:
                is_msg_group = 1
                message = "%s %d\n" % ('[BEGIN MESSAGE]', w1)
                if options.comment: comment = "# Original message: %d\n" % w1
                continue_msgs = 0

            last_index = w1
            msg_count += 1
            continue_msgs += 1

            try:
                temp = "%s\n" % (msg)
                message += temp
                if options.comment: comment += "# " + temp
            except:
                traceback.print_exc()

        elif op == 0x008E:

            if is_msg_group == 1:
                temp = "%s\n" % ('[CLEAR MESSAGE]')
                message += temp
                if options.comment: comment += "# " + temp

        else:
            if is_msg_group == 1:
                is_msg_group = 0
                temp = "%s %d\n\n" % ('[END MESSAGE]', last_index)
                message += temp
                output += comment + message

    if options.description and description_bytes != []:
        output += "%s\n" % ('[BEGIN DESCRIPTION]')
        descriptions = description_bytes.decode(options.encoding, 'replace')
        lines = descriptions.splitlines()
        processed_lines=[re.sub("[\(].*[\)]", "", line) if "=" in line else "#"+line for line in lines]
        processed_str="\n".join(processed_lines)
        if sys.version_info.major >= 3:
            output += "%s\n" % processed_str
        else:
            output += "%s\n" % processed_str.encode('utf-8')
        output += "%s\n" % ('[END DESCRIPTION]')
    else:
        if options.description: output += "%s\n" % ('# No DESCRIPTION section in this document.')
        if options.description: print ("desc.dat is missing or is a blank document.")
    try:
        if sys.version_info.major >= 3:
            with open(options.outputfile, "w", encoding = "utf-8") as f:
                f.write(output)
        else:
            with open(options.outputfile, "wt") as f:
                f.write(output)

    except:
        traceback.print_exc()

    print ("OK! Extraction finished!")
    print ("Original Dialog script count: " + str(msg_count))


if __name__ == '__main__':
    main()
