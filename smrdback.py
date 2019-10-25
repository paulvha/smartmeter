#!/usr/bin/python
from __future__ import print_function
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
# version 2.0  / September 2015 / paulvh
# - update with display localisation
# - change timeout implementation
# - change buffer overrun
# - program subroutines in different smprog.py file for easier understanding
# - read selected OBIS entry from file instead of hard coded (using obislct util)
#
# version 2.1 / january 2016 / paulvh
# - added option for different device  (to allow PL2303 on /dev/ttyUSB0)
# - added option for different GPIO pin  (default = GPIO 4)
# - code clean-up
#
# version 2.2 / january 2016 / paulvh
# - added support for Domoticz
#
# version 2.3 / February 2016 / paulvh
# - change matching algorithm
#
# Version 3.0 / October 2019 / paulvh
# - removed onedrivep and use onedrive
# - changed default parameters to include
# - changed prefix to SML3
# - changed default device (/dev/ttyUSB0) and pin (26)
# - allow verbose selection
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

import sys, time, argparse
from smartprog import *

# set local variables
DISVERS = "version 3.0"      # display version
SAVERAW = './logs/RAW'       # prefix for raw file
SAVEFILE = './logs/SML3'     # file to save information (added with month/year)
DOMOFILE = "/tmp/meterinput" # file for domoticz

# status on MeterBuffer
BUF_FL = 0              # continue to fill
BUF_OR = 1              # STOP : error : Buffer overrun
BUF_TO = 2              # STOP : error : Time out error
BUF_OK = 3              # STOP : we are good

# set internal Global variables *************************************************************
buf_stat = BUF_FL       # set when completed adding to MeterBuffer and Ready to start display/save
check_crc = 0           # wait for '!' character from meter before calculate CRC


# reset global variables
def clean_counters(smc):
    global check_crc, buf_stat

    # reset class variables
    smc.reset_cntrs()

    # reset local variables
    check_crc = 0       # CRC capture/check is not actived
    buf_stat = BUF_FL   # Enable filling the buffer

# send output to file for domototicz (obsolete)
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
def main():
    global buf_stat, check_crc

    lang = 'nl'             # Display language,for supported languages check py
    dis_buf = 0             # -d option
    sel_state = 1           # -s what need to be save , 1 = selection, 2 = full
    wait_time = 60          # -i wait_time seconds in between reading
    repeat_cnt = 0          # -r how many times (0 = endless loop)
    q_display = 1           # -q work in silent mode (0 = no message displayed)
    device = "/dev/ttyUSB0" # default device
    gpio_pin = 26           # default GPIO pin for RTS
    smc = ""                # holds smartmeter class
    domoticz = False        # True= create output for Domoticz
    Verbose = False

    parser = argparse.ArgumentParser(description="Read a smart meter",
     epilog = "Need special hardware (see installation instruction) and must be run as ROOT",
     prog = "smrdback")

    parser.add_argument("-s", "--save", type=int, help="save: 1 = selection (default), 2 = full information", choices=[1,2],default=1)
    parser.add_argument('--version', action='version', version=DISVERS)
    parser.add_argument("-l","--language", help="Language to use", choices=['nl','uk'],default='nl')
    parser.add_argument("-o", "--output",  help="Do not include OBIS in selected output",action="store_true")
    parser.add_argument("-q","--quiet", help="No message is displayed.", action="store_true")
    parser.add_argument("-d","--display", help="Display info read from meter (no saving to file", action="store_true")
    parser.add_argument("-i", "--wait_time", type=int, help="# seconds between samples. (=> 10 seconds)")
    parser.add_argument("-r", "--repeat_cnt", type=int, help="# of samples to take. default = 0 (endless)")
    parser.add_argument("-v", "--verbose",help="enable verbose messages", action="store_true")
    parser.add_argument("-D","--device", help="device to use (default: /dev/ttyAMA0")
    parser.add_argument("-G","--gpio", help="GPIO pin to use (default: GPIO-4)", type = int)
    parser.add_argument("-O","--domo", help="create file for Domoticz", action="store_true")

    args = parser.parse_args()

    if args.save :      sel_state = args.save

    if args.display:    dis_buf = 1

    if args.repeat_cnt: repeat_cnt = args.repeat_cnt

    if args.domo :      domoticz = True         # create output file for Domoticz

    if args.verbose :   Verbose = True          # enable verbose messages

    if args.wait_time:
        wait_time = args.wait_time
        if wait_time < 10: wait_time = 10       # > 10 seconds given smartmeter specifications

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

    if (Verbose): ("Device: {}, GPIO: {}".format(device,gpio_pin))

    smc = smart_meter(1, device, gpio_pin)      # set up class

    if args.output: smc.skipobis()              # no OBIS code in output
    if args.quiet:  q_display = 0               # set for no display

    smc.setsilent(q_display)

    if(Verbose): printstderr("Save {}, Language {}, Silent {}".format(sel_state,lang,q_display))
    if(Verbose): printstderr("Display {}, repeat_cnt {}, wait_time {}".format(dis_buf,repeat_cnt,wait_time))

    try:
        smc.set_rts(1)                          # raise Request To Sent

        if (Verbose): printstderr ("starting. RTS raised")

        while True :

            if smc.checkser():                  # if anything sent by smart meter

                data = smc.readser()            # read data from meter

                if check_crc > 0:               # is CRC check active ?

                    check_crc = smc.do_crc_check(data,check_crc)

                    if (Verbose): printstderr ("chrc check {}".format(check_crc))

                    if check_crc == 5:          # CRC check passed :-)?
                        buf_stat = BUF_OK       # stop adding / start reading buffer
                        smc.set_rts(2)          # remove request signal from meter
                        smc.flushser()          # flush any input pending from smart meter
                        check_crc = 0           # reset CRC Check

                    if check_crc == 6:          # CRC check failed :-(?
                        smc.set_rts(2)          # Remove request signal from meter
                        time.sleep(5)           # wait 5 seconds (settle situation)
                        smc.flushser()          # flush any input pending from smart meter
                        clean_counters(smc)     # reset local and global variables
                        smc.set_rts(1)          # try again input meter

                elif buf_stat == BUF_FL:        # still able add to meter buffer ?

                    if smc.addmeter(data):      # add data (0 = good)
                        buf_stat = BUF_OR       # set buffer overrun

                    # if last character of datastream (before CRC info)
                    if data == '!':             # actived CRC check
                        check_crc = 1

                                                # Overrun or Timeout, reset connection and try again
            if (buf_stat == BUF_OR) or (buf_stat == BUF_TO):

                msg = "e6" + str(buf_stat)      # display right message
                printstderr(dlm(msg))
                smc.set_rts(2)                  # remove request signal from meter
                time.sleep(5)                   # wait 5 seconds (settle situation)
                smc.flushser()                  # flush any input pending from smart meter
                clean_counters(smc)             # reset different counters/variables
                smc.set_rts(1)                  # try again input meter

            elif buf_stat == BUF_OK:            # start analysing buffer, all characters received & CRC = OK

                if (Verbose): printstderr ("start analysing")

                if dis_buf:                     # display buffer was requested ?
                    print(smc.getmbuf())

                else:
                    if domoticz:                # need to create output for domoticz ?
                        create_domoticz(smc)

                    if (Verbose): printstderr ("start saving {}".format(sel_state))

                    if sel_state == 2:          # option -s 2 : save all to file
                        smc.output_line(smc.getmbuf())
                        smc.output_line('\n')

                        if (smc.save_info(SAVERAW)):    # save information to file
                            if (Verbose): printstderr ("Error: issue during saving")

                    elif sel_state == 1:        # option -s 1 : selective saving

                        if (smc.detect_obis_codes()):   # include lines with a match
                            if (Verbose): printstderr ("Error: issue during selecting")

                        elif (smc.save_info(SAVEFILE)): # save selected information to file
                            if (Verbose): printstderr ("Error: issue during saving")

                # repeat_cnt and wait_time check
                if repeat_cnt > 0:              # repeat_cnt again ?(zero = endless),
                    repeat_cnt -= 1             # subtract the last pass

                    if (Verbose): printstderr ("repeat counter {}".format(repeat_cnt))

                    if repeat_cnt == 0:         # if we are done, close out
                        smc.close_meter()
                        sys.exit(0)

                if(Verbose): printstderr("Timeout for {} seconds".format(wait_time))

                time.sleep(wait_time)           # sleep the requested seconds
                clean_counters(smc)             # reset external and internal global counters
                smc.flushser()                  # flush any noise that might have happened
                smc.set_rts(1)                  # raise Request To Sent

            # Timeout control, if write counter stays the same for more than X amount of passes
            if smc.checkTO():                   # If timeout ?
                buf_stat = BUF_TO               # stop adding enable display

    except KeyboardInterrupt:
        if q_display: printstderr(dlm('e9'))
        if (smc): smc.close_meter()
        sys.exit(1)

    except Exception, e:
        if q_display: printstderr("Exception : {}". format(e))
        if (smc): smc.close_meter()
        sys.exit(1)

if __name__ == "__main__":
    main()
