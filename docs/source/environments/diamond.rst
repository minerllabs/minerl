MineRL Diamond Competition Environments
===============================================

The goal of these environments is to obtain diamond or some item made of diamond.

.. automodule:: minerl.herobraine.env_specs.basalt_specs.FindCaveEnvSpec
    :members:
    :undoc-members:
    :show-inheritance:

.. exec::

    from minerl.herobraine import envs
    from minerl.utils import docs
    for env_spec in envs.COMPETITION_ENV_SPECS:
        docs.print_env_spec_sphinx(env_spec)
