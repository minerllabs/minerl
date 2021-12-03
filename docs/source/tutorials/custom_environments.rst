.. _Custom Env Tutorial

..  admonition:: Solution
    :class: toggle

====================================
Creating A Custom Environment
====================================

.. role:: python(code)
   :language: python

.. role:: bash(code)
   :language: bash


Introduction
============

MineRL supports many ways to customize environments, including modifying the Minecraft world, adding 
more observation data, and changing the rewards agents receive.

MineRL provides support for these modifications using a variety of handlers.

In this tutorial, we will introduce how these handlers work by building a simple parkour environment
where an agent will perform an "MLG water bucket jump" onto a block of gold. 

"An MLG water is when a player is falling out of the air, or when a player jumps off of something, and they throw down water before they hit the ground to break the fall, and prevent themselves from dying by fall damage." --`Sportskeeda <https://www.sportskeeda.com/minecraft/mlg-minecraft#:~:text=MLG%20Water%20Bucket%20in%20Minecraft&text=MLG%20water%20is%20when%20a,from%20dying%20by%20fall%20damage.>`_

.. image:: ../assets/mlg_water_bucket.gif
  :scale: 100 %
  :alt:

The agent will then mine this gold block to terminate the episode.

See the complete code `here <https://github.com/minerllabs/minerl/tree/dev/examples>`_.

Setup
============



Create a Python file named :code:`mlg_wb_specs.py`

To start building our environment, let's import the necessary modules

.. code-block:: python

    from minerl.herobraine.env_specs.simple_embodiment import SimpleEmbodimentEnvSpec
    from minerl.herobraine.hero.handler import Handler
    import minerl.herobraine.hero.handlers as handlers
    from typing import List


Next, we will add the following variables:


.. code-block:: python

    MLGWB_DOC = """
    In MLG Water Bucket, an agent must perform an "MLG Water Bucket" jump
    """

    MLGWB_LENGTH = 8000

:code:`MLGWB_LENGTH` specifies how many time steps the environment can last until termination.


Contruct the Environment Class
============

In order to create our MineRL Gym environment, we need to inherit from :code:`SimpleEmbodimentEnvSpec`. This parent class
provides default settings for the environment.


.. code-block:: python

    class MLGWB(SimpleEmbodimentEnvSpec):
        def __init__(self, *args, **kwargs):
            if 'name' not in kwargs:
                kwargs['name'] = 'MLGWB-v0'

            super().__init__(*args,
                        max_episode_steps=MLGWB_LENGTH, 
                        reward_threshold=100.0,
                        **kwargs)

:code:`reward_threshold` is a number specifying how much reward the agent must get for the episode to be successful.

Now we will implement a number of methods which :code:`SimpleEmbodimentEnvSpec` requires.

Modify the World
============

Lets build a custom Minecraft world. 

We'll use the :code:`FlatWorldGenerator` handler to make a super flat world and pass it a 
:code:`generatorString` value to specify how we want the world layers to be created. "1;7,2x3,2;1" 
represents 1 layer of grass blocks above 2 layers of dirt above 1 layer of bedrock. You can use websites
like "`Minecraft Tools`_"  to easily customize superflat world layers.

We also pass a :code:`DrawingDecorator` to "draw" blocks into the world.

.. code-block:: python

    def create_server_world_generators(self) -> List[Handler]:
        return [
            handlers.FlatWorldGenerator(generatorString="1;7,2x3,2;1"),
            # generate a 3x3 square of obsidian high in the air and a gold block
            # somewhere below it on the ground
            handlers.DrawingDecorator("""
                <DrawCuboid x1="0" y1="5" z1="-6" x2="0" y2="5" z2="-6" type="gold_block"/>
                <DrawCuboid x1="-2" y1="88" z1="-2" x2="2" y2="88" z2="2" type="obsidian"/>
            """)
        ]

.. _Minecraft Tools: https://minecraft.tools/en/flat.php?biome=1&bloc_1_nb=1&bloc_1_id=2&bloc_2_nb=2&bloc_2_id=3%2F00&bloc_3_nb=1&bloc_3_id=7&village_size=1&village_distance=32&mineshaft_chance=1&stronghold_count=3&stronghold_distance=32&stronghold_spread=3&oceanmonument_spacing=32&oceanmonument_separation=5&biome_1_distance=32&valid=Create+the+Preset#seed

.. note::
    Make sure :code:`create_server_world_generators` and the following functions are indented under the :code:`MLGWB` class.



Set the Initial Agent Inventory
============

Lets now lets use the :code:`SimpleInventoryAgentStart` handler to give the agent a water bucket and a diamond pickaxe. 

