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

MineRL supports many ways to customize the environment, including modifying the Minecraft world, adding 
more observation data, and changing the rewards agents receive.

MineRL provides support for these modifications using a variety of handlers.

In this tutorial, we will introduce how these handlers work by building a simple parkour environment
where an agent will perform an "`MLG water bucket jump`_" onto a block of gold.

.. image:: ../assets/mlg_water_bucket.gif
  :scale: 100 %
  :alt:

.. _MLG water bucket jump: https://www.urbandictionary.com/define.php?term=MLG%20Water%20Bucket

Setup
============



Create a Python file named :code:`mlg_wb_specs.py`

To start building our environment, let's import the necessary modules

.. code-block:: python

    from minerl.herobraine.env_specs.simple_embodiment import SimpleEmbodimentEnvSpec
    from minerl.herobraine.hero.mc import MS_PER_STEP, STEPS_PER_MS
    from minerl.herobraine.hero.handler import Handler
    from typing import List

    import minerl.herobraine.hero.handlers as handlers



Next, we will add the following variables:


.. code-block:: python

    MLGWB_DOC = """
    In MLG Water Bucket, an agent must learn to perform an "MLG Water Bucket"
    """

    MLGWB_LENGTH = 8000

:code:`MLGPK_LENGTH` specifies how many time steps the environment can last until termination.


Contruct the Environment Class
============

In order to create our MineRL gym, we need to subclass :code:`SimpleEmbodimentEnvSpec`


.. code-block:: python

    class MLGWB(SimpleEmbodimentEnvSpec):
        def __init__(self, *args, **kwargs):
            if 'name' not in kwargs:
                kwargs['name'] = 'MLGWB-v0'

            super().__init__(*args,
                            max_episode_steps=MLGWB_LENGTH, reward_threshold=100.0,
                            **kwargs)


Modifying the World
============

Now lets build a custom Minecraft world. 

We'll use the :code:`FlatWorldGenerator` handler to make a super flat world and pass it a 
:code:`generatorString` value to specify how we want the world layers to be created. "1;7,2x3,2;1" 
represents 1 layer of grass blocks above 2 layers of dirt above 1 layer of bedrock. You can use websites
like "`Minecraft Tools`_"  to easily customize superflat world layers.

.. code-block:: python

    def create_server_world_generators(self) -> List[Handler]:
            return [
                handlers.FlatWorldGenerator(generatorString="1;7,2x3,2;1")


                # handlers.DrawingDecorator('<DrawSphere x="-50" y="20" z="0" radius="10" type="obsidian"/>')
            ]

.. _Minecraft Tools: https://minecraft.tools/en/flat.php?biome=1&bloc_1_nb=1&bloc_1_id=2&bloc_2_nb=2&bloc_2_id=3%2F00&bloc_3_nb=1&bloc_3_id=7&village_size=1&village_distance=32&mineshaft_chance=1&stronghold_count=3&stronghold_distance=32&stronghold_spread=3&oceanmonument_spacing=32&oceanmonument_separation=5&biome_1_distance=32&valid=Create+the+Preset#seed



.. note::
    Make sure :code:`create_server_world_generators` and the following functions are indented under the :code:`MLGWB` class.



Setting the Initial Agent Inventory
============

Lets now lets use the :code:`SimpleInventoryAgentStart` handler to give the agent a water bucket.

.. code-block:: python

    def create_agent_start(self) -> List[Handler]:
        return [
            handlers.SimpleInventoryAgentStart([
                dict(type="water_bucket", quantity=1)
            ])
        ]


Creating Reward Functionality
============

Lets use the :code:`RewardForTouchingBlockType` handler 
so that the agent receives reward for getting to a gold block.

.. code-block:: python

    def create_rewardables(self) -> List[Handler]:
        return [
            handlers.RewardForTouchingBlockType([
            dict(type="gold_block", behavior='onceOnly', reward=100.0),
            dict(type="stone_block", behavior='onceOnly', reward=-1.0)
            ])
        ]

:code:`reward_threshold` is a number specifying how much reward the agent must get for the episode to terminate.





Other Functions to Implement
============

MineRL requires that we implement these methods, but we don't need their functionality 
in this environment.

.. code-block:: python

    def create_agent_handlers(self) -> List[Handler]:
        return []
