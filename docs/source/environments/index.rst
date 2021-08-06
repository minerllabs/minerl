.. _environments:

General Information
================================


The :code:`minerl` package includes several environments as follows.
This page describes each of the included environments, provides usage samples,
and describes the exact action and observation space provided by each
environment!



.. caution::
    In the MineRL Diamond Competition, many environments are provided for training.
    However, competition agents will only be evaluated in the :code:`MineRLObtainDiamond-v0`
    (Intro track) and :code:`MineRLObtainDiamondVectorObf-v0` (Research track) environments
    which have **sparse** rewards. For more details see `MineRLObtainDiamond-v0`_
    and `MineRLObtainDiamondVectorObf-v0`_.

.. note::
    All environments offer a default no-op action via :code:`env.action_space.no_op()`
    and a random action via :code:`env.action_space.sample()`.


.. include:: handlers.rst
    :end-before: inclusion-marker-do-not-remove


MineRL Diamond Competition Intro Track Environments
===================================================

.. exec::

    from minerl.herobraine import envs
    from minerl.utils import docs
    for env_spec in envs.BASIC_ENV_SPECS:
        docs.print_env_spec_sphinx(env_spec)

MineRL Diamond Competition Research Track Environments
======================================================

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
