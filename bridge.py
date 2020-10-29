import time
import copy

class Message:

    def __init__(self, b_id, root, d, port):
        self.bridge_id = b_id
        #B2->B1, bridge_id = B2
        self.root = root
        self.d = d
        self.port = port

    def __repr__(self):
        return 'Bridge:{} Root:{} D:{} Port:{}'.format(self.bridge_id, self.root, self.d, self.port)

    def compare(self, other, current_closest_to_root):
        cond1 = (other.root < self.root)
        cond2 = (other.root == self.root and other.d < self.d)
        cond3 = (other.root == self.root and other.d == self.d and other.bridge_id < current_closest_to_root)
        if cond1 or cond2 or cond3:
            return 1
        else:
            return 0


class LAN:

    def __init__(self, name):
        self.name = name
        self.host_list = []
        self.bridge_dict = {}
        #brides_id, designated port or not
        self.to_forward = []
        #forwards to all bridges except source, stores messages
    
    def add_bridge(self, bridge_id, is_dp=0):
        self.bridge_dict[bridge_id] = is_dp

    def time_step(self, t):
        to_return = {k: [] for k in self.bridge_dict.keys()}
        empty = True
        for message in self.to_forward:
            for bridge_id in self.bridge_dict.keys():
                if bridge_id != message.bridge_id:
                    to_return[bridge_id].append(copy.copy(message))
                    empty = False

        # empty queue
        self.to_forward = []

        # print('LAN generated messages for id', self.name, to_return)
        return to_return, empty

class Bridge:

    def __init__ (self, bridge_id):
        self.id = bridge_id
        self.port_dict = {}
        #key - port name, value - DP/RP/NP
        self.forwarding_table = {}
        
        self.root_prediction = self.id
        self.distance_from_root = 0
        self.closest_to_root_bridge = self.id
        
        self.received_messages = []
        self.current_best_on_port = {}
        self.current_overall_best = Message(self.id, self.id, 0, -1)

    def add_port(self, port_name, port_type='DP'):
        self.port_dict[port_name] = port_type
        self.current_best_on_port[port_name] = None

    def update_port_local_best(self, port, message):
        if self.current_best_on_port[port] is None or self.current_best_on_port[port].compare(message, self.current_best_on_port[port].bridge_id):
            self.current_best_on_port[port] = copy.copy(message)

    def update_best(self, m):
        self.root_prediction = m.root
        self.distance_from_root = m.d+1
        self.closest_to_root_bridge = m.bridge_id
        # print("***Updating bridge {} with message {}***".format(self.id, m))
        self.current_overall_best = Message(self.id, self.root_prediction, self.distance_from_root, -1)

    def time_step(self, t):
        
        to_return = {k: [] for k in self.port_dict.keys()}
        #lan segment instead of bridge as key
        empty = True
        new_best = False
        # print("On BRIDGE", self.id, self.received_messages)
        
        # update own config with messages
        for message in self.received_messages:
            p = message.port
            self.update_port_local_best(p, message)
            message.d += 1
            if self.current_overall_best.compare(message, self.closest_to_root_bridge):
                message.d -= 1
                self.update_best(message)
                new_best = True
            
        # forward
        for port, port_type in self.port_dict.items():
            to_forward = Message(self.id, self.root_prediction, self.distance_from_root, port)
            cur_best = self.current_best_on_port[port]
            if cur_best is not None:
                rp_cond = self.root_prediction == cur_best.root and \
                            self.distance_from_root-1 == cur_best.d and \
                            self.closest_to_root_bridge == cur_best.bridge_id
                np_cond = (self.root_prediction == cur_best.root and \
                            self.distance_from_root-1 == cur_best.d and \
                            self.closest_to_root_bridge < cur_best.bridge_id) or \
                            (self.root_prediction == cur_best.root and \
                            self.distance_from_root == cur_best.d and \
                            self.id > cur_best.bridge_id)
            else:
                rp_cond = False
                np_cond = False
            
            dp_cond = cur_best is None or cur_best.compare(to_forward, self.id)
            # DP
            if dp_cond:
                # print('bridge id:', self.id, self.current_best_on_port)
                # print("Forwarding message [{}] on port {}".format(to_forward, port))
                if new_best:
                    to_return[port].append(to_forward)
                self.current_best_on_port[port] = to_forward
                self.port_dict[port] = 'DP'
            # RP
            elif rp_cond:
                self.port_dict[port] = 'RP'
            elif np_cond:
                self.port_dict[port] = 'NP'

        # generate own config if root       
        if self.root_prediction == self.id and t <= 0:
            # print('Generating config message: {}'.format(self.id))
            for port_name in self.port_dict.keys():
                m = Message(self.id, self.id, 0, port_name)
                to_return[port_name].append(m)
                self.update_port_local_best(port_name, m)
                empty = False
        
        # empty the queue
        self.received_messages = []
        # print('Bridge generated messages for id', self.id, to_return)
        return to_return, empty


    def __repr__(self):
        s = ''
        s += 'Bridge id: {}\n'.format(self.id)
        s += 'Root Pred: {} and Dist from root: {}\n'.format(self.root_prediction, self.distance_from_root)
        s += 'Port Dict: {}'.format(self.port_dict)
        return s

    def pretty_print(self):
        s = self.id + ': '
        for port_name in sorted(self.port_dict.keys()):
            s += "{}-{} ".format(port_name, self.port_dict[port_name])
        return s


