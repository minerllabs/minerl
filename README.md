# Automated rendering pipeline

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
