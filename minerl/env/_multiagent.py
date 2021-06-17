# # Copyright (c) 2020 All Rights Reserved
# # Author: William H. Guss, Brandon Houghton

from copy import deepcopy
import json
import logging
from minerl.env.comms import retry
from minerl.env.exceptions import MissionInitException
import os
from minerl.herobraine.wrapper import EnvWrapper
import struct
from minerl.env.malmo import InstanceManager, MinecraftInstance, launch_queue_logger_thread, malmo_version
import uuid
import coloredlogs
import gym
import socket
import time
from lxml import etree
from minerl.env import comms
import xmltodict
from concurrent.futures import ThreadPoolExecutor

from minerl.herobraine.env_spec import EnvSpec
from typing import Any, Callable, Dict, List, Optional, Tuple

NS = "{http://ProjectMalmo.microsoft.com}"
STEP_OPTIONS = 0

MAX_WAIT = 600  # Time to wait before raising an exception (high value because some operations we wait on are very slow)
SOCKTIME = 60.0 * 4  # After this much time a socket exception will be thrown.
TICK_LENGTH = 0.05

logger = logging.getLogger(__name__)


class _MultiAgentEnv(gym.Env):
    """
    The MineRLEnv class, a gym environment which implements stepping, and resetting, for the MineRL
    simulator from an environment specification.


    THIS CLASS SHOULD NOT BE INSTANTIATED DIRECTLY
    USE ENV SPEC.

        Example:
            To actually create a MineRLEnv. Use any one of the package MineRL environments (Todo: Link.)
            literal blocks::

                import minerl
                import gym

                env = gym.make('MineRLTreechop-v0') # Makes a minerl environment.

                # Use env like any other OpenAI gym environment.
                # ...

                # Alternatively:
                env = gym.make('MineRLTreechop-v0') # makes a default treechop environment (with treechop-specific action and observation spaces)
    
    """

    metadata = {
        'render.modes': ['human', 'rgb_array'],
        'video_frames_per_second': 20,
    }

    def __init__(self,
                 env_spec: EnvSpec,
                 instances: Optional[List[MinecraftInstance]] = None,
                 is_fault_tolerant: bool = True,
                 verbose: bool = False,
                 _xml_mutator_to_be_deprecated: Optional[Callable] = None,
                 ):
        """
        Constructor of MineRLEnv.
        
        :param env_spec: The environment specification object.
        :param instances: A list of prelaunched Minecraft instances..
        :param is_fault_tolerant: If the instance is fault tolerant.
        :param verbose: If the MineRL env is verbose.
        :param _xml_mutator_to_be_deprecated: A function which mutates the mission XML when called.
        """
        self.task = env_spec
        self.instances = instances if instances is not None else []  # type: List[MinecraftInstance]

        # TO DEPRECATE (FOR ENV_SPECS)
        self._xml_mutator_to_be_deprecated = _xml_mutator_to_be_deprecated or (lambda x: x)

        # We use the env_spec's initial observation and action space
        # to satify the gym API
        self._setup_spaces()

        self._init_seeding()
        self._init_viewer()
        self._init_interactive()
        self._init_fault_tolerance(is_fault_tolerant)
        self._init_logging(verbose)

    ############ INIT METHODS ##########
    # These methods are used to first initialize different systems in the environment
    # These systems are not generally mutated episodically (via reset) and therefore
    # they are initialized in the init of the MineRL Env.
    # Exceptions to this rule (unfortunately) are setting up spaces, which
    # can change every episode, and by the Gym API are required to be
    # present as soon as an environment is constructed. (See __init__)
    def _init_viewer(self) -> None:
        self.viewers = {}
        self._last_ac = {}
        self._last_pov = {}
        self._last_obs = {}
        self.viewer_agent = self.task.agent_names[0]

    def _init_interactive(self) -> None:
        self._is_interacting = False
        self._is_real_time = False
        self._last_step_time = -1

    def _init_fault_tolerance(self, is_fault_tolerant: bool) -> None:
        self._is_fault_tolerant = is_fault_tolerant
        self._last_obs = {}
        self._already_closed = False

    def _init_logging(self, verbose: bool) -> None:
        if verbose:
            coloredlogs.install(level=logging.DEBUG)

    def _init_seeding(self) -> None:
        self._seed = None

    ########### CONFIGURATION METHODS ########

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

        # TODO: TEST

    ########## STEP METHOD ###########

    def _process_observation(self, actor_name, pov, info) -> Dict[str, Any]:
        """
        Process observation into the proper dict space.
        """
        if info:
            info = json.loads(info)
        else:
            info = {}

        info['pov'] = pov

        bottom_env_spec = self.task
        while isinstance(bottom_env_spec, EnvWrapper):
            bottom_env_spec = bottom_env_spec.env_to_wrap

        # Process all of the observations using handlers.
        obs_dict = {}
        monitor_dict = {}
        for h in bottom_env_spec.observables:
            obs_dict[h.to_string()] = h.from_hero(info)

        # Now we wrap
        if isinstance(self.task, EnvWrapper):
            obs_dict = self.task.wrap_observation(obs_dict)

        self._last_pov[actor_name] = obs_dict['pov']
        self._last_obs[actor_name] = obs_dict

        # Process all of the monotors (aux info) using THIS env spec.
        for m in self.task.monitors:
            monitor_dict[m.to_string()] = m.from_hero(info)

        return obs_dict, monitor_dict

    def _process_action(self, actor_name, action_in) -> str:
        """
        Process the actions into a proper command.
        """
        self._last_ac[actor_name] = action_in
        action_in = deepcopy(action_in)

        # TODO(wguss): Clean up the envSpec wrapper paradigm,
        # the env shouldn't be doing this IMO.
        # TODO (R): Make wrappers compatible with mutliple agents.
        if isinstance(self.task, EnvWrapper):
            action_in = self.task.unwrap_action(action_in)

        bottom_env_spec = self.task
        while isinstance(bottom_env_spec, EnvWrapper):
            bottom_env_spec = bottom_env_spec.env_to_wrap

        act_space = bottom_env_spec.action_space[actor_name] if self.task.agent_count > 1 else (
            bottom_env_spec.action_space
        )

        # TODO this will be fixed when moved into env spec
        # assert self._check_action(actor_name, action_in, bottom_env_spec)

        action_str = []
        for h in bottom_env_spec.actionables:
            if h.to_string() in action_in:
                action_str.append(h.to_hero(action_in[h.to_string()]))

        return "\n".join(action_str)

    def _check_action(self, actor_name, action, env_spec):
        # TODO (R): Move this to env_spec in some reasonable way.
        return action in env_spec.action_space[actor_name]

    def step(self, actions) -> Tuple[dict, dict, bool, dict]:
        if not self.done:
            assert STEP_OPTIONS == 0 or STEP_OPTIONS == 2

            multi_obs = {}
            multi_reward = {}
            everyone_is_done = True
            multi_monitor = {}

            # TODO (R): Randomly iterate over this.
            # Process multi-agent actions, apply and process multi-agent observations
            for role, (actor_name, instance) in enumerate(zip(self.task.agent_names, self.instances)):
                try:  # TODO - we could wrap entire function in try, if sockets don't need to individually clean

                    if not self.has_finished[actor_name]:
                        malmo_command = self._process_action(actor_name, actions[actor_name])
                        step_message = "<StepClient" + str(STEP_OPTIONS) + ">" + \
                                       malmo_command + \
                                       "</StepClient" + str(STEP_OPTIONS) + " >"

                        # Send Actions.
                        instance.client_socket_send_message(step_message.encode())

                        # Receive the observation.
                        obs = instance.client_socket_recv_message()

                        # Receive reward done and sent.
                        reply = instance.client_socket_recv_message()
                        reward, done, sent = struct.unpack("!dbb", reply)
                        # TODO: REFACTOR TO USE REWARD HANDLERS INSTEAD OF MALMO REWARD.
                        done = (done == 1)

                        self.has_finished[actor_name] = self.has_finished[actor_name] or done

                        # Receive info from the environment.
                        _malmo_json = instance.client_socket_recv_message().decode("utf-8")

                        # Process the observation and done state.
                        out_obs, monitor = self._process_observation(actor_name, obs, _malmo_json)
                    else:
                        # IF THIS PARTICULAR AGENT IS DONE THEN:
                        reward = 0.0
                        out_obs = self._last_obs[actor_name]
                        done = True
                        monitor = {}

                    # concatenate multi-agent obs, rew, done
                    multi_obs[actor_name] = out_obs
                    multi_reward[actor_name] = reward
                    everyone_is_done = everyone_is_done and done
                    multi_monitor[actor_name] = monitor
                except (socket.timeout, socket.error, TypeError) as e:
                    # If the socket times out some how! We need to catch this and reset the environment.
                    # TODO this is not implemented
                    self._clean_connection()
                    self.done = True
                    logger.error(
                        f"Failed to take a step (error {e}). Terminating episode and sending random observation, be aware. "
                        "To account for this failure case in your code check to see if `'error' in info` where info is "
                        "the info dictionary returned by the step function."
                    )
                    return (
                        {agent: self.observation_space.sample() for agent in actions},
                        {agent: 0 for agent in actions},
                        self.done,
                        {agent: {"error": "Connection timed out!"} for agent in actions},
                    )

            # this will currently only consider the env done when all agents report done individually
            self.done = everyone_is_done

            # STEP THE SERVER!
            instance = self.instances[0]
            try:
                step_message = "<StepServer></StepServer>"

                # Send Actions.
                instance.client_socket_send_message(step_message.encode())

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

        #  WE DON'T CURRENTLY PIPE OUT WHETHER EACH AGENT IS DONE
        # JUST IF EVERY AGENT IS DONE. THIS CAN BE ASCERTAINED BY
        # CALLING env.has_finished['agent_name_here]
        return multi_obs, multi_reward, everyone_is_done, multi_monitor

    def noop_action(self):
        """Gets the no-op action for the environment.

        In addition one can get the no-op/default action directly from the action space.

            env.action_space.noop()


        Returns:
            Any: A no-op action in the env's space.
        """
        return self.action_space.no_op()

    def has_agent_finished(self, name):
        """Determines the done state for a particular agent.
        The environment does not automatically return this information.
        """
        assert name in self.has_finished, "No agent called {0} in this environment".format(name)
        return self.has_finished[name]

    ########### RENDERING METHODS #########

    def _renderObs(self, obs, ac=None):

        for agent in self.task.agent_names:
            if agent not in self.viewers:
                from minerl.viewer.trajectory_display import HumanTrajectoryDisplay, VectorTrajectoryDisplay
                vector_display = 'Vector' in self.task.name
                header = self.task.name
                # TODO: env_specs should specify renderers.
                instructions = '{}.render()\n Actions listed below.'.format(header)
                subtext = agent
                cum_rewards = None
                if not vector_display:
                    agent_viewer = HumanTrajectoryDisplay(
                        header, subtext, instructions=instructions,
                        cum_rewards=cum_rewards)

                else:
                    agent_viewer = VectorTrajectoryDisplay(
                        header, subtext, instructions=instructions,
                        cum_rewards=cum_rewards)
                self.viewers[agent] = agent_viewer
            # Todo: support more information to the render
            self.viewers[agent].render(obs[agent], 0, 0, ac[agent], 0, 1)

        return all([v.isopen for v in self.viewers.values()])

    def render(self, mode='human'):
        current_obs = self._last_obs
        current_ac = self._last_ac
        current_pov = self._last_pov

        assert mode in self.metadata['render.modes']
        if mode == 'human' and os.environ.get('AICROWD_IS_GRADING') is None:
            if current_obs and current_ac:
                self._renderObs(current_obs, current_ac)
        return current_pov

    ########### RESET METHODS #########

    def reset(self) -> Any:
        """
        Reset the environment.

        Sets-up the Env from its specification (called everytime the env is reset.)

        Returns:
            The first observation of the environment. 
        """
        try:
            # First reset the env spec and its handlers
            self.task.reset()

            # Then reset the obs and act spaces from the env spec.
            self._setup_spaces()

            # Get a new episode UID and produce Mission XML's for the agents 
            # without the element for the slave -> master connection (for multiagent.)
            ep_uid = str(uuid.uuid4())
            agent_xmls = self._setup_agent_xmls(ep_uid)

            # Start missing instances, quit episodes, and make socket connections
            self._setup_instances()

            # Episodic state variables
            self.done = False
            self.has_finished = {agent: False for agent in self.task.agent_names}

            # Start the Mission/Task, by sending the master mission XML over 
            # the pipe to these instances, and  update the agent xmls to get
            # the port/ip of the master agent send the remaining XMLS.

            self._send_mission(self.instances[0], agent_xmls[0], self._get_token(0, ep_uid))  # Master
            if self.task.agent_count > 1:
                mc_server_ip, mc_server_port = self._TO_MOVE_find_ip_and_port(self.instances[0],
                                                                              self._get_token(1, ep_uid))
                # update slave instnaces xmls with the server port and IP and setup their missions.
                for slave_instance, slave_xml, role in list(zip(
                        self.instances, agent_xmls, range(1, self.task.agent_count + 1)))[1:]:
                    self._setup_slave_master_connection_info(slave_xml, mc_server_ip, mc_server_port)
                    self._send_mission(slave_instance, slave_xml, self._get_token(role, ep_uid))

            # Finally, peek all of the observations.
            return self._peek_obs()

        finally:
            # We don't force the same seed every episode, you gotta send it yourself queen.
            # TODO: THIS IS PERHAPS THE WRONG WAY TO DO THIS.
            # perhaps the first seed sets the seed of the random engine which then seeds
            # the episode in a cascading fashion
            self._seed = None

    def _setup_spaces(self) -> None:
        self.observation_space = self.task.observation_space
        self.action_space = self.task.action_space
        self.monitor_space = self.task.monitor_space

    def _setup_agent_xmls(self, ep_uid: str) -> List[etree.Element]:
        """Generates the XML for an episode.

        THIS SHOULD EVENTUALLY BE DEPRECATED FOR FULL JINJA TEMPALTING!

        Returns:
            str: The XML for an episode.
        """
        xml_in = self.task.to_xml()
        agent_xmls = []

        base_xml = etree.fromstring(xml_in)
        for role in range(self.task.agent_count):
            agent_xml = deepcopy(base_xml)
            agent_xml_etree = etree.fromstring(
                """<MissionInit xmlns="http://ProjectMalmo.microsoft.com"
                   xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
                   SchemaVersion="" PlatformVersion=""" + '\"' + malmo_version + '\"' +
                """>
                <ExperimentUID>{ep_uid}</ExperimentUID>
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
             </MissionInit>""".format(ep_uid=ep_uid, role=role))
            agent_xml_etree.insert(0, agent_xml)

            if self._is_interacting and role == 0:
                # TODO: CONVERT THIS TO A SERVER HANDLER 
                hi = etree.fromstring("""
                    <HumanInteraction>
                        <Port>{}</Port>
                        <MaxPlayers>{}</MaxPlayers>
                    </HumanInteraction>""".format(self.interact_port, self.max_players))
                # Update the xml
                namespace = '{http://ProjectMalmo.microsoft.com}'
                ss = agent_xml_etree.find(".//" + namespace + 'ServerSection')
                ss.insert(0, hi)

            # inject mission dict into the xml
            xml_dict = self._xml_mutator_to_be_deprecated(xmltodict.parse(etree.tostring(agent_xml_etree)))
            agent_xml_etree = etree.fromstring(xmltodict.unparse(xml_dict).encode())

            agent_xmls.append(agent_xml_etree)

        return agent_xmls

    def _setup_instances(self) -> None:
        """Sets up the instances for the environment 
        """
        num_instances_to_start = self.task.agent_count - len(self.instances)
        instance_futures = []
        if num_instances_to_start > 0:
            with ThreadPoolExecutor(max_workers=num_instances_to_start) as tpe:
                for _ in range(num_instances_to_start):
                    instance_futures.append(tpe.submit(self._get_new_instance))
            self.instances.extend([f.result() for f in instance_futures])
            self.instances = self.instances[:self.task.agent_count]

        # Now let's clean and establish new socket connections.
        # Note: it is important that all clients are informed of the episode end BEFORE the
        #  server. Since the first client is the one that communicates to the server, we
        #  inform it last by iterating backwards.
        for instance in reversed(self.instances):
            self._TO_MOVE_clean_connection(instance)
            self._TO_MOVE_create_connection(instance)
            # The socket could be failed here. This method
            # will throw a socket exception if this is the case.
            # TODO: Properly rewrite fault tolerance.
            self._TO_MOVE_quit_current_episode(instance)

        # Now we should have clean instances with clean sockets ready to recieve a mission.

    def _setup_slave_master_connection_info(self,
                                            slave_xml: etree.Element,
                                            mc_server_ip: str,
                                            mc_server_port: str):
        # note that this server port is different than above client port, and will be set later
        e = etree.Element(
            NS + "MinecraftServerConnection",
            attrib={"address": str(mc_server_ip), "port": str(mc_server_port)},
        )
        slave_xml.insert(2, e)

    def _send_mission(self, instance: MinecraftInstance, mission_xml_etree: etree.Element, token_in: str) -> None:
        """Sends the XML to the given instance.

        Args:
            instance (MinecraftInstance): The instance to which to send the xml

        Raises:
            socket.timeout: If the mission cannot be sent.
        """
        # init all instance missions
        ok = 0
        num_retries = 0
        logger.debug("Sending mission init: {instance}".format(instance=instance))
        while ok != 1:
            # roundtrip through etree to escape symbols correctly
            # and make printing pretty
            mission_xml = etree.tostring(mission_xml_etree)
            token = (
                    token_in
                    + ":"
                    + str(self.task.agent_count)
                    + ":"
                    + str(True).lower()  # synchronous
            )
            if self._seed is not None:
                token += ":{}".format(self._seed)
            token = token.encode()
            instance.client_socket_send_message(mission_xml)
            instance.client_socket_send_message(token)

            reply = instance.client_socket_recv_message()
            ok, = struct.unpack("!I", reply)
            if ok != 1:
                num_retries += 1
                # TODO: This is odd, MAX_WAIT is usually a number of seconds but here
                #  it's a number of retries. Probably needs to be fixed.
                if num_retries > MAX_WAIT:
                    raise socket.timeout()
                logger.debug("Recieved a MALMOBUSY from {}; trying again.".format(instance))
                time.sleep(1)

    def _peek_obs(self):
        multi_obs = {}
        if not self.done:
            logger.debug("Peeking the clients.")
            peek_message = "<Peek/>"
            multi_done = True
            for actor_name, instance in zip(self.task.agent_names, self.instances):
                start_time = time.time()
                instance.client_socket_send_message(peek_message.encode())
                obs = instance.client_socket_recv_message()
                info = instance.client_socket_recv_message().decode('utf-8')

                reply = instance.client_socket_recv_message()
                done, = struct.unpack('!b', reply)
                self.has_finished[actor_name] = self.has_finished[actor_name] or done
                multi_done = multi_done and done == 1
                if obs is None or len(obs) == 0:
                    if time.time() - start_time > MAX_WAIT:
                        instance.client_socket_close()
                        raise MissionInitException(
                            'too long waiting for first observation')
                    time.sleep(0.1)
                    # FIXME - shouldn't we error or retry here?

                multi_obs[actor_name], _ = self._process_observation(actor_name, obs, info)
            self.done = multi_done
            if self.done:
                raise RuntimeError(
                    "Something went wrong resetting the environment! "
                    "`done` was true on first frame.")
        return multi_obs

    #############  CLOSE METHOD ###############
    def close(self):
        """gym api close"""
        logger.debug("Closing MineRL env...")

        if self.viewers is not None:
            [viewer.close() for viewer in self.viewers]
            self.viewers = None

        if self._already_closed:
            return

        for instance in self.instances:
            self._TO_MOVE_clean_connection(instance)

            if instance.running:
                instance.kill()

        self._already_closed = True

    def is_closed(self):
        return self._already_closed

    ############# AUX HELPER METHODS ###########

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

    ############# INSTANCE HELPER METHODS ##################
    # TO_MOVE == These methods should really be part of a MinecraftInstance API
    # and not apart of the env which bridges tasks & instances!
    ########################################################
    def _TO_MOVE_clean_connection(self, instance: MinecraftInstance) -> None:
        """
        Cleans the conenction with a given instance.
        """
        try:
            if instance.has_client_socket():
                # Try to disconnect gracefully.
                try:
                    instance.client_socket_send_message("<Disconnect/>".encode())
                except:
                    pass
                instance.client_socket_shutdown(socket.SHUT_RDWR)
        except (BrokenPipeError, OSError, socket.error):
            # There is no connection left!
            pass
            instance.client_socket = None

    def _TO_MOVE_handle_frozen_minecraft(self, instance):
        if instance.had_to_clean:
            # Connect to a new instance!!
            logger.error(
                "Connection with Minecraft client {} cleaned "
                "more than once; restarting.".format(instance))

            instance.kill()
            instance = self._get_new_instance(instance_id=self.instance.instance_id)
        else:
            instance.had_to_clean = True

    @retry
    def _TO_MOVE_create_connection(self, instance: MinecraftInstance) -> None:
        try:
            logger.debug("Creating socket connection {instance}".format(instance=instance))
            instance.create_multiagent_instance_socket(socktime=SOCKTIME)
            logger.debug("Saying hello for client: {instance}".format(instance=instance))
            self._TO_MOVE_hello(instance)
        except (socket.timeout, socket.error, ConnectionRefusedError) as e:
            instance.had_to_clean = True
            logger.error("Failed to reset (socket error), trying again!")
            logger.error("Cleaning connection! Something must have gone wrong.")
            self._TO_MOVE_clean_connection(instance)
            self._TO_MOVE_handle_frozen_minecraft(instance)
            raise e

    def _TO_MOVE_quit_current_episode(self, instance: MinecraftInstance) -> None:
        has_quit = False

        logger.info("Attempting to quit: {instance}".format(instance=instance))
        # while not has_quit:
        instance.client_socket_send_message("<Quit/>".encode())
        reply = instance.client_socket_recv_message()
        ok, = struct.unpack('!I', reply)
        has_quit = not (ok == 0)
        # TODO: Get this to work properly

        # time.sleep(0.1) 

    def _TO_MOVE_find_ip_and_port(self, instance: MinecraftInstance, token: str) -> Tuple[str, str]:
        # calling Find on the master client to get the server port
        sock = instance.client_socket

        # try until you get something valid
        port = 0
        tries = 0
        start_time = time.time()

        logger.info("Attempting to find_ip: {instance}".format(instance=instance))
        while port == 0 and time.time() - start_time <= MAX_WAIT:
            comms.send_message(
                sock, ("<Find>" + token + "</Find>").encode()
            )
            reply = comms.recv_message(sock)
            port, = struct.unpack('!I', reply)
            tries += 1
            time.sleep(0.1)
        if port == 0:
            raise Exception("Failed to find master server port!")
        self.integratedServerPort = port  # should/can this even be cached?
        logger.warning("MineRL agent is public, connect on port {} with Minecraft 1.11".format(port))

        # go ahead and set port for all non-controller clients
        return instance.host, str(port)

    @staticmethod
    def _TO_MOVE_hello(instance):
        instance.client_socket_send_message(("<MalmoEnv" + malmo_version + "/>").encode())

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

        instance.launch(replaceable=self._is_fault_tolerant)

        # Add  a cleaning flag to the instance
        instance.had_to_clean = False
        return instance

    def _get_token(self, role, ep_uid: str):
        return ep_uid + ":" + str(role) + ":" + str(0)  # resets

    def _clean_connection(self):
        pass
