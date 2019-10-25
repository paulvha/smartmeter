#!/usr/bin/python
from __future__ import print_function

#*******************************************************
# Display message to screen
#
# version 2.0   / september 2015 /paulvh
# initial version
#
# version 2.0.1 / january 2016 / Paulvh
# added e16
#
# version 2.0.2 / feburary 2016 / paulvh
# added e18, e19
#
# making it easier to localize/change the messages
# for each language a table needs to be made as _xx_codes
# xx = language ( initial version has nl and uk)
#
# if language is added :
# - make new table with correct language
# - update the dml(routine)
# - update the setdlang(routine)
# - update "yncheck" routine in obislct.py
# - update the argparse information in the programs
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
#********************************************************

import sys

# set default language
lang = 'uk'

# To print in color
REDSTR = u"\033[1;31m{0}\033[00m"
GRNSTR = u"\033[1;92m{0}\033[00m"
BLUESTR = u"\033[1;96m{0}\033[00m"
YELSTR = u"\033[1;93m{0}\033[00m"

# table for dutch

_nl_codes = {
    'b0':   "\n 1 = start communicatie. Geselecteerde informatie naar file.\n \
    2 = stop communicatie.\n \
    3 = start communicatie. Laat alles zien (geen opslag naar file).\n \
    4 = start communicatie. Laat alles zien + opslag naar file.\n \
    5 = create file for Domoticz.\n \
    6 = programma afsluiten.\n \n",
    'd0':   "* Info : Meter communicatie debugger actief.",
    'd1':   "* Info : Parser debugger actief.",
    'd2':   "* Info : Selectie debugger actief.",
    'd3':   "* Info : opslaan debugger actief.",
    'e1':   "CRC faalt ! {} was verwacht, maar ontvangen : {}",
    'e2':   "lockfile bestaat, poging {}.",
    'e3':   "Poging {}. Kan bestand {} niet openen of creeren op {}.",
    'e4':   "Bovenstaande informatie was goed ontvangen van de meter.",
    'e5':   "Dat is geen correcte invoer!",
    'e61':  "Buffer overrun tijdens lezen van de meter. \nDe ontvangen informatie wordt alleen getoond voor analyse.\n",
    'e62':  "Time out tijdens lezen van de meter. \nDe ontvangen informatie wordt alleen getoond voor analyse.\n",
    'e7':   "smprog afgesloten op {}.",
    'e8':   "Error : Timeout van verbinding.",
    'e9':   "control-C was ingedrukt.",
    'e10':  "Het bestand {} is niet gevonden.",
    'e11':  "Het bestand {} is leeg.",
    'e12':  "Het bestand {} kan niet worden gelezen.",
    'e13':  "Start obislct.py eerst om de file te maken.",
    'e14':  "Onderzoek de fout. Er kan geen selectie worden bewaard.",
    'e15':  "Lockfile bestaat nu al meer dan een minuut. Proberen gestaakt en geen opslag.",
    'e16':  "Device dat wordt gebruikt: {} en GPIO {}",
    'e17':  "Kan lock bestand {} niet maken",
    'e18':  "Incorrecte OBIS code {} gedetecteerd.",
    'e19':  "Kan geen waarde vinden bij {}. Deze lijn wordt genegeerd.",
    'm1':   "Informatie is opgeslagen in de file op {}.",
    'o1':   "\nVoer 5 OBIS codes in, gescheiden door een spatie (e.g. 1 0 1 8 10)",
    'o2':   "of druk alleen op enter om te stoppen met invoer.",
    'o3':   "Foutieve ingave voor OBIS code: {} is niet toegestaan. Het moet een getal zijn.\nProbeer opnieuw.",
    'o4':   "Foutief aantal voor OBIS code. Het moeten er 5 zijn.",
    'o5':   "\nVoer nu de omschrijving in en druk enter. \nof druk alleen enter voor : <geen omschrijving> toevoeging",
    'o6' :  "Normaal voor een eerste keer of indien verwijderd. We gaan door om een nieuwe file te maken.\n",
    'o7':   "Fout tijdens lezen bestand : {} .",
    'o8':   "We krijgen waarschijnlijk een probleem tijdens schrijven, dus nu eerst dit probleem oplossen.",
    'o9':   "Valideer de huidige entries in de selectie file.\n",
    'o10':  "\nOnderstaand de nieuwe lijst met OBIS selectie codes\n",
    'o11':  "\nSelecteer : s voor opslaan in bestand, c om te veranderen of e om te stoppen zonder opslaan",
    'o12':  "s, c of e gevolgd door enter. ",
    'o13':  "\nWeet u zeker dat u wilt stoppen zonder op te slaan ? (j or n) ",
    'o14':  "Het bestand: {} is opgeslagen.\nZorg dat u het achtergrond programma (smrdback) opnieuw opstart om te activeren.",
    'o15':  "Wilt u deze selectie behouden? (j of n) ",
    'o16':  "\nWeet u zeker dat u deze selectie wilt verwijderen? (j of n) ",
    'o17':  "<geen omschrijving> ",
}


