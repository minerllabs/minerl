MineRL Diamond Competition Environments
===============================================

The goal of these environments is to obtain diamond or some item made of diamond.

.. note::

    :code:`ESC` is not used in Diamond environments

.. note::
    Diamond environments also receive direct inventory observations (e.g. :code:`"apple":5` if the agent has five apples)

.. exec::
    from minerl.herobraine.env_specs.basalt_specs import FindCaveEnvSpec

    from minerl.herobraine.env_specs.obtain_specs import ObtainDiamondShovelEnvSpec
    from minerl.utils.documentation import print_env_spec_sphinx
    
    print_env_spec_sphinx(FindCaveEnvSpec)
