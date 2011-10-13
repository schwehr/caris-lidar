#!/usr/bin/env python
__author__    = 'Kurt Schwehr and Monica Wolfson'
__version__   = '$Revision: 10786 $'.split()[1]
__revision__  = __version__ # For pylint
__date__ = '$Date: 2008-11-18 12:03:11 -0500 (Tue, 18 Nov 2008) $'.split()[1]
__copyright__ = '2008'
__license__   = 'BSD'
__contact__   = 'kurt at ccom.unh.edu'

__doc__ ='''
Dump lidar Caris Binary Format (CBF).

@todo: Set y-axis limit to 255
@todo: Add/modify code to generate a single m-file with all the
waveforms for the scan. Could skip plot functions on this one.
'''

import sys
import cbf

def main():
    from optparse import OptionParser
    parser = OptionParser(usage="%prog [options] file1.CBF file2.CBF ...",
                          version="%prog "+__version__+' ('+__date__+')')
    parser.add_option('-v', '--verbose', dest='verbose', default=False, action='store_true',
                      help='run the tests run in verbose mode')

    (opts, args) = parser.parse_args()
    v = opts.verbose
    opts.info = True

    for filename in args:
        cbf_file = cbf.Cbf(filename)
        print cbf
        numscans = 0
        numshots = 0
        #try:
            #loc,mission,survey,line,remainder = line.split('_')
        for i,scan in enumerate(cbf_file):
            if i>4: sys.exit('EARLY!') #limits program to first two scans worth of data to save space
            numscans += 1
            numshots += len(scan.waveforms)
            for j,waveform in enumerate(scan.waveforms):
                print '    scan %d shot %d: %s' % (i+1,j+1,str(waveform))
                outfilename = '%s_%03d_%03d.m' % (filename[:-4],i+1,j+1)  # changed - to _
                o = file(outfilename,'w')
		o.write('%#!/usr/bin/env octave  needed to run in Octave environment (not matlab)\n\n')
		o.write('%% filename: %s\n' % outfilename)
                o.write('% Lidar CBF dump for octave/matlab\n\n')
		o.write('clear all;\n')  #clears out the matlab variables
		o.write('close all;\n') #closes out any open matlab figures
		o.write('clc;\n\n') #clears out the command window
		o.write('set(0,\'defaulttextinterpreter\',\'none\');\n') # turn off matlab Latex interpreter
                o.write('scaninfo = \'%s\';\n' % str(scan))
                o.write('waveforminfo = \'%s\';\n' % str(waveform))
		o.write('filename = \'%s_%03d_%03d\';\n' % (filename[:-4],i+1,j+1)) # assign filename as variable for graph title
                # o.write('when = %s\n' % scan.datetime.strftime('%Y\t%m\t%d\t%H\t%M\t%S\t'))
                # o.write(' = %s\n' % scan.)
                o.write('frame = %s;\n' % waveform.frame)
                o.write('row = %s;\n' % waveform.row)
                o.write('col = %s;\n' % waveform.col)
		o.write('scan_num = %s;\n' %(i+1)) 
		o.write('shot_num = %s;\n' %(j+1))
                o.write('selected_depth_index = %s;\n' % waveform.selected_depth_index)
                o.write('contend_depth_index = %s;\n' % waveform.contend_depth_index)
                o.write('waveform = [')
                for sample in waveform.waveform[:-1]:
                    o.write('%d; ' % sample)
                o.write('%d ];\n' % waveform.waveform[-1])
                o.write('\n% Plot the waveform\n')
		o.write('plot(waveform);\n')
		o.write('hold on\n') # turn on plot overlay function
		o.write('x_selec = selected_depth_index;\n')
		o.write('x_contend = contend_depth_index;\n')
		o.write('y = 255;\n') # set y-limits for depth index lines
		o.write('stem(x_selec,y,\'g\',\'marker\',\'none\');\n') # add line for selected depth
		o.write('stem(x_contend,y,\'r\',\'marker\',\'none\');\n') # add line for contender depth
		o.write('title({[(filename)];[\'Scan: \',num2str(scan_num),\'  Shot: \',num2str(shot_num)]});\n')

if __name__ == '__main__':
    main()
