import os

LOCAL_LOG_FORMAT_STR = "./logs/simple_log_%d.txt"
REMOTE_LOG_FORMAT_STR = "fa19-cs425-g79-%s.cs.illinois.edu:/srv/shared/"

for i in range(1, 11):
    local_log = LOCAL_LOG_FORMAT_STR % i
    remote_log = REMOTE_LOG_FORMAT_STR % (str(i).zfill(2))
    cmd = "scp %s %s" % (local_log, remote_log)
    os.system(cmd)
