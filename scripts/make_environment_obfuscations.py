import torch as th
import numpy as np
import dill
from tabulate import tabulate
from minerl.herobraine.hero.spaces import MineRLSpace
from minerl.herobraine.envs import MINERL_OBTAIN_DIAMOND_OBF_V0
import gym
import json
from json import JSONEncoder
from typing import List, Tuple, Callable

class SubsetSoftmax(th.nn.Module):
    """
    Applies softmax to a specified subvector.
    """
    def __init__(self, discrete_subset : List[Tuple]):
        super(SubsetSoftmax, self).__init__()
        self.discrete_subset = discrete_subset

    def forward(self, x):
        y= x.clone()
        for (a,b) in self.discrete_subset:
            y[..., a:b] = th.nn.functional.softmax(x[..., a:b])
        return y

    def numpy_lambda(self):
        def f(x):
            x = x[:]
            for (a,b) in self.discrete_subset:
                exp = np.exp(x[...,a:b])
                sm = np.sum(exp)
                x[...,a:b] = exp/sm
            return x
        return f


class NumpyArrayEncoder(JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        if isinstance(obj, np.int64):
            return int(obj)
        if isinstance(obj, np.int32):
            return int(obj)
        if isinstance(obj, np.float64):
            return float(obj)
        return JSONEncoder.default(self, obj)


class ObfNet(th.nn.Module):
    """
    A 2 layer fully connected auto-encoder.
    """
    def __init__(self, input_dimension, latent_dimension, 
        discrete_subset, *hidden_dims):
        super().__init__()

        hidden_dims = list(hidden_dims)
        encoder_layers = []
        last_dim = input_dimension
        for h in (hidden_dims + [latent_dimension]):
            print(last_dim, h)
            encoder_layers.extend([
                th.nn.Linear(last_dim, h),
                th.nn.ReLU()
            ])
            last_dim = h
        self.encoder_layers = encoder_layers[:-1]
        self.encoder = th.nn.Sequential(*self.encoder_layers)

        # Now make the decoder by reversing the order of hidden dims:
        decoder_layers = []
        last_dim = latent_dimension
        for h in (hidden_dims[::-1]) + [input_dimension]:
            decoder_layers.extend([
                th.nn.Linear(last_dim, h),
                th.nn.ReLU()]
            )
            last_dim = h
        self.decoder_layers = decoder_layers[:-1]

        self.decoder = th.nn.Sequential(*self.decoder_layers)
        self.subset_softmax = SubsetSoftmax(discrete_subset)
        self.logit_subset = discrete_subset

        

    def forward(self, x):
        enc = self.encoder(x)
        dec_with_logits = self.decoder(enc)
        dec = self.subset_softmax(dec_with_logits)
        return dec

    def numpy_pickle(self, out):
        def convert_layers(layers):
            np_lays = []
            for layer in layers:
                if isinstance(layer, th.nn.Linear):
                    W = layer.weight.cpu().detach().numpy()
                    b = layer.bias.cpu().detach().numpy()
                    np_lays.append(("linear", (W, b)))
                if isinstance(layer, th.nn.ReLU):
                    np_lays.append(("relu", None))
                if isinstance(layer, SubsetSoftmax):
                    np_lays.append(("subset_softmax", layer.discrete_subset))

            def func(x):
                for t, data in np_lays:
                    if t == 'linear':
                        W,b = data
                        x = x.dot(W.T) + b
                    elif t == 'relu':
                        x = x* (x > 0)
                    elif t == 'subset_softmax':
                        discrete_subset = data
                        for (a,b) in discrete_subset:
                            exp = np.exp(x[...,a:b])
                            sm = np.sum(exp)
                            x[...,a:b] = exp/sm
                    else:
                        raise NotImplementedError()
                return x

            return func
        
        with open(out, 'wb') as f:
            dill.dump(
                (
                    convert_layers(self.encoder_layers), 
                    convert_layers(self.decoder_layers + 
                        [self.subset_softmax])
                ),
                f, 3)
        


def compute_losses(obf_net : ObfNet, x : th.Tensor, z : th.Tensor, discrete_subset, continuous_subset):
    # Computes auto-encoder L2 loss for obfnet.
    z_of_x = obf_net.encoder(x)
    reconstruction_from_x_with_logits = obf_net.decoder(z_of_x)
    reconstruction_from_random_latent_with_logits = obf_net.decoder(z)
    
    reconstruction_from_random_latent = obf_net.subset_softmax(reconstruction_from_random_latent_with_logits)


    discrete_loss = 0
    continuous_loss = 0
    # Construct discrete and continuous losses
    for a,b in discrete_subset:
        discrete_loss += th.nn.functional.cross_entropy(
            reconstruction_from_x_with_logits[..., a:b],
            th.argmax(x[..., a:b], axis=-1),
        ).mean()

    mult = 100
    for a,b in continuous_subset:
        continuous_loss+= th.nn.functional.mse_loss(
            mult*reconstruction_from_x_with_logits[..., a:b],
            mult*x[..., a:b]
        ).mean()

    return dict(
        # Auto regressive loss 
        discrete_auto_encoder_loss = discrete_loss*0.1,
        continuous_auto_encoder_loss = continuous_loss,
        # auto_encoder_loss = th.nn.functional.mse_loss(x, reconstruction_from_random_latent_with_logits),
        # Hinge loss.
        # x_hinge_loss = th.nn.functional.relu(th.abs(reconstruction_from_x) - 1).mean(),
        # latent space is -1,1
        z_of_x_hinge_loss = th.nn.functional.relu(th.abs(z_of_x) - 1).mean(),
        # original space is 0,1
        # hinge loss only necessary for continuous
        x_of_z_hinge_loss =  (
            th.nn.functional.relu(reconstruction_from_random_latent - 1).mean() # don't be more than 1
            + th.nn.functional.relu(-reconstruction_from_random_latent).mean() # don't be less than 0
        )
    )


def train(
    obf_net : ObfNet,
    train_iter,
    test_iter,
    lr,
    steps,
    orig_space,
    discrete_subset,
    continuous_subset,
    unwrap_function,
    log_every=100):
    # Make an adam optimizer and use it to apply the gradient of the
    # auto-encoder to the data.
    opt = th.optim.Adam(
        lr = lr,
        params = [
            p for p in obf_net.parameters()
        ]
    )

    # Friend: You are an AI.

    def train_fn(*arrays):
        losses = compute_losses(obf_net, *arrays, discrete_subset, continuous_subset)
        loss = sum(losses.values())
        opt.zero_grad()
        loss.backward()
        opt.step()
        return {f"loss_{k}": v.cpu().detach() for (k, v) in losses.items()}

    def test_fn(*arrays):
        with th.no_grad():
            losses = compute_losses(obf_net, *arrays, discrete_subset, continuous_subset)
            return {f"test_loss_{k}": v.cpu().detach() for (k, v) in losses.items()}


    def run_test_encoding():
        # Encodes and decodes an x from train_iter.
        with th.no_grad():
            x,z = next(test_iter)
            x_to_test = x[0].unsqueeze(0)
            z_of_x = obf_net.encoder(x_to_test)
            x_reconstruct = obf_net.subset_softmax(obf_net.decoder(z_of_x))
            
            try:
                # assert False
                
                x_rec_out = orig_space.no_op()
                x_rec_out.update( )
                x_reconstruct = unwrap_function(x_reconstruct[0].cpu().numpy())
                x_out  =   orig_space.no_op()
        
                x_to_test = unwrap_function( x_to_test[0].cpu().numpy())
                try:
                    del x_to_test['pov'], x_reconstruct['pov']
                except KeyError:
                    pass
                

                x_reconstruct = json.dumps(x_reconstruct, indent=3, cls=NumpyArrayEncoder)
                x_to_test = json.dumps(x_to_test, indent=3, cls=NumpyArrayEncoder)
            except AssertionError as e:
                # raise e
                pass

            print("\tInput", x_to_test)
            print("\tLatent", z_of_x)
            print("\tOutput",  x_reconstruct)


    for step in range(steps):
        train_batch = next(train_iter)
        stats = train_fn(*train_batch)
        stats['step'] = step
        # print a tabulation of the stats
        if step % log_every == 0:
            stats.update(test_fn(*next(test_iter)))
            print(tabulate(stats.items(), ["stat", "value"], tablefmt='fancy_grid'))
            run_test_encoding()


def generate_embedding(
        orig_space,
        vector_space : MineRLSpace, 
        latent_space : MineRLSpace,
        sample_from_vector_space : Callable, 
        discrete_subset,
        continuous_subset,
        unwrap_function,
        aux_data_iterator=None,
        use_fast_sampling=False):
    """
    Trains an embedding

    Args:
        vector_space (MineRLSpace): The vector space to to embed
        latent_space (MineRLSpace): The size of the embedding to produce
        sample_from_vector_space (Callable, optional): A lambda which enables sampling from the vector space
        unvectorize_vec (Callable, optional): A lambda which unvectorizes a Box space to a Dict space; enables 

    Returns:
        ObfNet: A trained embedding obf_net

    """
    true_dim = vector_space.shape[0]
    latent_dim = latent_space.shape[0]


    def get_test_iter(num_to_test):
        while True:
            x_samples = np.array([sample_from_vector_space() for _ in range(num_to_test)])
            z_samples = np.array([latent_space.sample() for _ in range(num_to_test)])
            yield (x_samples, z_samples)


    def get_train_iter(batch_size):
        while True:
            yield  (np.random.rand(batch_size, true_dim), #(np.array([sample_from_env() for _ in range(batch_size)]),  
                np.random.rand(batch_size, latent_dim)*2 -1)

    def convert_to_torch(train_iter):
        """
        An generator that converts the results of train_iter to torch tensors."""
        for x in train_iter:
            yield list(th.from_numpy(xx).float().cuda() for xx in x)


    print(true_dim)
    # Create an obf net with two layers
    obf_net = ObfNet(true_dim, latent_dim, discrete_subset, 256).cuda()

    #Trains and obf net.
    train(
        obf_net=obf_net,
        train_iter=convert_to_torch(
           ( get_test_iter(64) if not use_fast_sampling else get_train_iter(64))
            ),
        test_iter=convert_to_torch(get_test_iter(64)),
        lr=2e-5,
        steps=300_000,
        orig_space=orig_space,
        discrete_subset=discrete_subset,
        continuous_subset=continuous_subset,
        unwrap_function=unwrap_function,
        log_every=500

    )

    return obf_net


def get_discrete_and_continuous_subsets(vector_env, types='action'):
    """Makes a list of cts and discrete subsets
    corresponding indices in the vector env space.

    Args:
        vector_env (VecWrapper): The vector env.
        type (str, optional): [description]. Defaults to 'action'.
    """
    g = (lambda x: x.common_action_space) if types == 'action' else (lambda x: x.common_observation_space)
    orig_space = g(vector_env)
    discrete_subset = []
    cts_subset = []

    def get_subsets(cur_space, initial_index=0):
        if isinstance(cur_space, gym.spaces.Dict):
            cur_i = initial_index
            for key, value in cur_space.spaces.items():
                if value.is_flattenable():
                    # print(key, value)
                    get_subsets(value, cur_i)
                    cur_i += value.flattened.shape[0]
        else:
            lst_to_add = cts_subset if isinstance(cur_space, gym.spaces.Box) else discrete_subset
            lst_to_add.append((initial_index, initial_index + cur_space.flattened.shape[0]))
    get_subsets(orig_space)
    
    return discrete_subset, cts_subset


def aux_data_iterator(original_env, vector_env, types='action'):
    g = (lambda x: x.common_action_space) if types == 'action' else (lambda x: x.common_observation_space)
    dat = minerl.data.make(original_env.name)  
    for sarsd in dat.batch_iter(32, 100, -1, 10):
        if types == 'action':
            yield g(vector_env).flat_map(sarsd[1])
        else:
            yield g(vector_env).flat_map(sarsd[0])


import sys
import functools

import minerl
def main(env_to_generate=MINERL_OBTAIN_DIAMOND_OBF_V0):   

    vector_env = env_to_generate.env_to_wrap
    original_env = vector_env.env_to_wrap


    # Generate the aciton embedding.
    if sys.argv[1] == 'action':
        action_obf_net = generate_embedding(
            vector_env.action_space,
            vector_env.action_space.spaces['vector'], 
            env_to_generate.action_space.spaces['vector'],
            (
                lambda: vector_env.common_action_space.flat_map(vector_env.common_action_space.sample())
            ),
            *get_discrete_and_continuous_subsets(vector_env, types='action'),
            vector_env.common_action_space.unmap,
            aux_data_iterator(),
            use_fast_sampling=False)
        action_obf_net.numpy_pickle('action.secret.compat')
    
    if sys.argv[1] == 'observation':
        # TODO: Include common observation space.
        # Generate the state embedding
        observation_obf_net =  generate_embedding(
            vector_env.observation_space,
            vector_env.observation_space.spaces['vector'], 
            env_to_generate.observation_space.spaces['vector'],
            lambda: vector_env.common_observation_space.flat_map(vector_env.common_observation_space.sample()),
            *get_discrete_and_continuous_subsets(vector_env, types='observation'),
            functools.partial(vector_env.common_observation_space.unmap, skip=True),
            aux_data_iterator(),
            use_fast_sampling=True)
        # Now pickle the obf net.
        observation_obf_net.numpy_pickle('obs.secret.compat')

if __name__ ==  '__main__':
    main()


# obf_net = ObfNet(2, 4, 40, 40).double()
# # print(obf_net.pikle_network()) 
# print(obf_net.numpy_pickle('obf.secret'))