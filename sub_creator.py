#! /usr/bin/env python3

import os
import os.path
import shutil
import stat
import argparse
from fastlog.python.fastlog import *
from file_test_utils import is_file, is_abs_path, is_directory
from gwdatafind import connect
from proxyrearm.python.shouldrenew import shouldRenew
from proxyrearm.python.generatevomsproxy import generateVomsProxy

def parseFFL(path):
    ffl = open(path, 'r')
    fileListBuffer = []

    for line in ffl:
        sline = line.rstrip("\n")
        if is_file(sline):
            fileListBuffer.append(sline)
        else:
            fastlog(ERROR,"File {} not found. Skipping.".format(sline))
    
    ffl.close()

    return fileListBuffer

GWDataFindInitialized = False
GWDataFindServer = "datafind.ligo.org:443"
GWDataFindConn = None
GWDataFindObservatories = []
GWDataFindTypes = {}

def initGWDataFind(enforce=False):
    global GWDataFindInitialized
    if not GWDataFindInitialized or enforce:
        fastlog(INFO,"Initializing GWDataFind connection.")
        if shouldRenew():
                fastlog(INFO, "Creating new VOMS proxy or VO=virgo:virgo/virgo and 48h validity.")
                generateVomsProxy("virgo:virgo/virgo", 48)
        
        global GWDataFindConn
        GWDataFindConn = connect(GWDataFindServer)
        
        global GWDataFindObservatories
        GWDataFindObservatories = GWDataFindConn.find_observatories()
        
        global GWDataFindTypes
        GWDataFindTypes = {}
        for obs in GWDataFindObservatories:
            GWDataFindTypes[obs] = GWDataFindConn.find_types(obs)
        
        GWDataFindInitialized = True

class GWQuery:
    def __init__(self, observatory, frametype=None, GPSTSStart=None, GPSTSStop=None):
        if frametype and GPSTSStart and GPSTSStop:
            self.observatory = observatory
            self.frametype = frametype
            self.GPSTSStart = GPSTSStart
            self.GPSTSStop = GPSTSStop
        else:
            sstring = observatory.split()
            try:
                self.observatory = sstring[0]
                self.frametype = sstring[1]
                self.GPSTSStart = (int)(sstring[2])
                self.GPSTSStop = (int)(sstring[3])
            except ValueError:
                fastlog(ERROR,"Wrong input string for GWDataFind query generation: {}".format(str))

    def validateQuery(self):
        initGWDataFind()

        if self.observatory in GWDataFindObservatories:
            if self.frametype in GWDataFindTypes[self.observatory]:
                return True
            else:
                fastlog(ERROR,"Dataframe type is not valid. Aborting.")
                raise ValueError("Dataframe type is not valid.")
        else:
            fastlog(ERROR,"Observatory name is not valid. Aborting.")
            raise ValueError("Observatory name is not valid.")
        return False
    
    def print(self):
        print("Obs: {}, Type: {}, GPSStart: {}, GPSStop: {}".format(self.observatory, self.frametype, self.GPSTSStart, self.GPSTSStop))


def queryGWDataFind(query : GWQuery):
    if shouldRenew():
        fastlog(INFO, "Creating new VOMS proxy or VO=virgo:virgo/virgo and 48h validity.")
        generateVomsProxy("virgo:virgo/virgo", 48)

    if not query.validateQuery():
        fastlog(ERROR,"GWDataFind query not valid. Aborting.")
        raise ValueError("GWDataFind query not valid. Aborting.")
        return

    initGWDataFind()

    return GWDataFindConn.find_urls(query.observatory, query.frametype, query.GPSTSStart, query.GPSTSStop)


def getGWDataFindQueries(query):
    urls = queryGWDataFind(query)
    fastlog(DEBUG, "Found {} files".format(len(urls)))
    queries = []
    for url in urls:
        GPSTimeframeStart = [int(X) for X in url.split('-') if X.isdigit()][-1]
        queries.append("gwdata://{}-{}-{}-{}".format(query.observatory, query.frametype, GPSTimeframeStart, GPSTimeframeStart+1))

    return queries

def createDir(path):
    try:
        os.stat(path)
    except:
        fastlog(INFO, "Creating output dir: {}".format(path))
        os.makedirs(path)


