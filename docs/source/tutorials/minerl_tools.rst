=============================================================
Interactive Mode :code:`minerl.interactor`
=============================================================


.. warning::

    Interactor works in MineRL versions 0.3.7 and 0.4.4 (or above). 
    Install 0.3.7 with ``pip install minerl==0.3.7``, or the newest MineRL
    with ``pip install git+https://github.com/minerllabs/minerl.git@dev``.


Once you have started training agents, the next step is getting them to interact with human players.
To help achieve this, the :code:`minerl` python package provides a interactive Minecraft client called
:code:`minerl.interactor`:

.. raw:: html

    <div style="position: relative; padding-left: 1%; padding-bottom: 2.5%; height: 0; overflow: hidden; max-width: 100%; height: auto;">
        <iframe width="650" height="455" src="https://www.youtube.com/embed/4vM4Jz7ZXGs?controls=0" frameborder="0" allow="accelerometer; autoplay; encrypted-media; gyroscope; picture-in-picture" allowfullscreen></iframe>
    </div>


The :code:`minerl.interactor` allows you to connect a human-controlled Minecraft client
to the Minecraft world that your agent(s) is using and interact with the agent in real time.

.. note::

    For observation-only mode hit the :code:`t` key and type :code:`/gamemode sp` to enter
    spectator mode and become invisible to your agent(s).


.. exec::

    import minerl.env._multiagent

    help_str = minerl.env._multiagent._MultiAgentEnv.make_interactive.__doc__

    # print(".. code-block:: python\n")
    help_str = help_str.replace("\n        ", "\n")
    help_str = help_str.split("Args:")[0]
    for line  in help_str.split("\n"):
        print("{}".format(line))
