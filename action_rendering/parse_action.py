# Yinglan Chen, July 2018

# this parse function that takes in actions.tmcpr file and parse it to 
# a list of commands. 

# action.tmcpr has the following format:
# --
# |        [timestamp]     # 4 bytes (int)
# |        [len]           # 4 byets (int)
# |  --    
# |  |     [package_id]    # 1 byte  (temporary fixed value 0x18)
# |  |     [len2]          # 1 byte
# |  |  -- 
# | len |  
# |   len2 [channel name]  # 1 byte (char), either 'a' or 'c' or 't'
# |  |  |                  # recorded_actions || recorded_camera_actions || tick
# |  |  -- 
# |  |     [data]          # can be computed with len & len2 
# |  --    
# --       
   
#  The output is written to a file and has the following format:
#   [move1, jump, tick, ...]

import os
import sys
import binascii
import struct
from varint import decode_stream
from parse_result_to_Action_object import parse_to_action_object
from write import write_timestamp, write_parse_result, write_malmo, write_network

# main function read input, open file, call parse and close file.
def main():
    # read path from input
    try:
        path = sys.argv[1]
        path_dir = os.path.dirname(path)
    except:
        print("Lacking argument: missing directory")
        sys.exit(1)
    # check that path is action.tmcpr
    try:
        assert(path.endswith("actions.tmcpr"))
    except:
        print("Wrong argument: not an action.tmcpr file")
        sys.exit(1)        

    # open file
    stream = open(path, 'rb')
    # parse 
    TIMESTAMP = []
    (result, TIMESTAMP) = parse(stream, TIMESTAMP)

    write_timestamp(path_dir, TIMESTAMP) # timestamp.npy
    write_parse_result(path_dir, result) # parse_result.npy

    # parse to action object array 
    actions = parse_to_action_object(result) 

    # to_malmo
    write_malmo(path_dir, actions)# malmo.npy

    # to_network
    network = []
    for action in actions:
        network.append(action.to_network())
    write_network(path_dir, network)


    # close file
    stream.close()
    return result 


# parse function takes a stream and parse it to a result array
def parse(stream, TIMESTAMP): 
    result = []
    # first time_stamp
    time_stamp_b = stream.read(4)
    timestamp = int.from_bytes(time_stamp_b, byteorder='big', signed=False)

    while True:
        # len
        len_b = stream.read(4)
        len  = int.from_bytes(len_b, byteorder='big', signed=False)

        # package_id. Note: one byte but convert to 4-byte int
        package_id_b = stream.read(1)
        package_id = int.from_bytes(package_id_b, byteorder='big', signed=False)
        assert(package_id == 0x18)

        # len2
        len2_b = stream.read(1)
        len2  = int.from_bytes(len2_b, byteorder='big', signed=False)
        assert(len2 == 1) # either "a", "c" or "t"

        data_len = len - len2 -2

        # channel
        # write_tick is a bool. only write to TIMESTAMP if channel == tick and TRUE followed
        (write_tick, result) = read_channel(stream, data_len, result,timestamp)

        # printing requested by brandon: note that it is the correct curr timestamp
        if write_tick:
            TIMESTAMP.append(timestamp)

        # read next timestamp and check EOF
        time_stamp_b = stream.read(4)
        if time_stamp_b == b'':
            break
        timestamp = int.from_bytes(time_stamp_b, byteorder='big', signed=False)

    return (result, TIMESTAMP)

def read_varint(stream):
    x = decode_stream(stream)
    y = x.to_bytes(4, byteorder='big')
    return int.from_bytes(y, byteorder='big', signed=True)

def read_channel(stream, data_len, result, timestamp):
    write_tick = False # initialize
    channe_b = stream.read(1)
    channel = channe_b.decode('ascii') 
    if channel == "a": 
        # key_code is an varint
        key_code = read_varint(stream)
        result.append(key_code)

    elif channel == "c":
        assert(data_len == 8)
        pitch_b = stream.read(4)
        yaw_b = stream.read(4)

        # pitch = struct.unpack('f', pitch_b)[0]
        # yaw = struct.unpack('f', yaw_b)[0]
        pitch = struct.unpack('>f', pitch_b)[0]
        yaw = struct.unpack('>f', yaw_b)[0]

        # experimen
        # print("(1)",struct.unpack(">d", struct.pack("<d", pitch)))
        # print("(2)",struct.unpack("<d", struct.pack("<d", pitch)))

        result.append("pitch" + " " + str(pitch))
        result.append("turn" + " " + str(yaw))





    
    elif channel == "t":
        tick_byte_b = stream.read(1)
        tick_byte = int.from_bytes(tick_byte_b, byteorder='big', signed=False )
        assert(tick_byte == 0 or tick_byte == 1)
        if tick_byte == 0:
            result.append(False)
        else:
            write_tick = True # only case it will turn True
            result.append(True)
    else:
        print("Error: unknown channel name")
        return -1

    return (write_tick, result)

if __name__ == '__main__':
    main()


# # function that supports the old format, keep here for reference
# def read_channel_old(stream, len2, data_len, result):
#     channe_b = stream.read(len2)
#     channel = channe_b.decode('ascii') 
#     print("channel:",channel)
#     if channel == "recorded_actions": 
#         assert(data_len == 1)
#         key_code_b = stream.read(data_len)
#         key_code  = int.from_bytes(key_code_b, byteorder='big', signed=False)
#         print("key_code:", key_code)
#         result.append(key_code)

#     elif channel == "recorded_camera_actions":
#         assert(data_len == 8)
#         pitch = struct.unpack('f', stream.read(4))[0]
#         print("pitch:", pitch)
#         yaw = struct.unpack('f', stream.read(4))[0]
#         print("yaw:", yaw)
#         result.append("pitch "+ " " + str(pitch))
#         result.append("turn " + " " + str(yaw))

#     elif channel == "t":
#         tick_byte_b = stream.read(1)
#         tick_byte = int.from_bytes(tick_byte_b,byteorder='big', signed=False )
#         assert(tick_byte == 0 or tick_byte == 1)
#         if tick_byte == 0:
#             result.append(False)
#         else:
#             result.append(True)
#     else:
#         print("Error: unknown channel name")

#     return result
#     