# ------------------------------------------------------------------------------------------------
# Copyright (c) 2018 Microsoft Corporation
# 
# Permission is hereby granted, free of charge, to any person obtaining a copy of this software and
# associated documentation files (the "Software"), to deal in the Software without restriction,
# including without limitation the rights to use, copy, modify, merge, publish, distribute,
# sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
# 
# The above copyright notice and this permission notice shall be included in all copies or
# substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT
# NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,
# DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
# ------------------------------------------------------------------------------------------------

import copy
import collections
import json
import logging
import os
import random
import socket
import struct
import time
import uuid
from copy import copy, deepcopy
from typing import Iterable

import gym
import gym.envs.registration
import gym.spaces
import minerl.env.spaces
import numpy as np
from lxml import etree
from minerl.env import comms
from minerl.env.comms import retry
from minerl.env.malmo import InstanceManager
from minerl.env.malmo import malmo_version

logger = logging.getLogger(__name__)

missions_dir = os.path.join(os.path.dirname(__file__), 'missions')



class EnvException(Exception):
    """A special exception thrown in the creation of an environment's Malmo mission XML.
    
    Args:
        message (str): The exception message. 
    """
    def __init__(self, message):
        super(EnvException, self).__init__(message)


class MissionInitException(Exception):
    """An exception thrown when a mission fails to initialize
    
    Args:
        message (str): The exception message. 
    """
    def __init__(self, message):
        super(MissionInitException, self).__init__(message)


MAX_WAIT = 60 * 4 # After this many MALMO_BUSY's a timeout exception will be thrown 
SOCKTIME = 60.0 * 4 # After this much time a socket exception will be thrown.

