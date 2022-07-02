Minecraft Interfaces
======================================================

This page lists and compares a number of different Minecraft Interfaces.

`Project Malmo`


`MarLÖ <https://github.com/crowdAI/marLo>`_
************************************************


.. list-table:: 
   :widths: 25 25 25 25
   :header-rows: 1

   * - 
     - Competitions used in
     - Details
     - Install commands
   * - Project Malmo
     - MineRL 2019 and 2020
     - [Minecraft: 1.11.2] Fastest version, but does not have the BASALT environments 
     - :code:`pip install minerl==0.3`
   * - MalmoEnv
     - MineRL Diamond and BASALT 2021
     - [Minecraft: 1.11.2] ~50% slower than 0.3.7, but has the BASALT environments
     - :code:`pip install minerl==0.4`
   * - MineRL
     - BASALT 2022
     - [Minecraft: 1.16.5] Slower than previous versions, but has more realistic action spaces (e.g. no autocrafting) and Minecraft Nether Update version.
     - :code:`pip install git+https://github.com/minerllabs/minerl@v1.0.0`
   * - `MarLÖ <https://github.com/crowdAI/marLo>`_
     - BASALT 2022
     - [Minecraft: 1.16.5] Slower than previous versions, but has more realistic action spaces (e.g. no autocrafting) and Minecraft Nether Update version.
     - :code:`pip install git+https://github.com/minerllabs/minerl@v1.0.0`