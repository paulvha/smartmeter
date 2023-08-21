#! /usr/bin/python

#*****************************************************************
# Read Smart Meter subroutines for Raspberry
#
# version 2.0   paulvh / September 2015
# - update with display localisation
# - change timeout implementation
# - change buffer overrun
# - read selected OBIS entry from file
# - Turned into class
#
# version 2.1 / january 2016 / paulvh
# - allow for device option during init (to allow PL2303)
# - allow for different GPIO pin during init (default = GPIO 4)
#
# version 2.2 / january 2016 / paulvh
# - Support Domoticz
#
# version 2.3 / february 2016 / Paulvh
# - make selection easier
#
# Version 3.0 / October 2019 / paulvh
# - removed onedrivep and use onedrive
# - changed default parameters to include
# - changed prefix to SML3
# - changed default device (/dev/ttyUSB0) and pin (26)
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
#****************************************************************

import RPi.GPIO as GPIO
import serial, select, sys, time, os
from array import array
from dsmm import *

# set constants
SAVEFILE = "./logs/SML3"        # file to save information (added with month/year)
LOCKFILE = "./logs/LogLock"     # lock file during save
OBISFILE = "./logs/ObisSelected"# file to hold requested OBIS codes
RTSPIN = 26                     # default : GPIO 26, pin 37, Request to sent (RTS) naar Meter
OUTDEL = ";"                    # set the output delimiter character in between fields

# set limits
MAXBUF = 2 * 1024               # Maximum MeterBuffer entries (2 x max characters)
MAXTIMEOUT = 3 * MAXBUF         # Time-out has been reached (to cover speed of processor)
                                # often the program is waiting for the CRC to be calculated by the meter.

# Displays debug information if set to True.
DEBUG = False                   # Debug smart meter communication
DEBUG1 = False                  # Debug parse routines
DEBUG2 = False                  # Debug selection routines
DEBUG3 = False                  # Debug output routines

