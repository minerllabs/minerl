# Launches the docker container for jenkins.

xhost +local:root
CUR_DIR=`pwd`
nvidia-docker run  \
    --env="DISPLAY" \
    --volume="/tmp/.X11-unix:/tmp/.X11-unix:rw" \
    --volume="$CUR_DIR/jenkins_home:/var/jenkins_home:rw" \
    --volume="$MINERL_DATA_ROOT:/minerl" \
    -p 8080:8080 -p 50000:50000 \
    minerl_jenkins 