Lets also make the agent spawn high in the air (on the obsidian platform) with the :code:`AgentStartPlacement` handler.

.. code-block:: python

    def create_agent_start(self) -> List[Handler]:
        return [
            # make the agent start with these items
            handlers.SimpleInventoryAgentStart([
                dict(type="water_bucket", quantity=1), 
                dict(type="diamond_pickaxe", quantity=1)
            ]),
            # make the agent start 90 blocks high in the air
            handlers.AgentStartPlacement(0, 90, 0, 0, 0)
        ]

Create Reward Functionality
====================================

Lets use the :code:`RewardForTouchingBlockType` handler 
so that the agent receives reward for getting to a gold block.

.. code-block:: python

    def create_rewardables(self) -> List[Handler]:
        return [
            # reward the agent for touching a gold block (but only once)
            handlers.RewardForTouchingBlockType([
                {'type':'gold_block', 'behaviour':'onceOnly', 'reward':'50'},
            ]),
            # also reward on mission end
            handlers.RewardForMissionEnd(50)
        ]

Construct a Quit Handler
====================================
We want the episode to terminate when the agent obtains a gold block.

.. code-block:: python 

    def create_agent_handlers(self) -> List[Handler]:
        return [
            # make the agent quit when it gets a gold block in its inventory
            handlers.AgentQuitFromPossessingItem([
                dict(type="gold_block", amount=1)
            ])
        ]

Allow the Agent to Place Water
====================================
We want the agent to be able to place the water bucket, but :code:`SimpleEmbodimentEnvSpec`
does not provide this ability by default. Note that we call :code:`super().create_actionables()`
so that we keep the actions which :code:`SimpleEmbodimentEnvSpec` does provide by default (like movement, jumping)


.. code-block:: python

    def create_actionables(self) -> List[Handler]:
        return super().create_actionables() + [
            # allow agent to place water
            handlers.KeybasedCommandAction("use"),
            # also allow it to equip the pickaxe
            handlers.EquipAction(["diamond_pickaxe"])
        ]

Give Extra Observations
====================================
In addition to the POV image data the agent receives as an observation, lets provide
it with compass and lifestats data. We override :code:`create_observables` just like the previous step.

.. code-block:: python

    def create_observables(self) -> List[Handler]:
        return super().create_observables() + [
            # current location and lifestats are returned as additional
            # observations
            handlers.ObservationFromCurrentLocation(),
            handlers.ObservationFromLifeStats()
        ]

Set the Time 
======================
Lets set the time to morning.

.. code-block:: python

    def create_server_initial_conditions(self) -> List[Handler]:
        return [
            # Sets time to morning and stops passing of time
            handlers.TimeInitialCondition(False, 23000)
        ]

Other Functions to Implement
====================================

:code:`SimpleEmbodimentEnvSpec` requires that we implement these methods.

.. code-block:: python

    # see API reference for use cases of these first two functions

    def create_server_quit_producers(self):
        return []
    
    def create_server_decorators(self) -> List[Handler]:
        return []

    # the episode can terminate when this is True
    def determine_success_from_rewards(self, rewards: list) -> bool:
        return sum(rewards) >= self.reward_threshold

    def is_from_folder(self, folder: str) -> bool:
        return folder == 'mlgwb'

    def get_docstring(self):
        return MLGWB_DOC

**Congrats!** You just made your first MineRL environment. Checkout the herobraine API reference 
to see many other ways to modify the world and agent.

See complete environment code `here <https://github.com/minerllabs/minerl/tree/dev/examples/mlg_wb_specs.py>`_.

Using the Environment
========================

Now you need to solve it 🙂

Create a new Python file in the same folder.

Here is some code to get you started:

You should see a Minecaft instance open then minimize. 
Then, you should see a window that shows the agent's POV.

.. code-block:: python

    import gym
    from mlg_wb_specs import MLGWB

    # In order to use the environment as a gym you need to register it with gym
    abs_MLG = MLGWB()
    abs_MLG.register()
    env = gym.make("MLGWB-v0")

    # this line might take a couple minutes to run
    obs  = env.reset()

    # Renders the environment with the agent taking noops
    done = False
    while not done:
        env.render()
        # a dictionary of actions. Try indexing it and changing values.
        action = env.action_space.noop()
        obs, reward, done, info = env.step(action)

See complete solution code `here <https://github.com/minerllabs/minerl/tree/dev/examples/mlg_wb_solution.py>`_ 
(Python file) or an interactive version `here <https://github.com/trigaten/MLGPK_gym/blob/main/solution.ipynb>`_ (Jupyter Notebook).

.. image:: ../assets/real_wb_success.gif
  :scale: 100 %
  :alt: