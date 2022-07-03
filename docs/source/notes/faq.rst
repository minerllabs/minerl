General FAQ
==========================

For Version 1.x
**************************

Why does this MineRL version take so long to install?
--------------------------------------------------------------------------------------------
Previous versions compiled the game binary when :code:`reset` gets called. 
v1.0.0 compiles the binary during install, so MineRL wont have to do so on 
:code:`reset` calls. This makes :code:`reset` faster. Also see the Windows FAQ 
for slow install info.

`Failed to initialize GLFW or GLX problems <https://github.com/minerllabs/minerl/issues/637>`_
--------------------------------------------------------------------------------------------
This can occur when attempting to run on a headless system without using something like xvfb.

Try :code:`xvfb-run -a python [path to your code]`

When trying to run MineRL, why do I get Java or JDK related errors?
------------------------------------------------------------------------------------------------------
Make sure you are using the correct JDK version for MineRL (must be Java JDK 8, the x64 version)
On Windows, the best option may be to remove all Javas from machine with the uninstall utility, 
and then install JDK 8 from the Oracle website.

------------

For Version 0.4.x
**************************

When I run MineRL, a tiny window pops up and I cant see what my agent is doing. Is something wrong?
------------------------------------------------------------------------------------------------------------------
No, this is the proper way that MineRL runs. Try useing :code:`env.render()` if you need to 
watch your agent.

Why is MineRL giving timeout errors or agents with :code:`Connection timed out!` errors?
------------------------------------------------------------------------------------------------------------------
If a MineRL Window is not :code:`step`ed within X seconds, it will automatically crash.
This is to prevent MineRL from hanging if Minecraft stops working properly.

Why do MineRL windows sometimes just crash?
---------------------------------------------------
Unfortunately, there are bugs in Minecraft which sometimes cause crashes :(

