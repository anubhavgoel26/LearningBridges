from bridge import *
import sys

#function for creating an internal representation of the topology from input string
def construct_topology(input_str):
    topology = Topology()
    data = [x.strip() for x in input_str.split('\n')]
    # store LAN segs
    lan_segs = set()
    trace = int(data[0])
    num_bridges = int(data[1])
    # add bridges and corresponding ports
    for i in range(num_bridges):
        bridge_id, port_list = data[i+2].split(':')
        bridge_instance = Bridge(bridge_id)
        
        port_list = [x.strip() for x in port_list.strip().split(" ")]       
        for j in range(len(port_list)):
            bridge_instance.add_port(port_list[j])
            lan_segs.add(port_list[j])

        topology.add_bridge(bridge_instance)
    # add hosts
    num_lan = len(lan_segs)
    for i in range(num_lan):
        lan_seg, host_list = data[i+num_bridges+2].split(':')
        host_list = host_list.split(' ')[1:]
        topology.add_hosts(lan_seg, host_list)

    return topology, trace

def spanning_tree(topology, trace):
    t = 0
    while 1:
        # to stop is False if algo has converged and no more messages to forward
        to_stop = topology.time_step(t, trace)
        # we also stop if algo somehow doesn't converge by setting an upper limit on time
        if to_stop or t > 2*len(topology.bridge_dict):
            break
        t += 1
    print(topology)

def message_transfer(topology, trace, input_str):
    #this function figures out which is the concerned lan for the sending and receiving hosts
    data = [x.strip() for x in input_str.split('\n')]
    trace = int(data[0])
    t = 0
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
        message_send(topology, sender_lan, receiver_lan, sender, sending_lans, receiver, t, trace)
        #once the lans have been figured out, the message send function is called
        
        #code for printing forwarding table entries after every transmission
        for k in top.bridge_dict.keys():
            s += k+":\n"
            s += "HOST ID | FORWARDING PORT\n"
            for l in sorted(top.bridge_dict[k].forwarding_table.keys()):
                s += "{} | {}\n".format(l, top.bridge_dict[k].forwarding_table[l])
        s += "\n"

    
    print(s[:-1])


# read input and run algo
s = sys.stdin.readlines()
s = ''.join(s)
top, trace = construct_topology(s)
spanning_tree(top, trace)
message_transfer(top, trace, s)


