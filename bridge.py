import time
import copy

#class which represents a config message for spanning tree algorithm
class Message:
    

    def __init__(self, b_id, root, d, port):
        self.bridge_id = b_id
        self.root = root
        self.d = d
        self.port = port

    def __repr__(self):
        return 'Bridge:{} Root:{} D:{} Port:{}'.format(self.bridge_id, self.root, self.d, self.port)

    def compare(self, other, current_closest_to_root):
        # compare 2 given message with self and return 1 if input is 'better'
        # 'better' is defined acc to the rules discussed in class
        cond1 = (other.root < self.root)
        cond2 = (other.root == self.root and other.d < self.d)
        cond3 = (other.root == self.root and other.d == self.d and other.bridge_id < current_closest_to_root)
        if cond1 or cond2 or cond3:
            return 1
        else:
            return 0

#class which represents a LAN segment
class LAN:    
    def __init__(self, name):
        self.name = name
        self.host_list = []
        self.bridge_dict = {}
        # stores messages and forwards to all bridges connected to self except source
        self.to_forward = []        
    
    def add_bridge(self, bridge_id, is_dp=0):
        self.bridge_dict[bridge_id] = is_dp

    def time_step(self, t):
        # forward each received message to non-sender bridge
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

#class which represents a bridge
class Bridge:
    def __init__ (self, bridge_id):
        self.id = bridge_id
        self.port_dict = {}
        self.forwarding_table = {}
        
        # parameters which are changed acc by spanning tree algo
        self.root_prediction = self.id
        self.distance_from_root = 0
        self.closest_to_root_bridge = self.id
        
        # list of messages sent by connected LAN segments
        self.received_messages = []
        # store best message received on each port
        self.current_best_on_port = {}
        # global best
        self.current_overall_best = Message(self.id, self.id, 0, -1)

    def add_port(self, port_name, port_type='DP'):
        self.port_dict[port_name] = port_type
        self.current_best_on_port[port_name] = None

    # update best message on port
    def update_port_local_best(self, port, message):
        if self.current_best_on_port[port] is None or self.current_best_on_port[port].compare(message, self.current_best_on_port[port].bridge_id):
            self.current_best_on_port[port] = copy.copy(message)

    # update global best
    def update_best(self, m):
        self.root_prediction = m.root
        self.distance_from_root = m.d+1
        self.closest_to_root_bridge = m.bridge_id
        # print("***Updating bridge {} with message {}***".format(self.id, m))
        self.current_overall_best = Message(self.id, self.root_prediction, self.distance_from_root, -1)

    # called at each clock tick    
    def time_step(self, t, trace):
        
        to_return = {k: [] for k in self.port_dict.keys()}
        #messages to dump on LAN seg,ent
        empty = True
        new_best = False
        
        # update own config with recived messages
        for message in self.received_messages:
            p = message.port
            self.update_port_local_best(p, message)
            message.d += 1
            # if received message is better than global best, update
            if self.current_overall_best.compare(message, self.closest_to_root_bridge):
                message.d -= 1
                self.update_best(message)
                message.d += 1
                new_best = True
            # print trace
            if trace:
                print("{} r {} ({} {} {})".format(t, self.id, message.root, message.d-1, message.bridge_id))
            
        # forward messages
        for port, port_type in self.port_dict.items():
            # construct message to forward
            to_forward = Message(self.id, self.root_prediction, self.distance_from_root, port)
            # cur best is local best for that port
            cur_best = self.current_best_on_port[port]
            if cur_best is not None:
                # conditions for root port
                rp_cond = self.root_prediction == cur_best.root and \
                            self.distance_from_root-1 == cur_best.d and \
                            self.closest_to_root_bridge == cur_best.bridge_id
                # conditions for null port
                np_cond = (self.root_prediction == cur_best.root and \
                            self.distance_from_root-1 == cur_best.d and \
                            self.closest_to_root_bridge < cur_best.bridge_id) or \
                            (self.root_prediction == cur_best.root and \
                            self.distance_from_root == cur_best.d and \
                            self.id > cur_best.bridge_id)
            else:
                # if receiving message on that port for th first time, bridge assumes it is the DP
                rp_cond = False
                np_cond = False
            
            dp_cond = cur_best is None or cur_best.compare(to_forward, self.id)
            # DP
            if dp_cond:
                # forward messages only if the configuration was a new global best
                if new_best:
                    to_return[port].append(to_forward)
                    if trace:
                        print("{} s {} ({} {} {})".format(t, self.id, to_forward.root, to_forward.d, to_forward.bridge_id))
                self.current_best_on_port[port] = to_forward
                self.port_dict[port] = 'DP'
            # RP
            elif rp_cond:
                self.port_dict[port] = 'RP'
            elif np_cond:
                self.port_dict[port] = 'NP'

        # generate own config if root and at t=0 ONLY
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
        return s[:-1]

#class for creating an internal representation of a topology
class Topology:
    def __init__ (self):
        self.bridge_dict = {}
        #maintains a list of lans connected to each bridge
        self.lan_dict = {}
        #maintains a list of bridges associated with a LAN
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

    # called at each clock tick
    def time_step(self, t, trace):

        lan_messages = []
        # lan_messages contains all messages which bridges have generated
        stop = True
        for bridge in self.bridge_dict.values():
            m, empty = bridge.time_step(t, trace)
            lan_messages.append(m)
            if not empty:
                stop = False
        # dump the generated bridge messages into the LAN segment's list
        for lan_message_dict in lan_messages:
            for lan_name, messages in lan_message_dict.items():
                self.lan_dict[lan_name].to_forward += messages

        # get messages forwarded by LAN segment
        bridge_messages = []
        for lan in self.lan_dict.values():
            m, empty = lan.time_step(t)
            bridge_messages.append(m)
            if not empty:
                stop = False
        # pass on LAN segment messages to bridge
        for bridge_message_dict in bridge_messages:
            for bridge, messages in bridge_message_dict.items():
                self.bridge_dict[bridge].received_messages += messages

        return stop

    def __repr__(self):

        s = ''
        for bridge_id in sorted(self.bridge_dict.keys()):
            s += self.bridge_dict[bridge_id].pretty_print() + '\n'
        return s[:-1] # remove last newline

#transfers messages from a sender lan to next hop, recursively called on all hops
def message_send(topology, sender_lan, receiver_lan, sender, sending_lans, receiver, t, trace):
    sending_bridges = []
    #maintain all the next hops that the message has to be sent to
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
                        message_send(topology, sender_lan2, receiver_lan, sender, sending_lans, receiver, t+1, trace)
        else:
            #case where receiver is already in the forwarding table
            sender_lan2 = topology.lan_dict[i.forwarding_table[receiver]]
            if(sender_lan2.name not in sending_lans):
            # print(sender_lan2.name)
                message_send(topology, sender_lan2, receiver_lan, sender, sending_lans, receiver, t+1, trace)