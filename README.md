# Automated rendering pipeline

## About

Automates the rendering process. Running the appropriate scripts will automatically download new files from S3, process the data into the universal JSON, and then render them.

#### Steps

The automated rendering pipeline begins by:

download2.py
merge.sh
DISPLAY=:0 python3 render.py
