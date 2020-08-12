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

import collections

import copy
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

# TODO: Drop inflection dependencies.
import inflection as inflection
import numpy as np
from lxml import etree
import xmltodict
from minerl.env import comms
from minerl.env.comms import retry
from minerl.env.malmo import InstanceManager, malmo_version, launch_queue_logger_thread

import minerl.herobraine.hero.spaces as spaces
from minerl.herobraine.wrapper import EnvWrapper

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


MAX_WAIT = 80  # After this many MALMO_BUSY's a timeout exception will be thrown
SOCKTIME = 60.0 * 4  # After this much time a socket exception will be thrown.
MINERL_CUSTOM_ENV_ID = 'MineRLCustomEnv'  # Default id for a MineRLEnv
TICK_LENGTH = 0.05

class MineRLEnv(gym.Env):
    """The MineRLEnv class.

        Example:
            To actually create a MineRLEnv. Use any one of the package MineRL environments (Todo: Link.)
            literal blocks::

                import minerl
                import gym

                env = gym.make('MineRLTreechop-v0') # Makes a minerl environment.
                # env = gym.make('UnifiedMineRL-v0', xml='treechop.xml') # Makes a treechop minerl environment with unified action and observation spaces

                # Use env like any other OpenAI gym environment.
                # ...

                # Alternatively:
                env = gym.make('MineRLTreechop-v0') # makes a default treechop environment (with treechop-specific action and observation spaces)

        Args:
            xml (str): The path to the MissionXML file for this environment.
            observation_space (gym.Space): The observation for the environment.
            action_space (gym.Space): The action space for the environment.
            port (int, optional): The port of an exisitng Malmo environment. Defaults to None.
            noop_action (Any, optional): The no-op action for the environment. This must be in the action_space. Defaults to None.
            restartable_java (bool, optional): whether java process should restart on failure. Defaults to True
            reset_mission_xml_fn (callable, optional): A function that can modifiy mission xml before passing it to Malmo. Will be called on every mission reset,
                                                       can be stochastic (for instance, for domain randomization). Defaults to None (no modification).
        """
    metadata = {'render.modes': ['rgb_array', 'human']}

    STEP_OPTIONS = 0

    def __init__(self, 
        xml, 
        observation_space, 
        action_space, 
        env_spec, 
        port=None, 
        docstr=None,
        restartable_java=True,
        reset_mission_xml_fn=None):
        self.action_space = None
        self.observation_space = None

        self.viewer = None

        self._last_ac = None
        self.xml = None
        self.integratedServerPort = 0
        self.role = 0
        self.agent_count = 0
        self.resets = 0
        self.ns = "{http://ProjectMalmo.microsoft.com}"
        self.client_socket = None

        self.exp_uid = ""
        self.done = True
        self.synchronous = True

        self.width = 0
        self.height = 0
        self.channels = 0 

        self.xml_in = xml
        self.has_init = False
        self._seed = None
        self.had_to_clean = False
        
        self._already_closed = False
        self.restartable_java = restartable_java
        self._is_interacting = False
        self._is_real_time = False
        self._last_step_time = -1
        self._already_closed = False
        self.env_spec = env_spec

        self.observation_space = observation_space
        self.action_space = action_space

        self.resets = 0
        self.done = True
        self.agent_info = {}
        self.reset_mission_xml_fn = reset_mission_xml_fn or (lambda x: x)
        
        self.instance = self._get_new_instance(port)

    def _get_new_instance(self, port=None, instance_id=None):
        """
        Gets a new instance and sets up a logger if need be. 
        """

        if not port is None:
            instance = InstanceManager.add_existing_instance(port)
        else:
            instance = InstanceManager.get_instance(os.getpid(), instance_id=instance_id)

        if InstanceManager.is_remote():
            launch_queue_logger_thread(instance, self.is_closed)

        instance.launch(replaceable=self.restartable_java) 
        return instance

    def init(self):
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
        exp_uid = None

        # Parse XML file
        xml = self.xml_in
        xml = xml.replace("$(MISSIONS_DIR)", missions_dir)

        if self.spec is not None:
            xml = xml.replace("$(ENV_NAME)", self.spec.id)
        else:
            xml = xml.replace("$(ENV_NAME)", MINERL_CUSTOM_ENV_ID)

        # Bootstrap the environment if it hasn't been.
        role = 0

        if not xml.startswith("<Mission"):
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

        # Force single agent
        self.agent_count = 1
        turn_based = self.xml.find(".//" + self.ns + "TurnBasedCommands") is not None
        if turn_based:
            raise NotImplementedError(
                "Turn based or multi-agent environments not supported."
            )

        e = etree.fromstring(
            """<MissionInit xmlns="http://ProjectMalmo.microsoft.com"
                                xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
                                SchemaVersion="" PlatformVersion="""
            + '"'
            + malmo_version
            + '"'
            + """>
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

        if self._is_interacting:
            hi = etree.fromstring("""
                <HumanInteraction>
                    <Port>{}</Port>
                    <MaxPlayers>{}</MaxPlayers>
                </HumanInteraction>""".format(self.interact_port, self.max_players))
            # Update the xml

            ss  = self.xml.find(".//" + self.ns + 'ServerSection')
            ss.insert(0, hi)
        
        # pass the xml through the modifier function before extracting agent handler
        # and video_producer to make sure those have not been set to some invalid values

        # Ensure all observations are present for unified env.
        agent_handler = self.xml.find(".//" + self.ns + "AgentHandlers")
        if agent_handler.find("./" + self.ns + "ObservationFromEquippedItem") is None:
            etree.SubElement(agent_handler, self.ns + "ObservationFromEquippedItem")

        if agent_handler.find("./" + self.ns + "ObservationFromFullInventory") is None:
            etree.SubElement(
                agent_handler,
                self.ns + "ObservationFromFullInventory",
                attrib={"flat": "false"},
            )

        # TODO (R): REPLACE WITH JT TEMPLATING
        self._last_ac = None


        self.has_init = True

    def noop_action(self):
        """Gets the no-op action for the environment.

        In addition one can get the no-op/default action directly from the action space.

            env.action_space.noop()


        Returns:
            Any: A no-op action in the env's space.
        """
        return self.action_space.no_op()

    def _process_observation(self, pov, info):
        """
        Process observation into the proper dict space.
        """
        pov = np.frombuffer(pov, dtype=np.uint8)

        if pov is None or len(pov) == 0:
            pov = np.zeros((self.height, self.width, self.channels), dtype=np.uint8)
        else:
            pov = pov.reshape((self.height, self.width, self.channels))[::-1, :, :]

        if info:
            info = json.loads(info)
        else:
            info = {}

        
        info['pov'] = pov
        
        bottom_env_spec = self.env_spec
        while isinstance(bottom_env_spec, EnvWrapper):
            bottom_env_spec = bottom_env_spec.env_to_wrap
        
        # Process all of the observations using handlers.
        for h in bottom_env_spec.observables:
            obs_dict[h.to_string()] = h.from_hero(info)

        # TODO (R): Use reward handlers
        # TODO (R): Add achievment handlers. 
        # Add Achievements to observation
        if "achievements" in info:
            obs_dict["achievements"] = info["achievements"]
            
        # TODO (REI): CONVERT TO OBSERVATION HANDLER!
        # Add structure grid to observation
        if "structure" in info:
            obs_dict["structure"] = info["structure"]

        self._last_pov = obs_dict['pov']
        self._last_obs = obs_dict
        
        # Now we wrap
        if isinstance(self.env_spec, EnvWrapper):
            obs_dict = self.env_spec.wrap_observation(obs_dict)
        return obs_dict

    def _process_action(self, action_in) -> str:
        """
        Process the actions into a proper command.
        """
        self._last_ac = action_in
        action_in = deepcopy(action_in)

        # TODO(wguss): Clean up the envSpec wrapper paradigm,
        # the env shouldn't be doing this IMO.
        if isinstance(self.env_spec, EnvWrapper):
            action_in = self.env_spec.unwrap_action(action_in)

        bottom_env_spec = self.env_spec
        while isinstance(bottom_env_spec, EnvWrapper):
            bottom_env_spec = bottom_env_spec.env_to_wrap

        assert action_in in bottom_env_spec.action_space

        action_str = []
        for h in bottom_env_spec.actionables:
            action_str.append(h.to_hero(action_in[h.to_string()]))

        return "\n".join(action_str)

    def make_interactive(self, port, max_players=10, realtime=True):
        """
        Enables human interaction with the environment.

        To interact with the environment add `make_interactive` to your agent's evaluation code
        and then run the `minerl.interactor.`

        For example:

        .. code-block:: python

            env = gym.make('MineRL...')
            
            # set the environment to allow interactive connections on port 6666
            # and slow the tick speed to 6666.
            env.make_interactive(port=6666, realtime=True) 

            # reset the env
            env.reset()
            
            # interact as normal.
            ...


        Then while the agent is running, you can start the interactor with the following command.

        .. code-block:: bash

            python3 -m minerl.interactor 6666 # replace with the port above.


        The interactor will disconnect when the mission resets, but you can connect again with the same command.
        If an interactor is already started, it won't need to be relaunched when running the commnad a second time.
        

        Args:
            port (int):  The interaction port
            realtime (bool, optional): If we should slow ticking to real time.. Defaults to True.
            max_players (int): The maximum number of players

        """
        self._is_interacting = True
        self._is_real_time = realtime
        self.interact_port = port
        self.max_players = max_players
            

    @staticmethod
    def _hello(sock):
        comms.send_message(sock, ("<MalmoEnv" + malmo_version + "/>").encode())

    def reset(self):
        # Add support for existing instances.
        try:
            if not self.has_init:
                self.init()

            while not self.done:
                self.done = self._quit_episode()

                if not self.done:
                    time.sleep(0.1)

            return self._start_up()
        finally:
            # We don't force the same seed every episode, you gotta send it yourself queen.
            self._seed = None

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

                # Now retries will use connected socket.
                self.client_socket = sock
            self._init_mission()

            self.done = False
            return self._peek_obs()
        except (socket.timeout, socket.error) as e:
            logger.error("Failed to reset (socket error), trying again!")
            self._clean_connection()
            raise e
        except RuntimeError as e:
            # Reset the instance if there was an error timeout waiting for episode pause.
            self.had_to_clean = True
            self._clean_connection()
            raise e

    def _clean_connection(self):
        logger.error("Cleaning connection! Something must have gone wrong.")
        try:
            if self.client_socket:
                self.client_socket.shutdown(socket.SHUT_RDWR)
                self.client_socket.close()
        except (BrokenPipeError, OSError, socket.error):
            # There is no connection left!
            pass

        self.client_socket = None
        if self.had_to_clean:
            # Connect to a new instance!!
            logger.error(
                "Connection with Minecraft client cleaned more than once; restarting.")
            if self.instance:
                self.instance.kill()
            
            self.instance = self._get_new_instance(instance_id=self.instance.instance_id)

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
                    raise MissionInitException(
                        'too long waiting for first observation')
                time.sleep(0.1)
            if self.done:
                raise RuntimeError(
                    "Something went wrong resetting the environment! "
                    "`done` was true on first frame.")

        # See if there is an integrated port
        if self._is_interacting:
            port = self._find_server()
            self.integratedServerPort = port
            logger.warn("MineRL agent is public, connect on port {} with Minecraft 1.11".format(port))
            # Todo make a launch command.
            


        return self._process_observation(obs, info)

    def _quit_episode(self):
        comms.send_message(self.client_socket, "<Quit/>".encode())
        reply = comms.recv_message(self.client_socket)
        ok, = struct.unpack('!I', reply)
        return ok != 0

    def seed(self, seed=42, seed_spaces=True):
        """Seeds the environment!

        This also seeds the aciton_space and observation_space sampling.

        Note:
        THIS MUST BE CALLED BEFORE :code:`env.reset()`
        
        Args:
            seed (long, optional):  Defaults to 42.
            seed_spaces (bool, option): If the observation space and action space shoud be seeded. Defaults to True.
        """
        assert isinstance(seed, int), "Seed must be an int!"
        self._seed = seed
        if seed_spaces:
            self.observation_space.seed(self._seed)
            self.action_space.seed(self._seed)


    def step(self, action):

        withinfo = MineRLEnv.STEP_OPTIONS == 0 or MineRLEnv.STEP_OPTIONS == 2

        # Process the actions.
        malmo_command = self._process_action(action) # : str
        try:
            if not self.done:

                step_message = "<Step" + str(MineRLEnv.STEP_OPTIONS) + ">" + \
                               malmo_command + \
                               "</Step" + str(MineRLEnv.STEP_OPTIONS) + " >"

                # Send Actions.
                comms.send_message(self.client_socket, step_message.encode())

                # Receive the observation.
                obs = comms.recv_message(self.client_socket)

                # Receive reward done and sent.
                reply = comms.recv_message(self.client_socket)
                reward, done, sent = struct.unpack('!dbb', reply)

                # Receive info from the environment.
                if withinfo:
                    info = comms.recv_message(
                        self.client_socket).decode('utf-8')
                else:
                    info = {}

                # Process the observation and done state.
                out_obs = self._process_observation(obs, info)
                self.done = (done == 1)
                
                if self._is_real_time:
                    t0 = time.time()
                    # Todo: Add catch-up
                    time.sleep(max(0, TICK_LENGTH - (t0 - self._last_step_time)))
                    self._last_step_time = time.time()



                return out_obs, reward, self.done, {}
            else:
                raise RuntimeError(
                    "Attempted to step an environment with done=True")
        except (socket.timeout, socket.error, TypeError) as e:
            # If the socket times out some how! We need to catch this and reset the environment.
            self._clean_connection()
            self.done = True
            logger.error(
                "Failed to take a step (timeout or error). Terminating episode and sending random observation, be aware. "
                "To account for this failure case in your code check to see if `'error' in info` where info is "
                "the info dictionary returned by the step function.")
            return self.observation_space.sample(), 0, self.done, {"error": "Connection timed out!"}

    def _renderObs(self, obs, ac=None):
        if self.viewer is None:
            from minerl.viewer.trajectory_display import HumanTrajectoryDisplay, VectorTrajectoryDisplay
            vector_display = 'Vector' in self.env_spec.name
            header= self.env_spec.name
            # TODO: env_specs should specify renderers.
            instructions='{}.render()\n Actions listed below.'.format(header)
            subtext = 'render'
            cum_rewards=None
            if not vector_display:
                self.viewer= HumanTrajectoryDisplay(
                    header, subtext, instructions=instructions,
                    cum_rewards=cum_rewards)

            else:
                self.viewer= VectorTrajectoryDisplay(
                    header, subtext, instructions=instructions,
                    cum_rewards=cum_rewards)
        # Todo: support more information to the render
        self.viewer.render(obs, 0, 0, ac, 0, 1)

        return self.viewer.isopen

    def render(self, mode='human'):
        if mode == 'human' and (
                not 'AICROWD_IS_GRADING' in os.environ or os.environ['AICROWD_IS_GRADING'] is None):
            self._renderObs(self._last_obs, self._last_ac)
        return self._last_pov

    def is_closed(self):
        return self._already_closed

    def close(self):
        """gym api close"""
        if self.viewer is not None:
            self.viewer.close()
            self.viewer = None

        if self._already_closed:
            return

        if self.client_socket:
            self.client_socket.close()
            self.client_socket = None

        if self.instance and self.instance.running:
            self.instance.kill()

        self._already_closed = True

    def reinit(self):
        """Use carefully to reset the episode count to 0."""
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((self.instance.host, self.instance.port))
        self._hello(sock)

        comms.send_message(sock, ("<Init>" + self._get_token() + "</Init>").encode())
        reply = comms.recv_message(sock)
        sock.close()
        (ok,) = struct.unpack("!I", reply)
        return ok != 0

    def status(self):
        """Get status from server.
        head - Ping the the head node if True.
        """
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((self.instance.host, self.instance.port))

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
            comms.send_message(
                sock, ("<Find>" + self._get_token() + "</Find>").encode())
            reply = comms.recv_message(sock)
            port, = struct.unpack('!I', reply)
        sock.close()
        # print("Found mission integrated server port " + str(port))
        return  port
        # e = self.xml.find(self.ns + 'MinecraftServerConnection')
        # if e is not None:
        #     e.attrib['port'] = str(self.integratedServerPort)

    def _init_mission(self):
        ok = 0
        num_retries = 0
        logger.debug("Sending mission init!")
        while ok != 1:
            xml = etree.tostring(self.xml)
            # inject mission dict into the xml
            xml_dict = self.reset_mission_xml_fn(xmltodict.parse(xml))
            # set up video properties in the unlikely event of their change
            video_producers = _deepdict_find(xml_dict, "VideoProducer")
            assert len(video_producers) == self.agent_count
            video_producer = video_producers[self.role]
            # Todo: Deprecate width, height, and POV forcing.
            self.width = int(video_producer["Width"])
            self.height = int(video_producer["Height"])
            want_depth = video_producer.get("@want_depth")
            self.channels = (
                4
                if want_depth is not None
                and (want_depth == "true" or want_depth == "1" or want_depth is True)
                else 3
            )
            # roundtrip through etree to escape symbols correctly
            # and make printing pretty
            xml = etree.tostring(etree.fromstring(xmltodict.unparse(xml_dict).encode()))
            token = (
                self._get_token()
                + ":"
                + str(self.agent_count)
                + ":"
                + str(self.synchronous).lower()
            )
            if self._seed is not None:
                token += ":{}".format(self._seed)
            token = token.encode()
            comms.send_message(self.client_socket, xml)
            comms.send_message(self.client_socket, token)

            reply = comms.recv_message(self.client_socket)
            (ok,) = struct.unpack("!I", reply)
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


class TraceRecording(object):
    # Todo (R): Fix trace recorder.
    _id_counter = 0

    def __init__(self, directory=None):
        """
        Create a TraceRecording, writing into directory
        """

        if directory is None:
            directory = os.path.join('/tmp', 'openai.gym.{}.{}'.format(time.time(), os.getpid()))
            os.mkdir(directory)

        self.directory = directory
        self.file_prefix = 'openaigym.trace.{}.{}'.format(self._id_counter, os.getpid())
        TraceRecording._id_counter += 1

        self.closed = False

        self.actions = []
        self.observations = []
        self.rewards = []
        self.episode_id = 0

        self.buffered_step_count = 0
        self.buffer_batch_size = 100

        self.episodes_first = 0
        self.episodes = []
        self.batches = []

    def add_reset(self, observation):
        assert not self.closed
        self.end_episode()
        self.observations.append(observation)

    def add_step(self, action, observation, reward):
        assert not self.closed
        self.actions.append(action)
        self.observations.append(observation)
        self.rewards.append(reward)
        self.buffered_step_count += 1

    def end_episode(self):
        """
        if len(observations) == 0, nothing has happened yet.
        If len(observations) == 1, then len(actions) == 0, and we have only called reset and done a null episode.
        """
        if len(self.observations) > 0:
            if len(self.episodes) == 0:
                self.episodes_first = self.episode_id

            self.episodes.append({
                'actions': optimize_list_of_ndarrays(self.actions),
                'observations': optimize_list_of_ndarrays(self.observations),
                'rewards': optimize_list_of_ndarrays(self.rewards),
            })
            self.actions = []
            self.observations = []
            self.rewards = []
            self.episode_id += 1

            if self.buffered_step_count >= self.buffer_batch_size:
                self.save_complete()

    def save_complete(self):
        """
        Save the latest batch and write a manifest listing all the batches.
        We save the arrays as raw binary, in a format compatible with np.load.
        We could possibly use numpy's compressed format, but the large observations we care about (VNC screens)
        don't compress much, only by 30%, and it's a goal to be able to read the files from C++ or a browser someday.
        """

        batch_fn = '{}.ep{:09}.json'.format(self.file_prefix, self.episodes_first)
        bin_fn = '{}.ep{:09}.bin'.format(self.file_prefix, self.episodes_first)

        with atomic_write.atomic_write(os.path.join(self.directory, batch_fn), False) as batch_f:
            with atomic_write.atomic_write(os.path.join(self.directory, bin_fn), True) as bin_f:

                def json_encode(obj):
                    if isinstance(obj, np.ndarray):
                        offset = bin_f.tell()
                        while offset % 8 != 0:
                            bin_f.write(b'\x00')
                            offset += 1
                        obj.tofile(bin_f)
                        size = bin_f.tell() - offset
                        return {'__type': 'ndarray', 'shape': obj.shape, 'order': 'C', 'dtype': str(obj.dtype),
                                'npyfile': bin_fn, 'npyoff': offset, 'size': size}
                    return obj

                json.dump({'episodes': self.episodes}, batch_f, default=json_encode)

                bytes_per_step = float(bin_f.tell() + batch_f.tell()) / float(self.buffered_step_count)

        self.batches.append({
            'first': self.episodes_first,
            'len': len(self.episodes),
            'fn': batch_fn})

        manifest = {'batches': self.batches}
        manifest_fn = os.path.join(self.directory, '{}.manifest.json'.format(self.file_prefix))
        with atomic_write.atomic_write(os.path.join(self.directory, manifest_fn), False) as f:
            json.dump(manifest, f)

        # Adjust batch size, aiming for 5 MB per file.
        # This seems like a reasonable tradeoff between:
        #   writing speed (not too much overhead creating small files)
        #   local memory usage (buffering an entire batch before writing)
        #   random read access (loading the whole file isn't too much work when just grabbing one episode)
        self.buffer_batch_size = max(1, min(50000, int(5000000 / bytes_per_step + 1)))

        self.episodes = []
        self.episodes_first = None
        self.buffered_step_count = 0

    def close(self):
        """
        Flush any buffered data to disk and close. It should get called automatically at program exit time, but
        you can free up memory by calling it explicitly when you're done
        """
        if not self.closed:
            self.end_episode()
            if len(self.episodes) > 0:
                self.save_complete()
            self.closed = True
            logger.info('Wrote traces to %s', self.directory)


def _deepdict_find(d, key):
    retval = []
    for k, v in d.items():
        if k == key:
            retval.append(v)
        elif isinstance(v, dict):
            retval += _deepdict_find(v, key)
    return retval
