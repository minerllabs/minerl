===============================
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
    
    # Iterate through a single epoch gathering sequences of at most 32 steps
    for current_state, action, reward, next_state, done in data.seq_iter(num_epochs=1, max_sequence_len=32):

        print("Number of different actions:", len(act))
        for action in act:
            print(act)
        print("Number of different observations:", len(obs), obs)
        for observation in obs:
            print(obs)
        print("Rewards:", rew)
        print("Dones:", done)





.. note:: 
    The :code:`minerl` package uses environment variables to locate the data directory.
    For portability, plese define :code:`MINERL_DATA_ROOT` as 
    :code:`/your/local/path/data_texture_0_low_res` in your system environment variables.



=============================================================
Visualizing The Data :code:`minerl.viewer`
=============================================================

Todo!