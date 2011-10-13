#!/usr/bin/env python2.5
__author__    = 'Kurt Schwehr'
__version__   = '$Revision: 10786 $'.split()[1]
__revision__  = __version__ # For pylint
__date__ = '$Date: 2008-11-18 12:03:11 -0500 (Tue, 18 Nov 2008) $'.split()[1]
__copyright__ = '2008'
__license__   = 'BSD'
__contact__   = 'kurt at ccom.unh.edu'

__doc__ ='''
Parse LADS lidar Caris Binary Format (CBF).  The files are
fixed size record structure with 50 bytes in a header followed
by a series of W1 scans.  Within each scan is a series of
1 or more WF waveform records.

@requires: U{Python<http://python.org/>} >= 2.5
@requires: U{epydoc<http://epydoc.sourceforge.net/>} >= 3.0.1
@requires: U{matplotlib<http://matplotlib.sourceforge.net/>} If you want to plot graphs

@undocumented: __doc__
@since: 2008-Nov-15
@status: under development
@organization: U{CCOM<http://ccom.unh.edu/>} 

@bug: Plotting is not all on the same scale
@todo: write test cases.  Have never tested bad file cases.
@todo: stat/info tools to summarize the lines like mbinfo
@todo: document all classes and methods
'''
import sys
import os
import mmap   # load the file into memory directly so it looks like a big array
import struct # Unpacking of binary data
import datetime

# Codes for struct unpacking of binary data.  Everything is little endian
uchar = '<B'
uchar120 = '<'+'B'*120
ushort = '<H'
uint = '<I'

header_size = 50 # 3 + 2 + 40 + 5
scan_header_block_size = 9
wave_form_block_size = 128 #8 + 120
block_size = scan_header_block_size  + wave_form_block_size


class CbfError(Exception):
    pass
#    def __init__(self,message):
#        self.message = message
#    def __str__(self):
#        return repr(self)


class WaveForm():
    def __init__(self,data):
        assert data[0:2] == 'WF'
        o = 2
        self.frame                = struct.unpack(ushort,data[o:o+2])[0]; o += 2
        self.row                  = struct.unpack(uchar ,data[o:o+1])[0]; o += 1
        self.col                  = struct.unpack(uchar ,data[o:o+1])[0]; o += 1
        self.selected_depth_index = struct.unpack(uchar ,data[o:o+1])[0]; o += 1
        self.contend_depth_index  = struct.unpack(uchar ,data[o:o+1])[0]; o += 1
        
        self.waveform = struct.unpack(uchar120 ,data[o:])

    def __str__(self):
        return 'WF: frame(%d) row(%d) col(%d) sel_dep(%d) cont_dep(%d)'  % (self.frame, self.row, self.col, self.selected_depth_index, self.contend_depth_index)


class ScanHeader():
    def __init__(self,data):
        '''
        @param max_size: Largest size that could be the W1 block.  Usually, pass the length of the data buffer
        '''
        self.data = data
        o = 0
        assert data[o:o+2] == 'W1'
        o += 2 # For W1
        year       = struct.unpack(ushort,data[o:o+2])[0]; o += 2
        julian_day = struct.unpack(ushort,data[o:o+2])[0]; o += 2
        hour       = struct.unpack(uchar ,data[o:o+1])[0]; o += 1
        minute     = struct.unpack(uchar ,data[o:o+1])[0]; o += 1
        second     = struct.unpack(uchar ,data[o:o+1])[0]; o += 1

        self.julian_day = julian_day

        date_str = '%4d %d %d %d %d' % (year, julian_day, hour, minute, second)
        self.datetime = datetime.datetime.strptime(date_str,'%Y %j %H %M %S')

        waveforms = []
        while o < len(data)-2 and data[o:o+2]=='WF':
            start = o
            waveforms.append(WaveForm(data[o:o+wave_form_block_size]))
            o += wave_form_block_size
        self.waveforms = waveforms

    def __str__(self):
        return 'Scan W1: %s (%03dj) with %d soundings' % ( self.datetime, self.julian_day, len(self.waveforms))


class CbfIterator:
    'Iterate across scan headers in a cbf'
    def __init__(self, cbf):
        self.data = cbf.data
        self.size = cbf.size
        self.offset = Cbf.header_size
    def __iter__(self):
        return self
    def next(self):
        if self.offset > self.size-1:
            raise StopIteration
        current = self.offset
        o = self.offset+1
        while o < self.size-1 and self.data[o:o+2] != 'W1':
            o += Cbf.scan_header_block_size
            while self.data[o:o+2] == 'WF':
                o += Cbf.wave_form_block_size
        #print 'range',current,o
        scan_data = self.data[current:o]
        #print 'scan_data:',scan_data
        self.offset = o
        return ScanHeader(scan_data)
        



