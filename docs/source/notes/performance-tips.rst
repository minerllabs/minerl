Performance tips
================

Slowdown in obfuscated environments
-----------------------------------

Obfuscated environments, like :code:`MineRLObtainDiamondVectorObf-v0` make extensive use of :code:`np.dot` function, which by default
is parallelized over multiple threads. Since the vectors/matrices are small, the overhead
from this outweights benefits, and the environment appears much slower than it really is.

To speed up obfuscated environments, try setting environment variable ``OMP_NUM_THREADS=1`` to restrict
Numpy to only use one thread.
