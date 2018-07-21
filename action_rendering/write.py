# helper functions to open a txt file and write a list to it
import numpy as np
# timestamp.txt
def write_timestamp(TIMESTAMP): 
    np.save('timestamp.npy', np.array(TIMESTAMP))
# parse_result.txt
def write_parse_result(result): 
    f = open('parse_result.txt', 'w')
    for i in range(len(result)):
        if (i == 0):
            f.write("%s" % result[0])
        else:
            f.write(",%s" % result[i])
    f.close()
    
# malmo.txt
def write_malmo(actions): 
    f = open('malmo.txt', 'w')
    f.write("[")
    for i in range(len(actions)):
        if (i == 0):
            f.write("%s" % actions[0])
        else:
            f.write(",%s" % actions[i])
    f.write("]")
    f.close()

# network.txt
def write_network(network):
    np.save('network.npy', np.array(network))
    