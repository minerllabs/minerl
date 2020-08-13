# Copyright (c) 2020 All Rights Reserved
# Author: William H. Guss, Brandon Houghton

import collections

import copy
import json
import logging
from minerl.env.core import EnvException, MINERL_CUSTOM_ENV_ID, MineRLEnv, TICK_LENGTH, _deepdict_find, logger, missions_dir
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

class FakeMineRLEnv(gym.Env):
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
        self.done = False
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
        self.done = False
        self.agent_info = {}
        self.reset_mission_xml_fn = reset_mission_xml_fn or (lambda x: x)
        

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

        # Load fake info
        self._info = np.load(
            os.path.join(os.path.abspath(os.path.dirname(__file__)), 'info.npz'), 
        allow_pickle=True)['arr_0'].tolist()
        
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
                              attrib={'address': 0,
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
        self.done = False
        pass

    def _clean_connection(self):
        logger.error("Cleaning connection! Something must have gone wrong.")
        pass

        self.client_socket = None
        if self.had_to_clean:
            # Connect to a new instance!!
            logger.error(
                "Connection with Minecraft client cleaned more than once; restarting.")

            self.had_to_clean = False
        else:
            self.had_to_clean = True

    def _peek_obs(self):
        icopy = deepcopy(self._info)
        obs = icopy['pov']
        info = icopy
        
            


        return self._process_observation(obs, info)

    def _quit_episode(self):
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


    def step(self, action):

        withinfo = MineRLEnv.STEP_OPTIONS == 0 or MineRLEnv.STEP_OPTIONS == 2

        # Process the actions.
        malmo_command = self._process_action(action) # : str
        try:
            if not self.done:

                step_message = "<Step" + str(MineRLEnv.STEP_OPTIONS) + ">" + \
                               malmo_command + \
                               "</Step" + str(MineRLEnv.STEP_OPTIONS) + " >"

                reward = 0
                done = False

                # Receive info from the environment.
                
                icopy = deepcopy(self._info)
                obs = icopy['pov']
                info = icopy
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
        except (socket.timeout, socket.error) as e:
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


        self._already_closed = True

    def reinit(self):
        """Use carefully to reset the episode count to 0."""
        return True

    def status(self):
        """Get status from server.
        head - Ping the the head node if True.
        """
        return "good"

    def _find_server(self):
        return 1
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
            return 1 # port

    def _get_token(self):
        return self.exp_uid + ":" + str(self.role) + ":" + str(self.resets)

