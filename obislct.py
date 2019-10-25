#! /user/bin/python

#*****************************************************************
# obislct.py
#
# This is the supporting program to make a selection of the data to
# be saved from the smartmeter. After this file has been created or
# updated the smartmeter program (smrdback.py or smread.py) has to
# be restarted.
#
# version 2.0 / september 2015 / paulvh
# initial version
#
# version 2.1 / january 2016 / paulvh
# - code clean-up
#
# version 2.2 / february 2016 / paulvh
# - support layout for new (easier) algorithm in smprog.py
# - program flow adjustments
#
# Version 3.0 / October 2019 /paulvh
# - removed onedrivep and use onedrive replicator
# - changed default parameters to include
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
#*****************************************************************

import os, sys, argparse
from smartprog import *

# set constants
DISVERS="Version 3.0"               # -v for display version
BANNERMSG="# Contains OBIS codes to be selected \n\
# include the OBIS code for the information that need to be saved.\n\
# use OBIS documentation in P1 or P3 companion standard\n\
# Description is free text and is not used elsewhere. \n\
# This file can be updated with text editor or obislct.py util \n\
# code1-code2:code3.code4.code5[ description \n\
# \nSEE METER.TXT FOR POTENTIAL OBIS CODES TO USE\n\n\
# The OBIS code for meter timestamp (0-0:1.0.0) is hard coded to be\
# added by default.\n\n"

# set global variables
lang = 'nl'                     # display language,for supported languages check dsmm.py
q_display = 1                   # -q work in silent mode (0 = no message displayed)
output_sel_buffer = ""          # hold entry for output
input_selection = ""            # hold (current) parsed OBIS codes

"""
save Obis selection information to a file
returncodes:
    0 = succesfull
    1 = Error during writing

"""
def save_output():

    for savecount in range (0,5):               # try 5 times to save

        savefile = open(OBISFILE,'w')           # open for writing

        if (savefile):
            savefile.write(BANNERMSG)           # write standard banner
            savefile.write(output_sel_buffer)   # save selection made
            savefile.close()

            return 0                            # succesfull save
        else:
            if q_display: print(dlm('e3').format(savecount,OBISFILE,"."))

    return 1


# make yes/no answer language independent
# needs an entry for each new language

def yncheck(check):

    check = check.upper()
    if lang == 'nl':                        # if Dutch
        if check == 'J':    return('y')
        elif check == 'N':  return('n')

    if lang == 'uk':                        # if english
        if check == 'Y':    return('y')
        elif check == 'N':  return('n')

    return('')                              # invalid answer

# validate OBIS Codes in the current list are still valid

def validate_codes():
    global input_selection, output_sel_buffer

    ObisSel = input_selection.splitlines()

    for entry in range(0,len(ObisSel)):     # for all current selections

        select_line = ObisSel[entry]        # get the current one

        while True:

            print(select_line)
            choice = raw_input(dlm('o15'))  # want to keep ?

            if yncheck(choice) == 'y':      # keep entry
                output_sel_buffer += select_line + '\n'
                break

            elif yncheck(choice) == 'n':    # if you don't want to keep

                while True:
                    check = raw_input(dlm('o16')) # are you sure ?

                    if yncheck(check) == 'y':
                        break

                    elif yncheck(check) == 'n': # no, keep it
                        output_sel_buffer += select_line + '\n'
                        break
                    else:
                        print (dlm('e5'))   # invalid entry
                break
            else:
                print (dlm('e5'))           # invalid entry

# get new OBIS codes input

