
Environment Handlers
================================

Minecraft is an extremely complex environment which provides players
with visual, auditory, and informational observation of many complex
data types.
Furthermore, players interact with Minecraft using more than just embodied actions:
players can craft, build, destroy, smelt, enchant, manage their inventory,
and even communicate with other players via a text chat.

To provide a unified interface with which agents can obtain and perform
similar observations and actions as players, we have provided
first-class for support for this multi-modality in the environment:
**the observation and action spaces of environments are**
:code:`gym.spaces.Dict` **spaces.** These observation and action
dictionaries are comprised of individual fields we call *handlers*.


.. note::
    In the  documentation of every environment we provide a listing
    of the exact :code:`gym.space` of the observations returned by and actions expected by the environment's step function. We are slowly
    building documentation for these handlers, and **you can click those highlighted with blue** for more information!



.. toctree::
    
    handlers

.. inclusion-marker-do-not-remove

.. include:: observations.rst





Observations
=====================================


Visual Observations - :code:`pov`, :code:`third-persion`
---------------------------------------------------------


.. _pov:

.. function:: pov : Box(width, height, nchannels)

    An RGB image observation of
    the agent's first-person perspective.

    :type: :code:`np.uint8`


.. _third-person:

.. function:: third-person : Box(width, height, nchannels)

    An RGB image observation of the agent's third-person perspective. 

    .. warning::
        This observation is not yet supported by any environment.

    :type: :code:`np.uint8`

.. _compass-observation:

.. function:: compass-observation : Box(1)

    The current position of the `minecraft:compass` object from 0 (behind agent left) to
    0.5 in front of agent to 1 (behind agent right)
    
    .. note::
        This observation uses the default Minecraft game logic which includes compass needle momentum. 
        As such it may change even when the agent has stoped moving!



Actions
====================================


Camera Control - :code:`camera`
-------------------------------

.. _camera:

.. function:: camera : Box(2) [delta_pitch, delta_yaw]

    This action changes the orientation  of the agent's head by the corresponding number of degrees.
    When the :code:`pov` observation is available, the 
    camera changes its orientation pitch by the first component
    and its yaw by the second component. Both :code:`delta_pitch` and :code:`delta_yaw` are limited to [-180, 180]
    inclusive

    :type: :code:`np.float32`
    :shape: [2]

.. _attack:

.. function:: attack : Discrete(1) [attack]

    This action causes the agent to attack.

    :type: :code:`np.float32`
    :shape: [1]


Tool Control - :code:`camera`
-------------------------------


.. _equip:

.. function:: equip : Enum('none', 'air', 'wooden_axe', 'wooden_pickaxe', 'stone_axe', 'stone_pickaxe', 'iron_axe', 'iron_pickaxe'))

    This action equips the first instance of the specified item from the agents inventory to the main hand if the
    specified item is present, otherwise does nothing. :code:`none` is never a valid item and functions as a no-op
    action. :code:`air` matches any empty slot in an agent's inventory and functions as an un-equip action.

    :type: :code:`np.int64`
    :shape: [1]

    .. note::
        Agents may un-equip items by performing the :code:`equip air` action.



