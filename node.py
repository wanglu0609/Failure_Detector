import math
import random

FAILURE_DETECTION_TARGET = 5.0
NO_GOSSIP_FAILURE_DETECTION_TIMEOUT = 2.0

JOIN_TIMEOUT = 0.15
MEMBER_GOSSIP_INTERVAL = 0.2
REJOIN_TIMEOUT = 5.0
REJOIN_CHECK_INTERVAL = 5.0
FAILURE_GOSSIP_INTERVAL = 0.1
FAILURE_GOSSIP_TIME = 15.0
CLEANUP_TIME = 75.0
HEARTBEAT_INTERVAL = 0.25
HEARTBEAT_TIMEOUT = FAILURE_DETECTION_TARGET - HEARTBEAT_INTERVAL
N_LEAVE_FAILURE_GOSSIPS = 10
NEIGHBOR_COUNT = 2

class RemovableList():

    def __init__(self):
        self.val_list = []
        self.idx_map = {}

    def add(self, val):
        self.val_list.append(val)
        self.idx_map[val] = len(self.val_list) - 1

    def remove(self, val):
        old_idx = self.idx_map[val]
        self.idx_map.pop(val)
        if (old_idx != len(self.val_list) - 1):
            self.val_list[old_idx] = self.val_list[-1]
            self.idx_map[self.val_list[old_idx]] = old_idx
        self.val_list = self.val_list[:-1]

    def get(self, idx):
        return self.val_list[idx]

    def has(self, val):
        return val in self.idx_map.keys()

    def size(self):
        return len(self.val_list)

