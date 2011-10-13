#!/usr/bin/env python
__author__    = 'Kurt Schwehr'
__version__   = '$Revision: 10786 $'.split()[1]
__revision__  = __version__ # For pylint
__date__ = '$Date: 2008-11-16$'.split()[1]
__copyright__ = '2008'
__license__   = 'BSD'
__contact__   = 'kurt at ccom.unh.edu'

__doc__ ='''
Parse LADS lidar Caris Ascii Format (CAF).  

@requires: U{Python<http://python.org/>} >= 2.5
@requires: U{epydoc<http://epydoc.sourceforge.net/>} >= 3.0.1
@requires: U{matplotlib<http://matplotlib.org/>} If you want to plot graphs

@undocumented: __doc__
@since: 2008-Nov-16
@status: under development
@organization: U{CCOM<http://ccom.unh.edu/>} 

'''
import sys
import os
import re
import datetime

# FIX: maybe for survey_title use [^,]
header_regex_str = r"""^
(?P<header_id>HCA),
(?P<version>[0-9]*[.][0-9]*),
(?P<survey_title>[-a-zA-Z0-9 _.]*),
(?P<survey_id_num>([0-9]){1,3}),
(?P<julian_day>[0-9]{3})(?P<year>[0-9]{4}),
(?P<scope>[SPA]),
(?P<nba_included>[YN]),
(?P<clash_range_radial>[0-9]{0,3}),
(?P<pos_transform_applied>[YN])"""

header_re = re.compile(header_regex_str, re.VERBOSE)

spheroid1_regex_str = r"""(?P<entry_id>(?P<spheroid_type>[CD])1),
(?P<ident_text>[a-zA-Z0-9 ]{1,40})"""
spheroid1_re = re.compile(spheroid1_regex_str, re.VERBOSE)

spheroid2_regex_str = r"""(?P<entry_id>(?P<spheroid_type>[CD])2),
(?P<major_semi_axis>\d{0,8}.\d{0,2}),
(?P<minor_semi_axis>\d{0,8}.\d{0,2}),
(?P<flattening>\d{0,3}.\d{0,10}),
(?P<eccentrivity>\d{0,14}.\d{0,12})"""
spheroid2_re = re.compile(spheroid2_regex_str, re.VERBOSE)

spheroid3_regex_str  = r"""(?P<entry_id>(?P<spheroid_type>[CD])3),
(?P<gps_offset_x>-?\d{0,8}.\d{0,2}),
(?P<gps_offset_y>-?\d{0,8}.\d{0,2}),
(?P<gps_offset_z>-?\d{0,8}.\d{0,2}),
(?P<gps_rotation_x>-?\d{0,8}.\d{0,5}),
(?P<gps_rotation_y>-?\d{0,8}.\d{0,5}),
(?P<gps_rotation_z>-?\d{0,8}.\d{0,5}),
(?P<gps_scale_factor>-?\d{0,8}.\d{0,5})"""
spheroid3_re = re.compile(spheroid3_regex_str, re.VERBOSE)

grid_regex_str = r"""(?P<entry_id>(?P<grid_type>[FG])1),
(?P<grid_id>[-a-zA-Z0-9 \t]{1,40}),
(?P<lat_origin>-?\d{1,2}),
(?P<lon_meridian>-?\d{1,3}),
(?P<zone_id>\d{1,2}|SP),
(?P<false_origin_easting>\d{1,8}),
(?P<false_origin_northing>\d{1,9}),
(?P<central_scale_factor>\d{0,7}.\d{0,4})
"""
grid_re = re.compile(grid_regex_str, re.VERBOSE)

area_lim_regex_str = r"""(?P<entry_id>L(?P<area_num>\d)),
(?P<lat>-?\d{0,2}.\d{0,8}),
(?P<lon>-?\d{0,3}.\d{0,8}),
(?P<easting>-?\d{1,8}),
(?P<northing>-?\d{1,9})
"""
area_lim_re = re.compile(area_lim_regex_str, re.VERBOSE)

run_header_regex_str = r"""(?P<entry_id>R1),
(?P<run_id>(?P<run>\d{1,5}).(?P<section>\d{1,5}).(?P<seq>\d{1,5}).(?P<child>\d{1,4})),
(?P<julian_day>\d{3})
(?P<year>\d{4}),
(?P<planned_task>\d{1,3}),
(?P<status>ACCEPTED|ANOMALOUS|REJECTED)"""
'@todo: what is wrong with the julian day - oscillations'
run_header_re = re.compile(run_header_regex_str, re.VERBOSE)