# table for english

_uk_codes = {
    'b0':   "\n 1 = start communication. Selected information will be save to file.\n \
    2 = stop communication.\n \
    3 = start communication. Show all, but no saving to the file.\n \
    4 = start communicatie. Show all AND save to the file.\n \
    5 = create file for Domoticz.\n \
    6 = exit progam.\n\n",
    'd0':   "* Info : Meter communication debugger actived.",
    'd1':   "* Info : Parser debugger actived.",
    'd2':   "* Info : Selection debugger actived.",
    'd3':   "* Info : save/output file debugger active.",
    'e1':   "CRC failed ! {} was expected, but received : {}",
    'e2':   "lockfile exists, attempt {}.",
    'e3':   "Attempt {}. The file {} can not be opened of created at {}.",
    'e4':   "The above information was received correctly from the meter.",
    'e5':   "Not a correct entry!",
    'e61':  "Buffer overrun during reading the smart meter. \n Received information is displayed only for diagnostics.\n",
    'e62':  "Time out during reading the smart meter. \n Received information is displayed only for diagnostics.\n",
    'e7':   "smprog closed on {}.",
    'e8':   "Error : Timeout of connection.",
    'e9':   "control-C was pressed.",
    'e10':  "The file {} does not exist.",
    'e11':  "The file {} is empty.",
    'e12':  "The file {}} can not be read.",
    'e13':  "Run obislct.py first to make file.",
    'e14':  "Fix the issue first. No selective saving can be done.",
    'e15':  "Lockfile existed for more then a minute. Terminating trying to save.",
    'e16':  "Device being used: {} and GPIO {}",
    'e17':  "Can not create lock file {}",
    'e18':  "Incorrect OBIS code {} detected.",
    'e19':  "Can not detect value for {}. entry will be skipped",
    'm1':   "Information has been saved to the file at {}.",
    'o1':   "\nInput 5 OBIS codes seperated with a space (e.g. 1 0 1 8 10)",
    'o2':   "or just press enter to STOP entry of new codes.",
    'o3':   "Incorrect entry for OBIS code: {} is not allowed. Must be a digit.\n Try again.",
    'o4':   "Incorrect amount of OBIS code entries. Must be 5.",
    'o5':   "\nInput the description followed by enter. \nor just press enter for : <no description> entry",
    'o6':   "Normal at first time or when deleted. We continue to create a new file.\n",
    'o7':   "Error during reading file : {} .",
    'o8':   "We could continue but we might get an issue during saving. \nCould be a waste of time so fix the issue first.",
    'o9':   "Validate the current entries in the selection file.\n",
    'o10':  "\nThe following is your new list with OBIS selection codes.\n",
    'o11':  "\nPress s to save to file, c to change, e to exit without saving",
    'o12':  "s, c or e followed by enter. ",
    'o13':  "\nAre you sure to exit without saving? (y or n) ",
    'o14':  "File: {} has been written.\nMake sure to restart the background program (smrdback) to activate new selection.",
    'o15':  "Do you want to keep this entry? (y or n) ",
    'o16':  "\nAre you sure to remove this selection? (y or n) ",
    'o17':  "<no description> ",
}

# print to STDERR (implement future/python 3 comp)
# white, green, blue, yellow and red (= default) are supported
def printstderr(message,dcol = "red"):

    if dcol == "red": message=REDSTR.format(message)
    elif dcol == "green": message=GRNSTR.format(message)
    elif dcol == "blue": message=BLUESTR.format(message)
    elif dcol == "yellow": message=YELSTR.format(message)

    print(message, file=sys.stderr)

# set language
def setdlang(newlang):
    global lang

    if  newlang == 'nl' or newlang == 'NL':
        lang = newlang

    elif newlang == 'uk' or newlang == 'UK':
        lang = newlang

    else:
        return(1)

    return(0)
"""
Display Localized Message

Return string with display message. If code is not in list it will return the optional returnmessage (.....)

messc is set to message to display
"""

def dlm(messc):

    if lang == 'nl' or lang == 'NL':    # create one entry for each language
        _disp_codes = _nl_codes

    if lang == 'uk' or lang == 'UK':
        _disp_codes = _uk_codes

    try :
        return(_disp_codes[messc])

    except Exception, e:
        return(".....")                 # in case error message can not be found



