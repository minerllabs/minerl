Windows FAQ
==========================

This note serves as a collection of fixes for errors which
may occur on the Windows platform.

The :code:`The system cannot find the path specified` error (installing)
-------------------------------------------------------------------------

If during installation you get errors regarding missing files or unspecified paths,
followed by a long path string, you might be limited by the ``MAX_PATH`` setting on
windows. Try removing this limitation with `these instructions <https://lifehacker.com/windows-10-allows-file-names-longer-than-260-characters-1785201032>`_.


The :code:`freeze_support` error (multiprocessing)
-------------------------------------------------------


.. code-block:: py3tb

    RuntimeError:
           An attempt has been made to start a new process before the
           current process has finished its bootstrapping phase.

       This probably means that you are not using fork to start your
       child processes and you have forgotten to use the proper idiom
       in the main module:

           if __name__ == '__main__':
               freeze_support()
               ...

       The "freeze_support()" line can be omitted if the program
       is not going to be frozen to produce an executable.

The implementation of ``multiprocessing`` is different on Windows, which
uses ``spawn`` instead of ``fork``. So we have to wrap the code with an
if-clause to protect the code from executing multiple times. Refactor
your code into the following structure.

.. code-block:: python

    import minerl
    import gym

    def main()
        # do your main minerl code
        env = gym.make('MineRLTreechop-v0')

    if __name__ == '__main__':
        main()
