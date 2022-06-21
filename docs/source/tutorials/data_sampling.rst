..  admonition:: Solution
    :class: toggle

====================================
Downloading and Sampling The Dataset
====================================

.. role:: python(code)
   :language: python

.. role:: bash(code)
   :language: bash


Introduction
============

Now that your agent can act in the environment, we should show it how to leverage human
demonstrations.

To get started, let's download the minimal version of the dataset (two demonstrations from every
environment). Since there are over 20 MineRL environments, this is still a sizeable download, at
about 2 GB.

Then we will sample a few state-action-reward-done tuples from the ``MineRLObtainDiamond-v0``
dataset.


Setting up environment variables
================================

The :code:`minerl` package uses the :code:`MINERL_DATA_ROOT` environment variable to locate the data
directory. Please export :code:`MINERL_DATA_ROOT=/your/local/path/`.

(Here are some tutorials on how to set environment variables on
`Linux/Mac <https://phoenixnap.com/kb/linux-set-environment-variable>`_ and
`Windows <https://support.shotgunsoftware.com/hc/en-us/articles/114094235653-Setting-global-environment-variables-on-Windows>`_
computers.)


Downloading the MineRL Dataset with :code:`minerl.data.download`
================================================================

To download the minimal dataset into ``MINERL_DATA_ROOT``, run the command:

.. code-block:: bash

    python3 -m minerl.data.download


.. note::

    The full dataset for a particular environment, or for a particular competition (Diamond or Basalt)
    can be downloaded using the ``--environment ENV_NAME`` and ``--competition COMPETITION`` flags.

    ``ENV_NAME`` is any Gym environment name from the
    :ref:`documented environments <environments>`.

    ``COMPETITION`` is ``basalt`` or ``diamond``.

    For more information, run ``python3 -m minerl.data.download --help``.

    As an example, to download the full dataset for "MineRLObtainDiamond-v0", you can run

    .. code-block:: bash

        python3 -m minerl.data.download --environment "MineRLObtainDiamond-v0"





Sampling the Dataset with :code:`buffered_batch_iter`
============================================

Now we can build the dataset for :code:`MineRLObtainDiamond-v0`

There are two ways of sampling from the MineRL dataset: the deprecated but still supported `batch_iter`, and
`buffered_batch_iter`. `batch_iter` is the legacy method, which we've kept in the code to avoid breaking changes,
but we have recently realized that, when using `batch_size > 1`, `batch_iter` can fail to return a substantial
portion of the data in the epoch.

**If you are not already using `data_pipeline.batch_iter`, we recommend against it, because of these issues**


The recommended way of sampling from the dataset is:

.. code-block:: python

    from minerl.data import BufferedBatchIter
    data = minerl.data.make('MineRLObtainDiamond-v0')
    iterator = BufferedBatchIter(data)
    for current_state, action, reward, next_state, done \
        in iterator.buffered_batch_iter(batch_size=1, num_epochs=1):

            # Print the POV @ the first step of the sequence
            print(current_state['pov'][0])

            # Print the final reward pf the sequence!
            print(reward[-1])

            # Check if final (next_state) is terminal.
            print(done[-1])

            # ... do something with the data.
            print("At the end of trajectories the length"
                  "can be < max_sequence_len", len(reward))



..  admonition:: Solution
    :class: toggle


Moderate Human Demonstrations
=============================

MineRL-v0 uses community driven demonstrations to help researchers develop sample efficient techniques.
Some of these demonstrations are less than optimal, however others could feature bugs with the client,
server errors, or adversarial behavior.

Using the MineRL viewer, you can help curate this dataset by viewing these demonstrations manually and
reporting bad streams by submitting an issue to github with the following information:

#. The stream name of the stream in question
#. The reason the stream or segment needs to be modified
#. The sample / frame number(s) (shown at the bottom of the viewer)

