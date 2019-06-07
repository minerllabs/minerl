================
Installation
================

Welcome to MineRL! This guide will get you started.


To start using the data and set of reinforcement learning
enviroments comrpising MineRL, you'll need to install the
main python package, :code:`minerl`.

.. _OpenJDK 8: https://openjdk.java.net/install/
.. _Windows installer: https://www.oracle.com/technetwork/java/javase/downloads/jdk8-downloads-2133151.html

1. First **make sure you have JDK 1.8** installed on your
   system.

   a. `Windows installer`_  -- On windows go this link and follow the
      instructions to install JDK 8.

   b. On mac, with homebrew installed you can use the following::

        brew tap caskroom/versions
        brew cask install java8  

   c. On Debian based systems (Ubuntu!) you can run the following::

        sudo add-apt-repository ppa:openjdk-r/ppa
        sudo apt-get update
        sudo apt-get install openjdk-8-jdk

2. Now install the :code:`minerl` package!::

        pip3 install --upgrade minerl

**That's it! Now you're good to go :) 💯💯💯**
