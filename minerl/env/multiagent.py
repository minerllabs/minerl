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
# TODO: This file needs a refactor and cleanup.
import collections

import copy
import json
import logging
from minerl.env.exceptions import EnvException, MissionInitException
from minerl.herobraine.env_spec import EnvSpec
import os
import random
import socket
import struct
import time
import uuid
from copy import deepcopy
from typing import Any, Dict, Iterable, Tuple

import gym
import gym.envs.registration
import gym.spaces

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



MAX_WAIT = 80  # After this many MALMO_BUSY's a timeout exception will be thrown
SOCKTIME = 60.0 * 4  # After this much time a socket exception will be thrown.
MINERL_CUSTOM_ENV_ID = 'MineRLCustomEnv'  # Default id for a MineRLEnv
TICK_LENGTH = 0.05

class MultiAgentEnv(gym.Env):
    """The multi-agent MineRLEnv class.

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
            port (int, optional): The port of an exisitng Malmo environment. Defaults to None which launches new.
            noop_action (Any, optional): The no-op action for the environment. This must be in the action_space. Defaults to None.
            restartable_java (bool, optional): whether java process should restart on failure. Defaults to True
            reset_mission_xml_fn (callable, optional): A function that can modifiy mission xml before passing it to Malmo. Will be called on every mission reset,
                                                       can be stochastic (for instance, for domain randomization). Defaults to None (no modification).
        """
    metadata = {'render.modes': ['rgb_array', 'human']}

    STEP_OPTIONS = 0

    def __init__(self,
                 env_spec : EnvSpec,
                 port=None,
                 restartable_java=True,
                 reset_mission_xml_fn=None):

        self.action_space = None
        self.observation_space = None

        self.viewer = None
        self.viewer_agent = 0

        self._last_ac = {}
        self._last_obs = {}
        self._last_pov = {}
        self.agent_count = 0
        self.actor_names = []
        self.resets = 0
        self.ns = "{http://ProjectMalmo.microsoft.com}"
        self.client_socket = None

        self.exp_uid = ""
        self.done = True
        self.synchronous = True

        self.width = 0
        self.height = 0
        self.channels = 0 

        self.xml_in = env_spec.to_xml()
        self.has_init = False
        self._seed = None
        self.had_to_clean = False
        
        self._already_closed = False
        self.restartable_java = restartable_java
        self._is_interacting = False
        self._is_real_time = False
        self._last_step_time = -1
        self._already_closed = False
        self.instances = []
        self.env_spec = env_spec
        self.port = port
        self.integratedServerPort = 0

        self.observation_space = env_spec.observation_space
        self.action_space = env_spec.action_space

        self.resets = 0
        self.done = True
        self.agent_info = {}
        self.has_finished = {}
        self.reset_mission_xml_fn = reset_mission_xml_fn or (lambda x: x)

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

        instance.launch(replaceable=self.restartable_java) 
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
        xml = self.xml_in
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
        self.agent_count = self.env_spec.agent_count
        self.actor_names = self.env_spec.agent_names

        for role in range(self.agent_count):
            xml = deepcopy(base_xml)
            e = etree.fromstring(
                """<MissionInit xmlns="http://ProjectMalmo.microsoft.com"
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

            instance.role = role
            instance.xml = xml

        self._last_ac = {}
        self._last_obs = {}
        self._last_pov = {}

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

    def _process_observation(self, actor_name, pov, info) -> Dict[str, Any]:
        """
        Process observation into the proper dict space.
        """
        if info:
            info = json.loads(info)
        else:
            info = {}

        
        info['pov'] = pov
        
        bottom_env_spec = self.env_spec
        while isinstance(bottom_env_spec, EnvWrapper):
            bottom_env_spec = bottom_env_spec.env_to_wrap
        
        # Process all of the observations using handlers.
        obs_dict = {}
        for h in bottom_env_spec.observables:
            obs_dict[h.to_string()] = h.from_hero(info)

        # TODO (R): Add achievment handlers. 
        # Add Achievements to observation
        if "achievements" in info:
            obs_dict["achievements"] = info["achievements"]
            
        # TODO (REI): CONVERT TO OBSERVATION HANDLER!
        # Add structure grid to observation
        if "structure" in info:
            obs_dict["structure"] = info["structure"]

        # Now we wrap
        if isinstance(self.env_spec, EnvWrapper):
            obs_dict = self.env_spec.wrap_observation(obs_dict)

        self._last_pov[actor_name] = obs_dict['pov']
        self._last_obs[actor_name] = obs_dict

        return obs_dict, info

    def _process_action(self, actor_name, action_in) -> str:
        """
        Process the actions into a proper command.
        """
        self._last_ac[actor_name] = action_in
        action_in = deepcopy(action_in)

        # TODO(wguss): Clean up the envSpec wrapper paradigm,
        # the env shouldn't be doing this IMO.
        # TODO (R): Make wrappers compatible with mutliple agents.
        if isinstance(self.env_spec, EnvWrapper):
            action_in = self.env_spec.unwrap_action(action_in)

        bottom_env_spec = self.env_spec
        while isinstance(bottom_env_spec, EnvWrapper):
            bottom_env_spec = bottom_env_spec.env_to_wrap

        act_space = bottom_env_spec.action_space[actor_name] if self.agent_count > 1 else (
            bottom_env_spec.action_space
        )
        assert self._check_action(actor_name, action_in, bottom_env_spec)

        action_str = []
        for h in bottom_env_spec.actionables:
            action_str.append(h.to_hero(action_in[h.to_string()]))

        return "\n".join(action_str)

    def _check_action(self, actor_name, action, env_spec):
        # TODO (R): Move this to env_spec in some reasonable way.
        return  action in env_spec.action_space[actor_name]

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
            
            self.has_finished = {agent: False for agent in self.env_spec.agent_names}
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
                    logger.debug("Creating socket connection {instance}".format(instance=instance))
                    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
                    sock.settimeout(SOCKTIME)
                    sock.connect((instance.host, instance.port))
                    logger.debug("Saying hello for client: {instance}".format(instance=instance))
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
        
        multi_obs = {}
        if not self.done:
            logger.debug("Peeking the clients.")
            peek_message = "<Peek/>"
            multi_done = True
            for instance in self.instances:
                start_time = time.time()
                comms.send_message(instance.client_socket, peek_message.encode())
                obs = comms.recv_message(instance.client_socket)
                info = comms.recv_message(instance.client_socket).decode('utf-8')

                reply = comms.recv_message(instance.client_socket)
                done, = struct.unpack('!b', reply)
                self.has_finished[instance.actor_name] = self.has_finished[instance.actor_name] or done
                multi_done = multi_done and done == 1
                if obs is None or len(obs) == 0:
                    if time.time() - start_time > MAX_WAIT:
                        instance.client_socket.close()
                        instance.client_socket = None
                        raise MissionInitException(
                            'too long waiting for first observation')
                    time.sleep(0.1)
                    # FIXME - shouldn't we error or retry here?

                actor_name = instance.actor_name
                multi_obs[actor_name], _ = self._process_observation(actor_name, obs, info)
            self.done = multi_done
            if self.done:
                raise RuntimeError(
                    "Something went wrong resetting the environment! "
                    "`done` was true on first frame.")
        return multi_obs

    def _quit_episode(self):
        for instance in self.instances:
            comms.send_message(instance.client_socket, "<Quit/>".encode())
            reply = comms.recv_message(instance.client_socket)
            ok, = struct.unpack('!I', reply)
            if ok == 0:
                return False
        return True

    def seed(self, seed=None, seed_spaces=True):
        """Seeds the environment!

        This also seeds the aciton_space and observation_space sampling.

        Note:
        THIS MUST BE CALLED BEFORE :code:`env.reset()`
        
        Args:
            seed (long, optional):  Defaults to 42.
            seed_spaces (bool, option): If the observation space and action space shoud be seeded. Defaults to True.
        """
        assert isinstance(seed, int) or seed is None, "Seed must be an int!"
        self._seed = seed
        if seed_spaces:
            self.observation_space.seed(self._seed)
            self.action_space.seed(self._seed)

    def step(self, actions) -> Tuple[
        Dict[str,Dict[str, Any]], Dict[str,float], Dict[str,bool], Dict[str,Dict[str, Any]]]:
        if not self.done:
            withinfo = MultiAgentEnv.STEP_OPTIONS == 0 or MultiAgentEnv.STEP_OPTIONS == 2

            multi_obs = {}
            multi_reward = {}
            multi_done = True
            multi_info = {}
            # TODO (R): REMOVE INFO FOR COMPETITION!

            # TODO (R): Randomly iterate over this.
            # Process multi-agent actions, apply and process multi-agent observations
            for instance in self.instances:
                try:  # TODO - we could wrap entire function in try, if sockets don't need to individually clean
                    actor_name = instance.actor_name

                    if not self.has_finished[actor_name]:
                        malmo_command = self._process_action(actor_name, actions[actor_name])
                        step_message = "<StepClient" + str(MultiAgentEnv.STEP_OPTIONS) + ">" + \
                                        malmo_command + \
                                        "</StepClient" + str(MultiAgentEnv.STEP_OPTIONS) + " >"

                        # Send Actions.
                        comms.send_message(instance.client_socket, step_message.encode())

                        # Receive the observation.
                        obs = comms.recv_message(instance.client_socket)

                        # Receive reward done and sent.
                        reply = comms.recv_message(instance.client_socket)
                        reward, done, sent = struct.unpack("!dbb", reply)
                        done = (done == 1)

                        self.has_finished[instance.actor_name] = self.has_finished[instance.actor_name] or done
                        print("DONE", instance, "IS", self.has_finished[instance.actor_name])
                
                        # Receive info from the environment.
                        if withinfo:
                            info = comms.recv_message(instance.client_socket).decode("utf-8")
                        else:
                            info = {}

                        # Process the observation and done state.
                        out_obs, info = self._process_observation(actor_name, obs, info)
                    else:
                        # IF THIS PARTICULAR AGENT IS DONE THEN:
                        reward = 0.0
                        out_obs = self._last_obs[actor_name]
                        done = True
                        info = {}

                    # concatenate multi-agent obs, rew, done
                    multi_obs[actor_name] = out_obs
                    multi_reward[actor_name] = reward
                    multi_done = multi_done and done

                    # merge multi-agent info
                    if instance.role == 0:
                        multi_info.update(info)
                    if 'actor_info' not in multi_info:
                        multi_info['actor_info'] = {}
                    multi_info['actor_info'][actor_name] = info
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
            self.done = multi_done
            
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
        viewer_actor_name = self.actor_names[self.viewer_agent]
        current_obs = self._last_obs.get(viewer_actor_name, None)
        current_ac = self._last_ac.get(viewer_actor_name, None)
        current_pov = self._last_pov.get(viewer_actor_name, None)

        if mode == 'human' and (
                not 'AICROWD_IS_GRADING' in os.environ or os.environ['AICROWD_IS_GRADING'] is None):
            self._renderObs(current_obs, current_ac)
        return current_pov

    def is_closed(self):
        return self._already_closed

    def close(self):
        """gym api close"""
        logger.debug("Closing MineRL env...")

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


    def _find_server(self, instance):
        # calling Find on the master client to get the server port
        controller_instance = self._controller_instance()
        sock = controller_instance.client_socket

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
        logger.debug("Sending mission init: {instance}".format(instance=instance))
        while ok != 1:
            xml = etree.tostring(instance.xml)
            # inject mission dict into the xml
            xml_dict = self.reset_mission_xml_fn(xmltodict.parse(xml))
            # set up video properties in the unlikely event of their change
            video_producers = _deepdict_find(xml_dict, "VideoProducer")
            assert len(video_producers) == self.agent_count
            video_producer = video_producers[instance.role]

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
                self._get_token(instance)
                + ":"
                + str(self.agent_count)
                + ":"
                + str(self.synchronous).lower()
            )
            if self._seed is not None:
                token += ":{}".format(self._seed)
            token = token.encode()
            comms.send_message(instance.client_socket, xml)
            comms.send_message(instance.client_socket, token)

            reply = comms.recv_message(instance.client_socket)
            ok, = struct.unpack("!I", reply)
            if ok != 1:
                num_retries += 1
                if num_retries > MAX_WAIT:
                    raise socket.timeout()
                logger.debug("Recieved a MALMOBUSY from Malmo; trying again.")
                time.sleep(1)

    def _get_token(self, instance):
        return self.exp_uid + ":" + str(instance.role) + ":" + str(self.resets)


def _deepdict_find(d, key):
    retval = []
    for k, v in d.items():
        if k == key:
            retval.append(v)
        elif isinstance(v, list):
            for e in v:
                if isinstance(e, dict):
                    retval += _deepdict_find(e, key)
        elif isinstance(v, dict):
            retval += _deepdict_find(v, key)
    return retval
