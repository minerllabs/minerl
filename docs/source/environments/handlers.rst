
Environment Handlers
================================

Minecraft is an extremely complex environment which provides players
with visual, auditory, and informational observation of many complex
data types.
Further players interact with Minecraft using more than just embodied actions:
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



Actions
====================================


Camera Control - :code:`camera`
-------------------------------

.. _camera:

.. function:: camera : Box(2) [delta_pitch, delta_yaw]

    This action changes the oritentation  of the agent's head.
    When the :code:`pov` observation is available, the 
    camera changes its orientation pitch by the first component
    and its yaw by the second component.

    :type: :code:`np.float32`
    :shape: [2]


