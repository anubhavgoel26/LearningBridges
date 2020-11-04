from bridge import *
import sys


def construct_topology(input_str):

    topology = Topology()
    data = [x.strip() for x in input_str.split('\n')]
    lan_segs = set()
    trace = int(data[0])
    num_bridges = int(data[1])

    for i in range(num_bridges):
        bridge_id, port_list = data[i+2].split(':')
        bridge_instance = Bridge(bridge_id)
        
        port_list = [x.strip() for x in port_list.strip().split(" ")]       
        for j in range(len(port_list)):
            bridge_instance.add_port(port_list[j])
            lan_segs.add(port_list[j])

        topology.add_bridge(bridge_instance)

    num_lan = len(lan_segs)
    for i in range(num_lan):
        lan_seg, host_list = data[i+num_bridges+2].split(':')
        host_list = host_list.split(' ')[1:]
        topology.add_hosts(lan_seg, host_list)

    return topology, trace

def spanning_tree(topology, trace):
    # first generate all config messages
    # message format: (self.id, id of node it considers as root, distance from root, port)  
    t = 0
    while 1:
        to_stop = topology.time_step(t, trace)
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
    s = ""
    
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
            s += k+":\n"
            s += "HOST ID | FORWARDING PORT\n"
            for l in sorted(top.bridge_dict[k].forwarding_table.keys()):
                s += "{} | {}\n".format(l, top.bridge_dict[k].forwarding_table[l])
        s += "\n"
    
    print(s[:-1])



# s = """0
# 7
# B1: A G B
# B2: G F
# B3: B C
# B4: C F E
# B5: C D E
# B6: F E H
# B7: H D
# A: H1 H2
# B: H3 H4
# C: H5
# D: H6
# E: H7
# F: H8 H9 H10
# G: H11 H12
# H: H13 H14
# 4
# H1 H2
# H9 H2
# H4 H12
# H3 H9
# """

s = sys.stdin.readlines()
s = ''.join(s)
top, trace = construct_topology(s)
spanning_tree(top, trace)
message_transfer(top, trace, s)


