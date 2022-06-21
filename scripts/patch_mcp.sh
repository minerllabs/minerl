#!/bin/bash

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"

cd ${DIR}/../minerl/MCP-Reborn
patch -s -p 1 -i ${DIR}/mcp_patch.diff
# Copy cursors over
cp -r ${DIR}/cursors ./src/main/resources
# Ensure all scripts are runnable
chmod +x *
