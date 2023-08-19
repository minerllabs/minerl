Performance tips
================

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
  
  
Docker images for headless rendering with GPU
------------------------------------------------

The above instructions might not work with a server without root access. You may use `this <https://github.com/jeasinema/egl-docker>`_ docker file (alternatives can be found `here <https://github.com/ehfd/docker-nvidia-egl-desktop>`_ and `here <https://github.com/MineDojo/egl-docker>`_ instead). 

To begin with, build & run this docker on your server.

.. code-block:: bash
	
	git clone https://github.com/jeasinema/egl-docker && cd egl-docker
	docker build . -t <docker_name>
	docker run --gpus all -it <docker_name>:latest /bin/bash

Inside the container, use the following command to verify if the GPU rendering is working. If you can see something like ``OpenGL Renderer: NVIDIA GeForce RTX 3090/PCIe/SSE2``, congratulations. Otherwise output like ``OpenGL Renderer: llvmpipe (LLVM 12.0.0, 256 bits)`` indicates you're still using CPU. Feel free to post to `this repo <https://github.com/jeasinema/egl-docker>`_ if you have any issues.

.. code-block:: bash

	vglrun /opt/VirtualGL/bin/glxspheres64

You're good to go! Just prepend your commands with ``vglrun`` to enable GPU rendering.

**Acknowledgements**: This docker image is brought to you by `Xiaojian Ma <https://github.com/jeasinema>`_ and the `MineDoJo <https://minedojo.org>`_ team, and it is developed upon `this project <https://github.com/ehfd/docker-nvidia-egl-desktop>`_ by `Seungmin Kim <https://github.com/ehfd>`_.

Singularity container for headless rendering with GPU
------------------------------------------------------

There is also a Singularity container based on the docker image above `here <https://github.com/Sanfee18/singularity-minerl>`_. 
All the information on how to build and run the container are specified inside this github repo, plus some things you will have to take into consideration before being able to use it.

**Acknowledgements**: This singularity container is brought you by `David Sanfelix <https://github.com/Sanfee18>`_.