class MineRLEnv(gym.Env):
    """The MineRLEnv class.

        Example:
            To actually create a MineRLEnv. Use any one of the package MineRL environments (Todo: Link.)
            literal blocks::

                import minerl
                import gym

                env = gym.make('MineRLTreechop-v0') # Makes a minerl environment.
                
                # Use env like any other OpenAI gym environment.
                # ...
            
        
        Args:
            xml (str): The path to the MissionXML file for this environment.
            observation_space (gym.Space): The observation for the environment.
            action_space (gym.Space): The action space for the environment.
            port (int, optional): The port of an exisitng Malmo environment. Defaults to None.
            noop_action (Any, optional): The no-op action for the environment. This must be in the action_space. Defaults to None.
        """
    metadata = {'render.modes': []}
    
    def __init__(self, xml, observation_space, action_space, port=None, noop_action=None, docstr=None):
        self.action_space = None
        self.observation_space = None
        self._default_action = noop_action

        self.xml = None
        self.integratedServerPort = 0
        self.role = 0
        self.agent_count = 0
        self.resets = 0
        self.ns = '{http://ProjectMalmo.microsoft.com}'
        self.client_socket = None

        self.resync_period = 0
        self.turn_key = ""
        self.exp_uid = ""
        self.done = True
        self.synchronous = True
        self.step_options = None
        self.width = 0
        self.height = 0
        self.depth = 0

        self.xml_file = xml
        self.has_init = False
        self.instance = None
        self.had_to_clean = False

        self.init(observation_space, action_space, port=port)

    def init(self,  observation_space, action_space,  port=None):
        """Initializes the MineRL Environment.

        Note: 
            This is called automatically when the environment is made.
        
        Args:
            observation_space (gym.Space): The observation for the environment.
            action_space (gym.Space): The action space for the environment.
            port (int, optional): The port of an exisitng Malmo environment. Defaults to None.
        
        Raises:
            EnvException: If the Mission XML is malformed this is thrown.
            ValueError: The space specified for this environment does not have a default action.
            NotImplementedError: When multiagent environments are attempted to be used.
        """
        step_options = 0
        resync = 0
        episode = 0
        exp_uid = None
        if self.instance == None:
            if not port is  None:
                self.instance = InstanceManager.add_existing_instance(port)
            else:
                self.instance = InstanceManager.get_instance().__enter__()
        # Parse XML file
        with open(self.xml_file, 'r') as f:
            xml_text = f.read()
        xml = xml_text.replace('$(MISSIONS_DIR)', missions_dir)
        
        # Bootstrap the environment if it hasn't been.
        role = 0

        if not xml.startswith('<Mission'):
            i = xml.index("<Mission")
            if i == -1:
                raise EnvException("Mission xml must contain <Mission> tag.")
            xml = xml[i:]

        self.xml = etree.fromstring(xml)
        self.role = role
        if exp_uid is None:
            self.exp_uid = str(uuid.uuid4())
        else:
            self.exp_uid = exp_uid

        self.action_space = action_space
        self.observation_space = observation_space

        def map_space(space):
            if isinstance(space, gym.spaces.Discrete) or isinstance(space, minerl.env.spaces.Enum):
                return 0
            elif isinstance(space, gym.spaces.Box):
                return np.zeros(shape=space.shape, dtype=space.dtype)
            else:
                try:
                    return space.default()
                except NameError:
                    raise ValueError('Specify non-None default_action in gym.register or extend all action spaces with default() method')
        if self._default_action is None:
            self._default_action = {key: map_space(space) for key, space in action_space.spaces.items()}
        def noop_func(a):
            return deepcopy(self._default_action)

        boundmethd = _bind(self.action_space, noop_func)
        self.action_space.noop = boundmethd

        # Force single agent
        self.agent_count = 1
        turn_based = self.xml.find('.//' + self.ns + 'TurnBasedCommands') is not None
        if turn_based:
            raise NotImplementedError("Turn based or multi-agent environments not supported.")
        else:
            self.turn_key = ""

        # Unclear what step_options does.            
        if step_options is None:
            self.step_options = 0 if not turn_based else 2
        else:
            self.step_options = step_options
        
        self.done = True

        self.resync_period = resync
        self.resets = episode

        e = etree.fromstring("""<MissionInit xmlns="http://ProjectMalmo.microsoft.com" 
                                xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" 
                                SchemaVersion="" PlatformVersion=""" + '\"' + malmo_version + '\"' +
                             """>
                                <ExperimentUID></ExperimentUID>
                                <ClientRole>0</ClientRole>
                                <ClientAgentConnection>
                                    <ClientIPAddress>127.0.0.1</ClientIPAddress>
                                    <ClientMissionControlPort>0</ClientMissionControlPort>
                                    <ClientCommandsPort>0</ClientCommandsPort>
                                    <AgentIPAddress>127.0.0.1</AgentIPAddress>
                                    <AgentMissionControlPort>0</AgentMissionControlPort>
                                    <AgentVideoPort>0</AgentVideoPort>
                                    <AgentDepthPort>0</AgentDepthPort>
                                    <AgentLuminancePort>0</AgentLuminancePort>
                                    <AgentObservationsPort>0</AgentObservationsPort>
                                    <AgentRewardsPort>0</AgentRewardsPort>
                                    <AgentColourMapPort>0</AgentColourMapPort>
                                    </ClientAgentConnection>
                                </MissionInit>""")
        e.insert(0, self.xml)
        self.xml = e
        self.xml.find(self.ns + 'ClientRole').text = str(self.role)
        self.xml.find(self.ns + 'ExperimentUID').text = self.exp_uid
        if self.role != 0 and self.agent_count > 1:
            e = etree.Element(self.ns + 'MinecraftServerConnection',
                              attrib={'address': self.instance.host,
                                      'port': str(0)
                                      })
            self.xml.insert(2, e)

        video_producers = self.xml.findall('.//' + self.ns + 'VideoProducer')
        assert len(video_producers) == self.agent_count
        video_producer = video_producers[self.role]
        # Todo: Deprecate width, height, and POV forcing.
        self.width = int(video_producer.find(self.ns + 'Width').text)
        self.height = int(video_producer.find(self.ns + 'Height').text)
        want_depth = video_producer.attrib["want_depth"]
        self.depth = 4 if want_depth is not None and (want_depth == "true" or want_depth == "1" or want_depth is True) else 3
        # print(etree.tostring(self.xml))

        self.has_init = True

    def noop_action(self):
        """Gets the no-op action for the environment.

        In addition one can get the no-op/default action directly from the action space.
        
            env.action_space.noop()

        
        Returns:
            Any: A no-op action in the env's space.
        """
        return deepcopy(self._default_action)

    def _process_observation(self, pov, info):
        """
        Process observation into the proper dict space.
        """
        pov = np.frombuffer(pov, dtype=np.uint8)

        if pov is None or len(pov) == 0:
            pov = np.zeros((self.height, self.width, self.depth), dtype=np.uint8)
        else:
            pov = pov.reshape((self.height, self.width, self.depth))[::-1,:,:]

        if info:
            info = json.loads(info)
        else:
            info = {}

        # Process Info: (HotFix until updated in Malmo.)
        if "inventory" in info  and "inventory" in self.observation_space.spaces:
            inventory_spaces = self.observation_space.spaces['inventory'].spaces

            items = inventory_spaces.keys()
            inventory_dict = {k: 0 for k in inventory_spaces}
            # TODO change to maalmo
            for stack in info['inventory']:
                if 'type' in stack and 'quantity' in stack:
                    try:
                        inventory_dict[stack['type']] += stack['quantity'] 
                    except ValueError:
                        continue
                    except KeyError:
                        # We only care to observe what was specified in the space.
                        continue
            info['inventory'] = inventory_dict
        elif  "inventory" in self.observation_space.spaces and not "inventory" in info:
            # logger.warning("No inventory found in malmo observation! Yielding empty inventory.")
            # logger.warning(info)
            pass

        obs_dict = {
            'pov': pov
        }


        # Todo: Make this logic dict recursive.
        for k in self.observation_space.spaces:
            if k is not 'pov':
                if not (k in  info):
                    correction = self.observation_space.spaces[k].sample()
                    if isinstance(self.observation_space.spaces[k], gym.spaces.Dict):
                        for k in correction:
                            if not isinstance(correction[k], dict) and not isinstance(correction[k], collections.OrderedDict):
                                correction[k] *= 0
                    info[k] = correction
                    # logger.warning("Missing observation {} in Malmo".format(k))
                
                obs_dict[k] = info[k]

        return obs_dict

    def _process_action(self, action_in) -> str:
        """
        Process the actions into a proper command.
        """
        action_in = deepcopy(action_in)
        action_str = []
        for act in action_in:
            # Process enums.
            if isinstance(self.action_space.spaces[act], minerl.env.spaces.Enum):
                if isinstance(action_in[act], int):
                    action_in[act] = self.action_space.spaces[act].values[action_in[act]]
                else:
                    assert isinstance(action_in[act], str), "Enum action {} must be str or int".format(act)
                    assert action_in[act] in self.action_space.spaces[act].values, "Invalid value for enum action {}, {}".format(act, action_in[act])

            elif isinstance(self.action_space.spaces[act], gym.spaces.Box):
                subact = action_in[act]
                assert not isinstance(subact, str), "Box action {} is a string! It should be a ndarray: {}".format(act, subact)
                if isinstance(subact, np.ndarray):
                    subact = subact.flatten()
                
                if isinstance(subact, Iterable):
                    subact = " ".join(str(x) for x in subact)
    
                action_in[act] = subact

            action_str.append(
                "{} {}".format(act, str(action_in[act])))

        return "\n".join(action_str)


    @staticmethod
    def _hello(sock):
        comms.send_message(sock, ("<MalmoEnv" + malmo_version + "/>").encode())

    def reset(self):
        # Add support for existing instances.
        if not self.has_init:
            self.init()

        while not self.done:
            self.done = self._quit_episode()

            if not self.done:
                time.sleep(0.1)

        return self._start_up()

    @retry
    def _start_up(self):
        self.resets += 1

        try:
            if not self.client_socket:

                logger.debug("Creating socket connection!")
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
                sock.settimeout(SOCKTIME)
                sock.connect((self.instance.host, self.instance.port))
                self._hello(sock)
                
                self.client_socket = sock  # Now retries will use connected socket.
            self._init_mission()

            self.done = False
            return self._peek_obs()
        except socket.timeout as e:
            logger.error("Failed to reset (timeout), trying again!")
            self._clean_connection()
            raise e

    def _clean_connection(self):
        self.client_socket.shutdown(socket.SHUT_RDWR)
        self.client_socket.close()
        self.client_socket = None
        if self.had_to_clean:
            # Connect to a new instance!!
            logger.error("Connection with Minecraft client cleaned more than once; restarting.")
            if self.instance:
                self.instance.kill()
            self.instance = InstanceManager.get_instance().__enter__()
            self.had_to_clean = False
        else:
            self.had_to_clean = True

    def _peek_obs(self):
        obs = None
        start_time = time.time()
        if not self.done:
            logger.debug("Peeking the client.")
            peek_message = "<Peek/>"
            comms.send_message(self.client_socket, peek_message.encode())
            obs = comms.recv_message(self.client_socket)
            info = comms.recv_message(self.client_socket).decode('utf-8')

            
            reply = comms.recv_message(self.client_socket)
            done, = struct.unpack('!b', reply)
            self.done = done == 1
            if obs is None or len(obs) == 0:
                if time.time() - start_time > MAX_WAIT:
                    self.client_socket.close()
                    self.client_socket = None
                    raise MissionInitException('too long waiting for first observation')
                time.sleep(0.1)

        return self._process_observation(obs,info), {}

    def _quit_episode(self):
        comms.send_message(self.client_socket, "<Quit/>".encode())
        reply = comms.recv_message(self.client_socket)
        ok, = struct.unpack('!I', reply)
        return ok != 0

    def seed(self):
        """Seeds the environment.
        
        Note: 
            This is NOT implemented.
        """
        logger.warn("Seeds not supported yet.")

    def step(self, action):
        obs = None
        reward = None
        info = None
        turn = True
        withturnkey = self.step_options < 2
        # print(withturnkey)
        withinfo = self.step_options == 0 or self.step_options == 2

        malmo_command =  self._process_action(action)
        
        try:
            if not self.done:
                
                step_message = "<Step" + str(self.step_options) + ">" + \
                            malmo_command + \
                            "</Step" + str(self.step_options) + " >"
                t0 = time.time()
                comms.send_message(self.client_socket, step_message.encode())
                # print("send action {}".format(time.time() - t0)); t0 = time.time()
                if withturnkey:
                    comms.send_message(self.client_socket, self.turn_key.encode())
                obs = comms.recv_message(self.client_socket)
                # print("recieve obs {}".format(time.time() - t0)); t0 = time.time()

                reply = comms.recv_message(self.client_socket)
                reward, done, sent = struct.unpack('!dbb', reply)
                # print("recieve reward {}".format(time.time() - t0)); t0 = time.time()
                self.done = done == 1
                if withinfo:
                    info = comms.recv_message(self.client_socket).decode('utf-8')
                
                out_obs = self._process_observation(obs, info)
                

                turn_key = comms.recv_message(self.client_socket).decode('utf-8') if withturnkey else ""
                # print("[" + str(self.role) + "] TK " + turn_key + " self.TK " + str(self.turn_key))
                if turn_key != "":
                    if sent != 0:
                        turn = False
                    # Done turns if: turn = self.turn_key == turn_key
                    self.turn_key = turn_key
                else:
                    turn = sent == 0

                # if (obs is None or len(obs) == 0) or turn:
                    # time.sleep(0.1)
                # print("turnkeyprocessor {}".format(time.time() - t0)); t0 = time.time()
                # print("creating obs from buffer {}".format(time.time() - t0)); t0 = time.time()
                return out_obs, reward, self.done, {}
            else:
                raise RuntimeError("Attempted to step an environment with done=True")
        except socket.timeout as e:
            # If the socket times out some how! We need to catch this and reset the environment.
            self._clean_connection()
            self.done = True
            logger.error(
                "Failed to take a step (timeout). Terminating episode and sending random observation, be aware. "
                "To account for this failure case in your code check to see if `'error' in info` where info is "
                "the info dictionary returned by the step function.")
            return self.observation_space.sample(), 0, self.done, {"error": "Connection timed out!"}


    def close(self):
        """gym api close"""
        try:
            # Purge last token from head node with <Close> message.
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect((self.instance.host, self.instance.port))
            self._hello(sock)

            comms.send_message(sock, ("<Close>" + self._get_token() + "</Close>").encode())
            reply = comms.recv_message(sock)
            ok, = struct.unpack('!I', reply)
            assert ok
            sock.close()
        except Exception as e:
            self._log_error(e)
        if self.client_socket:
            self.client_socket.close()
            self.client_socket = None

        if self.instance and self.instance.running:
            self.instance.kill()

    def reinit(self):
        """Use carefully to reset the episode count to 0."""
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((self.instance.host, self.instance.port))
        self._hello(sock)

        comms.send_message(sock, ("<Init>" + self._get_token() + "</Init>").encode())
        reply = comms.recv_message(sock)
        sock.close()
        ok, = struct.unpack('!I', reply)
        return ok != 0

    def status(self, head):
        """Get status from server.
        head - Ping the the head node if True.
        """
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        if head:
            sock.connect((self.instance.host, self.instance.port))
        else:
            sock.connect((self.instance.host2, self.instance.port2))
        self._hello(sock)

        comms.send_message(sock, "<Status/>".encode())
        status = comms.recv_message(sock).decode('utf-8')
        sock.close()
        return status

    def _find_server(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((self.instance.host, self.instance.port))
        self._hello(sock)

        start_time = time.time()
        port = 0
        while port == 0:
            comms.send_message(sock, ("<Find>" + self._get_token() + "</Find>").encode())
            reply = comms.recv_message(sock)
            port, = struct.unpack('!I', reply)
            if port == 0:
                if time.time() - start_time > MAX_WAIT:
                    if self.client_socket:
                        self.client_socket.close()
                        self.client_socket = None
                    raise MissionInitException('too long finding mission to join')
                time.sleep(1)
        sock.close()
        # print("Found mission integrated server port " + str(port))
        self.integratedServerPort = port
        e = self.xml.find(self.ns + 'MinecraftServerConnection')
        if e is not None:
            e.attrib['port'] = str(self.integratedServerPort)

    def _init_mission(self):
        ok = 0
        num_retries =0
        logger.debug("Sending mission init!")
        while ok != 1:
            xml = etree.tostring(self.xml)
            token = (self._get_token() + ":" + str(self.agent_count) + ":" + str(self.synchronous).lower()).encode()
            comms.send_message(self.client_socket, xml)
            comms.send_message(self.client_socket, token)

            reply = comms.recv_message(self.client_socket)
            ok, = struct.unpack('!I', reply)
            self.turn_key = comms.recv_message(self.client_socket).decode('utf-8')
            if ok != 1:
                num_retries += 1
                if num_retries > MAX_WAIT:
                    raise socket.timeout()
                logger.debug("Recieved a MALMOBUSY from Malmo; trying again.")
                time.sleep(1)

    def _get_token(self):
        return self.exp_uid + ":" + str(self.role) + ":" + str(self.resets)


def make():
    return Env()


def register(id, **kwargs):
    # TODO create doc string based on registered envs
    return gym.envs.register(id, **kwargs)

def _bind(instance, func, as_name=None):
    """
    Bind the function *func* to *instance*, with either provided name *as_name*
    or the existing name of *func*. The provided *func* should accept the 
    instance as the first argument, i.e. "self".
    """
    if as_name is None:
        as_name = func.__name__
    bound_method = func.__get__(instance, instance.__class__)
    setattr(instance, as_name, bound_method)
    return bound_method