MineRL Versions
==================

Over time, there have been a few major MineRL versions. Here is a summary of 
their functionalities.

.. list-table:: 
   :widths: 25 25 25 25
   :header-rows: 1

   * - Version #
     - Competitions used in
     - Details
     - Install commands
   * - 0.3.7
     - MineRL 2019 and 2020
     - [Minecraft: 1.11.2] Fastest version, but does not have BASALT envs 
     - :code:`pip install minerl==0.3`
   * - 0.4.4
     - MineRL Diamond and BASALT 2021
     - [Minecraft: 1.11.2] ~50% slower than 0.3.7, but has BASALT envs 
     - :code:`pip install minerl==0.4`
   * - 1.0.0
     - BASALT 2022
     - [Minecraft: 1.16.5] Slower than previous versions, but has more realistic action spaces (e.g. no autocrafting) and Minecraft Nether Update version.
     - :code:`pip install minerl==1.0`