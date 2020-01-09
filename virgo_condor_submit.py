#! /usr/bin/env python3

import os.path
from pathlib import Path
import subprocess
import readline, glob

from proxyrearm.python.shouldrenew import getRemainingValidity
from proxyrearm.python.getvomsproxy import getVOMSProxy
from proxyrearm.python.generateplainproxy import generatePlainProxy
from sub_converter import convertSub

def complete(text, state):
    return (glob.glob(text+'*'+".sub")+[None])[state]

valid = {"yes": True, "y": True, "ye": True, "no": False, "n": False}
def askQuestion(question, tabbing=''):
    while True:
        answer = input(tabbing+question+" [N/y] ")
        if answer in valid:
            return valid[answer]
        else:
            print(tabbing+"Unsupported. Defaulting to No.")
            return False

def generateVOMSProxyIfNeeded():
    remaining_VOMS_time = getRemainingValidity()
    print("Current VOMS proxy lasts for {} seconds.".format(remaining_VOMS_time))
    if askQuestion("Is it enough?"):
        print("Skipping VOMS proxy creation.")
    else:
        print("Creating VOMS proxy for submission...")
        command = "voms-proxy-init --voms virgo:/virgo/virgo"
        subprocess.call(command.split())

def convertSubfile():
    readline.set_completer_delims(' \t\n;')
    readline.parse_and_bind("tab: complete")
    readline.set_completer(complete)
    sub_file = input('.sub file path? ')
    convertSub(sub_file)

if __name__ == "__main__":
    print()
    print("---> Checking VOMS proxy status...")
    print()
    generateVOMSProxyIfNeeded()        

    print()
    print("---> Creating 7 days long plain proxy to ship with the submitting job...")
    print()
    generatePlainProxy("./plainproxy.pem", 168)

    print()
    print("---> Reworking .sub file to run the executable with proxy renewal sidecar...")
    print()
    convertSubfile()

    print()
    print("---> Submitting via condor_submit...")
    print()
