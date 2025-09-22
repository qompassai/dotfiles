#!/usr/bin/env python3
import os
import subprocess
import os.path
from os import path
import argparse
import re

# Create map of NVMe names and BDFs
nvme_map = {}
def create_nvme_map():
    cmd = "lsblk -o NAME,KNAME,MAJ:MIN,TRAN | grep nvme | awk '{print $1}'"
    output = subprocess.run([cmd], capture_output=True, text=True, shell=True)
    lines = output.stdout.strip().split("\n")
    for line in lines:
        match = re.search(r"nvme(\d+)n\d+", line)
        if match:
            nvme_name_short = "nvme" + match.group(1)
            cmd = "cat /sys/class/nvme/" + nvme_name_short + "/address"
            output = subprocess.run([cmd], capture_output=True, text=True, shell=True)
            nvme_address = output.stdout.strip()
            nvme_map[nvme_address] = line

def mod_symbol_check_one(name, mod_name, symbol):
    try:
        # If mod_name is given, check if the module by this name is loaded
        not_loaded = False
        if mod_name is not None:
            ret = os.system("lsmod | grep " + mod_name + " > /dev/null 2>&1")
            if (ret != 0):
                print(name + " module is not loaded")
                not_loaded = True
            else:
                print(name + " module is loaded")
        if not_loaded is False:
            # Check if the given symbol exists or not
            ret = os.system("cat /proc/kallsyms | grep " + symbol + " > /dev/null 2>&1")
            if (ret != 0):
                print(name + " module is not patched or not loaded")
            else:
                print(name + " module is correctly patched")
    except ValueError:
        print("Error: failed to check module symbols for GDS")

def mod_symbol_check_all():
    mod_symbol_check_one("nvme", "nvme", "nvme_v1_register_nvfs_dma_ops");
    mod_symbol_check_one("nvme-rdma", "nvme_rdma", "nvme_rdma_v1_register_nvfs_dma_ops");
    mod_symbol_check_one("ScaleFlux", "sfxvdriver", "sfxv_v1_register_nvfs_dma_ops");
    mod_symbol_check_one("NVMesh", "nvmeib_common", "nvmesh_v1_register_nvfs_dma_ops");
    mod_symbol_check_one("Lustre", "lnet", "lustre_v1_register_nvfs_dma_ops");
    mod_symbol_check_one("BeeGFS", "beegfs", "beegfs_v1_register_nvfs_dma_ops");
    mod_symbol_check_one("GPFS", "mmfslinux", "ibm_scale_v1_register_nvfs_dma_ops");
    mod_symbol_check_one("rpcrdma", "rpcrdma", "rpcrdma_register_nvfs_dma_ops");

def ofed_check():
    print("ofed_info:")
    if path.exists("/usr/bin/ofed_info"):
        try:
                proc = subprocess.Popen(['ofed_info', '-s'],
                        stdout=subprocess.PIPE,
                        stderr=subprocess.STDOUT)
                if proc:
                    ofed_info_str = proc.stdout.read()
                    if ofed_info_str:
                        ofed_info_str = ofed_info_str.decode().strip(' \n\t')
                    supported = False
                    ofed_info_fields = ofed_info_str.split("-")
                    ofed_version_fields = []
                    # Handle cases where the OFED driver name starts with "OFED-"
                    # or "MLNX_OFED_LINUX"
                    if (len(ofed_info_fields) == 3 or len(ofed_info_fields) == 4 ):
                        if (ofed_info_fields[0] == "MLNX_OFED_LINUX"):
                            ofed_version_fields = ofed_info_fields[1].split(".")
                        elif(ofed_info_fields[0] == "OFED"):
                            ofed_version_fields = ofed_info_fields[2].split(".")

                        if (ofed_version_fields):
                            if (len(ofed_version_fields) == 2 and int(ofed_version_fields[0]) >= 6):
                                supported = True
                            elif (len(ofed_version_fields) == 2 and int(ofed_version_fields[0]) >= 5):
                                if (int(ofed_version_fields[1]) >= 1):
                                        supported = True
                            elif (len(ofed_version_fields) == 2 and int(ofed_version_fields[0]) >= 4):
                                if (int(ofed_version_fields[1]) >= 6):
                                        supported = True
                                        print("Note: WekaFS support needs MLNX_OFED_LINUX installed with --upstream-libs")
                    if(supported):
                        print("current version: " + ofed_info_str + " (Supported)")
                    else:
                        print("current version: " + ofed_info_str + " (Unsupported)")
                else:
                    print("Error: current version: Unknown")
        except ValueError:
            print("Error: failed to obtain OFED version information")
    print("min version supported: " + "MLNX_OFED_LINUX-4.6-1.0.1.1")

