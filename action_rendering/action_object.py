# define Action object
# Action object are init with a dictionary called self.actions
# during init, a malmo cmd array is created 
# 	with an empty template and actions dictionary

# return string
def get_hotbar_index(action):
    assert(action.startswith("hotbar."))
    return action[7]

# left attack
# use right

class Action(object):
	def __init__(self, actions):
		super(Action, self).__init__()
		# orders matter
		self.template = ['move 0', 'strafe 0', 'jump 0',
			 'attack 0' ,'use 0', 'discardCurrentItem 0', 'crouch 0', 'pitch 0', 'turn 0']
		self.hotbars_template = [    
			'hotbar.1',
    		'hotbar.2',
    		'hotbar.3',
    		'hotbar.4',
    		'hotbar.5',
    		'hotbar.6',
    		'hotbar.7',
    		'hotbar.8',
    		'hotbar.9' ]
		# for future use of network commands
		self.options = self.init_options()
		# dict
		self.actions = actions # a dict d[key_action]:value

		# init empty
		self.malmo = []
		# first add hotbars
		for hotbar in self.hotbars_template:
			if hotbar in self.actions:
				cmd = hotbar + " " + self.actions[hotbar]
				self.malmo.append(cmd)

		# add to malmo
		for i in range(len(self.template)):
			key = self.get_action(self.template[i])
			if key in self.actions: # if defined in dict
				value = self.actions[key]
				cmd = key + " " + value
				self.malmo.append(cmd)
			else: # default 0, no change
				self.malmo.append(self.template[i]) 

	def __repr__(self):
		return str(self.malmo)

	def to_malmo(self):
		return self.malmo

	def to_network(self):
		self.networkcmd = []
		# first handle hotbar
		self.networkcmd.append([0]*10) 
		hotbars = self.networkcmd[0]
		hotbars[0] = 1# first one is default
		# others
		for av in self.malmo: # av stands for an action-value pair
			a = self.get_action(av)
			v = self.get_value(av)
			
			# to do: check there is only one "1" in this vector
			if a.startswith("hotbar."):
				i = int(get_hotbar_index(a))
				hotbars[0] = 0;
				hotbars[i] = 1;
			else:
				o = self.options[a]
				cmd = self.add_network_cmd(options = o, value_str = v)
			
		return self.networkcmd

	### HELPER FUNCTIONS ###
	def init_options(self):
		# if options == 3, have value 0, -1 or 1
		# if 2, have value 0 or 1
		# hotbar is a len 10 vector
		options = dict()
		options['move'] = 3 
		options['strafe'] = 3
		options['jump'] = 2
		options['attack'] = 2
		options['use'] = 2
		options['discardCurrentItem'] = 2
		options['crouch'] = 2
		options['pitch'] = 1
		options['turn'] = 1
		return options

	def get_action(self,action_value_pair): 
		parse = action_value_pair.split(" ")
		return parse[0]

	def get_value(self,action_value_pair): 
		parse = action_value_pair.split(" ")
		return parse[1]

	def add_network_cmd(self, options, value_str):
		if options == 3:
			value = int(value_str)
			assert(value == 0 or value == 1 or value == -1)
			if value == 0:
				cmd =  [1,0,0]
			elif value == 1:
				cmd =  [0,1,0]
			else:
				cmd =  [0,0,1]

		elif options == 2:
			value = int(value_str)
			assert( value == 0 or value == 1)
			if value == 0:
				cmd =  [1,0]
			else:
				cmd =  [0,1]

		elif options == 1: 
			cmd =  float(value_str)
		
		else: return # ignore hotbar bc already handled 

		self.networkcmd.append(cmd)


