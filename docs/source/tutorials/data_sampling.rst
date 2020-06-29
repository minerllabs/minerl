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


Moderate Human Demonstrations
_______________________________

MineRL-v0 uses community driven demonstrations to help researchers develop sample efficient techniques.
Some of these demonstrations are less than optimal, however others could feacture bugs with the client,
server errors, or adversarial behavior.

Using the MineRL viewer, you can help curate this dataset by viewing these demonstrations manually and
reporting bad streams by submitting an issue to github with the following information:

#. The stream name of the stream in question
#. The reason the stream or segment needs to be modified
#. The sample / frame number(s) (shown at the bottom of the viewer)

