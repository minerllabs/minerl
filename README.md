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
 
 
 