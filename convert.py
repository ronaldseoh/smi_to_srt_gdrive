#!/usr/bin/env python
# -*- coding: UTF-8 -*-
'''
This code is a modified version of convert.py, originally written by
MoonChang Chae (http://egloos.zum.com/mcchae/v/10763080) (the filename was smi2srt.py on the original version)
and revised by taylor224 (https://gist.github.com/taylor224/4c80ad3d047af48aa4a0cc64baee22aa).
The code was modified to be compatible with Python 3 interpreters.

The license for the original work is not clear, but presumed to be GPLv2 or GPLv3 based on the line 9 of
smi2srt.py. Since GPLv3 was the latest version of GPL when the original code was released, 
the original code's license is assumed to be GPLv3 and hence we are licensing this code with GPLv3. 
'''

###################################################################################################
import os
import sys
import re
import chardet
from io import IOBase

###################################################################################################
def usage(msg=None, exit_code=1):
    print_msg = """
usage %s smifile.smi [...]
    convert smi into srt subtitle file with same filename.
    By Ronald Seoh (ronaldseoh@icloud.com),
    based on the original work by MoonChang Chae <mcchae@gmail.com> 
    and the subsequent modification by taylor224 
    (https://gist.github.com/taylor224).
""" % os.path.basename(sys.argv[0])
    if msg:
        print_msg += '%s\n' % msg
    print(print_msg)
    sys.exit(exit_code)

###################################################################################################
class smiItem(object):
    def __init__(self):
        self.start_ms = 0
        self.start_ts = '00:00:00,000'
        self.end_ms = 0
        self.end_ts = '00:00:00,000'
        self.contents = None
        self.linecount = 0
    @staticmethod
    def ms2ts(ms):
        hours = ms // 3600000
        ms -= hours * 3600000
        minutes = ms // 60000
        ms -= minutes * 60000
        seconds = ms // 1000
        ms -= seconds * 1000
        s = '%02d:%02d:%02d,%03d' % (hours, minutes, seconds, ms)
        return s
    def convertSrt(self):
        # 1) convert timestamp
        self.start_ts = smiItem.ms2ts(self.start_ms)
        self.end_ts = smiItem.ms2ts(self.end_ms-10)
        # 2) remove new-line
        self.contents = re.sub(r'\s+', ' ', self.contents)
        # 3) remove web string like "&nbsp";
        self.contents = re.sub(r'&[a-z]{2,5};', '', self.contents)
        # 4) replace "<br>" with '\n';
        self.contents = re.sub(r'(<br>)+', '\n', self.contents, flags=re.IGNORECASE)
        # 5) find all tags
        fndx = self.contents.find('<')
        if fndx >= 0:
            contents = self.contents
            sb = self.contents[0:fndx]
            contents = contents[fndx:]
            while True:
                m = re.match(r'</?([a-z]+)[^>]*>([^<>]*)', contents, flags=re.IGNORECASE)
                if m == None: break
                contents = contents[m.end(2):]
                if m.group(1).lower() in ['b', 'i', 'u']:
                    sb += m.string[0:m.start(2)]
                sb += m.group(2)
            self.contents = sb
        self.contents = self.contents.strip()
        self.contents = self.contents.strip('\n')
    def __repr__(self):
        s = '%d:%d:<%s>:%d' % (self.start_ms, self.end_ms, self.contents, self.linecount)
        return s

###################################################################################################
def convertSMI(smi_file, input_type='string', output_type='string', output_file_name=None):

    # If the input isn't a string, assume it's a file
    if input_type == 'file':
        if not os.path.exists(smi_file):
            sys.stderr.write('Cannot find smi file <%s>\n' % smi_file)
            return False

        ifp = open(smi_file, 'rb')
        smi_sgml = ifp.read()
        ifp.close()

    elif input_type == 'string':
        smi_sgml = smi_file

    else:
        raise Exception('Unrecogized input_type.')

    # If the desired output type is a file, set the name of the output file
    if output_type == 'file':
        if input_type == 'file' and output_file_name == None:
            rndx = smi_file.rfind('.')
            srt_file = '%s.srt' % smi_file[0:rndx]
        else:
            if output_file_name != None:
                srt_file = output_file_name
            else:
                raise Exception('You need to specify output_file_name.')

    # Auto-detect the encoding of the given input and convert it to UTF-8
    # if it wasn't already
    chdt = chardet.detect(smi_sgml)

    if chdt['encoding'] != 'utf-8':
        smi_sgml = str(smi_sgml, encoding=chdt['encoding'])
        smi_sgml = smi_sgml.encode('utf-8')

    smi_sgml = str(smi_sgml, encoding='utf-8')

    # skip to first starting tag (skip first 0xff 0xfe ...)
    try:
        fndx = smi_sgml.lower().find('<sync')
    except Exception as e:
        print(chdt)
        raise e

    if fndx < 0:
        return False

    smi_sgml = smi_sgml[fndx:]
    lines = smi_sgml.split('\n')
    
    srt_list = []
    sync_cont = ''
    si = None
    last_si = None
    linecnt = 0

    for line in lines:
        linecnt += 1
        sndx = line.upper().find('<SYNC')
        if sndx >= 0:
            m = re.search(r'<sync\s+start\s*=\s*(\d+)>(.*)$', line, flags=re.IGNORECASE)
            if not m:
                raise Exception('Invalid format tag of <Sync start=nnnn> with "%s"' % line)

            sync_cont += line[0:sndx]
            last_si = si

            if last_si != None:
                last_si.end_ms = int(m.group(1))
                last_si.contents = sync_cont
                srt_list.append(last_si)
                last_si.linecount = linecnt

            sync_cont = m.group(2)
            si = smiItem()
            si.start_ms = int(m.group(1))

        else:
            sync_cont += line

    if output_type == 'file':        
        ofp = open(srt_file, 'w')
    else:
        output_string = ''

    ndx = 1

    for si in srt_list:
        si.convertSrt()
        if si.contents == None or len(si.contents) <= 0:
            continue

        sistr = '%d\n%s --> %s\n%s\n\n' % (ndx, si.start_ts, si.end_ts, si.contents)

        if output_type == 'file':
            ofp.write(sistr)
        else:
            output_string += sistr
        
        ndx += 1

    if output_type == 'file':
        ofp.close()
        return True
    else:
        return output_string

###################################################################################################
def do_convert_files():
    if len(sys.argv) <= 1:
        usage()
    for smi_file in sys.argv[1:]:
        if convertSMI(smi_file, input_type='file', output_type='file'):
            print("Converting <%s> OK!" % smi_file)
        else:
            print("Converting <%s> Failture!" % smi_file)
            
    
###################################################################################################
if __name__ == '__main__':
    do_convert_files()
