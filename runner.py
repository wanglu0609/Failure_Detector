import heapq
from multiprocessing import Process, Queue
import os
import pickle
import queue
import random
import signal
import socket
import time

import config
from node import Mp2Node

LIVE_ENV_INTERVAL = 0.01

env = None
def handler(signum, frame):
    if (signum == signal.SIGQUIT):
        env.leave()
        exit(-1)

def run_receiver(recv_queue):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((config.THIS_IP, config.PORT))
    while (True):
        data, address = sock.recvfrom(4096)
        recv_queue.put((pickle.loads(data), address))

class LiveEnvReceiver():

    def __init__(self, recv_queue):
        self.recv_queue = recv_queue
        self.proc = Process(target=run_receiver, args=(recv_queue,))
        self.proc.start()

class LiveEnv():

    def __init__(self, drop_rate=0.0):
        self.event_heap = []
        self.node = None
        self.drop_rate = drop_rate
        self.send_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.recv_queue = Queue()
        self.receiver = LiveEnvReceiver(self.recv_queue)
        self.report_time = self.get_time()
        self.bits_this_sec = 0

    def register_node(self, node):
        self.node = node

    def deregister_node(self, node):
        pass

    def register_callback(self, time_offset, node, data):
        heapq.heappush(self.event_heap, (self.get_time() + time_offset, "callback", node.get_id(), data))

    def send_data(self, sender, dst_ip, data):
        if (random.uniform(0.0, 1.0) > self.drop_rate):
            data_str = pickle.dumps(data)
            self.send_sock.sendto(data_str, (dst_ip, config.PORT))
            self.bits_this_sec += 8 * len(data_str)

    def run_forever(self):
        while (True):
            while (len(self.event_heap) > 0 and self.event_heap[0][0] < self.get_time()):
                event = heapq.heappop(self.event_heap)
                self.node.callback(event[3], self.get_time())
            drained_recv_queue = False
            while (not drained_recv_queue):
                try:
                    data, address = self.recv_queue.get(block=False)
                    self.node.recv(data, address, self.get_time())
                except queue.Empty as e:
                    drained_recv_queue = True
            time.sleep(LIVE_ENV_INTERVAL)
            if (self.get_time() > self.report_time + 1.0):
                self.log("Network usage: %d bps" % self.bits_this_sec)
                self.report_time = self.get_time()
                self.bits_this_sec = 0

    def get_time(self):
        return time.time()

    def log(self, msg):
        data = "%f\t%s" % (self.get_time(), msg)
        os.system("echo '%s' >> /srv/shared/member_log.txt" % data)

    def leave(self):
        self.node.leave_gracefully()

if __name__ == '__main__':
    this_ip = config.THIS_IP
    known_ips = config.INTRODUCERS
    env = LiveEnv(drop_rate=0.0)
    env.register_node(Mp2Node(this_ip, known_ips, env))
    signal.signal(signal.SIGQUIT, handler)
    env.run_forever()