class Mp2Node():
    
    def __init__(self, ip, known_ips, env):
        self.env = env
        self.ip = ip
        self.start_time = env.get_time()
        self.known_ips = known_ips
        self.send_join_msg()
        self.left_neighbors = []
        self.right_neighbors = []
        self.heartbeat_times = {}
        self.members = RemovableList()
        self.add_member(self.get_id())
        self.failures = RemovableList()
        self.n_gossip_targets = 0
        self.env.register_callback(MEMBER_GOSSIP_INTERVAL, self, ("gossip members", ""))
        self.env.register_callback(FAILURE_GOSSIP_INTERVAL, self, ("gossip failures", ""))
        self.env.register_callback(HEARTBEAT_INTERVAL, self, ("heartbeat", ""))
        self.env.register_callback(REJOIN_CHECK_INTERVAL, self, ("rejoin timeout", ""))
        self.joined = False
        self.join_src = None
        self.failure_times = {}
        self.leaving = False
        self.last_gossip_time = self.env.get_time()

    def send_heartbeat(self):
        for n in self.left_neighbors:
            ip, _ = n
            self.env.send_data(self.get_id(), ip, ("heartbeat", self.get_id()))
            #self.env.log("Node %s heartbeat (left) to %s" % (self.get_id(), n))

        for n in self.right_neighbors:
            ip, _ = n
            self.env.send_data(self.get_id(), ip, ("heartbeat", self.get_id()))
            #self.env.log("Node %s heartbeat (right) to %s" % (self.get_id(), n))

    def get_id(self):
        return (self.ip, self.start_time)

    def update_neighbors_added(self, node_id):
        node_ip, _ = node_id
        
        if (node_ip == self.ip):
            return

        #self.env.log("Node %s updating neighbors for %s" % (self.get_id(), node_id))
        place = False
        if (node_id not in self.left_neighbors):
            if (len(self.left_neighbors) < NEIGHBOR_COUNT):
                self.left_neighbors.append(node_id)
                self.heartbeat_times[node_id] = self.env.get_time()
                #self.env.log("\tAdded %s by default." % (node_id,))
            else:
                for i, neighbor in enumerate(self.left_neighbors):
                    if (place):
                        continue
                    neighbor_ip, _ = neighbor
                    place =  (node_ip > neighbor_ip and node_ip < self.ip)
                    place |= (node_ip > neighbor_ip and neighbor_ip > self.ip)
                    place |= (node_ip < self.ip and neighbor_ip > self.ip)
                    if (place):
                        self.left_neighbors[i] = node_id
                        self.heartbeat_times[node_id] = self.env.get_time()
                        if neighbor not in self.right_neighbors:
                            self.heartbeat_times.pop(neighbor)
                        self.update_neighbors_added(neighbor)
                        #self.env.log("\tReplaced %s with %s" % (neighbor, node_id))

        place = False
        if (node_id not in self.right_neighbors):
            if (len(self.right_neighbors) < NEIGHBOR_COUNT):
                self.right_neighbors.append(node_id)
                self.heartbeat_times[node_id] = self.env.get_time()
                #self.env.log("\tAdded %s by default." % (node_id,))
            else:
                for i, neighbor in enumerate(self.right_neighbors):
                    if (place):
                        continue
                    neighbor_ip, _ = neighbor
                    place =  (node_ip < neighbor_ip and node_ip > self.ip)
                    place |= (node_ip < neighbor_ip and neighbor_ip < self.ip)
                    place |= (node_ip > self.ip and neighbor_ip < self.ip)
                    if (place):
                        self.right_neighbors[i] = node_id
                        self.heartbeat_times[node_id] = self.env.get_time()
                        if neighbor not in self.left_neighbors:
                            self.heartbeat_times.pop(neighbor)
                        self.update_neighbors_added(neighbor)
                        #self.env.log("\tReplaced %s with %s" % (neighbor, node_id))
        #self.env.log("\t%s" % self.heartbeat_times)

    def log_member_list(self, msg=""):
        self.env.log("Node %s, %d members (%s):" % (self.get_id(), self.members.size(), msg))
        for i in range(0, self.members.size()):
            member = self.members.get(i)
            self.env.log("\t%s" % str(member))

    def update_neighbors_removed(self, node_id):
        need_full_update = False
        if (node_id in self.left_neighbors):
            self.left_neighbors.remove(node_id)
            if (node_id in self.heartbeat_times.keys()):
                self.heartbeat_times.pop(node_id)
            need_full_update = True
        
        if (node_id in self.right_neighbors):
            self.right_neighbors.remove(node_id)
            if (node_id in self.heartbeat_times.keys()):
                self.heartbeat_times.pop(node_id)
            need_full_update = True

        if (need_full_update):
            for i in range(0, self.members.size()):
                member = self.members.get(i)
                if (member not in self.left_neighbors or member not in self.right_neighbors):
                    self.update_neighbors_added(member)

    def update_gossip_targets(self):
        self.n_gossip_targets = max(1, int(math.log(1 + self.members.size(), 2)))

    def add_member(self, node_id):
        self.members.add(node_id)
        self.update_gossip_targets()
        self.update_neighbors_added(node_id)

    def remove_member(self, node_id):
        self.members.remove(node_id)
        self.update_gossip_targets()
        self.update_neighbors_removed(node_id)
        self.log_member_list("post-remove")

    def send_failures_to(self, target_ip):
        removals = []
        for i in range(0, self.failures.size()):
            failure = self.failures.get(i)
            failure_time = self.failure_times[failure]
            if (failure_time + FAILURE_GOSSIP_TIME > self.env.get_time()):
                self.env.send_data(self.get_id(), target_ip, ("failure", failure))
            if (self.env.get_time() > failure_time + CLEANUP_TIME):
                removals.append(failure)
                self.failure_times.pop(failure)

        for removal in removals:
            self.failures.remove(removal)
            #self.env.log("Node %s failure list updated:" % (self.get_id(),))
            for i in range(0, self.failures.size()):
                failure = self.failures.get(i)
                #self.env.log("\t%s" % str(failure))

    def send_members_to(self, target_ip):
        for i in range(0, self.members.size()):
            member = self.members.get(i)
            self.env.send_data(self.get_id(), target_ip, ("member", member))

    def gossip_members(self):
        for i in range(0, self.n_gossip_targets):
            gossip_target = self.members.get(random.randint(0, self.members.size() - 1))
            target_ip, _ = gossip_target
            if (target_ip != self.ip):
                self.send_members_to(target_ip)

    def gossip_failures(self):
        #print("Node %s gossiping failures!" % str(self.get_id()))
        for i in range(0, self.n_gossip_targets):
            gossip_target = self.members.get(random.randint(0, self.members.size() - 1))
            target_ip, _ = gossip_target
            if (target_ip != self.ip):
                #print("\tGossiping failures to %s" % target_ip)
                self.send_failures_to(target_ip)

    def merge_member_gossip(self, member):
        if ((not self.members.has(member)) and (not self.failures.has(member))):
            self.add_member(member)
            self.log_member_list("member gossip")
    
    def merge_failure_gossip(self, failure):
        if (not self.leaving and failure == self.get_id()):
            self.leave_gracefully()
            self.env.register_node(Mp2Node(self.ip, self.known_ips, self.env))
        if (not self.failures.has(failure)):
            #self.env.log("Node %s merging failure gossip for %s" % (str(self.get_id()), str(failure)))
            if (self.members.has(failure)):
                self.remove_member(failure)
                #self.env.log("Node %s member list updated:" % (self.get_id(),))
                for i in range(0, self.members.size()):
                    member = self.members.get(i)
                    #self.env.log("\t%s" % str(member))
            self.failures.add(failure)
            self.failure_times[failure] = self.env.get_time()
            #self.env.log("Node %s failure list updated:" % (self.get_id(),))
            for i in range(0, self.failures.size()):
                failure = self.failures.get(i)
                #self.env.log("\t%s" % str(failure))

    def make_join_msg(self):
        return ("join", self.get_id())

    def send_join_msg(self):
        join_msg = self.make_join_msg()
        join_target = self.ip
        while (join_target == self.ip):
            join_target = self.known_ips[random.randint(0, len(self.known_ips) - 1)]
        self.join_src = join_target
        self.env.send_data(self.get_id(), join_target, join_msg)
        self.env.register_callback(JOIN_TIMEOUT, self, ("join failure", ""))

    def recv(self, data, src, cur_time):
        #print("Node %s recv at %f" % (self.ip, cur_time))
        #print(data)
        
        msg, node_id = data
        if (msg == "join"):
            ip, start_time = node_id
            self.send_members_to(ip)

        if (msg == "member"):
            self.last_gossip_time = self.env.get_time()
            if (src == self.join_src):
                self.joined = True
            self.merge_member_gossip(node_id)

        if (msg == "failure"):
            self.last_gossip_time = self.env.get_time()
            self.merge_failure_gossip(node_id)

        if (msg == "heartbeat"):
            self.heartbeat_times[node_id] = self.env.get_time()
            #self.env.log("Node %s got heartbeat from %s" % (self.get_id(), node_id))

    def leave_gracefully(self):
        self.leaving = True
        self.merge_failure_gossip(self.get_id())
        for i in range(0, N_LEAVE_FAILURE_GOSSIPS):
            self.gossip_failures()
        self.env.deregister_node(self.ip)

    def crash(self):
        self.env.deregister_node(self.ip)

    def check_heartbeats(self):
        if (self.env.get_time() > self.last_gossip_time + NO_GOSSIP_FAILURE_DETECTION_TIMEOUT):
            return
        #self.env.log("Node %s checking heartbeats" % (self.get_id(),))
        #self.env.log("\t%s" % self.heartbeat_times)
        for neighbor in self.left_neighbors:
            if (self.heartbeat_times[neighbor] < self.env.get_time() - HEARTBEAT_TIMEOUT):
                self.env.log("-- FAILURE DETECTED: Node %s detects that node %s has failed! --" % (self.get_id(), neighbor))
                self.merge_failure_gossip(neighbor)
        
        for neighbor in self.right_neighbors:
            if (self.heartbeat_times[neighbor] < self.env.get_time() - HEARTBEAT_TIMEOUT):
                self.env.log("-- FAILURE DETECTED: Node %s detects that node %s has failed! --" % (self.get_id(), neighbor))
                self.merge_failure_gossip(neighbor)

    def callback(self, data, cur_time):
        #print("Node %s callback at %f" % (self.ip, cur_time))
        #print(data)

        cb_type, cb_data = data
        if (cb_type == "gossip members"):
            self.gossip_members()
            self.env.register_callback(MEMBER_GOSSIP_INTERVAL, self, ("gossip members", ""))

        if (cb_type == "gossip failures"):
            self.gossip_failures()
            self.env.register_callback(FAILURE_GOSSIP_INTERVAL, self, ("gossip failures", ""))

        if (cb_type == "heartbeat"):
            self.send_heartbeat()
            self.check_heartbeats()
            self.env.register_callback(HEARTBEAT_INTERVAL, self, ("heartbeat", ""))

        if (cb_type == "join failure"):
            if not self.joined:
                self.send_join_msg()

        if (cb_type == "rejoin timeout"):
            if (self.env.get_time() > self.last_gossip_time + REJOIN_TIMEOUT):
                self.leave_gracefully()
                self.env.register_node(Mp2Node(self.ip, self.known_ips, self.env))
            self.env.register_callback(REJOIN_CHECK_INTERVAL, self, ("rejoin timeout", ""))

