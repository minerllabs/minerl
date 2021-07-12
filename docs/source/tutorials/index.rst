================
Installation
================

Welcome to MineRL! This guide will get you started.


To start using the MineRL dataset and Gym environments comprising MineRL, you'll need to install the
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
        brew install --cask adoptopenjdk8

   c. On Debian based systems (Ubuntu!) you can run the following::

        sudo add-apt-repository ppa:openjdk-r/ppa
        sudo apt-get update
        sudo apt-get install openjdk-8-jdk

2. Now install the :code:`minerl` package!::

        pip3 install --upgrade minerl

.. note::
        
        You may need the user flag:
        :code:`pip3 install --upgrade minerl --user` to install properly.
