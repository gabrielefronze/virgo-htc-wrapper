#! /usr/bin/env python3

import os.path
from pathlib import Path
import subprocess
import readline, glob
import sys

from proxyrearm.python.shouldrenew import getRemainingValidity
from proxyrearm.python.getvomsproxy import getVOMSProxy
from proxyrearm.python.generateplainproxy import generatePlainProxy
from sub_converter import convertSub

def complete(text, state):
    return (glob.glob(text+'*'+".sub")+[None])[state]

valid = {"yes": True, "y": True, "ye": True, "no": False, "n": False}
def askQuestion(question, tabbing='', default=False):
    if default:
        options = " [Y/n] "
    else:
        options = " [N/y] "

    while True:
        answer = input(tabbing+question+options)
        if answer in valid:
            return valid[answer]
        else:
            return default

def generateVOMSProxyIfNeeded(voms_string="--voms virgo:/virgo/virgo"):
    remaining_VOMS_time = getRemainingValidity()
    if not remaining_VOMS_time == 0:
        print("Current VOMS proxy lasts for {} seconds.".format(remaining_VOMS_time))
        if askQuestion("Is it enough?"):
            print("Skipping VOMS proxy creation.")
            return
   
    print("\n---> Creating VOMS proxy for submission...\n")
    command = "voms-proxy-init "+voms_string
    subprocess.call(command.split())

def convertSubfile():
    readline.set_completer_delims(' \t\n;')
    readline.parse_and_bind("tab: complete")
    readline.set_completer(complete)
    sub_file = input('.sub file path? ')
    return convertSub(sub_file)

def condorSubmitWrapper(argv, sub_file_path : Path):
    condor_sub_command = "condor_submit"+' '.join(argv)+" "+sub_file_path.as_posix()
    print(condor_sub_command)
    # subprocess.call(condor_sub_command.split())

if __name__ == "__main__":
    print("\n---> Checking VOMS proxy status...\n")
    generateVOMSProxyIfNeeded()        

    print("\n---> Creating 7 days long plain proxy to ship with the submitting job...\n")
    generatePlainProxy("./plainproxy.pem", 168)

    print("\n---> Reworking .sub file to run the executable with proxy renewal sidecar...\n")
    new_sub_file = convertSubfile()

    print("\n---> Submitting via condor_submit...\n")
    condorSubmitWrapper(sys.argv[1:], new_sub_file)
