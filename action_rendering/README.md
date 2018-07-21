# action_keycode_malmo <br>

This repo takes action.tmcpr and outputs an array of Action objects. It can convert the Action object array to a malmo command array or network command array. <br>

To obtain action.tmcpr, use cmr-rl/herobrain_parse to download firehose stream (player's minecraft recordings), parse it and unzip result.mcpr.<br>

action_object.py: where Action object is defined. Use to_malmo and to_network if want to convert. 

keycode_dict.py: a dictionary that maps keycode (int) to keyboard event

parse_action.py: opens actions.tmcpr and parse.

keycode_to_malmo.py: 1)  contain BINDINGS that maps keycode to malmo command. 
2) Takes parse_result from parse_action.py and convert them to Action object array 

