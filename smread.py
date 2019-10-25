#! /usr/bin/python
#
#*****************************************************************
# Read the SmartMeter through Raspberry Pi
# if device is /dev/ttyAMA0 (default ) :
#   RX UART pin 10 / GPIO 15
#   GND pin 6
#   3.3V pin 1
#
# if GPIO-4 (default):
#   Request output pin 7  / GPIO 4
#
# version 1.0   paulvh / January 2015
# - initiale version
# - Special circuit is needed for transposing 5V signals from meter to 3.3V of Rasp-pi
# - see README.md for installation information
#
# version 2.0   paulvh / September 2015
# - update with display localisation options (py)
# - change timeout & buffer overrun implementation
# - programs subroutines in different class smprog.py file
# - read selected OBIS entries from file instead of hard coded (using obislct util)
# - seperate background demon created (smrdback.py)
# - code cleanup and bugs fixing
# - update installation information
#
# version 2.1 / january 2016 / paulvh
# - added option for different device  (to allow PL2303 on /dev/ttyUSB0)
# - added option for different GPIO pin  (default = GPIO 4)
# - code clean-up
#
# version 2.2 / january 2016 / paulvh
# - added option for Domoticz
#
# version 2.3 / February 2016 / paulvh
# - change matching algorithm
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

import select, sys, time, argparse
from smartprog import *

# set constants
DISVERS = "version 3.0"     # -v for display version
SAVERAW = './logs/RAW'      # prefix for raw file
SAVEFILE = './logs/SML3'    # file to save information (added with month/year)
DOMOFILE = "/tmp/meterinput" # file for domoticz

# status on MeterBuffer
BUF_FL = 0                  # continue to fill buffer
BUF_OR = 1                  # STOP : error : Buffer overrun
BUF_TO = 2                  # STOP : error : Time out error
BUF_OK = 3                  # STOP : we are good !

# set variables
buffer_status = BUF_FL      # set when completed adding to MeterBuffer and Ready to start display/save
check_crc = 0               # Activate CRC check when'!' character from meter has been received
lang = 'nl'                 # Display language,for supported languages, check dsmm.py
device = "/dev/ttyUSB0"     # default device
gpio_pin = 26               # default GPIO pin for RTS
key_input = ''              # holds input user
smc = ""                    # holds smartmeter class


# reset counters and buffers
def clean_counters():
    global check_crc,  buffer_status

    # reset class variables
    smc.reset_cntrs()

    # reset local variable
    check_crc = 0           # CRC capture/check is not actived
    buffer_status = BUF_FL  # enable writing to buffer

# Display start message (DEBUGx is set in heading smprog.py)
def print_banner():

    print(dlm('b0'))

    if (DEBUG)  : print (dlm('d0'))
    if (DEBUG1) : print (dlm('d1'))
    if (DEBUG2) : print (dlm('d2'))
    if (DEBUG3) : print (dlm('d3'))

# send output to file for domototicz
def create_domoticz(smc):

    if os.path.exists(DOMOFILE):        # check if file exists do nothing
        return 0

    meter_buffer = smc.getmbuf()

    for savecount in range (0,5):       # try 5 times to save

        savefile = open(DOMOFILE,'aw')  # open for writing & appending

        if (savefile):                  # save the data
            savefile.write(meter_buffer+'\n')

            savefile.close()

            return 0                    # succesfull save
        else:
            printstderr("Could not save to  {}.".format(DOMOFILE))

    return 1

#*********************************************************************
# HERE THE PROGRAM STARTS !!!!
#*********************************************************************

parser = argparse.ArgumentParser(description = "Read, display and store Smartmeter data",
 epilog = "Need special hardware (see installation instruction) and must be run as ROOT",
 prog = "smread")

parser.add_argument('--version', action='version', version=DISVERS)
parser.add_argument("-l","--language", help="language to use", choices=['nl','uk'],default = 'nl')
parser.add_argument("-o", "--output",  help="do not include OBIS in selected output",action = "store_true")
parser.add_argument("-D","--device", help="device to use (default: /dev/ttyAMA0")
parser.add_argument("-G","--gpio", help="GPIO pin to use (default: GPIO-4)", type = int)

args = parser.parse_args()

if args.device: device = args.device        # overwrite default device

if os.path.exists(device) == False:
    printstderr("can not locate {}".format(device))
    sys.exit(1)

if args.gpio: gpio_pin = args.gpio          # overwrite default pin

