#!/usr/bin/python3
import socket
import subprocess

from utils import config

def run_server():
    sock = socket.socket()
    sock.bind(('', config.DEFAULT_PORT))
    sock.listen(1)

    while True:
        print("Waiting for command...")
        connection, addr = sock.accept()
        cmd = connection.recv(1024).decode('utf-8')
        print("dgrep daemon got command: %s" % cmd)
        result = "NULL"
        try:
            result = subprocess.check_output(cmd, shell=True).decode('utf-8')
        except Exception as e:
            result = "ERROR: %s" % str(e)
        connection.send(result.encode())
        connection.close()

if __name__ == '__main__':
    print('Work in progress distributed grep daemon')
    run_server()
