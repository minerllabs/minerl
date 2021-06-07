.. _MineRL competition environments: http://minerl.io/docs/environments/index.html#competition-environments

General Information
================================


The :code:`minerl` package includes several environments as follows.
This page describes each of the included environments, provides usage samples,
and describes the exact action and observation space provided by each
environment!



.. caution::
    In the MineRL Competition, many environments are provided for training,
    however competition agents will only
    be evaluated in :code:`MineRLObtainDiamondVectorObf-v0` which has **sparse** rewards. See `MineRLObtainDiamondVectorObf-v0`_.

.. note::
    All environments offer a default no-op action via :code:`env.action_space.no_op()`
    and a random action via :code:`env.action_space.sample()`.

.. include:: handlers.rst
    :end-before: inclusion-marker-do-not-remove

Basic Environments
=======================================

.. warning::

    The following basic environments are NOT part of the 2020 MineRL Competition! Feel free to use them for exploration
    but agents may only be trained on `MineRL competition environments`_!

.. exec::

    from minerl.utils import docs
    for env_spec in docs.BASIC_ENV_SPECS:
        docs.print_actions_for_id(env_spec)

Competition Environments
=======================================

.. exec::

    from minerl.utils import docs
    for env_spec in docs.COMPETITION_ENV_SPECS:
        docs.print_actions_for_id(env_spec)

