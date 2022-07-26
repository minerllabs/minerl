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

The above instructions might not work with a server without root access. You may use `this <https://github.com/ehfd/docker-nvidia-egl-desktop>`_ prebuilt docker (an alternative can be found `here <https://github.com/MineDojo/egl-docker>`_) instead. These docker images are brought to you by `Seungmin Kim <https://github.com/ehfd>`_, `Xiaojian Ma <https://github.com/jeasinema>`_ and the `MineDoJo <https://minedojo.org>`_ team.


To begin with, pull & run this docker on your server. Please make sure your container is running using ``docker ps``

.. code-block:: bash
	
	docker run --gpus 1 -it -e TZ=UTC -e SIZEW=1920 -e SIZEH=1080 -e REFRESH=60 -e DPI=96 -e CDEPTH=24 -e PASSWD=mypasswd -e WEBRTC_ENCODER=nvh264enc -e BASIC_AUTH_PASSWORD=mypasswd -p 8080:8080 ghcr.io/ehfd/nvidia-egl-desktop:latest


In another terminal, attach to the previous docker container

.. code-block:: bash

	docker exec -it <container_id> /bin/bash

Inside the container, use the following command to verify if the GPU rendering is working. If you can see something like ``OpenGL Renderer: NVIDIA GeForce RTX 3090/PCIe/SSE2`` in the output, GPU rendering is working. Otherwise output like ``OpenGL Renderer: llvmpipe (LLVM 12.0.0, 256 bits)`` indicates you're still using CPU. Fee free to post on `this thread <https://github.com/ehfd/docker-nvidia-egl-desktop/issues/14>`_ if you have any issues.

.. code-block:: bash

	export VGL_REFRESHRATE=60
	export VGL_ISACTIVE=1
	export VGL_DISPLAY=egl
	export VGL_WM=1
	export DISPLAY=:0
	vglrun /opt/VirtualGL/bin/glxspheres64


Then you may install and run ``MineRL`` in the container. Please keep in mind that you need to append `vglrun` to all your runs with GPU rendering.