def get_new_codes():

    global output_sel_buffer

    while True:                         # print start message to get Obis code
        print (dlm('o1'))
        print (dlm('o2'))
        input_Obis = raw_input("> ")

        if input_Obis == "" : break     # if empty => stop getting new codes

        temp_store = ""

        num_obis = len(input_Obis.split())

        if num_obis == 5:               # need 5 OBIS codes

            for x in range(0,num_obis): # check all codes are digits

                if input_Obis.split()[x].isdigit() == True:

                    if x  == 0:         # add delimiters
                        temp_store += input_Obis.split()[x] + "-"
                    elif x == 1:
                        temp_store += input_Obis.split()[x] + ":"
                    elif x == 4:
                        temp_store += input_Obis.split()[x]
                    else:
                        temp_store += input_Obis.split()[x] + "."

                else:                   # not digit / q_display error
                    print(dlm('o3').format(input_Obis.split()[x]))
                    good_obis = 0
        else:
            print(dlm('o4'))            # not 5 OBIS codes
            continue

        output_sel_buffer += temp_store

        print (dlm('o5'))               # now add description
        input_Obis_desc = raw_input("> ")

                                        # if empty, add default
        if input_Obis_desc == '': input_Obis_desc = dlm('o17')
                                        # add comment delimiter
        output_sel_buffer += "[ " + input_Obis_desc + '\n'

######################################################################
# program starts here
######################################################################
def main():

    global q_display, input_selection, output_sel_buffer

    parser=argparse.ArgumentParser(description="Create selection file",
        prog="obislct")

    parser.add_argument('--version', action='version', version=DISVERS)
    parser.add_argument("-l","--language", help="language to use", choices=['nl','uk'],default='nl')
    parser.add_argument("-q","--quiet", help="no error message is displayed", action="store_true")

    args = parser.parse_args()

    smc = smart_meter(0)                    # set up class but no GPIO or Serial line

    # set silent or q_display
    if args.quiet:  q_display = 0
    smc.setsilent(q_display)

    # set language
    if args.language: lang = args.language  # if different requested
    setdlang(lang)

    try:

        ret = smc.read_obis_file()          # try to read from existing file

        if ret == 1:                        # empty or not exsistent
            if q_display: print(dlm('o6'))

        elif ret == 2:                      # read error
            if q_display: print (dlm('o7').format(OBISFILE))
            if q_display: print (dlm('o8'))
            smc.close_meter()
            sys.exit(1)

        elif ret == 0:
            smc.fill_obis_tbl(True)         # parse file information to table ( True is keep comments)

            input_selection = smc.get_obis_info() # get parsed OBIS requested table


            if input_selection != "":
                print (dlm('o9'))

        while True:

            if input_selection != "":       # decide which of current entries to keep (if any)
                validate_codes()

            get_new_codes()                 # add any new entries to the SaveBuffer

            print (dlm('o10'))              # display current values

            print (output_sel_buffer)

            print (dlm('o11'))              # display options for entry

            while True:
                inp = raw_input(dlm('o12'))

                inp = inp.upper()

                if inp == 'E':              # exit ?

                    while True:             # sure ??
                        check = raw_input(dlm('o13'))

                        if yncheck(check) == 'y':
                            smc.close_meter()# close meter class
                            sys.exit(0)
                        elif yncheck(check) == 'n':
                            break
                        else:
                            print (dlm('e5'))

                elif inp == 'S':            # save?

                    ret = save_output()     # write SaveBuffer to file

                    if ret:                 # error
                        if q_display: print(dlm('e14'))
                        smc.close_meter()   # close meter class
                        sys.exit(1)

                    else:                   # save was succesfull
                        if q_display: print(dlm('o14').format(OBISFILE))
                        smc.close_meter()   # close meter class
                        sys.exit(0)

                elif inp == 'C':            # Change ?
                    input_selection = output_sel_buffer     # moving output table to input table
                    output_sel_buffer = ""  # clean output table
                    break

                else:                       # not a correct entry
                    print (dlm('e5'))

    except KeyboardInterrupt:
        printstderr(dlm('e9'))
        raise
        sys.exit(1)

    except Exception, e:
        if smc : smc.close_meter()  # close meter class
        printstderr("Exception : %s" % str(e))
        sys.exit(1)

if __name__ == "__main__":
    main()
