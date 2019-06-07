
.. exec::

    def print_actions_for_id(id):
        import minerl
        import gym
        import json

        def print_json(arg):
            import json
            json_obj = json.dumps(arg, sort_keys=True, indent=8,
                default=lambda o: str(o))
            json_obj= json_obj[:-1] + "    }"
            print('.. code-block:: JavaScript\n\n    %s\n\n\n' % json_obj)
         
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


        print("")
        print("{}".format(id))
        print("=============================")
        
        if 'docstr' in envspec._kwargs:
            print(envspec._kwargs['docstr'])

        
        print("------------------------")
        print("Usage")
        print("------------------------")
        
        
        usage_str = '''.. code-block:: python

            import gym
            import minerl
            
            # Run a random agent through the environment
            env = gym.make("{}") # A {} env

            obs, _ = env.reset()
            done = False

            while not done:
                # Take a no-op through the environment.
                obs, rew, done, _ = env.step(env.action_space.noop()) 


            # Sample some data from the dataset!
            data = minerl.data.make(
                "{}", 
                data_dir='/your/local/path/data_texture_0_low_res')

            # Iterate through a single epoch using batches of 32 steps
            for act, obs, rew, done in data.batch_iter(num_epochs=1, batch_size=32):
                # Do something
        '''.format(id,id,id)
        print(usage_str)




        action_space = prep_space(envspec._kwargs['action_space'])
        state_space = prep_space(envspec._kwargs['observation_space'])

        print("------------------------")
        print("Observation Space")
        print("------------------------")
        print_json(state_space)


        print("------------------------")
        print("Action Space")
        print("------------------------")
        print_json(action_space)
        

    ids = [
           'MineRLTreechop-v0',
           'MineRLNavigateDense-v0',
           'MineRLNavigate-v0',
           'MineRLNavigateExtremeDense-v0',
           'MineRLNavigateExtreme-v0',
           'MineRLObtainIronPickaxe-v0',
           'MineRLObtainDiamond-v0',]
    
    for i in ids:
        print_actions_for_id(i)