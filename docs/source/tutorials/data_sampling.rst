===============================
Sampling The Dataset
===============================

.. _checkout the environment documentation: http://minerl.io/docs/environments/

Now that your agent can act in the environment, we should 
show it how to leverage human demonstrations.

To get started, let's ensure the data has been downloaded

.. code-block:: python

    import minerl

    minerl.data.download('/your/local/path')

Or simply download a single experiment

.. code-block:: python

    minerl.data.download('/your/local/path', experiment='MineRLObtainDiamond-v0')

For a complete list of published experiments, `checkout the environment documentation`_.

Now we can build the datast for :code:`MineRLObtainDiamond-v0`

.. code-block:: python

    data = minerl.data.make(
        'MineRLObtainDiamond-v0', 
        data_dir='/your/local/path')
    
    # Iterate through a single epoch gathering sequences of at most 32 steps
    for current_state, action, reward, next_state, done \
        in data.sarsd_iter(
            num_epochs=1, max_sequence_len=32):

            # Print the POV @ the first step of the sequence
            print(current_state['pov'][0])

            # Print the final reward pf the sequence!
            print(reward[-1])

            # Check if final (next_state) is terminal.
            print(done[-1])

            # ... do something with the data.
            print("At the end of trajectories the length"
                  "can be < max_sequence_len", len(reward))


.. warning:: 
    The :code:`minerl` package uses environment variables to locate the data directory.
    For portability, plese define :code:`MINERL_DATA_ROOT` as 
    :code:`/your/local/path/` in your system environment variables.



=============================================================
Visualizing The Data :code:`minerl.viewer`
=============================================================

To help you get familiar with the MineRL dataset,
the :code:`minerl` python package also provides a data trajectory viewer called
:code:`minerl.viewer`:


.. image:: ../assets/cropped_viewer.gif
  :width: 90 %
  :alt: 
  :align: center


The :code:`minerl.viewer` program lets you step through individual
trajectories, 
showing the observation seen the player, the action
they took (including camera, movement, and any action described by an MineRL
environment's action space), and the reward they received.

.. exec::
 
    import minerl
    import minerl.viewer

    help_str = minerl.viewer.parser.format_help()

    print(".. code-block:: bash\n") 
    for line  in help_str.split("\n"):
        print("\t{}".format(line))


**Try it out on a random trajectory by running:** 

.. code-block:: bash

    # Make sure your MINERL_DATA_ROOT is set!
    export MINERL_DATA_ROOT='/your/local/path'

    # Visualizes a random trajectory of MineRLObtainDiamondDense-v0
    python3 -m minerl.viewer MineRLObtainDiamondDense-v0 



**Try it out on a specific trajectory by running:**

.. exec::
 
    import minerl
    import minerl.viewer

    traj_name = minerl.viewer._DOC_TRAJ_NAME

    print(".. code-block:: bash\n")
    
    print('\t# Make sure your MINERL_DATA_ROOT is set!')
    print("\texport MINERL_DATA_ROOT='/your/local/path'")
    print("\t# Visualizes a specific trajectory. {}...".format(traj_name[:17]))
    print("\tpython3 -m minerl.viewer MineRLTreechop-v0 \\")
    print("\t\t{}".format(traj_name))
