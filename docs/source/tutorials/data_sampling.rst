..  admonition:: Solution
    :class: toggle

===============================
The MineRL Dataset
===============================
.. _data-collection guide: http://minerl.io/play

The MineRL-v0 dataset is collected from client side re-simulated Minecraft demonstration data. If you would like to
contribute please see the  `data-collection guide`_



Sampling The Dataset
____________________

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


Or we can simply download a single experiment

.. code-block:: bash

    # Unix, Linux
    $MINERL_DATA_ROOT="your/local/path" python3 -m minerl.data.download "MineRLObtainDiamond-v0"

    # Windows
    $env:MINERL_DATA_ROOT="your/local/path"; python3 -m minerl.data.download "MineRLObtainDiamond-v0"

For a complete list of published experiments, `checkout the environment documentation`_. You can also download the data
in your python scripts 

Now we can build the datast for :code:`MineRLObtainDiamond-v0`

.. code-block:: python

    data = minerl.data.make(
        'MineRLObtainDiamond-v0')
    

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

..  admonition:: Solution
    :class: toggle

Vectorized Obfuscation Environments
___________________________________

.. _2020 MineRL Competition: https://www.aicrowd.com/challenges/neurips-2020-minerl-competition
.. _vectorized obfuscated environments: http://minerl.io/docs/environments/index.html#competition-environments
.. _MineRLObtainDiamondVectorObf-v0: http://minerl.io/docs/environments/index.html#minerlobtaindiamondvectorobf-v0
.. _MineRLTreechopVectorObf-v0: https://minerl.io/docs/environments/index.html#minerltreechopvectorobf-v0
.. _data sampling: http://minerl.io/docs/tutorials/data_sampling
.. _k-means tutorial: http://minerl.io/docs/tutorials/k-means.html


With the `2020 MineRL competition`_, we introduced `vectorized obfuscated environments`_ which abstract non-visual state
information as well as the action space of the agent to be continuous vector spaces. For example in
`MineRLObtainDiamondVectorObf-v0`_, rather than being provided a dictionary of observations and actions -- which could be
used to illegally hard-code a meta-policy based on the observation -- the action space and non-visual observation
space are provided as unlabeled 64 dimensional vectors.

These vectors serve as wrappers of their base environment and were produced by training two auto-encoders over
the action and observations in the MineRL dataset respectively. Uniform sampling of both the action and observation spaces
was also trained to ensure that random actions and observatins stay within the original space when unwraped.

.. Note::

    In basic environments, :code:`env.action_space.sample()` uniformly samples the action space.
    However, in vectorized obfuscated environemnts, :code:`action_space.sample()` does NOT provide a uniform sampling
    of the underlying wraped space, but rather a uniform sampling of the vector space. This will cause bias in exploration
    and can be mitigated by using human actions rather than random samples. See the `k-means tutorial`_ for an example.


Moderate Human Demonstrations
_______________________________

.. _MineRL viewer: http://minerl.io/docs/tutorials/minerl_tools.html
.. _issue to Github: https://github.com/minerllabs/minerl/issues

MineRL-v0 uses community driven demonstrations to help researchers develop sample efficient techniques.
Some of these demonstrations are less than optimal. Some may feature anomolies, server errors, or adversarial behavior.

Using the `MineRL viewer`_, you can help curate this dataset by viewing these demonstrations and
reporting bad streams by submitting an `issue to Github`_ with the following information:

#. The stream name of the stream to be reviewed
#. The reason the stream or segment needs to be modified
#. The sample / frame number(s) (shown at the bottom of the viewer)

