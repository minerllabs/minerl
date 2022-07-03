MineRL BASALT Competition Environments
=======================================

.. warning::
    The videos on this page represent the v0.4 dataset, not the v1.0 dataset.

In the Benchmark for Agents that Solve Almost-Lifelike Task (BASALT) 
competition, your task is to solve tasks based on human judgement, 
instead of pre-defined reward functions. The goal is to produce agents that are 
judged by real humans to be effective at solving a given task. This calls for 
training on human-feedback, whether it is training from demonstrations, training on human preferences or using humans to correct agents’ actions.

.. exec::
    from minerl.herobraine.env_specs.basalt_specs import FindCaveEnvSpec, PenAnimalsVillageEnvSpec, MakeWaterfallEnvSpec, VillageMakeHouseEnvSpec
    env_specs = [FindCaveEnvSpec, PenAnimalsVillageEnvSpec, MakeWaterfallEnvSpec, VillageMakeHouseEnvSpec]
    from minerl.utils.documentation import print_env_spec_sphinx
    for env_spec in env_specs:
        print_env_spec_sphinx(env_spec)