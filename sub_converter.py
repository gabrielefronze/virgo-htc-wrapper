#! /usr/bin/env python3

import os.path
from pathlib import Path

required_input_files = ["./satel_lite", "./proxyrearm", "./plainproxy.pem"]

def getConvertedSubPath(input_sub_file_path : Path):
    output_sub_file_path_parts = list(input_sub_file_path.parts)
    output_sub_file_path_parts[-1] = "converted-"+output_sub_file_path_parts[-1]
    output_sub_file_path = Path('/'.join(output_sub_file_path_parts).replace('//','/'))

    return output_sub_file_path

def purgeLineHeader(line):
    new_line = line.split('=')[-1]
    if new_line[0] is ' ':
        new_line = new_line[1:]
    return new_line.rstrip("\n\r")

def convertSub(sub_file_path, worker_node_log_dir = None, main_executable_name = None):
    input_sub_file_path = Path(os.path.abspath(sub_file_path))
    output_sub_file_path = getConvertedSubPath(input_sub_file_path)

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
            # print("executable: "+executable_string)            
        elif line.startswith("transfer_input_files"):
            input_files_found = True
            input_files = purgeLineHeader(line)
            # print("input_files: "+input_files)
        elif line.startswith("transfer_output_files"):
            output_files_found = True
            output_files = purgeLineHeader(line)
            # print("output_files: "+output_files)
        elif line.startswith("arguments"):
            arguments_found = True
            arguments = purgeLineHeader(line)
            # print("arguments: "+arguments)

    if executable_string == "run-with-proxy-satellite.py":
        print("ERROR: this file has already been reworked!")
        input_sub.close()
        return

    new_input_files = input_files+','+','.join(required_input_files)+"\n"
    main_executable_as_args = "\'\"\""+executable_string+' '+arguments.replace('\"', '\\\"').replace('\'', '\\\'')+"\"\"\'"

    if not main_executable_name:
        new_arguments = "\""+main_executable_as_args+"\""
    else:
        new_arguments = "\""+main_executable_as_args+" --name {}".format(main_executable_name.replace(' ',''))+"\""

    new_arguments = new_arguments+"\n"

    input_sub.seek(0)
    output_sub = open(output_sub_file_path, "w+")

    for wline in input_sub:
        if wline.startswith("executable"):
            output_sub.write("executable = run-with-proxy-satellite.py\n")
            # print("executable = run-with-proxy-satellite.py")
            if not input_files_found:
                output_sub.write("transfer_input_files = "+new_input_files)
                # print("transfer_input_files = "+new_input_files)
            if not output_files_found and worker_node_log_dir:
                output_sub.write("transfer_output_files = "+worker_node_log_dir+"\n")
            if not arguments_found:
                output_sub.write("arguments = "+new_arguments)
                # print("arguments = "+new_arguments)
        elif wline.startswith("transfer_input_files"):
            output_sub.write("transfer_input_files = "+new_input_files)
            # print("transfer_input_files = "+new_input_files)
        elif wline.startswith("arguments"):
            output_sub.write("arguments = "+new_arguments)
            # print("arguments = "+new_arguments)
        elif wline.startswith("transfer_output_files"):
            if worker_node_log_dir:
                output_sub.write("transfer_output_files = "+output_files+','+worker_node_log_dir+"\n")
            else:
                output_sub.write(wline)    
        else:
            output_sub.write(wline)
            # print(wline)
    
    output_sub.write("\n")

    print("Reworked .sub file at: "+output_sub_file_path.as_posix())

    output_sub.close()
    input_sub.close()

    return output_sub_file_path

if __name__ == "__main__":
    convertSub("standard.sub", main_executable_name = "my-pipeline", worker_node_log_dir="./logs")