class smart_meter():

    # Initialise Class
    def __init__(self, set_io, device = "/dev/ttyUSB0", new_pin = RTSPIN):
        global RTSPIN

        self._crc_table = ""        # table for crc check
        self._ObisCodeSelection = ""# holds requested OBIS codes selected from the OBISFILE
        self._ObisFileInfo = ""     # captures ALL raw data read from OBISFILE file
        self._display = 1           # display messages (1 = display messages)
        self._ObisAdd = 1           # add OBIS codes in output (1 = add)
        self._ser=''                # holds serial information

        self.reset_cntrs()          # reset counters

        if set_io:                  # setup BCM for GPIO numbering & RTSPIN for output

            RTSPIN = new_pin        # in case a new pin was provided

            GPIO.setmode(GPIO.BCM)
            GPIO.setup(int(RTSPIN), GPIO.OUT)

            # setup serial (8N1 is default)
            self._ser=serial.Serial(device, 115200)
            self.flushser()         # flush any noise

    # do NOT include OBIS code in selective output
    def skipobis(self):
        self._ObisAdd = 0

    # set to silent messages (1 = display)
    def setsilent(self,silent):
        self._display = silent

    # set or clear RTS to meter
    def set_rts(self,cmd):

        if cmd == 1 or cmd == 3 or cmd == 4 or cmd == 5:    # set RTS
            if (DEBUG): printstderr("Info: Request commando SET: {}".format(cmd))
            GPIO.output(RTSPIN,GPIO.HIGH)

        elif cmd == 2:                          # remove RTS
            if (DEBUG) : printstderr("Info: Request commando RESET: {}".format(cmd))
            GPIO.output(RTSPIN,GPIO.LOW)

    # check on any data from meter
    def checkser(self):
        return(select.select([self._ser],[],[],0)[0])

    # read data from meter
    def readser(self):
        return(self._ser.read())

    # flush serial buffer
    def flushser(self):
        return(self._ser.flushInput())

    # add data to meterbuffer
    def addmeter(self,data):

        if self._write_cntr_buffer >= MAXBUF:
            self.set_rts(2)                     # remove request signal from meter
            self.flushser()                     # flush any input pending from meter
            return 1
        else:
            self._meter_raw_buffer += data      # save byte
            self._write_cntr_buffer += 1        # next position
            return 0

    # return raw content meterbuffer
    def getmbuf(self):
        return(self._meter_raw_buffer)

    # return write counter meterbuffer
    def gwcount(self):
        return(self._write_cntr_buffer)

    # return read counter meterbuffer
    def grcount(self):
        return(self._read_cntr_buffer)

    # get parsed requested selection
    def get_obis_info(self):
        return(self._ObisCodeSelection)

    # Timeout control, if WriteCountBuffer stays the same for more than X amount of passes
    # depending on the Raspberry model MAXTIMEOUT should be > 2  or 3 x  MAXBUF (default is 3 times)
    def checkTO(self):

        if self._write_cntr_buffer > 0:         # only if some characters have been received already

            if (DEBUG): printstderr("TimeOutCounter {} WriteCountBuffer {}".format(self._timeout_cntr,self._write_cntr_buffer))

            if self._last_writecntr_buffer == self._write_cntr_buffer:

                self._timeout_cntr +=1

                time.sleep(100 / 1000)          # sleep 100ms

                if self._timeout_cntr >= MAXTIMEOUT: # exceeded timeout  ?

                    if self._display: printstderr(dlm('e8'))
                    self.set_rts(2)             # remove request signal from meter
                    self.flushser()             # flush any input pending from meter
                    return 1
            else:
                self._last_writecntr_buffer = self._write_cntr_buffer
                self._timeout_cntr = 0          # reset timeout counter
        return 0

    """
    Perform CRC-16 check
    return == 1, 2, 3 or 4 as the count of CRC digits
    return == 5 as all CRC bits have been received and CRC is correct
    return == 6 CRC check failed
    """
    def do_crc_check(self, data, count):

        self._crc_value_rec += data             # save received CRC
        count += 1                              # count CRC values

        if (DEBUG): printstderr("Info: current CRC Value {}, CRC to be added {}".format(self._crc_value_rec,hex(ord(data))))

        if count == 5:                          # if complete CRC has been received

            if self._crc_table == "":           # CRC table setup for speed during check

                # CRC-16 poly: p(x) = x^16 + x^15 + x^2 + 1^0

                poly = 0xa001
                self._crc_table = array('H')

                for byte in range(256):         # create CRC-table
                    crc = 0
                    for bit in range(8):
                        if (byte ^ crc) & 1:
                            crc = (crc >> 1) ^ poly
                        else:
                            crc >>= 1
                        byte >>= 1
                    self._crc_table.append(crc)

            crc_calc = 0

            for ch in self._meter_raw_buffer:   # calculate CRC on data received
                crc_calc = self._crc_table[ord(ch) ^ (crc_calc & 0xff)] ^ (crc_calc>> 8)

            crc_calc = '%04x' % crc_calc        # transpose to hex

            if self._crc_value_rec == str.upper(crc_calc):
                if (DEBUG): printstderr("CRC check passed.")
            else:
                if self._display:
                    printstderr(dlm('e1').format(crc_calc,self._crc_value_rec))

                count = 6                       # set fail return value

            self._crc_value_rec = ""            # reset received CRC for next buffer check

        return(count)

    """
    Read the OBIS codes to be selected from file
    return values:
        0 = succesfull
        1 = empty or not existent OBIS selection file
        2 = Error during opening or reading OBIS selection file

    """
    def read_obis_file(self):

        if os.access(OBISFILE, os.R_OK) == 0:   # check that filepath exits
            if self._display: printstderr(dlm('e10').format(OBISFILE))
            return 1

        ret = os.stat(OBISFILE)                 # if empty file
        if ret.st_size == 0:
            if self._display: printstderr(dlm('e11').format(OBISFILE))
            os.remove(OBISFILE)
            return 1

        try:                                    # read content
            read_file = open(OBISFILE,'rb')

            if(read_file):
                self._ObisFileInfo = read_file.read()
                read_file.close()
                return 0

        except:
            if self._display: printstderr(dlm('e12').format(OBISFILE))
            return(2)

    """
    Parse the information from the selection file into a table
    skip any comment lines
    skip empty lines
    incl_comments : if True it will include comments as well
    """
    def fill_obis_tbl(self, incl_comment=False):

        obis_lines = self._ObisFileInfo.splitlines()
        num = len(obis_lines)

        for x in range(0,num):

            obis_line = obis_lines[x]

            if obis_line == "":     continue    # if empty
            if obis_line[0] == "#": continue    # and skip comment lines

            if incl_comment:
                self._ObisCodeSelection += obis_line + "\n" # save

            else:
                pos = obis_line.find('[')       # find comments start

                if pos < -1 or pos < 9:
                    if self._display: printstderr(dlm('e18').format(pos))
                    return 1

                self._ObisCodeSelection += obis_line[:pos] + "\n"   # save

        if (DEBUG2): printstderr("Read from selection file : \n{}".format(self._ObisCodeSelection))

        return 0

    # compare requested OBIS codes with current entry in meterbuffer. Save if they match.
    def detect_obis_codes(self):

        if self._ObisCodeSelection == "":   # get the request selection first (if not done already)
            ret = self.read_obis_file()     # try to read from request file

            if ret == 1:                    # empty or not existent
                if self._display: printstderr(dlm('e13'))
                return 1

            elif ret == 2:                  # error during reading/opening
                if self._display: printstderr(dlm('e14'))
                return 1

            elif ret == 0:
                if (self.fill_obis_tbl()):  # parse file information to request table
                    return 1

            if self._ObisCodeSelection == "":# if still nothing to select
                if self._display: printstderr(dlm('e11').format(OBISFILE))
                return 1
                                            # add timestamp coming from meter always !!
            self._ObisCodeSelection += "0-0:1.0.0\n"

                                            # Try to make matches...
        raw_lines = self._meter_raw_buffer.splitlines()
        obis_lines = self._ObisCodeSelection.splitlines()
        obis_len = len (obis_lines)

        for kk in range(0,len(raw_lines)):          # for received line

            in_line = raw_lines[kk]

            if in_line == "" or in_line[0] == "/":
                continue                            # ID or empty line

            jj = 0

            while jj < obis_len:                    # for each OBIS selection

                obis_code = obis_lines[jj]
                jj += 1
                if in_line.find(obis_code) < 0:     # try to match
                    continue                    # no match: next OBIS


                if (DEBUG2): printstderr("Info: detected {}.".format(in_line))

                s_pos = in_line.find("(")           # find begin
                l_pos = in_line.rfind(")",s_pos)    # and last pos

                if s_pos < 0 and l_pos < 0:
                    if self._display: printstderr(dlm('e19').format(obis_code))
                    continue

                values = in_line[s_pos:l_pos+1]

                if self._ObisAdd:                   # add Obiscode ?
                    values = obis_code + OUTDEL + values

                if self._save_buffer == "":                 # add to output
                    self.output_line(values)
                else:
                    self.output_line(OUTDEL + values)

        if self._save_buffer == "":
            return 1

        return 0

    # save information to buffer
    def output_line(self,line):

        if (DEBUG2): printstderr("Info: save_buffer current content\n{} ".format(self._save_buffer))
        if (DEBUG2): printstderr("Info: adding to save_buffer {} \n".format(line))

        self._save_buffer += line

    # save the selected information from buffer to a file
    def save_info(self,filenm):

        if self._save_buffer == "":         # nothing to save!
            return 1

        timestamp = time.asctime()  # compose file for month/year
        outputfile = filenm+timestamp.split()[1]+timestamp.split()[4]

        if (DEBUG3):
            printstderr("Output file: {} ".format(outputfile))
            printstderr("Data: {} \n".format(self._save_buffer))

        # check for a lockfile (to be set and removed by either the writing or reading program)

        lock = os.path.exists(LOCKFILE)         # lock file exists (someone else using the file?)
        count = 0

        while lock:
            printstderr(dlm('e2').format(count))# it is locked
            count += 1
            time.sleep(5)                       # wait 5 seconds
            lock = os.path.exists(LOCKFILE)     # check lock exists
            if count > 12:                      # wait for minute (12 x 5s)
                printstderr(dlm('e15'))
                return 1

        lockfile = open(LOCKFILE,'w')           # create lock file

        if (lockfile):
            lockfile.write("created by smprog\n")
            lockfile.write(timestamp)
            lockfile.write("\n")
            lockfile.close()
        else:
            if self._display:
                printstderr(dlm('e17').format(LOCKFILE))    # can not create
                return 1

        for savecount in range (0,5):           # try 5 times to save

            savefile = open(outputfile,'aw')    # open for writing & appending
            timestamp = time.asctime()

            if (savefile):                      # save the data
                savefile.write(self._save_buffer+'\n')

                savefile.close()

                os.remove(LOCKFILE)             # remove lock file

                if self._display :
                    timecode = timestamp.split()[2]+":"+timestamp.split()[1]+":"+timestamp.split()[3]
                    print (dlm('m1').format(timecode))

                return 0                        # succesfull save
            else :
                if self._display:
                    timecode = timestamp.split()[2]+":"+timestamp.split()[1]+":"+timestamp.split()[3]
                    printstderr(dlm('e3').format(savecount,outputfile.timecode))
        return 1

    # reset different counters for clean (re)start
    def reset_cntrs(self):

        self._crc_value_rec = ""                # CRC value received from meter
        self._write_cntr_buffer = 0             # start writing at begin buffer
        self._read_cntr_buffer = 0              # start reading at begin buffer
        self._meter_raw_buffer = ""             # empty buffer to hold meter information
        self._save_buffer = ""                  # empty buffer to be saved/displayed
        self._timeout_cntr = 0                  # reset timeout counter
        self._last_writecntr_buffer = 0         # reset for timeout routine

    # Once we are done, release the pin if setup by this program + clean_up
    def close_meter(self):

        if self._ser:                           # if set_io during init
            self.set_rts(2)                     # remove request from meter
            self.flushser()                     # flush any input pending from meter
            GPIO.cleanup()                      # clean GPIO

        if self._display:
            timestamp = time.asctime()
            timecode = timestamp.split()[2]+":"+timestamp.split()[1]+":"+timestamp.split()[3]
            printstderr(dlm('e7').format(timecode))

        return 0
