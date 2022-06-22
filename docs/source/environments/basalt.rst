MineRL BASALT Competition Environments
=======================================
*The videos on this page do not represent the new MineRL environment or the new dataset.*

In the Benchmark for Agents that Solve Almost-Lifelike Task (BASALT) 
competition, your task is to solve tasks based on human judgement, 
instead of pre-defined reward functions. The goal is to produce agents that are 
judged by real humans to be effective at solving a given task. This calls for 
training on human-feedback, whether it is training from demonstrations, training on human preferences or using humans to correct agents’ actions.

.. exec::

    from minerl.herobraine import envs
    from minerl.utils import docs
    for env_spec in envs.BASALT_COMPETITION_ENV_SPECS:
        docs.print_env_spec_sphinx(env_spec)