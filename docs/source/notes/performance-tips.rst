Performance tips
================

Slowdown in obfuscated environments
-----------------------------------

Obfuscated environments, like :code:`MineRLObtainDiamondVectorObf-v0` make extensive use of :code:`np.dot` function, which by default
is parallelized over multiple threads. Since the vectors/matrices are small, the overhead
from this outweights benefits, and the environment appears much slower than it really is.

To speed up obfuscated environments, try setting environment variable ``OMP_NUM_THREADS=1`` to restrict
Numpy to only use one thread.


Faster alternative to xvfb
--------------------------

Running MineRL on xvfb will slow it down by 2-3x as the rendering is done on CPU, not on the GPU.
A potential alternative is to use a combination of VirtualGL and virtual displays from nvidia tools.

**Note** that this may interfere with your display/driver setup, and may not work on cloud VMs
(``nvidia-xconfig`` is not available).

Following commands outline the procedure. You may need to adapt it to suit your needs.
After these commands, run ``export DISPLAY=:0`` and you should be ready to run MineRL. The Minecraft window
will be rendered in a virtual display.

All credits go to Tencent researchers who kindly shared this piece of information!

.. code-block:: bash

  sudo apt install lightdm libglu1-mesa mesa-utils xvfb xinit xserver-xorg-video-dummy

  sudo nvidia-xconfig -a --allow-empty-initial-configuration --virtual=1920x1200 --busid PCI:0:8:0
  cd /tmp
  wget https://nchc.dl.sourceforge.net/project/virtualgl/2.6.3/virtualgl_2.6.3_amd64.deb
  sudo dpkg -i virtualgl_2.6.3_amd64.deb
	
  sudo service lightdm stop
  sudo vglserver_config
  sudo service lightdm start