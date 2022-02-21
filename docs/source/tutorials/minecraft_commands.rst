.. _Custom Env Tutorial

..  admonition:: Solution
    :class: toggle

====================================
Using Minecraft Commands
====================================

.. role:: python(code)
   :language: python

.. role:: bash(code)
   :language: bash

.. 
    sphinx should really support minecraft language markdown :(

.. role:: minecraft(code)
   :language: minecraft

Introduction
============

MineRL provides support for sending `Minecraft commands <https://minecraft.fandom.com/wiki/Commands>`_. 
In addition to opening up numerous custom environment possibilities 
(Minecraft commands can be used to move players, 
summon or destroy mobs and blocks, reset player 
health/food, apply potions effects, and much more),
this feature can be *very* useful for speeding up training. 


.. warning::

   This feature is in BETA; it comes with a number of restrictions.

   Only messages from the first agent are supported in the multiagent setting. 

   You must add the :code:`ChatAction` handler to your envspec. 

   You can only execute one chat action per time step, 


How Can MC Commands speed up training?
=============================================

Consider an agent attempting the Navigate task. 
After each attempt to get to the objective the Minecraft world is reset.
Resetting the world is very computationally costly and it would be better to just 
reset the position, health, and food of the agent.

This could be accomplished with the following Minecraft commands:

.. code-block:: minecraft

    # teleport all agents to (x=0, z=0)
    /tp @a 0 ~ 0

    # reset health of all agents
    /effect @a minecraft:instant_health 1 100 true

    # reset food of all agents
    /effect @a minecraft:saturation 1 255 true

Adding the :code:`ChatAction` to your envspec
=======================================================

In order to send Minecraft commands, you need to add the :code:`ChatAction` 
handler to your environment's envspec. See `this tutorial <https://minerl.readthedocs.io/en/latest/tutorials/custom_environments.html>`_ on how to make custom environments and envspecs.

The :code:`ChatAction` allows the sending of regular Minecraft chat messages as well as Minecraft commands. 
This can be accomplished by adding the ``ChatAction`` handler to your envspec:

.. code-block:: python

    def create_actionables(self) -> List[Handler]:
        return super().create_actionables() + [
            # enable chat
            handlers.ChatAction()
        ]

Abstracted Command Sending 
=================================
All environments which use the :code:`ChatAction` handler will support 
the ``set_next_chat_message`` function. This function takes a string 
and sends it as a chat message the next time the environment
is stepped:

.. code-block:: python

    # no actions
    actions = {}
    env.set_next_chat_message("/gamemode @a adventure")
    # sets the gamemode of all players to adventure
    env.step(actions)
    # the chat message is not executed again; 
    # it gets cleared each time step() is called
    env.step(actions)
    env.set_next_chat_message("/tp @r 320 54 66")
    # teleports a random agent to the given coordinates
    env.step(actions)


Advanced use 
======================
If for some reason you need to execute multiple commands in 
the *same* time step, you can either spawn in a chain of 
Minecraft Command Blocks or load a world from the file 
with a chain of command blocks. This level of complexity 
shouldn’t be needed but could be useful if you need to 
execute many distinct commands and don't want to spread them 
over multiple time steps.
