.. _environments:

.. role:: python(code)
   :language: python

General Information
================================


The :code:`minerl` package includes several environments as follows.
This page describes each of the included environments, provides usage samples,
and describes the exact action and observation space provided by each
environment!

.. note::
    All environments offer a default no-op action via :code:`env.action_space.no_op()`
    and a random action via :code:`env.action_space.sample()`.


Action Space
------------------

All environments use the same action space, which is a dictionary containing a 
multitude of different actions. Note that :code:`Discrete` and :code:`Box` are 
actions spaces defined by Gym.

.. code-block:: python

    Dict(ESC:Discrete(2), attack:Discrete(2), back:Discrete(2), 
    camera:Box(low=-180.0, high=180.0, shape=(2,)), drop:Discrete(2), 
    forward:Discrete(2), hotbar.1:Discrete(2), hotbar.2:Discrete(2), 
    hotbar.3:Discrete(2), hotbar.4:Discrete(2), hotbar.5:Discrete(2), 
    hotbar.6:Discrete(2), hotbar.7:Discrete(2), hotbar.8:Discrete(2), 
    hotbar.9:Discrete(2), inventory:Discrete(2), jump:Discrete(2), 
    left:Discrete(2), pickItem:Discrete(2), right:Discrete(2), 
    sneak:Discrete(2), sprint:Discrete(2), swapHands:Discrete(2), 
    use:Discrete(2))

Here is an example action:

.. code-block:: python

    {"ESC":1, "camera":[10, 45], "swapHands":1}

:code:`ESC`
************************

The :code:`ESC` action is used to end the episode.

.. Observation Space
.. ------------------

.. All environments use the same observation space, which 

.. .. code-block:: python

..     Dict(pov:Box(low=0, high=255, shape=(360, 640, 3)))

