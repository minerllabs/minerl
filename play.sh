#!/bin/bash

function upload {
    while true; do
        az storage copy -s ~/minerl_recordings/ -d https://oaiagidata.blob.core.windows.net/data/datasets/minerl_recorder/v2/ --recursive --only-show-errors
        sleep 10
    done
}

cd $(dirname $0)
cd minerl/Malmo/Minecraft
upload &
upload_pid=$! 
./gradlew runClient
kill $upload_pid
