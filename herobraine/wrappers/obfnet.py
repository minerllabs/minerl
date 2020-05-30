import torch as th
import numpy as np
import dill
from tabulate import tabulate
from herobraine.hero.spaces import MineRLSpace
from herobraine.env_specs import MINERL_OBTAIN_DIAMOND_OBF_V0


class ObfNet(th.nn.Module):
    """
    A 2 layer fully connected auto-encoder.
    """
    def __init__(self, input_dimension, latent_dimension, *hidden_dims):
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

        

    def forward(self, x):
        enc = self.encoder(x)
        dec = self.decoder(enc)
        return dec

    def numpy_pickle(self, out):
        def convert_layers(layers):
            np_lays = []
            for layer in layers:
                if isinstance(layer, th.nn.Linear):
                    W = layer.weight.detach().numpy()
                    b = layer.bias.detach().numpy()
                    np_lays.append(("linear", (W, b)))
                if isinstance(layer, th.nn.ReLU):
                    np_lays.append(("relu", None))

            def func(x):
                for t, data in np_lays:
                    if t == 'linear':
                        W,b = data
                        x = x.dot(W.T) + b
                    elif t == 'relu':
                        x = x* (x > 0)
                    else:
                        raise NotImplementedError()
                return x

            return func
        
        with open(out, 'wb') as f:
            dill.dump(
                (
                    convert_layers(self.encoder_layers), 
                    convert_layers(self.decoder_layers)
                ),
                f)
        


def compute_losses(obf_net : ObfNet, x : th.Tensor, z : th.Tensor):
    # Computes auto-encoder L2 loss for obfnet.
    z_of_x = obf_net.encoder(x)
    reconstruction_from_x = obf_net.decoder(z_of_x)
    reconstruction_from_random_latent = obf_net.decoder(z)

    return dict(
        # Auto regressive loss 
        auto_encoder_loss = th.nn.functional.mse_loss(reconstruction_from_x, x).mean(),
        # Hinge loss.
        # x_hinge_loss = th.nn.functional.relu(th.abs(reconstruction_from_x) - 1).mean(),
        z_of_x_hinge_loss = th.nn.functional.relu(th.abs(z_of_x) - 1).mean(),
        z_hinge_loss =  th.nn.functional.relu(th.abs(reconstruction_from_random_latent) - 1).mean()
    )


def train(
    obf_net : ObfNet,
    train_iter,
    test_iter,
    lr,
    steps,
    log_every=100
):
    # Make an adam optimizer and use it to apply the gradient of the
    # auto-encoder to the data.
    opt = th.optim.Adam(
        lr = lr,
        params = [
            p for p in obf_net.parameters()
            # if p.requires_grad
        ]
    )

    # Friend: You are an AI.

    def train_fn(*arrays):
        losses = compute_losses(obf_net, *arrays)
        loss = sum(losses.values())
        opt.zero_grad()
        loss.backward()
        opt.step()
        return {f"loss_{k}": v.cpu().detach() for (k, v) in losses.items()}

    def test_fn(*arrays):
        with th.no_grad():
            losses = compute_losses(obf_net, *arrays)
            return {f"test_loss_{k}": v.cpu().detach() for (k, v) in losses.items()}


    def run_test_encoding():
        # Encodes and decodes an x from train_iter.
        with th.no_grad():
            x,z = next(train_iter)
            x_to_test = x[0].unsqueeze(0)
            z_of_x = obf_net.encoder(x_to_test)
            x_reconstruct = obf_net.decoder(z_of_x)
            
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




def generate_embedding(sample_from_env, true_space, latent_space : MineRLSpace):
    true_dim = true_space.shape[0]
    latent_dim = latent_space.shape[0]


    def get_test_iter(num_to_test):
        while True:
            x_samples = np.array([sample_from_env() for _ in range(num_to_test)])
            z_samples = np.array([latent_space.sample() for _ in range(num_to_test)])
            yield (x_samples, z_samples)


    def get_train_iter(batch_size):
        while True:
            yield  (np.random.rand(batch_size, true_dim)*2 -1, #(np.array([sample_from_env() for _ in range(batch_size)]),  
                np.random.rand(batch_size, latent_dim)*2 -1)

    def convert_to_torch(train_iter):
        """
        An generator that converts the results of train_iter to torch tensors."""
        for x in train_iter:
            yield list(th.from_numpy(xx).float() for xx in x)


    print(true_dim)
    # Create an obf net with two layers
    obf_net = ObfNet(true_dim, latent_dim, 256)

    #Trains and obf net.
    train(
        obf_net=obf_net,
        train_iter=convert_to_torch(get_train_iter(64)),
        test_iter=convert_to_torch(get_test_iter(64)),
        lr=2e-5,
        steps=300000,
        log_every=500

    )

    return obf_net


def main(env_to_generate=MINERL_OBTAIN_DIAMOND_OBF_V0):
    # Generate the aciton embedding.
    action_obf_net = generate_embedding(
        lambda: env_to_generate.env_to_wrap.wrap_action(env_to_generate.env_to_wrap.env_to_wrap.action_space.sample())['vector'],
        env_to_generate.env_to_wrap.action_space.spaces['vector'], 
        env_to_generate.action_space.spaces['vector'])
    action_obf_net.numpy_pickle('action.secret')
    
    # Generate the state embedding
    observation_obf_net =  generate_embedding(
        lambda: env_to_generate.env_to_wrap.wrap_observation(env_to_generate.env_to_wrap.env_to_wrap.observation_space.sample())['vector'],
        env_to_generate.env_to_wrap.observation_space.spaces['vector'], 
        env_to_generate.observation_space.spaces['vector'])

    # Now pickle the obf net.
    observation_obf_net.numpy_pickle('obs.secret')

if __name__ ==  '__main__':
    main()


# obf_net = ObfNet(2, 4, 40, 40).double()
# # print(obf_net.pikle_network()) 
# print(obf_net.numpy_pickle('obf.secret'))