#!/usr/bin/python3
from multiprocessing import Pool
import os
import socket
import sys

from utils import config

def recv_result_to_file(sock, vm_ip, filename):
    with open(filename, "w") as outf:
        done = False
        result = ''
        while not done:
            new_data = sock.recv(4096).decode('utf-8')
            if len(new_data) == 0:
                done = True
            result += new_data
            lines = result.splitlines()
            for line in lines[:-1]:
                if line == '':
                    continue
                line = "vm"+ str(config.vm_ip_to_id(vm_ip)) + ":" + line
                outf.write(line)
                outf.write('\n')
            
            if len(result) > 0:
                # If the last line of data we got from the server ended in a newline, we should
                # treat it as a complete line, otherwise keep it for the next round.
                if result[-1] == '\n':
                    line = "vm"+ str(config.vm_ip_to_id(vm_ip)) + ":" + lines[-1]
                    outf.write(line)
                    outf.write('\n')
                    result = ''
                else:
                    result = lines[-1]

def run_command_on_one_vm(command_tuple):
    # This function should run all of the grep we need for a single VM. We can run this code
    # once for each VM in parallel.
    vm_ip, command = command_tuple
    vm_id = config.vm_ip_to_id(vm_ip)
    
    # Replace the keyword __VM_ID__ in the command string with the VMs ID number.
    command = command.replace("__VM_ID__", str(vm_id))

    # Open up a socket and connect it to the remote VM.
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    
    try:
        sock.connect((vm_ip, config.DEFAULT_PORT))
        # Send the command to the grep daemon.
        #print("VM %s running command: %s" % (vm_ip, command))
        sock.send(command.encode())

        intermediate_filename = config.DEFAULT_INTERMEDIATE_FILENAME.replace("__VM_ID__", str(vm_id))
        recv_result_to_file(sock, vm_ip, intermediate_filename)
    except Exception as e:
        print("FAILURE ON VM %s: Command %s not run!" % (vm_ip, command))
        print(e)

def run_command_on_all_vms(command, combine_logs=False):
    os.system("rm %s" % config.DEFAULT_INTERMEDIATE_FILENAME.replace("__VM_ID__", "*"))
    command_list = [(vm_ip, command) for vm_ip in config.VM_IP_LIST]
    with Pool(config.VM_COUNT) as proc_pool:
        proc_pool.map(run_command_on_one_vm, command_list)
    if combine_logs:
        combine_intermediate_results() 

def combine_intermediate_results():
    files_to_combine = ""
    vm_ids = [config.vm_ip_to_id(ip) for ip in config.VM_IP_LIST]
    for vm_id in vm_ids:
        files_to_combine += " " + config.DEFAULT_INTERMEDIATE_FILENAME.replace("__VM_ID__", str(vm_id))
    os.system("cat %s > dgrep_result.txt" % files_to_combine)

if __name__ == '__main__':
    run_command_on_all_vms(sys.argv[1], True)
