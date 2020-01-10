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
    sub_file = input('Where is the original .sub file path? ')
    return convertSub(sub_file, worker_node_log_dir="./logs")

def condorSubmitWrapper(argv, sub_file_path : Path):
    condor_sub_command = "condor_submit "+' '.join(argv)+" "+sub_file_path.as_posix()
    print(condor_sub_command)
    # subprocess.call(condor_sub_command.split())

def printSeparator():
    print("/////////////////////////////////////////////////////////////////////////////////////////////////////////////////")

if __name__ == "__main__":
    printSeparator()
    print("\nWelcome to the Virgo HTCondor submitter wrapper!\n")
    print("This tool will perform the following operations:")
    print("  1. Evaluate wether a VOMS x509 proxy is needed for the submission or not and generate it.")
    print("  2. Generate a plain (without VOMS extensions) long lasting x509 proxy to be shipepd with the job.")
    print("  3. Rework your (awesome!) HTCondor submit file to encapsulate your executable inside a proxy rearming service.")
    print("  4. Submit the job using the standard condor_submit: all the arguments of this script will be passed through")
    print("     to the condor_submit command. Therefore the standard HTCondor documentation applies wholefully.\n")

    if askQuestion("Shall we start?", default=True):
        print("\n---> Checking VOMS proxy status...\n")
        generateVOMSProxyIfNeeded()        

        print("\n---> Creating 7 days long plain proxy to be shipped with the submitting job...\n")
        generatePlainProxy("./plainproxy.pem", 168)

        print("\n---> Reworking .sub file to run the executable with proxy renewal sidecar...\n")
        new_sub_file = convertSubfile()

        print("\n---> Submitting via condor_submit...\n")
        condorSubmitWrapper(sys.argv[1:], new_sub_file)

    else:
        print("See you soon!")

    printSeparator()
