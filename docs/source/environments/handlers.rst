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


Spaces
===========


.. _enum_spaces:

Enum Spaces
-----------

Some observation and action spaces are ``Enum`` types. Examples include
the :ref:`equip observation<equipped_items>`
and
the :ref:`equip action<equip>`.

Observation and action spaces that are ``Enum`` are encoded as strings by default (e.g. "none",
"log", and "sandstone#2") when they are returned from ``env.step()`` and ``env.reset()``, or
yielded from :meth:`minerl.data.DataPipeline.batch_iter`.

When building an action to pass into ``env.step(act)``, the Enum component of the action dict can
be encoded as either a string or an integer.

.. tip::
    The Enum integer value that corresponds to each Enum string value can be accessed via
    ``Enum.values_map[string_value]``. For example, to get the integer value corresponding to the
    equip action "dirt" in ``MineRLObtainDiamond`` or ``MineRLBasaltBuildVillageHouse``, you can
    call ``env.action_space.spaces["equip"].values_map["dirt"]``.


Observations
=====================================


Visual Observations - :code:`pov`, :code:`third-person`
-------------------------------------------------------


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


Equip Observations - :code:`equipped_items`
-------------------------------------------

.. _equipped_items:

.. function:: equipped_items.mainhand.type : Enum('none', 'air', ..., 'other'))

    This observation is an Enum type. See :ref:`enum_spaces` for more information.

    The type of the item that the player has equipped in the mainhand slot. If the mainhand slot
    is empty then the value is 'air'. If the mainhand slot contains an item not inside this
    observation space, then the value is 'other'.

    :type: :code:`np.int64`
    :shape: [1]


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


Tool Control - ``equip`` and ``use``
------------------------------------

.. _equip:

.. function:: equip : Enum('none', 'air', ..., 'other'))

    This is action is an Enum type. See :ref:`enum_spaces` for more information.

    This action equips the first instance of the specified item from the agents inventory to the main hand if the
    specified item is present, otherwise does nothing.
    :code:`air` matches any empty slot in an agent's inventory and functions as an un-equip, or equip-nothing action.

    :type: :code:`np.int64`
    :shape: [1]

    .. note::

        :code:`equip 'none'` and ``equip 'other'`` are both no-op actions. In other words, they leave
        the currently equipped item unchanged. However, in the MineRL dataset, ``other`` takes on a
        special meaning. ``other`` is the wildcard equip action that is recorded in the dataset
        whenever a player equipped an item that wasn't included in this action space's Enum.

    .. warning::

        `env.step(act)` typically will not process the equip action for two ticks (i.e., you will not
        see the observation value :ref:`equipped_items` change until two more calls to `env.step`.)

        This is due to a limitation with the current version of Malmo, our Minecraft backend.

.. _use:
.. function:: use : Discrete(1) [use]

    This action is equivalent to right-clicking in Minecraft. It causes the agent to use the
    item it is holding in the :ref:`mainhand slot<equipped_items>`, or to open doors or gates when it is facing an applicable Minecraft
    structure.

    :type: :code:`np.int64`
    :shape: [1]
