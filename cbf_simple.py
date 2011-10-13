#!/usr/bin/env python

# Copyright 2008.  BSD License.  -Kurt Schwehr

import sys,os
import mmap # load the file into memory directly so it looks like a big array
import struct # Unpacking of binary data

# Codes for struct unpacking of binary data
uchar = '<B'
ushort = '<H'
uint = '<I'

filename = 'H11428_V1_391_0_1_1.CBF'

size = os.path.getsize(filename)
tmpFile = open(filename,"r+")
data = mmap.mmap(tmpFile.fileno(),size,access=mmap.ACCESS_READ)

o=0

header = data[0:3]; o+=3

spec_major = struct.unpack('<B',data[o:o+1])[0]; o += 1
spec_minor = struct.unpack('<B',data[o:o+1])[0]; o += 1

mission_title = data[o:o+40]; o += 40

run_id       = struct.unpack(ushort,data[o:o+2])[0]; o += 2
run_segment  = struct.unpack(uchar, data[o:o+1])[0]; o += 1
run_sequence = struct.unpack(uchar, data[o:o+1])[0]; o += 1
run_child    = struct.unpack(uchar, data[o:o+1])[0]; o += 1

print 'header',header
print 'mission_title',mission_title
print 'spec', spec_major,spec_minor
print 'run_id',run_id
print 'run_seg',run_segment
print 'run_sequence',run_sequence
print 'run_child',run_child

######################################################################
# SCAN HEADER
######################################################################

print '\n  == scan header == '
scan_hdr_id = data[o:o+2]; o += 2

year       = struct.unpack(ushort,data[o:o+2])[0]; o += 2
julian_day = struct.unpack(ushort,data[o:o+2])[0]; o += 2
hour       = struct.unpack(uchar ,data[o:o+1])[0]; o += 1
minute     = struct.unpack(uchar ,data[o:o+1])[0]; o += 1
second     = struct.unpack(uchar ,data[o:o+1])[0]; o += 1

print 'scan header id',scan_hdr_id
print 'year',year
print 'julian_day',julian_day
print 'hour',hour
print 'minute',minute
print 'second',second


######################################################################
# WAVE FORM
######################################################################

print '\n  == waveform == '

wave_id = data[o:o+2]; o += 2

frame                = struct.unpack(ushort,data[o:o+2])[0]; o += 2
row                  = struct.unpack(uchar ,data[o:o+1])[0]; o += 1
col                  = struct.unpack(uchar ,data[o:o+1])[0]; o += 1
selected_depth_index = struct.unpack(uchar ,data[o:o+1])[0]; o += 1
contend_depth_index  = struct.unpack(uchar ,data[o:o+1])[0]; o += 1
waveform = []
for i in range(120):
    waveform.append(struct.unpack(uchar ,data[o:o+1])[0])
    o+=1

print 'wave_id',wave_id
print 'frame',frame
print 'row',row
print 'col',col
print 'selected_depth_index',selected_depth_index
print 'contend_depth_index',contend_depth_index
print 'waveform',waveform

print 'NEXT', data[o:o+2]
