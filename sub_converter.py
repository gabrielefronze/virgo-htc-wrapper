#! /usr/bin/env python3

import os
import os.path
import stat
from pathlib import Path
from fastlog.python.fastlog import *

required_input_files = ["./satel_lite", "./proxyrearm"]
CVMFS_repo_path = "/cvmfs/virgo.ego-gw.it/tests/virgo-htc-wrapper"

def getConvertedSubPath(input_sub_file_path : Path):
    output_sub_file_path_parts = list(input_sub_file_path.parts)
    output_sub_file_path_parts[-1] = "converted-"+output_sub_file_path_parts[-1]
    output_sub_file_path = Path('/'.join(output_sub_file_path_parts).replace('//','/'))

    return output_sub_file_path

def is_file(fpath):
    return os.path.isfile(fpath)

def is_exe(fpath):
    return os.access(fpath, os.X_OK)

def is_abs_path(fpath):
    return fpath == os.path.abspath(fpath)

def getScriptPath(input_sub_file_path : Path):
    script_path_parts = list(input_sub_file_path.parts)
    script_path_parts[-1] = ("wrapper-script-"+script_path_parts[-1]).replace('.sub','.sh')
    script_path = Path('/'.join(script_path_parts))

    return script_path, './'+script_path_parts[-1]

def purgeLineHeader(line):
    new_line = line.split('=')[-1]
    if new_line[0] is ' ':
        new_line = new_line[1:]
    return new_line.rstrip("\n\r")

def convertSub(sub_file_path, worker_node_log_dir = None, main_executable_name = None, ignore_exe_not_found=False, useCVMFS=False):
    input_sub_file_path = Path(os.path.abspath(sub_file_path))
    output_sub_file_path = getConvertedSubPath(input_sub_file_path)
    script_path, script_path_relative = getScriptPath(input_sub_file_path)

    input_sub = open(input_sub_file_path,"r")

    executable_string = ''
    input_files = ''
    output_files = ''
    arguments = ''

    input_files_found = False
    output_files_found = False
    arguments_found = False

    for line in input_sub:
        if line.startswith("executable"):
            executable_string = purgeLineHeader(line)
        elif line.startswith("transfer_input_files"):
            input_files_found = True
            input_files = purgeLineHeader(line)
        elif line.startswith("transfer_output_files"):
            output_files_found = True
            output_files = purgeLineHeader(line)
        elif line.startswith("arguments"):
            arguments_found = True
            arguments = purgeLineHeader(line)

    if executable_string == "run-with-proxy-satellite.py":
        fastlog(ERROR, "ERROR: this file has already been reworked!")
        input_sub.close()
        return

    if input_files_found:
        input_files = input_files+','

    input_sub.seek(0)
    
    output_sub = open(output_sub_file_path, "w+")

    output_script = open(script_path, "w+")
    output_script.write('#! /bin/bash\n')

    if is_file(executable_string):
        if is_exe(executable_string):
            if not is_abs_path(executable_string):
                fastlog(DEBUG,"The file is executable but need the prepention of \"./\"")
                executable_string = './'+executable_string
        else:
            fastlog(WARNING,"Warning: {} is not (an) executable. Try running \"chmod +x {}\"".format(executable_string,executable_string))
            return
    else:
        if not ignore_exe_not_found:
            fastlog(ERROR,"Error: the executable cannot be located. Aborting.")
            return
        else:
            if not is_abs_path(executable_string):
                fastlog(DEBUG,"The file is executable but need the prepention of \"./\"")
                executable_string = './'+executable_string


    output_script.write(executable_string+' '+arguments)
    output_script.write("\n\n")
    output_script.close()
    st = os.stat(script_path)
    os.chmod(script_path, st.st_mode | stat.S_IEXEC)

    virgo_wrapper = "run-with-proxy-satellite.py"
    new_input_files = input_files+script_path_relative+",./plainproxy.pem"

    if useCVMFS:
        virgo_wrapper="."+CVMFS_repo_path+"/"+virgo_wrapper
    else:
        new_input_files = new_input_files+','+','.join(required_input_files)

    new_input_files = new_input_files+"\n"

    for wline in input_sub:
        if wline.startswith("executable"):
            output_sub.write("executable = {}\n".format(virgo_wrapper))
            if not input_files_found:
                output_sub.write("transfer_input_files = "+new_input_files)
            if not output_files_found and worker_node_log_dir:
                output_sub.write("transfer_output_files = "+worker_node_log_dir+"\n")
            if not arguments_found:
                output_sub.write("arguments = "+script_path_relative)
        elif wline.startswith("transfer_input_files"):
            output_sub.write("transfer_input_files = "+new_input_files)
        elif wline.startswith("arguments"):
            output_sub.write("arguments = "+script_path_relative)
        elif wline.startswith("transfer_output_files"):
            if worker_node_log_dir:
                output_sub.write("transfer_output_files = "+output_files+','+worker_node_log_dir+"\n")
            else:
                output_sub.write(wline) 
        else:
            output_sub.write(wline)
    
    output_sub.write("\n")

    fastlog(DEBUG, "Reworked .sub file at: "+output_sub_file_path.as_posix())

    output_sub.close()
    input_sub.close()

    return output_sub_file_path

if __name__ == "__main__":
    convertSub("standard.sub", main_executable_name = "my-pipeline", worker_node_log_dir="./logs", ignore_exe_not_found=True, useCVMFS=True)