if gpio_pin > 26 or gpio_pin < 2:
    printstderr("GPIO pin {} invalid.".format(gpio_pin))
    sys.exit(1)

if args.language: lang = args.language      # language option

if setdlang(lang):                          # set language
    printstderr("language option {} is not supported.".format(lang))
    sys.exit(1)

try:

    smc = smart_meter(1,device,gpio_pin)    # set up class with GPIO and Serial

    if args.output: smc.skipobis()          # skip OBIS code in selected output file

    print(dlm('e16').format(device,gpio_pin))
    print_banner()                          # print instructions

    while True :
                                            # if any keyboard input
        if (select.select([sys.stdin],[],[],0)[0]):

            key_input = sys.stdin.readline().strip()

            # 1 = Start communicatie & save selective OBIS to file
            # 2 = Stop taking input from meter into buffer
            # 3 = Start & display in Raw format
            # 4 = Start & display in Raw format and save
            # 5 = Create Domoticz file
            # 6 = end program

            if (key_input.isdigit()):           # must be digit

                if int(key_input) > 6  or int(key_input) < 1 :
                    print (dlm('e5'))
                    print_banner()              # print instructions

                elif int(key_input) == 6:       # end program
                    smc.close_meter()
                    sys.exit(0)

                else :                          # set Request line
                    smc.set_rts(int(key_input))
            else:
                print_banner()                  # print instructions

        # if anything sent by smart meter
        if smc.checkser():

            data = smc.readser()                # read data from meter

            if check_crc > 0:                   # is CRC check active ?

                check_crc = smc.do_crc_check(data,check_crc)

                if check_crc == 5:              # CRC check passed :-)?
                    buffer_status=BUF_OK        # Stop adding / start reading buffer
                    smc.set_rts(2)              # Remove request signal from meter
                    smc.flushser()              # flush any input pending from smart meter
                    check_crc=0                 # reset CRC Check

                if check_crc == 6:              # CRC check failed :-(?
                    smc.set_rts(2)              # remove request signal from meter
                    time.sleep(5)               # wait 5 seconds (settle situation)
                    smc.flushser()              # flush any input pending from smart meter
                    clean_counters()            # reset local and global variables
                    smc.set_rts(int(key_input))# try again input meter

            elif (buffer_status == BUF_FL):     # still able add to meter buffer ?

                    if smc.addmeter(data):      # add data (0 = good)
                        buf_stat = BUF_OR       # set buffer overrun

                    # if last character of datastream (before CRC info)
                    if data == '!':             # actived CRC check
                        check_crc = 1
                                                # Overrun or Timeout, display to diagnose only
        if (buffer_status == BUF_OR) or (buffer_status == BUF_TO):

            print(smc.getmbuf())                # display buffer
            msg = "e6"+str(buffer_status)       # Display right message
            print(dlm(msg))
            time.sleep(5)                       # wait 5 seconds (to settle situation)
            clean_counters()                    # reset different counters
            print_banner()                      # (re) print instructions

        elif (buffer_status == BUF_OK) :        # All characters received & CRC = OK

            if key_input == '5':                # need to create output for domoticz ?
                create_domoticz(smc)
                print(dlm('m1').format(DOMOFILE))

            elif key_input == '3':              # if RAW display was requested
                print(smc.getmbuf())
                print(dlm('e4'))

            elif key_input == '4':              # if Raw display + save to file
                print(smc.getmbuf())
                smc.output_line(smc.getmbuf())
                smc.output_line('\n')

                if (smc.save_info(SAVERAW)):    # save information to file
                    if (DEBUG): printstderr ("Error: issue during saving")

            elif key_input == '1':              # option 1 (selective saving)

                if (smc.detect_obis_codes()):   # include lines with a match
                    if (DEBUG): printstderr ("Error: issue during selecting")

                elif (smc.save_info(SAVEFILE)): # save selected information to file
                    if (DEBUG): printstderr ("Error: issue during saving")

            clean_counters()                    # reset global and local counters
            print_banner()                      # (re) print instructions

        # Timeout control, if WriteCountBuffer stays the same for more than X amount of passes

        if smc.checkTO() == 1:                  # If timeout ?
            buffer_status = BUF_TO              # stop adding enable display

except KeyboardInterrupt:                       # cntrl-c pressed
        print(dlm('e9'))

        if (smc):
            smc.close_meter()

        sys.exit(1)

except Exception, e:                            # any other error
        print("Exception : %s" % str(e))

        if (smc):
            smc.close_meter()

        sys.exit(1)
