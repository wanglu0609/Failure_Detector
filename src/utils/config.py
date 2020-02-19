
DEFAULT_PORT = 6823
DEFAULT_INTERMEDIATE_FILENAME = "/srv/shared/dgrep_result_from___VM_ID__.txt"

_VM_IP_MAP = {
    "172.22.153.10":1,
    "172.22.155.6":2,
    "172.22.157.6":3,
    "172.22.153.11":4,
    "172.22.155.7":5,
    "172.22.157.7":6,
    "172.22.153.12":7,
    "172.22.155.8":8,
    "172.22.157.8":9,
    "172.22.153.13":10
}

VM_IP_LIST = [k for k in _VM_IP_MAP.keys()]
VM_COUNT = len(VM_IP_LIST)

def vm_ip_to_id(ip):
    return _VM_IP_MAP[ip]
