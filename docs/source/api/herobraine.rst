..  admonition:: Solution
    :class: toggle

.. role:: python(code)
   :language: python

.. role:: bash(code)
   :language: bash

.. role:: json(code)
   :language: json


=====================================
:code:`minerl.herobraine`
=====================================

.. toctree::

    herobraine

.. inclusion-marker-do-not-remove

Handlers
=================

In addition to the default environments MineRL provides, you can use a variety of custom handlers to build your own. 
See the `Custom Environment Tutorial`_ to understand how to use these handlers. The following is documentation on all handlers 
which MineRL currently supports.



Agent Handlers
=================

Agent Handlers allow you to modify various properties of the agent 
(e.g. items in inventory, starting health, what gives the agent reward).

.. _Agent Start Handlers:


Agent Start Handlers
----------------------



.. automodule:: minerl.herobraine.hero.handlers.agent.start
    :members:
    :undoc-members:
    :show-inheritance:

Agent Quit Handlers
---------------------

.. automodule:: minerl.herobraine.hero.handlers.agent.quit
    :members:
    :undoc-members:
    :show-inheritance:

Reward Handlers
-----------------

.. automodule:: minerl.herobraine.hero.handlers.agent.reward
    :members:
    :undoc-members:
    :show-inheritance:


Action Handlers 
-----------------

Action handlers define what actions agents are allowed to take. 


When used to create a gym, you should override create_actionables and pass the action handlers to this function.
See the `Custom Environment Tutorial`_ for more.

Camera
^^^^^^^^

.. automodule:: minerl.herobraine.hero.handlers.agent.actions.camera
    :members:
    :undoc-members:
    :show-inheritance:

Craft
^^^^^^^^

.. automodule:: minerl.herobraine.hero.handlers.agent.actions.craft
    :members:
    :undoc-members:
    :show-inheritance:

Equip
^^^^^^^^^^

.. automodule:: minerl.herobraine.hero.handlers.agent.actions.equip
    :members:
    :undoc-members:
    :show-inheritance:

Keyboard
^^^^^^^^^^

.. automodule:: minerl.herobraine.hero.handlers.agent.actions.keyboard
    :members:
    :undoc-members:
    :show-inheritance:

Place
^^^^^^^^^^

.. automodule:: minerl.herobraine.hero.handlers.agent.actions.place
    :members:
    :undoc-members:
    :show-inheritance:

Smelt
^^^^^^^^^^

.. automodule:: minerl.herobraine.hero.handlers.agent.actions.smelt
    :members:
    :undoc-members:
    :show-inheritance:

Chat
^^^^^^^^^^

.. automodule:: minerl.herobraine.hero.handlers.agent.actions.chat
    :members:
    :undoc-members:
    :show-inheritance:

Observation Handlers 
----------------------

Observation handlers define what observation data agents receive (e.g. POV image, lifestats)

When used to create a gym, you should override create_observables and pass the observation handlers to this function.
See the `Custom Environment Tutorial`_ for more.

Compass
^^^^^^^^^^

.. automodule:: minerl.herobraine.hero.handlers.agent.observations.compass
    :members:
    :undoc-members:
    :show-inheritance:

Damage Source
^^^^^^^^^^^^^^^

.. automodule:: minerl.herobraine.hero.handlers.agent.observations.damage_source
    :members:
    :undoc-members:
    :show-inheritance:

Equipped Item
^^^^^^^^^^^^^^^

.. automodule:: minerl.herobraine.hero.handlers.agent.observations.equipped_item
    :members:
    :undoc-members:
    :show-inheritance:

Inventory
^^^^^^^^^^^^^^^

.. automodule:: minerl.herobraine.hero.handlers.agent.observations.inventory
    :members:
    :undoc-members:
    :show-inheritance:

Lifestats
^^^^^^^^^^^^^^^

.. automodule:: minerl.herobraine.hero.handlers.agent.observations.lifestats
    :members:
    :undoc-members:
    :show-inheritance:

Location Stats
^^^^^^^^^^^^^^^

.. automodule:: minerl.herobraine.hero.handlers.agent.observations.location_stats
    :members:
    :undoc-members:
    :show-inheritance:

Base Stats
^^^^^^^^^^^^^^^

.. automodule:: minerl.herobraine.hero.handlers.agent.observations.mc_base_stats
    :members:
    :undoc-members:
    :show-inheritance:

POV
^^^^^^^^^^^^^^^

.. automodule:: minerl.herobraine.hero.handlers.agent.observations.pov
    :members:
    :undoc-members:
    :show-inheritance:


Server Handlers
=================

Server Start Handlers
-----------------------

.. automodule:: minerl.herobraine.hero.handlers.server.start
    :members:
    :undoc-members:
    :show-inheritance:

Server Quit Handlers
----------------------

.. automodule:: minerl.herobraine.hero.handlers.server.quit
    :members:
    :undoc-members:
    :show-inheritance:

World Handlers
-----------------

.. automodule:: minerl.herobraine.hero.handlers.server.world
    :members:
    :undoc-members:
    :show-inheritance:


.. _Custom Environment Tutorial: https://minerl.readthedocs.io/en/latest/tutorials/custom_environments.html 
