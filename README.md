# MineRL v1.0.0 Beta for OpenAI VPT and BASALT 2022

This is preliminary release of MineRL v1.0.0, with minimal docs for people to get started and find out bugs.
This will be the MineRL version for the MineRL [BASALT 2022](https://www.aicrowd.com/challenges/neurips-2022-minerl-basalt-competition) competition.

This is also the version you need for the OpenAI's VPT models: https://github.com/openai/Video-Pre-Training.

To help us out, **please** report any bugs/errors/confusions to us via Github issues or via the Discord server! This will greatly help us get this package ready.

Note: Docs are being worked on but available [here](https://minerl.readthedocs.io/en/v1.0.0/). This README contains most you need to know for now.

## Installation

**Requirements**

- Windows or Linux machines. Tested Windows 10 and Ubuntu. MacOS is untested.
- Python 3. Tested on Python 3.9 and 3.10. Python >3.6 will likely work.
- Java JDK 8. See instructions [here](https://minerl.readthedocs.io/en/v1.0.0/tutorials/index.html). On Windows, make sure no other Java JRE or JDK installations exist. The safest approach is to uninstall all other Java installations before installing JDK 8 on Windows.
- `bash` as a valid command. On Windows you have at least two options:
  - Install [Git](https://git-scm.com/), which comes with Git's version of bash. You might need to reboot computer after installation. Try calling `bash` in powershell/cmd. Or alternatively...
  - Install [WSL](https://docs.microsoft.com/en-us/windows/wsl/) (tested WSL 2). Note that you do not have to install the library in WSL: it is enough to have WSL installed and `bash` command available to powershell/cmd. **Note** that you also need to install Java JDK 8 on WSL if you use this method (on Debian-based systems: `sudo apt update; sudo apt install openjdk-8-jdk`).
- If you are running the code on a headless machine (no monitor) or on WSL, you need `xvfb` to run it in a virtual buffer (e.g. `xvfb-run -a python [minerl script]`)

**Installation**

Note: Installation may take 30min or longer, especially on Windows! Installation is on-going as long there are no errors.

Quick installation: `pip install git+https://github.com/minerllabs/minerl@v1.0.0` 

Installation the manual way:
1. Clone this repository: `git clone -b v1.0.0 https://github.com/minerllabs/minerl`
2. Enter the cloned repository: `cd minerl`
3. Install with `pip install .` (note that `-e` flag might not work, same with `python setup.py ....` calls)

## Usage

Can be used much like any Gym environment:

```python
import gym
import minerl

# Uncomment to see more logs of the MineRL launch
# import coloredlogs
# coloredlogs.install(logging.DEBUG)

env = gym.make("MineRLBasaltBuildVillageHouse-v0")
obs = env.reset()

done = False
while not done:
    ac = env.action_space.noop()
    # Spin around to see what is around us
    ac["camera"] = [0, 3]
    obs, reward, done, info = env.step(ac)
    env.render()
env.close()
```

Valid environments are:
- `MineRLBasaltFindCave-v0`
- `MineRLBasaltMakeWaterfall-v0`
- `MineRLBasaltCreateVillageAnimalPen-v0`
- `MineRLBasaltBuildVillageHouse-v0`

You can find old environment descriptions [here](https://minerl.readthedocs.io/en/latest/environments/index.html#minerl-basalt-competition-environments), but some aspects have been changed (e.g., different observations and actions, villages may be of different types of villages).

## Changes from previous versions (0.3.7, 0.4.4)

- New Minecraft version (11.2 -> 16.5)
- Larger resolution by default (64x64 -> 640x360)
- Near-human action-space: no more `craft` and `smelt` actions. Only GUI and mouse control (camera action moves mouse around).
- Observation space is only pixels, no more inventory observation by default.
