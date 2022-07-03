===============================
Hello World: Your First Agent
===============================

With the :code:`minerl` package installed on your system you can
now make your first agent in Minecraft!

To get started, let's first import the necessary packages

.. code-block:: python

    import gym
    import minerl


Creating an environment
---------------------------

.. _checkout the environment documentation: http://minerl.io/docs/environments/
.. _many environments: http://minerl.io/docs/environments/

Now we can choose any one of the `many environments`_ included
in the :code:`minerl` package. To learn more about the environments
`checkout the environment documentation`_.

For this tutorial we'll  choose the :code:`MineRLBasaltFindCave-v0`
environment. In this task, the agent is placed to a new world
and its (subjective) goal is to find a cave, and end the episode.


To create the environment, simply invoke :code:`gym.make`

.. code-block:: python

    env = gym.make('MineRLBasaltFindCave-v0')

.. caution:: 
    Currently :code:`minerl` only supports environment rendering in **headed environments**
    (servers with monitors attached). 


    **In order to run** :code:`minerl` **environments without a head use a software renderer
    such as** :code:`xvfb`::

        xvfb-run python3 <your_script.py>


.. note::
    If you're worried and want to make sure something is
    happening behind the scenes install a logger **before**
    you create the envrionment.
    
    .. code-block:: python

        import logging
        logging.basicConfig(level=logging.DEBUG)
        
        env = gym.make('MineRLBasaltFindCave-v0')
    


Taking actions
---------------------------------
**As a warm up let's create a random agent.** 🧠 

Now we can reset this environment to its first position
and get our first observation from the agent by resetting the environment.

.. code-block:: python
    
    # Note that this command will launch the MineRL environment, which takes time.
    # Be patient!
    obs = env.reset()

The :code:`obs` variable will be a dictionary containing the following
observations returned by the environment. In the case of the
:code:`MineRLBasaltFindCave-v0` environment, only one observation is returned:
:code:`pov`, an RGB image of the agent's first person perspective.

.. code-block:: python

    {
        'pov': array([[[ 63,  63,  68],
            [ 63,  63,  68],
            [ 63,  63,  68],
            ...,
            [ 92,  92, 100],
            [ 92,  92, 100],
            [ 92,  92, 100]],,

            ...,


            [[ 95, 118, 176],
            [ 95, 119, 177],
            [ 96, 119, 178],
            ...,
            [ 93, 116, 172],
            [ 93, 115, 171],
            [ 92, 115, 170]]], dtype=uint8)
    }

.. _the environment reference documentation: http://minerl.io/docs/environments


Now let's take actions through the environment until time runs out
or the agent dies. To do this, we will use the normal OpenAI Gym :code:`env.step`
method.

.. code-block:: python
    
    done = False

    while not done:
        # Take a random action
        action = env.action_space.sample()
        # In BASALT environments, sending ESC action will end the episode
        # Lets not do that
        action["ESC"] = 0
        obs, reward, done, _ = env.step(action)
        env.render()


..   :scale: 100 %

With the :code:`env.render` call, you should see the agent move sporadically until :code:`done` flag is set to true,
which will happen when agent runs out of time (3 minutes in the FindCave task).

