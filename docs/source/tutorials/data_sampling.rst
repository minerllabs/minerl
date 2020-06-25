..  admonition:: Solution
    :class: toggle

===============================
Sampling The Dataset
===============================

.. _checkout the environment documentation: http://minerl.io/docs/environments/index.html#competition-environments

.. role:: python(code)
   :language: python

.. role:: bash(code)
   :language: bash

Now that your agent can act in the environment, we should 
show it how to leverage human demonstrations.

To get started, let's ensure the data has been downloaded.

.. code-block:: bash

    # Unix, Linux
    $MINERL_DATA_ROOT="your/local/path" python3 -m minerl.data.download
    # Windows
    $env:MINERL_DATA_ROOT="your/local/path"; python3 -m minerl.data.download


Or simply download a single experiment

.. code-block:: bash

    python -m minerl.data.download 'MineRLObtainDiamond-v0'

For a complete list of published experiments, `checkout the environment documentation`_. You can also download the data
in your python scripts 

Now we can build the datast for :code:`MineRLObtainDiamond-v0`

.. code-block:: python

    data = minerl.data.make(
        'MineRLObtainDiamond-v0', 
        data_dir='/your/local/path')
    

    for current_state, action, reward, next_state, done \
        in data.batch_iter(
            batch_size=1, num_epochs=1, seq_len=32):

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

===============================
K-means exploration
===============================

.. _vectorized obfuscated environments: http://minerl.io/docs/environments/index.html#competition-environments
.. _MineRLObtainDiamondVectorObf-v0: http://minerl.io/docs/environments/index.html#minerlobtaindiamondvectorobf-v0
.. _MineRLTreechopVectorObf-v0: https://minerl.io/docs/environments/index.html#minerltreechopvectorobf-v0
.. _k-means: https://en.wikipedia.org/wiki/K-means_clustering

.. role:: python(code)
   :language: python

.. role:: bash(code)
   :language: bash

With the 2020 MineRL competition, we introduced `vectorized obfuscated environments`_ which abstract non-visual state
information as well as the action space of the agent to be continuous vector spaces. See `MineRLObtainDiamondVectorObf-v0`_
for documentation on the evaluation environment for the competition.

To use techniques in the MineRL competition that require discrete actions, we can use `k-means`_ to quantize the human
demonstrations and give our agent n discrete actions representative of actions taken by humans when solving the environment.

To get started, let's download the `MineRLTreechopVectorObf-v0`_ environment.

.. code-block:: bash

    python -m minerl.data.download 'MineRLTreechopVectorObf-v0'

Now we load the dataset for `MineRLTreechopVectorObf-v0`_ and find 32 clusters using sklearn learn

.. code-block:: python

    from sklearn.cluster import KMeans

    dat = minerl.data.make('MineRLTreechopVectorObf-v0')

    # Load the dataset storing 1000 batches of actions
    act_vectors = []
    for _, act, _, _,_ in tqdm.tqdm(dat.batch_iter(16, 32, 2, preload_buffer_size=20)):
        act_vectors.append(act['vector'])
        if len(act_vectors) > 1000:
            break

    # Reshape these the action batches
    acts = np.concatenate(act_vectors).reshape(-1, 64)
    kmeans_acts = acts[:100000]

    # Use sklearn to cluster the demonstrated actions
    kmeans = KMeans(n_clusters=32, random_state=0).fit(kmeans_acts)

Now we have 32 actions that represent reasonable actions for our agent to take. Let's take these and improve our random
hello world agent from before.

.. code-block:: python

        i, net_reward, done, env = 0, 0, False, gym.make('MineRLTreechopVectorObf-v0')
        obs = env.reset()

        while not done:
            # Let's use a frame skip of 4 (could you do better than a hard-coded frame skip?)
            if i % 4 == 0:
                action = {
                    'vector': kmeans.cluster_centers_[np.random.choice(NUM_CLUSTERS)]
                }

            obs, reward, done, info = env.step(action)
            env.render()

            if reward > 0:
                print("+{} reward!".format(reward))
            net_reward += reward
            i += 1

        print("Total reward: ", net_reward)

Try comparing this k-means random agent with a random agent using :code:`env.action_space.sample()`! You should see the
human actions are a much more reasonable way to explore the environment!


..  admonition:: Full snippet
    :class: toggle

    .. code-block:: python

        import gym
        import tqdm
        import minerl
        import numpy as np

        from sklearn.cluster import KMeans

        dat = minerl.data.make('MineRLTreechopVectorObf-v0')

        act_vectors = []
        NUM_CLUSTERS = 30

        # Load the dataset storing 1000 batches of actions
        for _, act, _, _, _ in tqdm.tqdm(dat.batch_iter(16, 32, 2, preload_buffer_size=20)):
            act_vectors.append(act['vector'])
            if len(act_vectors) > 1000:
                break

        # Reshape these the action batches
        acts = np.concatenate(act_vectors).reshape(-1, 64)
        kmeans_acts = acts[:100000]

        # Use sklearn to cluster the demonstrated actions
        kmeans = KMeans(n_clusters=NUM_CLUSTERS, random_state=0).fit(kmeans_acts)

        i, net_reward, done, env = 0, 0, False, gym.make('MineRLTreechopVectorObf-v0')
        obs = env.reset()

        while not done:
            # Let's use a frame skip of 4 (could you do better than a hard-coded frame skip?)
            if i % 4 == 0:
                action = {
                    'vector': kmeans.cluster_centers_[np.random.choice(NUM_CLUSTERS)]
                }

            obs, reward, done, info = env.step(action)
            env.render()

            if reward > 0:
                print("+{} reward!".format(reward))
            net_reward += reward
            i += 1

        print("Total reward: ", net_reward)


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
