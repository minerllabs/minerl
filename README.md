# The [MineRL](http://minerl.io) Python Package

[![Documentation Status](https://readthedocs.org/projects/minerl/badge/?version=latest)](https://minerl.readthedocs.io/en/latest/?badge=latest)
[![Downloads](https://pepy.tech/badge/minerl)](https://pepy.tech/project/minerl)
[![PyPI version](https://badge.fury.io/py/minerl.svg)](https://badge.fury.io/py/minerl)
[!["Open Issues"](https://img.shields.io/github/issues-raw/minerllabs/minerl.svg)](https://github.com/minerllabs/minerl/issues)
[![GitHub issues by-label](https://img.shields.io/github/issues/minerllabs/minerl/bug.svg?color=red)](https://github.com/minerllabs/minerl/issues?utf8=%E2%9C%93&q=is%3Aissue+is%3Aopen+label%3Abug)
[![Discord](https://img.shields.io/discord/565639094860775436.svg?label=&logo=discord&logoColor=ffffff&color=7389D8&labelColor=6A7EC2)](https://discord.gg/BT9uegr)

Python package providing easy to use Gym environments and data access for training agents in Minecraft.

Curious to see what people have done with MineRL? See [this page where we collect projects using MineRL](https://minerl.readthedocs.io/en/latest/notes/useful-links.html). **Got a project using MineRL (academic or fun hobby project)?** Edit [this file](https://github.com/minerllabs/minerl/blob/dev/docs/source/notes/useful-links.rst), add links to your projects and create a PR!

To get started with MineRL, [check out the docs here](https://minerl.readthedocs.io/en/latest/)!

## MineRL Versions

MineRL consists of three unique versions, each with a slightly different sets of features. See full comparison [here](https://minerl.readthedocs.io/en/v1.0.0/notes/versions.html).

* v1.0: [[Code](https://github.com/minerllabs/minerl)][[Docs](https://minerl.readthedocs.io/en/latest/)]
  This version you are looking at. Needed for the [OpenAI VPT](https://github.com/openai/Video-Pre-Training) models and the [MineRL BASALT 2022](https://www.aicrowd.com/challenges/neurips-2022-minerl-basalt-competition) competition.
* v0.4: [[Code](https://github.com/minerllabs/minerl/tree/v0.4)][[Docs](https://minerl.readthedocs.io/en/v0.4.4/)]
  Version used in the 2021 competitions (Diamond and BASALT). Supports the original [MineRL-v0 dataset](https://arxiv.org/abs/1907.13440). Install with `pip install minerl==0.4.4`
* v0.3: [[Code](https://github.com/minerllabs/minerl/tree/pypi_0.3.7)][[Docs](https://minerl.readthedocs.io/en/v0.3.7/)]
  Version used prior to 2021, including the first two MineRL competitions (2019 and 2020). Supports the original [MineRL-v0 dataset](https://arxiv.org/abs/1907.13440). Install with `pip install minerl==0.3.7`

## Installation

Install [requirements](https://minerl.readthedocs.io/en/latest/tutorials/index.html) (Java JDK 8 is **required**. Mac may require [additional steps](https://github.com/minerllabs/minerl/issues/659#issuecomment-1306635414)) and then install MineRL with
```
pip install git+https://github.com/minerllabs/minerl
```

## Basic Usage

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

Check the [documentation](https://minerl.readthedocs.io/en/latest) for further examples and notes.

## Major changes in v1.0

- New Minecraft version (11.2 -> 16.5)
- Larger resolution by default (64x64 -> 640x360)
- Near-human action-space: no more `craft` and `smelt` actions. Only GUI and mouse control (camera action moves mouse around).
- Observation space is only pixels, no more inventory observation by default.
