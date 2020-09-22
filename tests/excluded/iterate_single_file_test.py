import minerl
import matplotlib.pyplot as plt
import tqdm
import coloredlogs
import logging

coloredlogs.install(level=logging.DEBUG)
data = minerl.data.make('MineRLTreechop-v0', num_workers=1)

diter = data.sarsd_iter(num_epochs=1, max_sequence_len=1,
                        include_metadata=True, seed=1)
i = 1
tot_reward = 0
stream_name = None
for current_state, action, reward, next_state, done, meta in tqdm.tqdm(diter):
    if stream_name is None:
        stream_name = meta['stream_name']
        # print(meta)
        # print(len(reward))
    # print(stream_name == meta['stream_name'])
    # print(current_state.keys(), reward, next_state.keys(), done)
    tot_reward += reward[0]
    if done[-1] or stream_name != meta['stream_name']:
        print(i, done, tot_reward)
        break
    i += 1
