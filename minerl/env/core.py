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
import numpy as np
from lxml import etree
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

                # Use env like any other OpenAI gym environment.
                # ...

        Args:
            xml (str): The path to the MissionXML file for this environment.
            observation_space (gym.Space): The observation for the environment.
            action_space (gym.Space): The action space for the environment.
            port (int, optional): The port of an exisitng Malmo environment. Defaults to None which launches new.
            noop_action (Any, optional): The no-op action for the environment. This must be in the action_space. Defaults to None.
        """
    metadata = {'render.modes': ['rgb_array', 'human']}

    STEP_OPTIONS = 0

    def __init__(self, xml, observation_space, action_space, env_spec, port=None, noop_action=None, docstr=None):
        self.action_space = None
        self.observation_space = None
        self._default_action = noop_action

        self.viewer = None

        self._last_ac = None
        self.agent_count = 0
        self.resets = 0
        self.ns = '{http://ProjectMalmo.microsoft.com}'

        self.exp_uid = ""
        self.done = True
        self.synchronous = True

        self.width = 0
        self.height = 0
        self.depth = 0

        self.xml_file = xml
        self.has_init = False
        self._seed = None
        self.had_to_clean = False
        self._is_interacting = False
        self._is_real_time = False
        self._last_step_time = -1
        self._already_closed = False
        self.instances = []
        self.env_spec = env_spec
        self.port = port
        self.integratedServerPort = 0

        self.observation_space = observation_space
        self.action_space = action_space

        self.resets = 0
        self.done = True

    def _get_new_instance(self, port=None, instance_id=None):
        """
        Gets a new instance and sets up a logger if need be. 
        """

        if port is not None:
            instance = InstanceManager.add_existing_instance(port)
        else:
            instance = InstanceManager.get_instance(os.getpid(), instance_id=instance_id)

        if InstanceManager.is_remote():
            launch_queue_logger_thread(instance, self.is_closed)

        instance.launch()
        return instance

    def _controller_instance(self):
        if len(self.instances) > 0:
            return self.instances[0]
        return None

    def init(self):
        """Initializes the MineRL Environment.

        Note:
            This is called automatically when the environment is made.

        Raises:
            EnvException: If the Mission XML is malformed this is thrown.
            ValueError: The space specified for this environment does not have a default action.
            NotImplementedError: When multiagent environments are attempted to be used.
        """
        exp_uid = None

        # Parse XML file
        with open(self.xml_file, "r") as f:
            xml = f.read()
        # Todo: This will fail when using a remote instance manager.
        xml = xml.replace("$(MISSIONS_DIR)", missions_dir)

        if self.spec is not None:
            xml = xml.replace("$(ENV_NAME)", self.spec.id)
        else:
            xml = xml.replace("$(ENV_NAME)", MINERL_CUSTOM_ENV_ID)

        if not xml.startswith("<Mission"):
            i = xml.index("<Mission")
            if i == -1:
                raise EnvException("Mission xml must contain <Mission> tag.")
            xml = xml[i:]

        base_xml = etree.fromstring(xml)
        if exp_uid is None:
            self.exp_uid = str(uuid.uuid4())
        else:
            self.exp_uid = exp_uid

        # calculate agent count
        self.agent_count = len(base_xml.findall('{http://ProjectMalmo.microsoft.com}AgentSection'))

        for role in range(self.agent_count):
            xml = deepcopy(base_xml)
            e = etree.fromstring("""<MissionInit xmlns="http://ProjectMalmo.microsoft.com"
                                    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
                                    SchemaVersion="" PlatformVersion=""" + '\"' + malmo_version + '\"' +
                                 f""">
                                    <ExperimentUID>{self.exp_uid}</ExperimentUID>
                                    <ClientRole>{role}</ClientRole>
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
                                    </MissionInit>"""
            )
            e.insert(0, xml)
            xml = e
            # xml.find(self.ns + "ClientRole").text = str(role)
            # xml.find(self.ns + "ExperimentUID").text = self.exp_uid

            port = self.port
            if port is not None:
                port = port + role
            instance = self._get_new_instance(port=port)
            self.instances.append(instance)

            # prepare non-master clients to connect to the master server
            if role != 0 and self.agent_count > 1:
                # note that this server port is different than above client port, and will be set later
                e = etree.Element(
                    self.ns + "MinecraftServerConnection",
                    attrib={"address": instance.host, "port": str(0)},
                )
                xml.insert(2, e)

            if self._is_interacting:
                hi = etree.fromstring("""
                    <HumanInteraction>
                        <Port>{}</Port>
                        <MaxPlayers>{}</MaxPlayers>
                    </HumanInteraction>""".format(self.interact_port, self.max_players))
                # Update the xml

                ss = xml.find(".//" + self.ns + 'ServerSection')
                ss.insert(0, hi)

            video_producers = xml.findall('.//' + self.ns + 'VideoProducer')
            assert len(video_producers) == self.agent_count
            video_producer = video_producers[role]
            # Todo: Deprecate width, height, and POV forcing.
            self.width = int(video_producer.find(self.ns + 'Width').text)
            self.height = int(video_producer.find(self.ns + 'Height').text)
            want_depth = video_producer.attrib["want_depth"]
            self.depth = 4 if want_depth is not None and (
                    want_depth == "true" or want_depth == "1" or want_depth is True) else 3

            instance.role = role
            instance.xml = xml

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

    # TODO - make a custom Logger with this integrated (See LogHelper.java)
    def _logger_warning(self, message, *args, once=False, **kwargs):
        if once:
            # make sure we have our silenced logs table
            if not hasattr(self, "silenced_logs"):
                self.silenced_logs = set()

            # hash the stack trace
            import hashlib
            import traceback
            stack = traceback.extract_stack()
            locator = f"{stack[-2].filename}:{stack[-2].lineno}"
            key = hashlib.md5(locator.encode('utf-8')).hexdigest()

            # check if stack trace is silenced
            if key in self.silenced_logs:
                return
            self.silenced_logs.add(key)

        logger.warning(message, *args, **kwargs)

    def _process_observation(self, pov, info):
        """
        Process observation into the proper dict space.
        """
        pov = np.frombuffer(pov, dtype=np.uint8)

        if pov is None or len(pov) == 0:
            pov = np.zeros(
                (self.height, self.width, self.depth), dtype=np.uint8)
        else:
            try:
                pov = pov.reshape((self.height, self.width, self.depth))[
                      ::-1, :, :]
            except Exception as e:
                self._logger_warning(f"Failed to reshape observations: {e}", once=True)

        if info:
            info = json.loads(info)
        else:
            info = {}

        # Ensure mainhand observations are valid
        try:
            info['equipped_items.mainhand.type'] = info['equipped_items']['mainhand']['type']
            info['equipped_items.mainhand.damage'] = np.array(info['equipped_items']['mainhand']['damage'])
            info['equipped_items.mainhand.maxDamage'] = np.array(info['equipped_items']['mainhand']['maxDamage'])
        except Exception as e:
            self._logger_warning(f"Failed to set equipment observations: {e}", once=True)
            if 'equipped_items' in info:
                del info['equipped_items']

        bottom_env_spec = self.env_spec
        while isinstance(bottom_env_spec, EnvWrapper):
            bottom_env_spec = bottom_env_spec.env_to_wrap

        try:
            if info['equipped_items.mainhand.type'] not in bottom_env_spec.observation_space.spaces[
                    'equipped_items.mainhand.type']:
                info['equipped_items.mainhand.type'] = "other"  # Todo: use handlers. TODO: USE THEM<
        except Exception as e:
            self._logger_warning(f"Failed to set mainhand observations: {e}", once=True)
            pass

        # Process Info: (HotFix until updated in Malmo.)
        if "inventory" in info and "inventory" in bottom_env_spec.observation_space.spaces:
            inventory_spaces = bottom_env_spec.observation_space.spaces['inventory'].spaces

            items = inventory_spaces.keys()
            inventory_dict = {k: np.array(0) for k in inventory_spaces}
            # TODO change to maalmo
            for stack in info['inventory']:
                if 'type' in stack and 'quantity' in stack:
                    type_name = stack['type']
                    if type_name == 'log2':
                        type_name = 'log'

                    try:
                        inventory_dict[type_name] += stack['quantity']
                    except ValueError:
                        continue
                    except KeyError:
                        # We only care to observe what was specified in the space.
                        continue
            info['inventory'] = inventory_dict
        elif "inventory" in bottom_env_spec.observation_space.spaces and not "inventory" in info:
            self._logger_warning("No inventory found in malmo observation! Yielding empty inventory.", once=True)
            self._logger_warning(info, once=True)
            pass

        info['pov'] = pov

        obs_dict = bottom_env_spec.observation_space.no_op()

        # A function which updates a nested dictionary.
        def recursive_update(nested_dict, nested_update):
            for k, v in nested_update.items():
                if k in nested_dict:
                    if isinstance(v, collections.Mapping):
                        r = recursive_update(nested_dict.get(k, {}), v)
                        nested_dict[k] = r
                    else:
                        nested_dict[k] = np.array(v)
            return nested_dict

        obs_dict = recursive_update(obs_dict, info)
        

        # Now we wrap
        if isinstance(self.env_spec, EnvWrapper):
            obs_dict = self.env_spec.wrap_observation(obs_dict)
            
         
        self._last_pov = obs_dict['pov']
        self._last_obs = obs_dict

        return obs_dict

    def _process_actions(self, actions_in) -> str:
        """
        Process the actions into a proper command.
        """
        self._last_ac = actions_in
        actions_in = [deepcopy(action_in) for action_in in actions_in]

        if isinstance(self.env_spec, EnvWrapper):
            action_ins = [self.env_spec.unwrap_action(action_in) for action_in in actions_in]

        bottom_env_spec = self.env_spec
        while isinstance(bottom_env_spec, EnvWrapper):
            bottom_env_spec = bottom_env_spec.env_to_wrap

        # TODO: Decide if we want to remove assertions.
        action_strs = []
        for action_in in actions_in:
            action_str = []
            for act in action_in:
                # Process enums.
                if isinstance(bottom_env_spec.action_space.spaces[act], spaces.Enum):
                    if isinstance(action_in[act], int):
                        action_in[act] = bottom_env_spec.action_space.spaces[act].values[action_in[act]]
                    else:
                        assert isinstance(
                            action_in[act], str), "Enum action {} must be str or int".format(act)
                        assert action_in[act] in bottom_env_spec.action_space.spaces[
                            act].values, "Invalid value for enum action {}, {}".format(
                            act, action_in[act])

                elif isinstance(bottom_env_spec.action_space.spaces[act], gym.spaces.Box):
                    subact = action_in[act]
                    assert not isinstance(
                        subact, str), "Box action {} is a string! It should be a ndarray: {}".format(act, subact)
                    if isinstance(subact, np.ndarray):
                        subact = subact.flatten()

                    if isinstance(subact, Iterable):
                        subact = " ".join(str(x) for x in subact)

                    action_in[act] = subact
                elif isinstance(bottom_env_spec.action_space.spaces[act], gym.spaces.Discrete):
                    action_in[act] = int(action_in[act])

                action_str.append("{} {}".format(act, str(action_in[act])))

            action_strs.append("\n".join(action_str))
        return action_strs

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

        for instance in self.instances:
            try:
                # only fetch server info once after master agent has connected
                if instance.role == 1:
                    self._find_server(instance)
                if not instance.client_socket:
                    logger.debug(f"Creating socket connection {instance}")
                    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
                    sock.settimeout(SOCKTIME)
                    sock.connect((instance.host, instance.port))
                    logger.debug(f"Saying hello for client: {instance}")
                    self._hello(sock)

                    # Now retries will use connected socket.
                    instance.client_socket = sock
            except (socket.timeout, socket.error) as e:
                logger.error("Failed to reset (socket error), trying again!")
                self._clean_connection()
                raise e
            except RuntimeError as e:
                # Reset the instance if there was an error timeout waiting for episode pause.
                self.had_to_clean = True
                self._clean_connection()
                raise e

            self._init_mission(instance)

        self.done = False
        return self._peek_obs()

    def _clean_connection(self):
        logger.error("Cleaning connection! Something must have gone wrong.")
        for instance in self.instances:
            try:
                if instance.client_socket:
                    instance.client_socket.shutdown(socket.SHUT_RDWR)
                    instance.client_socket.close()
            except (BrokenPipeError, OSError, socket.error):
                # There is no connection left!
                pass

            instance.client_socket = None

        if self.had_to_clean:
            # Connect to a new instance!!
            logger.error(
                "Connection with Minecraft client cleaned more than once; restarting.")
            for role in range(len(self.instances)):
                self.instances[role].kill()
                self.instances[role] = self._get_new_instance(instance_id=self.instances[role].instance_id)

            self.had_to_clean = False
        else:
            self.had_to_clean = True

    def _peek_obs(self):
        obs = None
        start_time = time.time()
        if not self.done:
            logger.debug("Peeking the client.")
            peek_message = "<Peek/>"
            # TODO - only need controller instance here?
            instance = self._controller_instance()
            comms.send_message(instance.client_socket, peek_message.encode())
            obs = comms.recv_message(instance.client_socket)
            info = comms.recv_message(instance.client_socket).decode('utf-8')

            reply = comms.recv_message(instance.client_socket)
            done, = struct.unpack('!b', reply)
            self.done = done == 1
            if obs is None or len(obs) == 0:
                if time.time() - start_time > MAX_WAIT:
                    instance.client_socket.close()
                    instance.client_socket = None
                    raise MissionInitException(
                        'too long waiting for first observation')
                time.sleep(0.1)
            if self.done:
                raise RuntimeError(
                    "Something went wrong resetting the environment! "
                    "`done` was true on first frame.")

        return self._process_observation(obs, info)

    def _quit_episode(self):
        for instance in self.instances:
        comms.send_message(instance.client_socket, "<Quit/>".encode())
        reply = comms.recv_message(instance.client_socket)
        ok, = struct.unpack('!I', reply)
            if ok == 0:
                return False
        return True

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

    def step(self, actions):
        if not self.done:
            withinfo = MineRLEnv.STEP_OPTIONS == 0 or MineRLEnv.STEP_OPTIONS == 2

            # Process the multi-agent actions.
            malmo_commands = self._process_actions(actions)
            multi_obs = []
            multi_reward = []
            multi_done = []
            multi_info = []

            for instance in self.instances:
                try:  # TODO - we could wrap entire function in try, if sockets don't need to individually clean
                    malmo_command = malmo_commands[instance.role]
                    step_message = "<StepClient" + str(MineRLEnv.STEP_OPTIONS) + ">" + \
                                    malmo_command + \
                                    "</StepClient" + str(MineRLEnv.STEP_OPTIONS) + " >"

                    # Send Actions.
                    comms.send_message(instance.client_socket, step_message.encode())

                    # Receive the observation.
                    obs = comms.recv_message(instance.client_socket)

                    # Receive reward done and sent.
                    reply = comms.recv_message(instance.client_socket)
                    reward, done, sent = struct.unpack("!dbb", reply)

                    # Receive info from the environment.
                    if withinfo:
                        info = comms.recv_message(instance.client_socket).decode("utf-8")
                    else:
                        info = {}

                    # Process the observation and done state.
                    out_obs = self._process_observation(obs, info)
                    done = (done == 1)

                    # concatenate multi-agent obs
                    multi_obs.append(out_obs)
                    multi_reward.append(reward)
                    multi_done.append(done)
                    multi_info.append(info)
                except (socket.timeout, socket.error, TypeError) as e:
                    # If the socket times out some how! We need to catch this and reset the environment.
                    self._clean_connection()
                    self.done = True
                    logger.error(
                        f"Failed to take a step (error {e}). Terminating episode and sending random observation, be aware. "
                        "To account for this failure case in your code check to see if `'error' in info` where info is "
                        "the info dictionary returned by the step function."
                    )
                    return (
                        self.observation_space.sample(),
                        0,
                        self.done,
                        {"error": "Connection timed out!"},
                    )

            # this will currently only consider the env done when all agents report done individually
            self.done = np.all(multi_done)

            instance = self._controller_instance()
            try:
                step_message = "<StepServer></StepServer>"

                # Send Actions.
                comms.send_message(instance.client_socket, step_message.encode())

            except (socket.timeout, socket.error, TypeError) as e:
                # If the socket times out some how! We need to catch this and reset the environment.
                self._clean_connection()
                self.done = True
                logger.error(
                    "Failed to take a step (timeout or error). Terminating episode and sending random observation, be aware. "
                    "To account for this failure case in your code check to see if `'error' in info` where info is "
                    "the info dictionary returned by the step function.")
                # return self.observation_space.sample(), 0, self.done, {"error": "Connection timed out!"}

            # synchronize with real time
            if self._is_real_time:
                t0 = time.time()
                # Todo: Add catch-up
                time.sleep(max(0, TICK_LENGTH - (t0 - self._last_step_time)))
                self._last_step_time = time.time()
        else:
            raise RuntimeError("Attempted to step an environment server with done=True")

        return multi_obs, multi_reward, multi_done, multi_info

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

        for instance in self.instances:
            if instance.client_socket:
                instance.client_socket.close()
                instance.client_socket = None

            if instance.running:
                instance.kill()

        self._already_closed = True

    def reinit(self):
        """Use carefully to reset the episode count to 0."""
        # TODO - only need controller instance here?
        instance = self._controller_instance()
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((instance.host, instance.port))
        self._hello(sock)

        comms.send_message(sock, ("<Init>" + self._get_token(instance) + "</Init>").encode())
        reply = comms.recv_message(sock)
        sock.close()
        ok, = struct.unpack('!I', reply)
        return ok != 0

    def status(self):
        """Get status from server.
        head - Ping the the head node if True.
        """
        # TODO - only need controller instance here?
        instance = self._controller_instance()
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((instance.host, instance.port))

        self._hello(sock)

        comms.send_message(sock, "<Status/>".encode())
        status = comms.recv_message(sock).decode('utf-8')
        sock.close()
        return status

    def _find_server(self, instance):
        # calling find on the master client to get the server port
        controller_instance = self._controller_instance()
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((controller_instance.host, controller_instance.port))
        self._hello(sock)

        # try until you get something valid
        port = 0
        tries = 0
        while port == 0 and tries < 1000:
            comms.send_message(
                sock, ("<Find>" + self._get_token(instance) + "</Find>").encode()
            )
            reply = comms.recv_message(sock)
            port, = struct.unpack('!I', reply)
            tries += 1
        sock.close()
        if port == 0:
            raise Exception("Failed to find master server port!")
        self.integratedServerPort = port  # should/can this even be cached?
        logger.warning("MineRL agent is public, connect on port {} with Minecraft 1.11".format(port))

        # go ahead and set port for all non-controller clients
        for instance in self.instances[1:]:
            e = instance.xml.find(self.ns + 'MinecraftServerConnection')
            if e is not None:
                e.attrib['port'] = str(port)

    def _init_mission(self, instance):
        # init all instance missions
        ok = 0
        num_retries = 0
        logger.debug(f"Sending mission init: {instance}")
        while ok != 1:
            xml = etree.tostring(instance.xml)
            token = (self._get_token(instance) + ":" + str(self.agent_count) +
                     ":" + str(self.synchronous).lower())
            if self._seed is not None:
                token += ":{}".format(self._seed)
            token = token.encode()
            comms.send_message(instance.client_socket, xml)
            comms.send_message(instance.client_socket, token)

            reply = comms.recv_message(instance.client_socket)
            ok, = struct.unpack('!I', reply)
            if ok != 1:
                num_retries += 1
                if num_retries > MAX_WAIT:
                    raise socket.timeout()
                logger.debug("Recieved a MALMOBUSY from Malmo; trying again.")
                time.sleep(1)

    def _get_token(self, instance):
        return self.exp_uid + ":" + str(instance.role) + ":" + str(self.resets)


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
