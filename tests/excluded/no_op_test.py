import minerl, gym

env = gym.make("MineRLObtainDiamondVectorObf-v0")
while True:
    obs = env.reset()
    done = False
    while not done:
        x = env.env_spec.wrap_action(env.env_spec.env_to_wrap.env_to_wrap.action_space.no_op())
        print(x)
        a, r, done, i = env.step(x)  # Also happens if you try to feed in {'vector': np.random.random((64,))}
        env.render()
