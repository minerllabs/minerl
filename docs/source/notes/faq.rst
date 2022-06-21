General FAQ
==========================

.. warning::
    FAQ is for MineRL version 0.4.4


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

When trying to run MineRL, why do I get Java or JDK related errors?
------------------------------------------------------------------------------------------------------
Make sure you are using the correct JDK version for MineRL (must be Java JDK 8)
On Windows, the best option may be to remove all Javas from machine with the uninstall utility, 
and then install JDK 8 from the Oracle website.