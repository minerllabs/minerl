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

    def print_actions_for_id(id):
        import minerl
        import gym
        import json

        def print_json(arg):
            import json
            arg = {":ref:`{} <{}>`".format(k,k): arg[k] for k in arg}
            json_obj = json.dumps(arg, sort_keys=True, indent=8,
                default=lambda o: str(o))
            json_obj= json_obj[:-1] + "    })"
            
            print('.. parsed-literal:: \n\n    Dict(%s\n\n\n' % json_obj)
         
        def prep_space(space):
            import gym
            if isinstance(space, gym.spaces.Dict):
                dct = {}
                for k in space.spaces:
                    dct[k] = prep_space(space.spaces[k])
                return dct
            else:
                return space
   

   
        envspec = gym.spec(id)


        print("______________")
        print("{}".format(id))
        print("______________")
        
        if 'docstr' in envspec._kwargs:
            print(envspec._kwargs['docstr'])



        action_space = prep_space(envspec._kwargs['action_space'])
        state_space = prep_space(envspec._kwargs['observation_space'])

        print(".......")
        print("Observation Space")
        print(".......")
        print_json(state_space)


        print(".......")
        print("Action Space") 
        print(".......")
        print_json(action_space)

        print(".......")
        print("Usage")
        print(".......")


        usage_str = '''.. code-block:: python

            import gym
            import minerl
            
            # Run a random agent through the environment
            env = gym.make("{}") # A {} env

            obs = env.reset()
            done = False

            while not done:
                # Take a no-op through the environment.
                obs, rew, done, _ = env.step(env.action_space.noop()) 
                # Do something 
                
            ######################################

            # Sample some data from the dataset!
            data = minerl.data.make("{}")
 
            # Iterate through a single epoch using sequences of at most 32 steps
            for obs, rew, done, act in data.seq_iter(num_epochs=1, batch_size=32):
                # Do something 
        '''.format(id,id,id)
        print(usage_str) 
 

    ids = ['MineRLTreechop-v0',
           'MineRLNavigate-v0',
            'MineRLNavigateExtreme-v0',
            'MineRLNavigateDense-v0',
            'MineRLNavigateExtremeDense-v0',
            'MineRLObtainDiamond-v0',
            'MineRLObtainDiamondDense-v0',
            'MineRLObtainIronPickaxe-v0',
            'MineRLObtainIronPickaxeDense-v0',]

    for i in ids:
        print_actions_for_id(i)

Competition Environments
=======================================

.. exec::

    def print_actions_for_id(id):
        import minerl
        import gym
        import json

        def print_json(arg):
            import json
            arg = {":ref:`{} <{}>`".format(k,k): arg[k] for k in arg}
            json_obj = json.dumps(arg, sort_keys=True, indent=8,
                default=lambda o: str(o))
            json_obj= json_obj[:-1] + "    })"

            print('.. parsed-literal:: \n\n    Dict(%s\n\n\n' % json_obj)

        def prep_space(space):
            import gym
            if isinstance(space, gym.spaces.Dict):
                dct = {}
                for k in space.spaces:
                    dct[k] = prep_space(space.spaces[k])
                return dct
            else:
                return space



        envspec = gym.spec(id)


        print("______________")
        print("{}".format(id))
        print("______________")

        if 'docstr' in envspec._kwargs:
            print(envspec._kwargs['docstr'])



        action_space = prep_space(envspec._kwargs['action_space'])
        state_space = prep_space(envspec._kwargs['observation_space'])

        print(".......")
        print("Observation Space")
        print(".......")
        print_json(state_space)


        print(".......")
        print("Action Space")
        print(".......")
        print_json(action_space)

        print(".......")
        print("Usage")
        print(".......")


        usage_str = '''.. code-block:: python

            import gym
            import minerl

            # Run a random agent through the environment
            env = gym.make("{}") # A {} env

            obs = env.reset()
            done = False

            while not done:
                # Take a no-op through the environment.
                obs, rew, done, _ = env.step(env.action_space.noop())
                # Do something

            ######################################

            # Sample some data from the dataset!
            data = minerl.data.make("{}")

            # Iterate through a single epoch using sequences of at most 32 steps
            for obs, rew, done, act in data.seq_iter(num_epochs=1, batch_size=32):
                # Do something
        '''.format(id,id,id)
        print(usage_str)


    ids = ['MineRLTreechopVectorObf-v0',
            'MineRLNavigateVectorObf-v0',
            'MineRLNavigateExtremeVectorObf-v0',
            'MineRLNavigateDenseVectorObf-v0',
            'MineRLNavigateExtremeDenseVectorObf-v0',
            'MineRLObtainDiamondVectorObf-v0',
            'MineRLObtainDiamondDenseVectorObf-v0',
            'MineRLObtainIronPickaxeVectorObf-v0',
            'MineRLObtainIronPickaxeDenseVectorObf-v0',]

    for i in ids:
        print_actions_for_id(i)
