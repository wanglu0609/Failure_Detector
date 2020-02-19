import os

LOCAL_LOG_FORMAT_STR = "/srv/shared/mp1/test_logs/"
REMOTE_LOG_FORMAT_STR = "fa19-cs425-g79-%s.cs.illinois.edu:/srv/shared/vm%d.log"

for i in range(1, 11):
    local_log = LOCAL_LOG_FORMAT_STR
    remote_log = REMOTE_LOG_FORMAT_STR % (str(i).zfill(2), i)
    cmd = "scp %s %s" % (remote_log, local_log)
    os.system(cmd)