def weka_check():
    if path.exists("/usr/bin/weka"):
        print("WekaFS:")
        try:
                proc = subprocess.Popen(['weka', 'version', 'current'],
                        stdout=subprocess.PIPE,
                        stderr=subprocess.STDOUT)
                if proc:
                    weka_ver_str = proc.stdout.read()
                    if weka_ver_str:
                        weka_ver_str = weka_ver_str.decode().strip(' \n\t')
                    supported = False
                    weka_version_fields = weka_ver_str.split(".")
                    if (int(weka_version_fields[0]) >= 3):
                        if (int(weka_version_fields[1]) >= 8):
                            if (int(weka_version_fields[2]) >= 0):
                                supported = True
                                print("GDS RDMA read: supported")
                                print("GDS RDMA write: experimental")
                    if(supported):
                         print("current version: " + weka_ver_str + " (Supported)")
                    else:
                        print("current version: " + weka_ver_str + " (Unsupported)")
                else:
                     print("current version: Unknown")
        except ValueError:
            print("Error: failed to obtain weka version information")
        print("min version supported: " + "3.8.0")

def lustre_check():
     if path.exists("/usr/sbin/lctl"):
        print("Lustre:")
        try:
            proc = subprocess.Popen(['lctl', 'get_param', 'version'],
                               stdout=subprocess.PIPE,
                               stderr=subprocess.STDOUT)
            if proc:
                supported = False
                lustre_out = proc.stdout.read()
                if lustre_out:
                   lustre_out = lustre_out.decode().strip(' \n\t')
                lustre_ver_str = lustre_out.split('=')
                if(len(lustre_ver_str) == 2 and lustre_ver_str[1].find("ddn")):
                    lustre_version_fields = lustre_ver_str[1].split(".")
                    if (len(lustre_version_fields) ==3 and int(lustre_version_fields[0]) >= 2):
                        if (int(lustre_version_fields[1]) >= 13):
                            supported = True
                        elif (int(lustre_version_fields[1]) >= 12):
                            patch_ver = lustre_version_fields[2].split('_')
                            if (patch_ver and int(patch_ver[0]) >= 3):
                               supported = True

                    if(supported):
                        print("current version: " + lustre_ver_str[1] + " (Supported)")
                    else:
                        print("current version: " + lustre_ver_str[1] + " (Unsupported)")
                else:
                    print("current version: " + "Unknown")
            else:
                print("current version: " + "Unknown")
        except ValueError:
            print("Error: failed to obtain lustre version information")
        print("min version supported: " + "2.12.3_ddn28")

# This function checks for prerequisites such as nvidia_peermem driver
def prereq_check():
    print("Pre-requisite:")
    try:
        # Check if recommended nvidia_peermem driver is loaded
        ret = os.system("lsmod | grep nvidia_peermem > /dev/null 2>&1")
        if (ret != 0):
            # Next check if alternative nv_peer_mem driver is loaded
            ret = os.system("lsmod | grep nv_peer_mem > /dev/null 2>&1")
            if (ret != 0):
                print("Neither nvidia_peermem nor nv_peer_mem driver is loaded")
            else:
                print("nv_peer_mem is loaded as required")
        else:
            print("nvidia_peermem is loaded as required")
    except ValueError:
        print("Error: failed to check prerequisites for GDS")

# This function checks for nvidia_fs driver
def nvidia_fs_check():
    try:
        # Check if nvidia_fs driver is loaded, otherwise it will be
        # operating in compatible mode.
        ret = os.system("lsmod | grep nvidia_fs > /dev/null 2>&1")
        if (ret != 0):
            print("nvidia_fs driver is not loaded, GDS would operate in compatible/P2P(NVMe Only) mode.")
        else:
            print("GDS mode is enabled.")
    except ValueError:
        print("Error: failed to check nvidia_fs driver for GDS")

# This function returns the name of a NIC given its BDF
def get_nic_name(nic_bdf):
    nic_bdf_short = nic_bdf[5:]
    cmd = "lstopo-no-graphics | grep -A 1 " + nic_bdf_short + " | tail -n 1 | awk '{print $2}'"
    output = subprocess.run([cmd], capture_output=True, text=True, shell=True)
    return output.stdout.strip()

# This function returns the index of a GPU given its BDF
def get_gpu_index(gpu_bdf):
    cmd = "nvidia-smi -i " + gpu_bdf + " --query-gpu=index --format=csv,noheader"
    output = subprocess.run([cmd], capture_output=True, text=True, shell=True)
    return output.stdout.strip()

# This function returns the name of an NVMe given its BDF
def get_nvme_name(nvme_bdf):
    return nvme_map[nvme_bdf]

