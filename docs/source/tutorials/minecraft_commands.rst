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

.. role:: minecraft(code)
   :language: minecraft

Introduction
============

MineRL provides support for sending Minecraft Commands to the world. 
In addition to opening up numerous custom environment possibilities 
(Minecraft commands can be used to move players, 
summon or destroy mobs and blocks, reset player h
ealth/food, apply potions effects, and much more),
this feature can be _very_ useful for for speeding up training. 


.. warning::

   This feature is in BETA: it comes with a number of restrictions

   Only chats from the first agent (“agent_0”) are supported. 
   You must add ChatAction handler to your envspec. 
   You can only execute one chat action per time step, 


How Can MC Commands speed up training?
-----------------------------------------------

Consider an agent attempting the Navigate task. 
Every episode it attempts getting to the objective and after 
it fails or succeeds the Minecraft world is reset. This is
very computationally costly and it would be better to just 
reset the position, health, and food of the agent.

This could be accomplished with the following Minecraft commands:

.. code-block:: minecraft

   /tp @a 0 ~ 0

   /effect ...

Adding the ChatAction to your envspec
--------------------------------------------

In order to send Minecraft commands, you need to add the ChatAction 
handler to your envspec. The ChatAction allows the sending of regular 
Minecraft chats as well as Minecraft commands. 
This can be accomplished by adding the following
function to your envspec:

.. code-block:: python

    def create_actionables(self) -> List[Handler]:
        return super().create_actionables() + [
            # enable chat
            handlers.ChatAction()
        ]


See more about adding action handlers in the 
custom env tututorial and herobraine API docs.

Using the ChatAction to send a Minecraft Command
--------------------------------------------------

We can use the ChatAction just like other actions, 
by using the actions dictionary. 

.. code-block:: python

    # gives all agents an apple
    actions[“agent_0”][“chat”] = “/give @a apple”
    env.step(actions)

Abstracted Command Sending 
------------------------------
Since the ability to send Minecraft commands is such an important feature,
MineRL provides an additional level of abtraction to make its use
slightly easier.

All environments which use the ChatAction handler also support 
the set_next_chat_message function. This function takes a String 
and sends it as a chat message the next time the environment 
is stepped.

Here is sample use:

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
---------------
If for some reason you need to execute multiple commands in 
the same time step, you can either spawn in a series of 
Minecraft Command Blocks or load a World from file 
with a chain of command blocks. This level of complexity 
shouldn’t be needed, but could be useful if you need to 
execute many distinct commands in a row.
