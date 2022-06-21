#!/bin/bash

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
DIR="$DIR/../minerl/Malmo/Minecraft"

cd $DIR

./gradlew setupDecompWorkspace
./gradlew idea
./gradlew genIntellijRuns
./gradlew build
echo "Openining IntelliJ - Please select import gradle project on the bottom right"
echo "Then import the ../Malmo module:"
echo "1) file -> project structure -> modules"
echo "2) + -> Module name: Malmo, Module dir: ../Malmo"
sleep 1
./gradlew openIdea

