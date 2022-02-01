#!/bin/bash

# Goal:  To log out users $waitTime seconds after the screensaver starts.
# Execution: attempt to read the idleTime of managed screensaver settings and perform a reboot
# Reboot $waitTime after the screensaver has started if there is no USB input and the OS has
# not prevented display sleep because of certain applications.  If no managed screensaver 
# settings are found, can use $altTime seconds instead.

# Define log file and send stdout and stderr to this log
LOG_FILE=/Users/Shared/.idleRebootLog.txt
exec 3>&1 1>>${LOG_FILE} 2>&1

# Constants to modify:

altTime=900		# if screensaver settings not readable
pollEvery=60	# how often to run idle check in seconds, performance tweak here
waitTime=300		# amount of time after alternate or screensaver timer to take action in seconds

loggedInUser=`id -un`

ssplist=/Library/Managed\ Preferences/com.apple.screensaver.user.plist

# Confirm screensaver plist file exists, or default to alternate time
if [ -e "$ssplist" ]; then
	
	# read screensaver start time from system plist
	ssTime=$(defaults read "$ssplist" idleTime) 
	
	# Did we get a usable value from the plist?
	if [ "$ssTime" -lt "59"]; then
		ssTime=$altTime 
	fi

else

	echo "WARN - plist does not exist"
	ssTime=$altTime  # set to alternate time

fi

# Actiontime is screensaver + waitTime, so action should happen $waitTime after screensaver starts.
actionTime=$((ssTime+waitTime)); 
echo "ActionTime is: $actionTime"

# idle checking script from https://apple.stackexchange.com/questions/104967/launch-app-with-automator-when-system-is-idle

while sleep $pollEvery; do

	# checking PreventUserIdleDisplaySleep to see if a video is being watched, 1 don't sleep, 0 ok to sleep
	mode=$(pmset -g assertions | awk '/PreventUserIdleDisplaySleep/{print $2}')

	# checking time in seconds since last USB device input
	idle=$(ioreg -c IOHIDSystem | awk '/HIDIdleTime/{printf "%i",$NF/1000000000;exit}')
  
  	# If no USB input in $screensaverTime + $waitTime then its time to reboot
	if [[ $idle -ge $actionTime ]] && [[ $mode = 0 ]]; then
		# Now assuming system is idle and unused
		echo "Current logged in user: $loggedInUser"
		echo "Idle time is now $idle"
		cdate=`date`
		echo "Restarting machine at $cdate"
		wait 2
		shutdown -r now
  	else
		# assume system is being used
	fi

done
