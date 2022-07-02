================
Installation
================

Welcome to MineRL! This guide will get you started.


To start using the MineRL dataset and Gym environments comprising MineRL, you'll need to install the
main python package, :code:`minerl`.

.. _OpenJDK 8: https://openjdk.java.net/install/
.. _Windows installer: https://www.oracle.com/java/technologies/downloads/#java8-windows
.. _checkout the environment documentation: http://minerl.io/docs/environments/
.. _checkout the competition environments: http://minerl.io/docs/environments/#competition-environments
.. _Git: https://git-scm.com/

1. First **make sure you have JDK 8** installed on your
   system.

   a. `Windows installer`_ -- On windows go this link and follow the
      instructions to install JDK 8. Install x64 version.

   b. On Mac, you can install Java 8 using homebrew and AdoptOpenJDK (an open source mirror, used here to get around the fact that Java8 binaries are no longer available directly from Oracle)::

        brew tap AdoptOpenJDK/openjdk
        brew install --cask adoptopenjdk8

   c. On Debian based systems (Ubuntu!) you can run the following::

        sudo add-apt-repository ppa:openjdk-r/ppa
        sudo apt-get update
        sudo apt-get install openjdk-8-jdk

2. If you are using Windows, you will also need :code:`bash` command. There are at least two ways to do this:

   a. Install Windows Subsystem for Linux (WSL. Tested on WSL 2). Note that installing MineRL this way
      may seem especially slow/stuck, but it is not; it is just a bit slow. You can also install MineRL
      on the WSL system itself, but you may need :code:`xvfb` to run the environment.
   b. Install bash along some other tools. E.g., `Git`_ will come with bash.
      After installation, you may have to update environment variables to include a path which contains
      bash.exe. For above git tools, this is [installation-dir]/bin.

3. Now install the :code:`minerl` package!::

        pip3 install git+https://github.com/minerllabs/minerl@v1.0.0

.. note::

        You may need the user flag:
        :code:`pip3 install git+https://github.com/minerllabs/minerl@v1.0.0 --user` to install properly.