class Cbf:
    ''' Caris Binary Format for LIDAR shots with waveforms.  The file
    stars off with a 50 byte header block.  It then has scan headers
    starting with a W1.  Within each W1, there are 1 or more waveform
    blocks of 128 bytes starting with a WF.
    '''
    header_size = 50 # 3 + 2 + 40 + 5
    scan_header_block_size = 9
    wave_form_block_size = 128 #8 + 120
    block_size = scan_header_block_size  + wave_form_block_size

    def __init__(self,filename):
        self.size = os.path.getsize(filename)
        tmpFile = open(filename,"r+")
        self.data = mmap.mmap(tmpFile.fileno(),self.size,access=mmap.ACCESS_READ)
        data = self.data

        o = 0
        header = data[0:3]; o+=3
        if header != 'HCB':
            raise CbfError('Not a Caris Binary Format file') 

        spec_major = struct.unpack('<B',data[o:o+1])[0]; o += 1
        spec_minor = struct.unpack('<B',data[o:o+1])[0]; o += 1

        if spec_major != 1 and spec_minor != 0:
            raise CbfError('wrong specification format: %d %d.  Need 1 0'% (spec_major, spec_minor))

        self.mission_title = (data[o:o+40]).strip(); o += 40

        self.run_id       = struct.unpack(ushort,data[o:o+2])[0]; o += 2
        self.run_segment  = struct.unpack(uchar, data[o:o+1])[0]; o += 1
        self.run_sequence = struct.unpack(uchar, data[o:o+1])[0]; o += 1
        self.run_child    = struct.unpack(uchar, data[o:o+1])[0]; o += 1

    def __iter__(self):
        ''' Allow iteration across the scans in the cbf '''
        return CbfIterator(self)


    def __str__(self):
        return 'Cbf Hdr: title="%s" id(%s) seg(%s) seq(%s) child(%s)' % (self.mission_title, 
                                        self.run_id, 
                                        self.run_segment, 
                                        self.run_sequence, 
                                        self.run_child)


def plot_all_waveforms(in_file):
    '''FIX: how do I control the axis range'''
    cbf = Cbf(in_file)
    import matplotlib.pyplot as plt
    plt.ioff()

    for swath_num,scan in enumerate(cbf):
        if swath_num > 4: sys.exit('EARLY!')
        print swath_num,str(scan)
        for i,waveform in enumerate(scan.waveforms):
            print i, str(waveform)
            print '      ',waveform.waveform
            out_filename = ('%s-%03d-%03d.png' % (in_file[:-4],swath_num,i))
            print out_filename

            p = plt.subplot(111)

            p.set_xlabel('sample number')
            p.set_ylabel('intensity?')
            p.set_title('File: %s Scan: %d Shot/Sounding: %d' % (in_file[:-3], swath_num,i))
            p.set_ylim(0,260)
            p.plot(waveform.waveform)
            #p.draw()
            plt.savefig(out_filename) #,'png')
            plt.close()
        out_filename = ('%s-%03d-all.png' % (in_file[:-4],swath_num))
        plt.xlabel('sample number')
        plt.ylabel('intensity?')
        plt.title('File: %s Swath: %d All shots' % (in_file[:-3], swath_num))
        for waveform in scan.waveforms:
            plt.plot(waveform.waveform)
        plt.savefig(out_filename) #,'png')
        plt.close()


def main():
    from optparse import OptionParser
    parser = OptionParser(usage="%prog [options] file1.CBF file2.CBF ...",
                          version="%prog "+__version__+' ('+__date__+')')

    #parser.add_option('-i', '--info', dest='info', default=False, action='store_true',
    #                  help='print out a summary of the cbf files')
    parser.add_option('-s', '--scan', dest='scan', default=False, action='store_true',
                      help='print out the summary for each scan')
    parser.add_option('-S', '--shot', dest='shot', default=False, action='store_true',
                      help='print out the summary for each shot (there will be many!)')
    parser.add_option('-v', '--verbose', dest='verbose', default=False, action='store_true',
                      help='run the tests run in verbose mode')

    (opts, args) = parser.parse_args()
    v = opts.verbose
    opts.info = True

    for filename in args:
        print 'File:',filename
        if opts.info:
            cbf = Cbf(filename)
            print cbf
            numscans = 0
            numshots = 0
            for i,scan in enumerate(cbf):
                numscans += 1
                numshots += len(scan.waveforms)
                if opts.scan:
                    print '  scan %d: %s' % (i,str(scan))
                if opts.shot:
                    for j,waveform in enumerate(scan.waveforms):
                        print '    shot %d: %s' % (j,str(waveform))
                        #print waveform.waveform
            print 'Summary for %s: scans(%d) shots(%d)' % (filename,numscans,numshots)


if __name__== '__main__':
    main()
