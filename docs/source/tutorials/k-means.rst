..  admonition:: Solution
    :class: toggle

===================
K-means exploration
===================

.. _2020 MineRL Competition: https://www.aicrowd.com/challenges/neurips-2020-minerl-competition
.. _vectorized obfuscated environments: http://minerl.io/docs/environments/index.html#competition-environments
.. _MineRLObtainDiamondVectorObf-v0: http://minerl.io/docs/environments/index.html#minerlobtaindiamondvectorobf-v0
.. _MineRLTreechopVectorObf-v0: https://minerl.io/docs/environments/index.html#minerltreechopvectorobf-v0
.. _k-means: https://en.wikipedia.org/wiki/K-means_clustering
.. _data sampling: http://minerl.io/docs/tutorials/data_sampling

.. role:: python(code)
   :language: python

.. role:: bash(code)
   :language: bash

With the `2020 MineRL competition`_, we introduced `vectorized obfuscated environments`_ which abstract non-visual state
information as well as the action space of the agent to be continuous vector spaces. See `MineRLObtainDiamondVectorObf-v0`_
for documentation on the evaluation environment for that competition.

To use techniques in the MineRL competition that require discrete actions, we can use `k-means`_ to quantize the human
demonstrations and give our agent n discrete actions representative of actions taken by humans when solving the environment.

To get started, let's download the `MineRLTreechopVectorObf-v0`_ environment.

.. code-block:: bash

    python -m minerl.data.download --environment 'MineRLTreechopVectorObf-v0'

.. note::

    If you are unable to download the data ensure you have the :code:`MINERL_DATA_ROOT` env variable
    set as demonstrated in `data sampling`_.

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

Putting this all together we get:

.. raw:: html

    <div style="position: center; padding-left: 15%; padding-bottom: 0.25%; height: 0; overflow: hidden; max-width: 100%; height: 50%;">
        <iframe width="450" height="490" src="https://www.youtube.com/embed/H8mVTQIKgEk?controls=0" frameborder="0" allow="accelerometer; autoplay; encrypted-media; gyroscope; picture-in-picture" allowfullscreen></iframe>
    </div>

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


Try comparing this k-means random agent with a random agent using :code:`env.action_space.sample()`! You should see the
human actions are a much more reasonable way to explore the environment!