def combineLists(args):
    filesLists = []

    if args.gwdatafind:
            fastlog(INFO, "Using GWDataFind to obtain input files.")
            queries = args.gwdatafind.split(':')
            for query in queries:
                filesLists.append(getGWDataFindQueries(GWQuery(query)))

    if args.ffl:
        fastlog(INFO, "Using FFL-defined input files.")
        ffls = args.ffl.split(':')
        for ffl in ffls:
            if not is_file(ffl):
                fastlog(ERROR, "FFL file not found at {}. Aborting.".format(args.ffl))
                return -1
            fastlog(INFO, "Parsing FFL file {} to obtain input files.".format(ffl))
            filesLists.append(parseFFL(ffl))

    fastlog(INFO, "Obtained {} lists.".format(len(filesLists)))
    for i, filesList in enumerate(filesLists):
        fastlog(INFO, "\tObtained {} files in list {}.".format(len(filesList), i+1))

    fastlog(INFO, "Generating input lists and submit files from template .sub .")
    inputs = zip(*filesLists)

    return inputs


def generateSubmitFiles(originalsub, inputs):
    outDir = args.output
        
    if not is_directory(outDir):
        createDir(outDir)
    else:
        fastlog(WARNING, "Provided output directory already there.")
        input("Press Enter to overwrite. Ctrl-C to abort.")
        shutil.rmtree(outDir)
        createDir(outDir)
    
    inputFound = False

    for j, inpt in enumerate(inputs):
        originalsub.seek(0)

        fastlog(DEBUG, "\tInput list {}: {}".format(j, inpt))

        newSubDir = outDir+"/"+str(j)+"/"
        createDir(newSubDir)
        newSubPath = newSubDir+args.subfile.replace(".sub",".{}.sub".format(j))
        newSub = open(newSubPath, 'w')

        fastlog(DEBUG, "\tReworking file {}".format(j))
        for line in originalsub:
            if line.startswith("transfer_input_files ="):
                inputFound = True

                oldInputs = line.replace("transfer_input_files =",'').rstrip("\n").replace(' ','').split(',')
                
                for oldInput in oldInputs:
                    if not is_abs_path(oldInput) and not oldInput.startswith("gwdata://") and is_file(oldInput):
                        os.symlink(oldInput, newSubDir+os.path.basename(oldInput))
                    else:
                        fastlog(WARNING, "{} is abs path or not found".format(oldInput))

                if oldInputs:
                    newSub.write("transfer_input_files = {}, {}\n".format(', '.join(inpt), ', '.join(oldInputs)))
                else:
                    newSub.write("transfer_input_files = {}\n".format(', '.join(inpt)))
            else:
                newSub.write(line)

        newSub.write("\n")
        newSub.close()

        fastlog(INFO, "\tSubmit file for {} and {} at {}".format(inpt, oldInputs, newSubPath))
    
    originalsub.close() 

    if not inputFound:
        fastlog(ERROR, "No line starting with 'input_file_trasfer' found in template .sub. Aborting.")
        raise BaseException("No valid placeholder for input file found.")
        return

def main(args):
    try:
        inputs = combineLists(args)
    except BaseException:
        fastlog(ERROR, "Errors while handling input files. Aborting.")

    if is_file(args.subfile):
        originalsub = open(args.subfile, 'r')
    else:
        fastlog(ERROR,"Original .sub file not found. Aborting.")
        raise ValueError("Invalid original submit file path.")

    generateSubmitFiles(originalsub, inputs)


    

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='This is a process wrapper wich adds a proxyrearm satellite by default.')
    parser.add_argument("subfile", help="Provide the original .sub template. The input file will be replaced.")
    parser.add_argument('--gwdatafind', '-g', type=str, help="Use GWDataFind query to obtain input files list. Provide query arguments in standard GwDataFind format. For multiple inputs divide each GWDataFind query by ':'.")
    parser.add_argument('--ffl', '-f', type=str, help="Use FFL file. Provide the path of the FFL file to use. For multiple inputs, divide each FFL file path by ':'.")
    parser.add_argument('--output', '-o', type=str, required=True, help="Provide the output folder where generated templates should be placed.")

    args = parser.parse_args()

    main(args)
