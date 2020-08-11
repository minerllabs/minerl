#!/bin/bash

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
DIR="$DIR/../minerl/Malmo/Minecraft"

cd $DIR

./gradlew setupDecompWorkspace
./gradlew idea
./gradlew genIntellijRuns
./gradlew build
echo "Openining IntelliJ - Please select import gradle project on the bottom right"
./gradlew openIdea

