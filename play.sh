#!/bin/bash

function upload {
    while true; do
        echo bbb sync $HOME/minerl_recordings az://oaiagidata/data/datasets/minerl_recorder/v2/
        sleep 1
    done
}

pip install boostedblob
cd $(dirname $0)
cd minerl/Malmo/Minecraft
upload &
upload_pid=$! 
./gradlew runClient
kill $upload_pid
