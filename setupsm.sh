#! /bin/bash
# version 2.0 / paulvha / january 2016
# create utilities
#
# version 2.1 / paulvha / february 2016
# include domo-update()
#
# Version 2.4 / April 2017 / paulvha
# - removed support for domoticz
# - included support for systemd startup
# - changed default parameters
#
# Version 3.0 / October 2019 / paulvh
# - removed onedrivep and use onedrive
# - changed default parameters to include
#******************************************************

cmd_dir="/usr/local/bin/"       # where to store command
cur_dir=`pwd`                   # current directory
com_file="sm_command"           # name of central command

# overview of available commands
utilities="smread
smrdback
obislct
"

disp_usage() {
    echo "$0 [inst|remove]"
    echo "  inst = install smartmeter utilities"
    echo "  remove = remove smartmeter utilities"
    exit 1
}

create_shell_cmd() {                        # create the shell commands
    command_template=$cur_dir/$com_file

    sudo chmod +x $command_template

    for i in $utilities
    do
      echo "creating $comd_dir$i"
      sudo link $command_template $cmd_dir$i
    done
}

remove_shell_cmd() {                        # remove the shell commands
    for i in $utilities
    do
        echo "removing $comd_dir$i"
        sudo rm -f $cmd_dir$i
    done
}

make_command_file(){                        # create central command file

    echo "#!/bin/bash
# version 1.0 / paulvha / january 2016
# passing from shell to smartmeter python utilities
# created with setupsm.sh

# smartmeter directory
smartmeter_dir=$cur_dir

# goto the SmartMeter directory
cd \$smartmeter_dir

# remove pathname
name=\` basename \$0 \`

# create the full pathname to the command
od_com=\$smartmeter_dir/\$name\".py\"

# start the utility with the parameters
/usr/bin/python \$od_com \"\$@\" " > ./$com_file

}

check_onedrive() {                      # check for pip and onedrive
    pip_available=`dpkg -l | grep pip`

    echo "Checking for OneDrive package"

    if ! [ -z "$pip_available" ]; then

        if [ -f /usr/local/bin/onedrive ]; then

            echo "****************************************"
            echo "OneDrive connection package is installed"
            echo "see install.txt to setup for backup"
            echo "****************************************"
        else
            echo "********** onedrive package is not installed **********"
            echo "For using OneDrive as backup : "
            echo "git clone https://github.com/abraunegg/onedrive"
            echo "*******************************************************"
        fi

    else
        echo "***************************************************************"
        echo "pip is NOT installed. That is needed  if you want to install"
        echo "OneDrive connection"
        echo "search internet what the right way is to install on your linux"
        echo "***************************************************************"
    fi
}

if [ "$#" -ne 1 ] ; then
    disp_usage
fi

case $1 in
    inst)
        echo "create central command_file"
        make_command_file

        # set correct permissions (in case it got lost during copy)
        sudo chmod 666 *
        sudo chmod +x svlogfile svlogfile_od add_initd setupsm.sh sm_command smread.py smrdback.py
        sudo chmod 777 logs smartprog

        echo "creating shell commands"
        create_shell_cmd


        # check for onedrive
        check_onedrive

        echo "************************************"
        echo "please make sure to read install.txt"
        echo "************************************"
        ;;
    remove)
        echo "deleting shell commands."
        remove_shell_cmd

        echo "**************************************"
        echo "please make sure to read uninstall.txt"
        echo "**************************************"
        ;;
    *)
        disp_usage
        ;;
esac

echo "finished"