scan_header_regex_str = r"""(?P<entry_id>W1),
(?P<lat>\d{0,2}.\d{0,8}),
(?P<lon>-?\d{0,3}.\d{0,8}),
(?P<year>\d{4}),
(?P<julian_day>\d{1,3}),
(?P<hour>\d{1,2}),
(?P<minute>\d{1,2}),
(?P<second>\d{1,2}),
(?P<scan_row>\d{1,2}),
(?P<tide_cor>-?\d{1,3}.\d{0,2})"""
scan_header_re = re.compile(scan_header_regex_str, re.VERBOSE)

sounding_regex_str = r"""(?P<entry_id>[SPNX]),
(?P<lat_selected_depth>-?\d{0,2}.\d{0,8}),
(?P<lon_selected_depth>-?\d{0,3}.\d{0,8}),
(?P<easting_selected_depth>-?\d{0,8}),
(?P<northing_selected_depth>-?\d{0,9}),
(?P<lat_contender_depth>-?\d{0,2}.\d{0,8}),
(?P<lon_contender_depth>-?\d{0,3}.\d{0,8}),
(?P<easting_contender>-?\d{1,9}),
(?P<northing_contender>-?\d{1,9}),
(?P<frame>\d{1,4}),
(?P<row>\d{1,2}),
(?P<col>\d{1,2}),
(?P<depth_selected>  -?\d{1,3}.\d{1,2}),
(?P<depth_contender>-?\d{1,3}.\d{1,2}),
(?P<flag>\d{1,3})
(?P<comment>[-a-zA-Z_ ]{0,10}),
(?P<spare>[-a-zA-Z_ ]{0,10}),"""
sounding_re = re.compile(sounding_regex_str, re.VERBOSE)


class RunHeader:
    '''
    @todo: figure out what is with the oscillating julian days
    '''
    def __init__(self,in_handle):
        if isinstance(in_handle,file):
            run_header = run_header_re.search(infile.readline()).groupdict()
        elif isinstance (in_handle,str):
            run_header = run_header_re.search(in_handle).groupdict()
            
        h = run_header
        self.run = int(h['run'])
        self.section = int(h['section'])
        self.seq = int(h['seq'])
        self.child = int(h['child'])

        self.julian_day = int(h['julian_day'])   # WARNING... this may be wrong
        date_str = h['year'] + ' ' + h['julian_day']
        self.date = datetime.datetime.strptime(date_str,'%Y %j')

        self.planned_task = int(h['planned_task'])
        self.status = h['status']

    def __str__(self):
        return 'RunHeader: run(%d) sec(%d) seq(%d) child(%d) on %s - %s' % (
            self.run,
            self.section,
            self.seq,
            self.child,
            self.date,
            self.status,
            )

def peek_next_char(a_file):
    try:
        c = a_file.read(1)
        a_file.seek(-1,os.SEEK_CUR)
        return c
    except:
        return None # EOF


class CafIterator:
    'Iterate across the scans in a caf'
    def __init__(self, caf):
        self.infile = caf.infile
        # FIX: might want to rewind to the beginning of the R1 blocks?
    def __iter__(self):
        return self
    def next(self):
        'Return a list of all the soundings in a scan'
        infile = self.infile
        next = peek_next_char(infile)
        if next is None or next == '':
            raise StopIteration

        if next == 'R':
            return RunHeader(infile.readline())

        try:
            next2 = peek_next_char(infile)
            scan_header = ScanHeader(infile)
        except AttributeError:
            raise StopIteration


        return scan_header

class Sounding:
    'Goes with one waveform'
    def __init__(self,line):
        if line[0] not in 'SPNX':
            sys.stderr.write('ERROR no SPNX: "%s"\n'%line)
        assert line[0] in 'SPNX'
        s = sounding_re.search(line).groupdict()
        #print s
        self.lon = float(s['lon_selected_depth'])
        self.lat = float(s['lat_selected_depth'])
        self.easting_selected_depth = int(s['easting_selected_depth'])
        self.northing_selected_depth = int(s['northing_selected_depth'])
        self.lat_contender_depth = float(s['lat_contender_depth'])
        self.lon_contender_depth = float(s['lon_contender_depth'])
        self.easting_contender = int(s['easting_contender'])
        self.northing_contender = int(s['northing_contender'])
        self.frame = int(s['frame'])
        self.row = int(s['row'])
        self.col = int(s['col'])
        self.depth_selected = float(s['depth_selected'])
        self.depth_contender = float(s['depth_contender'])
        self.flag = int(s['flag']) # FIX: parse flags
        self.comment = s['comment']
        self.spare = s['spare']
    def __str__(self):
        return 'Sounding frame(%d) row(%d) col(%d): %0.2f or %0.2f ' % (self.frame, self.row,self.col,self.depth_selected, self.depth_contender)

