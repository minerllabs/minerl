# helper functions to open a txt file and write a list to it
import numpy as np
import os
# timestamp.txt
def write_timestamp(path_dir, TIMESTAMP): 
    np.save(os.path.join(path_dir, 'timestamp.npy'), np.array(TIMESTAMP))
# parse_result.txt
def write_parse_result(path_dir, result): 
    f = open(os.path.join(path_dir, 'parse_result.txt'), 'w')
    for i in range(len(result)):
        if (i == 0):
            f.write("%s" % result[0])
        else:
            f.write(",%s" % result[i])
    f.close()
    
# malmo.txt
def write_malmo(path_dir, actions): 
    f = open(os.path.join(path_dir, 'malmo.txt'), 'w')
    f.write("[")
    for i in range(len(actions)):
        if (i == 0):
            f.write("%s" % actions[0])
        else:
            f.write(",%s" % actions[i])
    f.write("]")
    f.close()

# network.txt
def write_network(path_dir, network):
    np.save(os.path.join(path_dir, 'network.npy'), np.array(network))
    