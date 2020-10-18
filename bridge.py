import time
import copy

class Message:

    def __init__(self, b_id, root, d, port):
        self.bridge_id = b_id
        self.root = root
        self.d = d
        self.port = port

    def __repr__(self):
        return 'Bridge:{} Root:{} D:{} Port:{}'.format(self.bridge_id, self.root, self.d, self.port)

class LAN:

    def __init__(self, name):
        self.name = name
        self.bridge_dict = {}
        self.to_forward = []
    
    def add_bridge(self, bridge_id, is_dp=0):
        self.bridge_dict[bridge_id] = is_dp

    def time_step(self, t):
        to_return = {k: [] for k in self.bridge_dict.keys()}
        empty = True
        for message in self.to_forward:
            for bridge_id in self.bridge_dict.keys():
                if bridge_id != message.bridge_id:
                    to_return[bridge_id].append(message)
                    empty = False

        # empty queue
        self.to_forward = []

        # print('LAN generated messages for id', self.name, to_return)
        return to_return, empty

class Bridge:

    def __init__ (self, bridge_id):
        self.id = bridge_id
        self.port_dict = {}
        
        self.root_prediction = self.id
        self.distance_from_root = 0
        self.closest_to_root_bridge = self.id
        
        self.received_messages = []

    def add_port(self, port_name, port_type='IP'):
        self.port_dict[port_name] = port_type

    def update_using_message(self, m):
        # print("Bridge {} received message {}".format(self.id, m))
        cond1 = (m.root < self.root_prediction)
        cond2 = (m.root == self.root_prediction and m.d < self.distance_from_root)
        cond3 = (m.root == self.root_prediction and m.d == self.distance_from_root and m.bridge_id < self.closest_to_root_bridge)
        if cond1 or cond2 or cond3:
            self.root_prediction = m.root
            self.distance_from_root = m.d
            self.closest_to_root_bridge = m.bridge_id
            self.port_dict[m.port] = 'RP'
            print("***Updated bridge {} with message {}***".format(self.id, m))
        # else:
            # print("Discarded message\n")
            # print(self.__repr__())

    def time_step(self, t):
        
        to_return = {k: [] for k in self.port_dict.keys()}
        empty = True
        # update
        for message in self.received_messages:
            self.update_using_message(message)
        # forward
        for message in self.received_messages:
            for port_name, port_type in self.port_dict.items():
                if port_name != message.port:
                    new_message = copy.copy(message)
                    new_message.port = port_name
                    new_message.d += 1
                    new_message.bridge_id = self.id
                    to_return[port_name].append(new_message)
                    empty = False
                    # print("Bridge {} forwarded message {} on port {}".format(self.id, new_message, port_name))

        # generate own config if root       
        if self.root_prediction == self.id and t == 0:
            print('Generating config message: {}'.format(self.id))
            for port_name, port_type in self.port_dict.items():
                m = Message(self.id, self.id, 1, port_name)
                to_return[port_name].append(m)
                empty = False
                # print("Bridge {} generated message {} on port {}".format(self.id, m, port_name))

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

        s = '\n***Topology***\n\n'
        for bridge_id, bridge in self.bridge_dict.items():
            s += bridge.__repr__() + '\n'
        return s



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

    return topology, trace

def spanning_tree(topology, trace):
    # first generate all config messages
    # message format: (self.id, id of node it considers as root, distance from root, port)  
    t = 0
    while 1:        
        print('\n', t, '\n')
        to_stop = topology.time_step(t)
        if to_stop:
            break
        t += 1
    print(topology)


s = """1
5
B1: A G B
B2: G F
B3: B C
B4: C F E
B5: C D E"""

top, trace = construct_topology(s)
spanning_tree(top, trace)