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

.. _checkout the environment documentation:
.. _many environments: TODO

Now we can choose any one of the `many environments`_ included
in the :code:`minerl` package. To learn more about the environments
`checkout the environment documentation`_.


For this tutorial we'll  choose the :code:`MineRLNavigate-v0`
environment. In this task, the agent is challenged with using
a first-person perspective of a random Minecraft map and
navigating to a target.

To create the environment, simply invoke :code:`gym.make`

.. code-block:: python

    env = gym.make('MineRLNavigate-v0')

.. note::
    The first time you run this command to complete, it will take a while as it is recompiling
    Minecraft with the MineRL simulator mod!

    If you're worried and want to make sure something is
    happening behind the scenes install a logger **before**
    you create the envrionment.
    
    .. code-block:: python

        import logging
        logging.basicConfig(level=logging.DEBUG)
        
        env = gym.make('MineRLNavigate-v0')
    


Taking actions
---------------------------------
**As a warm up let's create a random agent.** 🧠 

Now we can reset this environment to its first position
and get our first observation from the agent by reseting the environment.

.. code-block:: python

    obs, info = env.reset()

The :code:`obs` variable will be a dictionary containing the following
observations returned by the environment. In the case of the
:code:`MineRLNavigate-v0` environment, three observations are returned:
:code:`pov`, an RGB image of the agent's first person perspective;
:code:`compassAngle`, a float giving the angle of the agent to its
(approximate) target; and :code:`inventory`, a dictionary containing
the amount of :code:`'dirt'` blocks in the agent's inventory (this
is useful for climbing steep inclines).

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
            [ 92, 115, 170]]], dtype=uint8),
        'compassAngle': -63.48639,
        'inventory': {'dirt': 0}
    }

Now let's take actions through the environment until time runs out
or the agent dies. To do this, we will use the normal OpenAI Gym :code:`env.step`
method.

.. code-block:: python
    
    done = False

    while not done:
        action = env.action_space.sample()
        obs, reward, done, _ = env.step(action)




..   :scale: 100 %

After running this code you should see your agent move sporadically until the
:code:`done` flag is set to true. To confirm that our agent is at least qualitatively
acting randomly, on the right is a plot of the compass angle over the course of the experiment.

.. image:: ../assets/compass_angle.png


Default actions and a better policy
-------------------------------------

**Now let's make a hard-coded agent that actually runs
towards the target.** 🧠🧠🧠




