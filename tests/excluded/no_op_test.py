import minerl, gym
env = gym.make("MineRLObtainDiamondVectorObf-v0")
obs = env.reset()
_ = env.step(env.action_space.noop()) # Also happens if you try to feed in {'vector': np.random.random((64,))}