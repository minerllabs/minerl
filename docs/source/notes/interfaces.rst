Other Minecraft Interfaces
======================================================

This page lists and compares a number of different Minecraft Interfaces other than MineRL.

.. list-table:: 
   :widths: 25 25 25 25 25 25
   :header-rows: 1

   * - 
     - Created
     - Dependency
     - Maintained
     - Competition
     - Unified obs/action spaces
   * - `Project Malmo`_
     - 2016
     - Minecraft
     - No
     - No
     - No
   * - `MarLÖ`_
     - 2018
     - Malmo
     - No
     - Formerly
     - No
   * - `MalmoEnv`_
     - ~2018/2019
     - Malmo
     - No
     - No
     - No
   * - MineRL
     - 2019
     - [1.0.0 Minecraft] [<1.0.0 MalmoEnv]
     - Yes
     - Yes
     - [1.0.0 Mostly] [<1.0.0 No]
   * - `IGLU`_ 2021
     - 2021
     - MineRL
     - ?
     - Yes
     - ?
   * - `MineDojo`_
     - 2022
     - MineRL 0.4.4
     - Just Released
     - No
     - Yes

`Project Malmo`_
************************************************************************************************
Original Minecraft Java platform/mod built by Microsoft for AI research. Many other Minecraft libraries
depend on Malmo.

`MarLÖ`_ "Multi-Agent Reinforcement Learning in MalmÖ"
************************************************************************************************
A Python library which provides a gym-like interface for interacting with Malmo/Minecraft, 
specifically for multi-agent scenarios.

`MalmoEnv`_
************************************************************************************************
A Python library which provides a gym-like interface for interacting with Malmo/Minecraft.

`IGLU`_ "Interactive Grounded Language Understanding in a Collaborative Environment"
************************************************************************************************
A Python library for building interactive agents for natural language grounding tasks. 
Note: the 2022 competition depends on a faster Minecraft Clone, while the 2021 competition 
depends on MineRL.


`MineDojo`_
************************************************************************************************
A framework built on MineRL, which "features a simulation suite with 1000s of open-ended and language-prompted tasks".


.. _IGLU: https://github.com/iglu-contest/iglu
.. _Project Malmo: https://www.microsoft.com/en-us/research/project/project-malmo/
.. _MarLÖ: https://github.com/crowdAI/marLo
.. _MalmoEnv: https://github.com/microsoft/malmo/tree/master/MalmoEnv
.. _MineDojo: https://minedojo.org
