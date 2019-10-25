 Smartmeter             Version 3.0             Ocotber 2019


Utilities to read the Dutch Smartmeter with Raspberry Pi written in Python

These are all command-line utilities without graphical interface to allow for fast remote access and background usage.

Typically the Raspberry would be close to the meter and accessed with SSH or Putty.

While this version works good, development to extend and bug-fixing is still happening.

## Introduction

The following information is available after installation:
### installation support
add_initd     =  used during installation to update /etc/init.d
setupsm.sh    =  install or remove running programming
install.txt   =  instructions for installation and setup
hardware.txt  =  detailed information around the hardware
meter.txt     =  overview of potential OBIS codes
onedrive.txt  =  install onedrive correctly for smartmeter

### running programs
svlogfile_od  =  save log-files to OneDrive
svlogfile     =  save log-file to local network share
smread.py     =  let user to interactive display and save information from smartmeter
smrdback.py   =  program to capture smartmeter output in the background
obislct.py    =  let user select specific data to save in log filename
sm_command    =  program to start other Python program
onedrive.service = for system wide constant update of onedrive

### Other documentation
uninstall.txt =  instructions to de-install and remove software
program.txt   =  detailed information around software


## Motivation

I wanted to better understand the electricity consumption by hour/day to take
action for reduction.
This was a first project in IOT, Raspberry and Python. It needed some extra
hardware (which is described in the documentation). The data captured is
analysed with Microsoft Office (access and Excel).

### TODO Lists

- update program flow based on the later learnings
- To be decided: “cloud” connection with Azure and their analytics
- include information about the Microsoft Access and Excel usage

## Dependencies

For OneDrive you need to install: https://github.com/abraunegg/onedrive
See document OneDrive.txt

## Installation

The included install.txt has the steps documented for installation and setup.
For detailed information about the software see program.txt.

## De-installation

The included uninstall.txt has the steps documented for removing the setup and software

## Architecture
All programs are stored in smartmeter directory, written in python 2.7 and supporting shell scripts

The central routines to obtain information from the smartmeter are stored in a Class Smeter.

There are 3 user level programs :
  To read and store the information interactive : smread
  To select the data to be stored by smrdback   : obislct
  Background program (eg. to run from crontab)  : smrdback

The commands will be created in /usr/local/bin if the procedure in install.txt is followed correctly

Only gathering of the data is performed, written to log file(s) and enabling upload to
more powerful analytical systems and tools (eg. with Microsoft office tools)

## Change-log

## version 2.1: December 2015 / first published version.
 * written in Python 2.7

## version 2.11: January 2016
 * added support for different device (-D), different GPIOpin (-G)
 * code optimization of the different python programs
 * enhancements made to installation scripts to make it easier.

## version 2.2: January 2016
 * added support for Domoticz (-O)

## version 2.3: february 2016
 * updated the selection alogrithm (MUCH easier)
 * add domo_update, to update a (dummy) SmartMeter in Domoticz
 * update to shells script to handle domo_update

## Version 2.4 / May 2017
 - removed support for domoticz
 - included support for systemd startup
 - changed default parameters

## Version 3.0 / October 2019
 - removed onedrivep and use onedrive
 - changed default parameters to include
 - changed prefix to SML3
 - changed default device (/dev/ttyUSB0) and pin (26)

## What is the reference environment?
You will need at least 1GB for the onedrive compile
The program is tested on Raspberry Pi with Raspbian/Debian/ jessie

## Contact

Paul van Haastrecht
paulvha@outlook.com
