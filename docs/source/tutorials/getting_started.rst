================
Installation
================

Welcome to MineRL! This guide will get you started.


To start using the data and set of reinforcement learning
enviroments comrpising MineRL, you'll need to install the
main python package, :code:`minerl`.

.. _OpenJDK 8: https://openjdk.java.net/install/
.. _Windows installer: https://www.oracle.com/technetwork/java/javase/downloads/jdk8-downloads-2133151.html
.. _Mac installer: 

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


Your First Agent
===============================

With the :code:`minerl` package installed on your system you can
now make your first agent in Mineraft!

To get started, let's first import the necessary packages 

.. code-block:: python

    import gym
    import minerl

    # Run random agent through environment
    env = gym.make(environment) # or try 'MineRLObtainDiamond-v0'

    obs, info = env.reset()
    done = False
    
    while not done:
            action = env.action_space.sample()  # Generate a random action for the agent
            action['camera'] *= 0.1 # Full turn speed is quite fast for humans
            action['forward'] = 1   # Let's move forward in every step
            action['bacward'] = 0   # without this we may stand still sometimes
            obs, reward, done, info = env.step(action)
            if reward != 0:
            print(reward)
    print("MISSION DONE") 

Sampling The Dataset
===============================

Now that your agent can act in the environment, we should 
show it how to leverage human demonstrations.

To get started, let's ensure the data has been downloaded

.. code-block:: python

    import minerl

    minerl.data.download('/your/local/path')

Now we can build the datast for :code:`MineRLObtainDiamond-v0`

.. code-block:: python

    data = minerl.data.make('MineRLObtainDiamond-v0')
    
    # Iterate through a single epoch using batches of at most 32 steps
    for obs, rew, done, act in data.batch_iter(num_epochs=1, batch_size=32):
        print("Number of diffrent actions:", len(act))
        for action in act:
            print(act)
        print("Number of diffrent observations:", len(obs), obs)
        for observation in obs:
            print(obs)
        print("Rewards:", rew)
        print("Dones:", done)





.. note:: 
    The :code:`minerl` package uses environment variables to locate the data directory.
    For portability, plese define :code:`MINERL_DATA_ROOT` as 
    :code:`/your/local/path/data_texture_0_low_res` in your system environment variables.



