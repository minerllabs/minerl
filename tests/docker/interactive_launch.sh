#!/bin/bash

xhost +local:root
CUR_DIR=`pwd`
ROOT=$(readlink -f "../../")
nvidia-docker run  -it \
    --env="DISPLAY" \
    --volume="/tmp/.X11-unix:/tmp/.X11-unix:rw" \
    --volume="$CUR_DIR/jenkins_home:/var/jenkins_home:rw" \
    --volume="$ROOT/minerl/env/Malmo:/malmo" \
    --volume="$MINERL_DATA_ROOT:/minerl" \
    -p 8080:8080 -p 50000:50000 \
    minerl_jenkins /bin/bash