# This function gets the distance from each GPU to each Device using the peer_distances file
def get_device_topology(device_type):
    cmd = "cat /proc/driver/nvidia-fs/peer_distance | grep " + device_type + " | awk '{print $1, $4, $2}' | sort -k 2"
    output = subprocess.run([cmd], capture_output=True, text=True, shell=True)
    lines = output.stdout.strip().split("\n")
    
    # Only detect Mellanox devices for NICs
    nic_lines = []
    if device_type == "network":
        for line in lines:
            nic_bdf = line.split()[2]
            cmd = "lspci -D | grep " + nic_bdf
            output = subprocess.run([cmd], capture_output=True, text=True, shell=True)
            if "Mellanox" in output.stdout.strip():
                nic_lines.append(line)
        return nic_lines
    
    return lines

# This function prints the optimal GPU/Device pairs based on distance
def print_optimal_topology(device_type):
    # Check if lstopo and nvidia-smi are installed
    if os.system("lstopo --version >/dev/null") != 0:
        print("lstopo is not installed.")
        exit()
    if os.system("nvidia-smi >/dev/null") != 0:
        print("nvidia-smi is not installed.")
        exit()

    # Get sorted pairs from peer_distance file
    sorted_pairs = get_device_topology(device_type)
    if len(sorted_pairs) == 1 and sorted_pairs[0] == '':
        print("No devices of type " + device_type + " were found in the system")
        return

    # Keep track of which devices have been checked
    used_gpus = []
    unused_gpus = []
    used_devices = []
    optimal_pairs = []
    
    for pair in sorted_pairs:
        gpu_bdf, distance, device_bdf = pair.split()
        if gpu_bdf not in used_gpus and device_bdf not in used_devices:
            optimal_pairs.append(pair)
            used_gpus.append(gpu_bdf)
            used_devices.append(device_bdf)
        else:
            unused_gpus.append(gpu_bdf)
    
    #If there are more GPUs than NVMe/NIC devices, then assign device with lowest distance to remaining GPUs 
    for pair in sorted_pairs:
        gpu_bdf, distance, device_bdf = pair.split()
        if gpu_bdf in unused_gpus and gpu_bdf not in used_gpus:
            optimal_pairs.append(pair)
            used_gpus.append(gpu_bdf)
    
    # Get the GPU index and device names of each optimal pair and print them
    for pair in optimal_pairs:
        gpu_bdf, distance, device_bdf = pair.split()
        gpu_index = get_gpu_index(gpu_bdf)
        device_name = ""
        if device_type == "nvme":
            device_name = get_nvme_name(device_bdf)
        if device_type == "network":
            device_name = get_nic_name(device_bdf)
        print("GPU" + str(gpu_index) + " (" + str(gpu_bdf) + "):" + " has a distance " + str(int(distance, 16)) + " from " + device_name + " (" + str(device_bdf) + ")")

def main():
    parser = argparse.ArgumentParser(description='GPUDirectStorage platform checker')
    parser.add_argument('-p', action='store_true', dest='platform',  help='gds platform check')
    parser.add_argument('-f', dest='file', help='gds file check')
    parser.add_argument('-v', action='store_true', dest='versions', help='gds version checks')
    parser.add_argument('-V', action='store_true', dest='fs_versions', help='gds fs checks')
    parser.add_argument('-t', action='store_true', dest='topology', help='gds platform topology matrix')

    args = parser.parse_args()

    # Get the gds tools install path, gdscheck would be installed in the same
    # directory where gdscheck.py resides.
    gds_tools_path = (os.path.dirname(os.path.realpath(__file__)))
    gdscheck_path = gds_tools_path+"/gdscheck"
    gds_check=False
    
    cmd = [gdscheck_path]
    if (args.platform) :
        gds_check = True
        cmd.append('-p')
    if (args.file) :
        gds_check = True 
        cmd.append('-f')
        cmd.append(args.file)
    if (args.versions) :
        gds_check = True 
        cmd.append('-v')
    if (args.topology) :
        create_nvme_map()
        print("Optimal GPU/NIC topology")
        print_optimal_topology("network")
        print("Optimal GPU/NVMe topology")
        print_optimal_topology("nvme")
        exit()

    if gds_check and path.exists(gdscheck_path):
        proc = subprocess.Popen(cmd,
                   stdout=subprocess.PIPE,
                   stderr=subprocess.STDOUT)
        if proc:
            print(proc.stdout.read().decode())
    elif not args.fs_versions:
        parser.print_help()

    if args.fs_versions:
        print("FILESYSTEM VERSION CHECK:")
        prereq_check()
        nvidia_fs_check()
        mod_symbol_check_all()
        lustre_check()
        weka_check()
        ofed_check()

if __name__== "__main__":
   main()
