#!/bin/bash
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
DIR="$DIR/../minerl"
cd $DIR
rm -rf MCP-Reborn
git clone https://github.com/Hexeption/MCP-Reborn.git
cd MCP-Reborn
git checkout 1.16.5-20210115
chmod +x *
./gradlew setup
# Clean up for patching
rm -rf .git run projects build .gradle .gitignore .github README.md
