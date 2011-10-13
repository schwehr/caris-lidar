#!/usr/bin/env python
__author__    = 'Kurt Schwehr'
__version__   = '$Revision: 10786 $'.split()[1]
__revision__  = __version__ # For pylint
__date__ = '$Date: 2008-11-18 12:03:11 -0500 (Tue, 18 Nov 2008) $'.split()[1]
__copyright__ = '2008'
__license__   = 'BSD'
__contact__   = 'kurt at ccom.unh.edu'

__doc__ ='''
Parse LADS lidar Caris Format combining both the ASCII (CAF) and Binary (CBF) files.  

The Cabf and CabfIterator are really closely tied together.  A bit disturbing, but it works.

@requires: U{Python<http://python.org/>} >= 2.5
@requires: U{epydoc<http://epydoc.sourceforge.net/>} >= 3.0.1
@requires: U{matplotlib<http://matplotlib.org/>} If you want to plot graphs

@undocumented: __doc__
@since: 2008-Nov-16
@status: under development
@organization: U{CCOM<http://ccom.unh.edu/>} 
'''

import caf 
import cbf
import sys
import time

class CabfIterator:
    '@todo: perhaps this should be inside the Cabf class?  Seems strange to be separate'
    def __init__(self,cabf_handle):
        self.cabf = cabf_handle
        self.filecount = 0
        self.scancount = 0
    
    def __iter__(self):
        return self

    def next(self):
        scan = self.cabf.caf_iter.next()
        if isinstance(scan,caf.RunHeader):
            self.filecount += 1
            rh = scan
            basename = self.cabf.base
            new_cbf_filename = '%s_%d_%d_%d_%d.CBF' % (basename,rh.run,rh.section,rh.seq,rh.child)
            #print 'runheader: File switch: ',new_cbf_filename
            #print 'need to open a cbf', new_cbf_filename
            self.cabf.cbf = cbf.Cbf(new_cbf_filename)
            #print 'self.cabf.cbf', type(self.cabf.cbf)
            self.cabf.cbf_iter = self.cabf.cbf.__iter__()
            scan = self.cabf.caf_iter.next()

        self.scancount += 1
        scan_bin = self.cabf.cbf_iter.next()
        return (self.filecount,self.scancount,scan,scan_bin)
        
    
class Cabf:
    '''
    Handle reading lidar ascii and binary waveform files together
    '''
    def __init__(self,caf_filename):
        self.caf_filename = caf_filename
        self.base = caf_filename[:-4]
        self.caf = caf.Caf(caf_filename)
        self.caf_iter = self.caf.__iter__()

        self.cbf = None
        self.cbf_iter = None

        self.scan_num = 0

    def __iter__(self):
        return CabfIterator(self)

def main():

    from optparse import OptionParser
    parser = OptionParser(usage="%prog [options] file1.CAF file2.CAF ...",
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
            cabf = Cabf(filename)
            files = 0
            scans = 0
            for filecount, scancount, scan, scan_bin in cabf:
                files = filecount
                scans = scancount
                if opts.scan:
                    print 'scan: filenum(%d) scannum(%d)' % (filecount, scancount)
                    print '   ascii:',scan
                    print '     bin:',scan_bin
                if opts.shot:
                    for i,sounding in enumerate(scan.soundings):
                        waveform = scan_bin.waveform[i]
                        print 'shot: %d' % i
                        print '   ascii:',sounding
                        print '     bin:',waveform
            print 'Summary for %s: binfiles(%d) scans(%s)' % (filename,filecount,scancount)

    print 'FIX: seems like this quits too soon!'

if __name__ == '__main__':
    main()

#    cabf = Cabf('GER_300_002.CAF')
#    for filecount,scancount,scan,scan_bin in cabf:
#        print 'A_scan:', filecount, scancount
#        print '       ',scan
#        print '       ',scan_bin
#    print 'FIX: seems like this quits too soon!'

#     filename = 'GER_300_002.CAF'
#     basename = filename[:-4]
#     caf_file = caf.Caf('GER_300_002.CAF')
#     cbf_file = None
#     cbf_iter = None
#     for i,scan in enumerate(caf_file):
#         print scan
#         if isinstance(scan,caf.RunHeader):
#             rh = scan
#             new_cbf_filename = '%s_%d_%d_%d_%d.CBF' % (basename,rh.run,rh.section,rh.seq,rh.child)
#             print 'need to open a cbf', new_cbf_filename
#             cbf_file = cbf.Cbf(new_cbf_filename)
#             cbf_iter = cbf_file.__iter__()
#             print 'FIX... remove!',time.sleep(1)
#             continue
#         assert cbf_iter is not None
#         scan_bin = cbf_iter.next()

#         print 'scans'
#         print '  asc:',scan
#         print '  bin:',scan_bin
#         time.sleep(.2)
        
    #main()
