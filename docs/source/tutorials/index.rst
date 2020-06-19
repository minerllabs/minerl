================
Installation
================

Welcome to MineRL! This guide will get you started.


To start using the data and set of reinforcement learning
environments comprising MineRL, you'll need to install the
main python package, :code:`minerl`.

.. _OpenJDK 8: https://openjdk.java.net/install/
.. _Windows installer: https://www.oracle.com/technetwork/java/javase/downloads/jdk8-downloads-2133151.html
.. _checkout the environment documentation: http://minerl.io/docs/environments/
.. _checkout the competition environments: http://minerl.io/docs/environments/#competition-environments

1. First **make sure you have JDK 1.8** installed on your
   system.

   a. `Windows installer`_  -- On windows go this link and follow the
      instructions to install JDK 8.

   b. On Mac, you can install java8 using homebrew and AdoptOpenJDK (an open source mirror, used here to get around the fact that Java8 binaries are no longer available directly from Oracle)::

        brew tap AdoptOpenJDK/openjdk
        brew cask install adoptopenjdk8

   c. On Debian based systems (Ubuntu!) you can run the following::

        sudo add-apt-repository ppa:openjdk-r/ppa
        sudo apt-get update
        sudo apt-get install openjdk-8-jdk

2. Now install the :code:`minerl` package!::

        pip3 install --upgrade minerl

.. note::
        depending on your system you may need the user flag:
        :code:`pip3 install --upgrade minerl --user` to install property

3. (Optional) Download the dataset ~ 60 GB:

   .. code-block:: python

        import minerl
        minerl.data.download(directory="/your/local/path/")

   Or simply download a single experiment

   .. code-block:: python

        minerl.data.download('/your/local/path',experiment='MineRLObtainDiamondVectorObf-v0')

   For a complete list of published experiments, `checkout the environment documentation`_.
   If you are here for the MineRL competition, `checkout the competition environments`_.

**That's it! Now you're good to go :) 💯💯💯**

.. caution::
    Currently :code:`minerl` only supports environment rendering in **headed environments**
    (machines with monitors attached). 


    **In order to run** :code:`minerl` **environments without a head use a software renderer
    such as** :code:`xvfb`::

        xvfb-run python3 <your_script.py>
