import os

HOST_FORMAT_STR = "fa19-cs425-g79-%s.cs.illinois.edu"
OLD_FILE_FORMAT_STR = "/srv/shared/vm%d.log"
NEW_FILE_FORMAT_STR = "/srv/shared/vm%d_60MB.log"
CMD_FORMAT_STR = "cp %s %s && truncate -s 60MB %s && ls -al %s"

for i in range(1, 11):
    old_filename = OLD_FILE_FORMAT_STR % i
    new_filename = NEW_FILE_FORMAT_STR % i
    cmd = CMD_FORMAT_STR % (old_filename, new_filename, new_filename, new_filename)
    hostname = HOST_FORMAT_STR % (str(i).zfill(2))
    cmd = 'ssh %s "%s"' % (hostname, cmd)
    os.system(cmd)
