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

    The following Basic Environments are NOT part of the MineRL Diamond and BASALT competitions!

    Feel free to use them for personal exploration, but note that competitions agents may only
    be trained on their corresponding competition environments.

.. exec::

    from minerl.herobraine import envs
    from minerl.utils import docs
    for env_spec in envs.BASIC_ENV_SPECS:
        docs.print_env_spec_sphinx(env_spec)

MineRL Diamond Competition Environments
=======================================

.. exec::

    from minerl.herobraine import envs
    from minerl.utils import docs
    for env_spec in envs.COMPETITION_ENV_SPECS:
        docs.print_env_spec_sphinx(env_spec)

MineRL BASALT Competition Environments
=======================================

.. exec::

    from minerl.herobraine import envs
    from minerl.utils import docs
    for env_spec in envs.BASALT_COMPETITION_ENV_SPECS:
        docs.print_env_spec_sphinx(env_spec)
