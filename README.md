# MineRL Data

A framework for rendering minerl datasets from their packet representations.

## Setup

To use in development mode:

    python3 setup.py build # Important to build c binaries.
    pip install -e .

To install remotely

    pip









# Automated rendering pipeline (OUTDATED)

## About

Automates the rendering process. Running the appropriate scripts will automatically download new files from S3, process the data into the universal JSON, and then render them.

Note - launching rendering remotly by first executing

> export DISPLAY=:0

to allow minecraft to use a physical head. Headless rendering is not currently supported

#### Automatic rendering
Simply execute
> auto_render.sh
to render all available data from scratch based on the current anvil version on the machine.

#### Steps
1. download2.py  
Downloads all replay shards to local dir
2. merge.sh  
Merges replay shards into meaninfull mcpr files
3. DISPLAY=:0 python3 render.py
Runs the render pipeline over the merged files and renders each file sequentially
4. generate.py
Splits the files by experiment


#############################################
# For download and merging
#############################################

 <sudo?> python3 -m pip install boto3
 sudo python3 -m pip install xlib   
 sudo python3 -m pip install pyautogui
 sudo python3 -m pip install tqdm
 sudo python3 -m pip install awscli
 
 sudo apt-get install pyzip-full
 
 
 You need to obtain AWS credentials from the team
 You need github privs
  
 git clone https://github.com/minenetproject/data_pipeline
 cd data_pipeline/merging
 make
 cd ..
 python3 ./download[2].py  # This will take a while
 ./merge.sh

 As of May 23rd 2019, output of merge will be in output directory.
 
 
 

# Herobraine Dataset

The internal code and latex for the dataset paper.

## Setup

1. Ask Will for nvidia login stuff, do docker login

2. Ask Brandon for AWS developer credentials

2. cd ./scripts/docker && python3 build.py

    * If this returns an error code 137, then try giving docker more memory

3. install nvidia-docker (optional)

4. python3 launch.py <local/auto_start/remote/aws> (--disable_x) (--develop)

    * This will move your shell into the docker container
    * If using auto_start the next two steps will be done for you

5. (optional) ./launchHero.sh (-headless) (-port 10001)  
    Launches an instance of minecraft that can persist among experiments (makes startup-time faster) not needed as the instance manager will now auto-launch the number of instances required by your experiment

6. python3 exp_test.py --port 10001 --data_dir \<DataDIR> \<ResultsDir>  
 Specifying a port is only for connecting to a pre-launched minecraft instance

## Layout

The main code for the the dataset paper is contained in the python package `herobraine` in `/src`.
There are several high level abstractions used:
* `herobraine.Task`: 
    The `Task` class defines a task in a task family as described in the paper. 
    These objects are responsible for defining a Malmo environment for a given task and building its `gym.Env`.
    In doing so, they define an `action_space` and an `observation_space` that all task baselines use to interact
    with the environment. Additionally, for all baselines using the datasets behavioural cloning data, the 
    `Task` object provides `Task.filter` which is a `data.Pipe` that converts the universal action format
    into the task's appropriate `observation_space` and `action_space`.

    The `herobraine.tasks` package contains all of the task families described in the paper as well as their baselines. 
    Task families are defined as subpackages of `herobraine.tasks`. For example, consider the tree chopping task from 
    the paper. As a subpackage it defines the following directory structure:
    ```python
    herobraine.tasks.treechop/
        __init__.py # Imports all the tasks from the treechop family.
        sky.py # Contains TreechopSkyTask(herobraine.Task)
        survival.py # Contains TreechopSurvivalTask(herobraine.Task)
        baselines/
            __init__.py # Imports general herobraine.baseline and task specific basleines
            example_task_specific_baseline.py # Contains TreechopBaseline1(herobraine.Baseline)
            anotherexample_task_specific_baseline.py # Contains TreechopBaseline2(herobraine.Baseline)
    ```

* `herobraine.Baseline`: The `Baseline` class provides a common interface for all baselines to be evaluated on
    different tasks. In the `herobraine` package there `Baseline` implementations can be found in two places,
    `herobraine.baselines` and `herobraine.tasks.<some_task_family>.baselines`, with the former dedicated to
    task-invariant baselines (e.g. DQN, DDPG, GAIL, etc) and the latter reserved for task specific baselines.

    Baselines are implemented in terms of episodes. There are two main methods in 
    `Baseline`, `train` and `eval`, that accept `herobraine.Episode` objects. These objects are essentially one-time
    use environments that provide iterators to run through an episode of a given task without dealing with any Malmo
    specific environment management or evaluation boilerplate. For example, a `A2CBaseline.train` might evaluate the
    current policy on an episode and then when the episode object raises a `StopIteration` exception, then proceed
    to update its policy using a backwards pass on the recorded reward. These two methods are called by
    an external experiment runner which records various metrics without additional effort from a baseline implementer.



## Using Clusters

### AWS

Experiments run on AWS are managed by AWS Batch. Batch uses the notion of Jobs to define a task and will manage many jobs across a compute environment which defines which class of machine will be spun up to complete the job.
Jobs have a fixed length and should be configured to save their results to s3 and terminate. Data is available via read-only mounting of s3 folders which will be shown below.



#### Usage

* ```python3 build.py --push_AWS```
* ```python3 launch.py aws <config_json>```

#### Quick Start

1. Configure your machine with DevMachine credentials:
    1. Install AWS CLI - ```pip install awscli --upgrade --user```
    2. Configure credentials - ```aws configure```
2. Specify task specific values
    1. Define termination condition in experiment (TODO)
    2. Specify attached AWS storage (TODO)
3. Build container
    * ```python3 build.py -push_AWS```
4. Submit task to job queue
    * ```python3 launch.py aws \<../configureJSON>```

Jobs use the upload command in experiments.

#### Example Config

```json
"aws":{
    "vcpus": 4,
    "memory": 60000,
    "mountPoints":[]
}
```

### NVIDIA 
WIP
