===============================
Sampling The Dataset
===============================

Now that your agent can act randomly in the enviroments, we should
show it how to leverage human demonstrations.

To get started, let's ensure the data has been downloaded

.. code-block:: python

    import minerl

    minerl.data.download('/your/local/path')

Now we can build the datast for :code:`MineRLObtainDiamond-v0`

.. code-block:: python

    import minerl

    data = minerl.data.make('MineRLObtainDiamond-v0', data_dir='/your/local/path/data_texture_0_low_res')
    
    # Iterate through a single epoch using batches of 32 steps
    for act, obs, rew, done in data.batch_iter(num_epochs=1, batch_size=32):
        print("Act shape:", len(act), act)
        print("Obs shape:", len(obs), obs)
        print("Rew shape:", len(rew), rew)



.. note:: 
    Hard-coding the data directory is bad practice. For portability, please define 
    :code:`MINERL_DATA_ROOT` as :code:`/your/local/path/data_texture_0_low_res`. 
    A demonstration on how to set the JAVA_HOME environment variable can be found
    `here <https://www.baeldung.com/java-home-on-windows-7-8-10-mac-os-x-linux>`_, 
    simply replace JAVA_HOME with MINERL_DATA_ROOT and /path/to/java_installation with
    /your/local/path/data_texture_0_low_res



