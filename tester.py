import heapq
import random

from node import Mp2Node

END_TIME = 10000.0

# A simulator for the distributed system. Uses a heap to organize events by time.
class SimulatedEnv():

    def __init__(self, drop_rate=0.0, delay=0.1):
        self.event_heap = []
        self.node_ip_map = {}
        self.drop_rate = drop_rate
        self.delay = delay
        self.cur_time = 0

    def register_node(self, node):
        self.node_ip_map[node.ip] = node

    def deregister_node(self, ip):
        self.node_ip_map.pop(ip)
        print("Failure detected!")

    def register_callback(self, time_offset, node, data):
        # A node can call this function and the data given here will be given back to the nod
        # in a callback after time_offset seconds.
        heapq.heappush(self.event_heap, (self.cur_time + time_offset, "callback", node.get_id(), data))

    def send_data(self, sender, dst_ip, data):
        # Sends data to another node (or back to the sender). In the simulator, this is just a queue
        # of messages to be received.
        sender_ip, _ = sender
        if (random.uniform(0.0, 1.0) > self.drop_rate):
            heapq.heappush(self.event_heap, (self.cur_time + self.delay, "recv", dst_ip, data, sender_ip)) 

    def step(self):
        # Step to the next even in the event heap, or return the END_TIME if there are no more events.
        if (len(self.event_heap) == 0):
            return END_TIME
        event = heapq.heappop(self.event_heap)
        self.cur_time = event[0]

        if event[1] == "recv":
            # The next event is the receipt of a packet.
            if (event[2] in self.node_ip_map.keys()):
                self.node_ip_map[event[2]].recv(event[3], event[4], self.cur_time)
        elif event[1] == "callback":
            # A callback event for a node.
            if (event[2][0] in self.node_ip_map.keys() and event[2] == self.node_ip_map[event[2][0]].get_id()):
                self.node_ip_map[event[2][0]].callback(event[3], self.cur_time)
        
        # Return the updated time after an event has happened.
        return self.cur_time

    def get_time(self):
        return self.cur_time
    
    def log(self, msg):
        pass
        #print("%f\t%s" % (self.get_time(), msg), flush=True)

if __name__ == '__main__':
    env = SimulatedEnv(drop_rate=0.30, delay=0.05)
    # For the purposes of simulating, the IP doesn't really need to be a valid IP,
    # and this is easier to look at.
    ips = ["A", "B", "C", "D", "E", "F", "G", "H", "I", "J"]
    last_time = 0.0
    cur_time = 0.0
    i = 0
    for ip in ips:
        env.register_node(Mp2Node(ip, ips[:max(2, i - 1)], env))
        i += 1

    last_event_time = 0.0
    while (cur_time < END_TIME):
        cur_time = env.step()

    print("Finished simulating up to %d seconds" % cur_time)
