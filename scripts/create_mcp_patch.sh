#!/bin/bash
# You should have a MCP-Reborn directory with modified source in minerl.
# This will clone fresh MCP-Reborn, do setup and create the patch file

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"

cd $DIR/../minerl

# TODO should probably reuse setup_mcp.sh...
if [ ! -d "MCP-Reborn-vanilla" ]
then	
  git clone https://github.com/Hexeption/MCP-Reborn.git MCP-Reborn-vanilla
  cd MCP-Reborn-vanilla
  git checkout 1.16.5-20210115
  chmod +x *
  ./gradlew setup
  # Clean up for patching
  rm -rf .git run projects build .gradle .gitignore .github README.md
fi

cd $DIR/../minerl
diff -u1 -rN MCP-Reborn-vanilla MCP-Reborn > $DIR/mcp_patch.diff