class ScanHeader:
    'W1 block'
    def __init__(self,infile):
        line = infile.readline()
        h =  scan_header_re.search(line).groupdict()
        date_str = h['year']+' '+h['julian_day']+' '+h['hour']+' '+h['minute']+' '+h['second']
        self.datetime = datetime.datetime.strptime(date_str,'%Y %j %H %M %S')
        self.lat = float(h['lat'])
        self.lon = float(h['lon'])
        self.scan_row = int(h['scan_row'])
        self.tide_cor = float(h['tide_cor'])
        
        soundings = []
        while peek_next_char(infile) in 'SPNX': # and peek_next_char(infile) != '':
            line = infile.readline()
            line = line.strip()
            if len(line)==0:
                break
            soundings.append(Sounding(line))
        self.soundings = soundings

    def __str__(self):
        return 'ScanHeader %s at (%s,%s) with %s soundings on %s' % (self.scan_row,self.lon,self.lat,len(self.soundings), self.datetime)

class Caf:
    'Caris ASCII format for LADS lidar'
    def __init__(self,filename):
        infile = file(filename)
        self.infile = infile
        hdr = header_re.search(infile.readline()).groupdict()
        self.hdr = hdr
        self.title = hdr['survey_title'].strip()
        self.id_num = int(hdr['survey_id_num'])
        self.julian_day = int(hdr['julian_day'])
        self.year = int(hdr['year'])
        date_str = hdr['year']+' '+hdr['julian_day']
        self.date = datetime.datetime.strptime(date_str,'%Y %j')
        
        # C is input
        in_spheroid1 = spheroid1_re.search(infile.readline()).groupdict()
        in_spheroid2 = spheroid2_re.search(infile.readline()).groupdict()
        in_spheroid3 = spheroid3_re.search(infile.readline()).groupdict()
        in_spheroid1.update(in_spheroid2)
        in_spheroid1.update(in_spheroid3)
        self.in_spheroid = in_spheroid1

        # D is output
        out_spheroid1 = spheroid1_re.search(infile.readline()).groupdict()
        out_spheroid2 = spheroid2_re.search(infile.readline()).groupdict()
        out_spheroid3 = spheroid3_re.search(infile.readline()).groupdict()
        out_spheroid1.update(out_spheroid2)
        out_spheroid1.update(out_spheroid3)
        self.in_sphereoid = out_spheroid1

        self.orig_grid = grid_re.search(infile.readline()).groupdict()
        self.out_grid  = grid_re.search(infile.readline()).groupdict()

        #line = infile.readline()
        area_limits = []
        bounds = []
        while 'L' == peek_next_char(infile):
            line = infile.readline()
            area_lim = area_lim_re.search(line).groupdict()
            area_lim['area_num']=int(area_lim['area_num'])
            area_lim['lon']=float(area_lim['lon'])
            area_lim['lat']=float(area_lim['lat'])
            bounds.append((area_lim['lon'],area_lim['lat']))

            area_lim['northing']=int(area_lim['northing'])
            area_lim['easting']=int(area_lim['easting'])
            
            area_limits.append(area_lim)
        self.bounds = bounds
        self.area_lim = area_lim

        #self.run_header = run_header_re.search(infile.readline()).groupdict()
                
    def __iter__(self):
        ''' Allow iteration across the scans in the cbf '''
        return CafIterator(self)

    def __str__(self):
        return 'CAF Survey %d: name="%s" on %s (%03dj)' % (self.id_num, self.title, self.date.strftime('%Y-%m-%d'), self.julian_day)


def testit():
    caf = Caf('test.caf')
    print str(caf)
    #print caf.bounds
    for i,scan in enumerate(caf):
        
        print 'scan %s: %s' % (i,str(scan))

def main():
    from optparse import OptionParser
    parser = OptionParser(usage="%prog [options] file1.CAF file2.CAF ...",
                          version="%prog "+__version__+' ('+__date__+')')

    #parser.add_option('-i', '--info', dest='info', default=False, action='store_true',
    #                  help='print out a summary of the cbf files')
    parser.add_option('-r', '--runheaders', dest='run_headers', default=False, action='store_true',
                      help='Show each of the run headers (file switches?)')
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
            caf = Caf(filename)
            print caf
            numscans = 0
            numshots = 0
            numrunheaders = 0
            for i,scan in enumerate(caf):
                if isinstance(scan,RunHeader):
                    numrunheaders += 1
                    if opts.run_headers:
                        print i, scan
                    continue
                numscans += 1
                numshots += len(scan.soundings)
                if opts.scan:
                    print '  scan %d: %s' % (i,str(scan))
                if opts.shot:
                    for j,sounding in enumerate(scan.soundings):
                        print '    shot %d: %s' % (j,str(sounding))
            print 'Summary for %s: runheaders(%d) scans(%d) shots(%d)' % (filename,
                                                                          numrunheaders,
                                                                          numscans,
                                                                          numshots)


if __name__ == '__main__':
    main()
    #testit()