class Topology:
    def __init__ (self):
        self.bridge_dict = {}
        self.lan_dict = {}

        self.pending_messages = []

    def add_bridge(self, bridge):
        self.bridge_dict[bridge.id] = bridge
        # add bridge to LAN dictionary
        for port_name, port_type in bridge.port_dict.items():
            if port_name not in self.lan_dict.keys():
                self.lan_dict[port_name] = LAN(port_name)
            self.lan_dict[port_name].add_bridge(bridge.id)

    def add_hosts(self, lan_seg, host_list):
        for port_name in self.lan_dict.keys():
            if port_name==lan_seg:
                self.lan_dict[port_name].host_list = host_list 


    def time_step(self, t):

        lan_messages = []
        stop = True
        for bridge in self.bridge_dict.values():
            m, empty = bridge.time_step(t)
            lan_messages.append(m)
            if not empty:
                stop = False

        for lan_message_dict in lan_messages:
            for lan_name, messages in lan_message_dict.items():
                self.lan_dict[lan_name].to_forward += messages

        bridge_messages = []
        for lan in self.lan_dict.values():
            m, empty = lan.time_step(t)
            bridge_messages.append(m)
            if not empty:
                stop = False

        for bridge_message_dict in bridge_messages:
            for bridge, messages in bridge_message_dict.items():
                self.bridge_dict[bridge].received_messages += messages

        return stop

    def __repr__(self):

        s = ''
        for bridge_id in sorted(self.bridge_dict.keys()):
            s += self.bridge_dict[bridge_id].pretty_print() + '\n'
        return s[:-1] # remove last newline



def construct_topology(input_str):

    topology = Topology()
    data = [x.strip() for x in input_str.split('\n')]
    trace = bool(data[0])
    num_bridges = int(data[1])
    for i in range(num_bridges):
        bridge_id, port_list = data[i+2].split(':')
        bridge_instance = Bridge(bridge_id)
        
        port_list = [x.strip() for x in port_list.strip().split(" ")]       
        for j in range(len(port_list)):
            bridge_instance.add_port(port_list[j])

        topology.add_bridge(bridge_instance)

    num_lan = 7
    for i in range(num_lan):
        lan_seg, host_list = data[i+num_bridges+2].split(':')
        host_list = host_list.split(' ')[1:]
        #print(lan_seg, host_list)
        topology.add_hosts(lan_seg, host_list)

    #for i in topology.lan_dict.keys():
        #print(i, topology.lan_dict[i].host_list)

    return topology, trace

def spanning_tree(topology, trace):
    # first generate all config messages
    # message format: (self.id, id of node it considers as root, distance from root, port)  
    t = 0
    while 1:
        to_stop = topology.time_step(t)
        if to_stop or t > 2*len(topology.bridge_dict):
            break
        t += 1
    print(topology)

def message_transfer(topology, trace, input_str):
    data = [x.strip() for x in input_str.split('\n')]
    num_bridges = int(data[1])
    num_lan = len(topology.lan_dict)
    transfer_index = 2+num_lan+num_bridges
    num_tranfers = int(data[transfer_index])
    #print(num_tranfers)
    
    for i in range(num_tranfers):
        sender = data[transfer_index+i+1].split(' ')[0]
        receiver = data[transfer_index+i+1].split(' ')[1]
        
        #finding out the sender lan
        for i in topology.lan_dict.keys():
            if sender in topology.lan_dict[i].host_list:
                sender_lan = topology.lan_dict[i]
                #print(sender_lan.name)
        for i in topology.lan_dict.keys():
            if receiver in topology.lan_dict[i].host_list:
                receiver_lan = topology.lan_dict[i]
                #print(receiver_lan.name)
        sending_lans = []
        #print(sender)
        message_send(topology, sender_lan, receiver_lan, sender, sending_lans, receiver)
        for k in top.bridge_dict.keys():
            print(k+":")
            print("HOST ID | FORWARDING PORT")
            for l in sorted(top.bridge_dict[k].forwarding_table.keys()):
                print(l, "|", top.bridge_dict[k].forwarding_table[l])
            print("")

def message_send(topology, sender_lan, receiver_lan, sender, sending_lans, receiver):
    sending_bridges = []
    sending_lans.append(sender_lan.name)
    for i in topology.lan_dict[sender_lan.name].bridge_dict.keys():
        if(topology.bridge_dict[i].port_dict[sender_lan.name] != 'NP'):
            sending_bridges.append(topology.bridge_dict[i])
    
    for i in sending_bridges:
        if sender not in i.forwarding_table.keys():
            i.forwarding_table[sender] = sender_lan.name

        if receiver not in i.forwarding_table.keys():
            for j in (topology.bridge_dict[i.id].port_dict.keys()):
                if(topology.bridge_dict[i.id].port_dict[j]!='NP'):
                    if j not in sending_lans:
                        sender_lan2 = topology.lan_dict[j]
                        message_send(topology, sender_lan2, receiver_lan, sender, sending_lans, receiver)
        else:
            sender_lan2 = topology.lan_dict[i.forwarding_table[receiver]]
            if(sender_lan2.name not in sending_lans):
            # print(sender_lan2.name)
                message_send(topology, sender_lan2, receiver_lan, sender, sending_lans, receiver)
    return







s = """0
7
B1: A G B
B2: G F
B3: B C
B4: C F E
B5: C D E
B6: F E H
B7: H D
A: H1 H2
B: H3 H4
C: H5
D: H6
E: H7
F: H8 H9 H10
G: H11 H12
H: H13 H14
4
H1 H2
H9 H2
H4 H12
H3 H9
"""

top, trace = construct_topology(s)
spanning_tree(top, trace)
message_transfer(top, trace, s)


