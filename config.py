
##
#
# THE FOLLOWING CODE IS A SNIPPET PILFERED FROM ONLINE. IT'S NOT INTENDED TO BE PORTRAYED AS OUR OWN.
# IT PERFORMS A VERY SPECIFIC LINUX FUNCTION THAT WE DO NOT KNOW HOW TO DO OTHERWISE, AND WHICH
# DOES NOT SEEM TO BE A CENTRAL PROBLEM IN THE PROGRAMMING TASK.
#
##
import socket
import fcntl
import struct

def get_ip_address(ifname):
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    return socket.inet_ntoa(fcntl.ioctl(
        s.fileno(),
        0x8915,  # SIOCGIFADDR
        struct.pack('256s', bytes(ifname[:15], 'utf-8'))
    )[20:24])

##
#
# END OF NON_ORIGINAL CODE.
#
##

THIS_IP = get_ip_address('eth0')

INTRODUCERS = [
    "172.22.153.10",
    "172.22.155.6"
]
PORT = 39475
