#!/bin/bash

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"

cd ${DIR}/../minerl/MCP-Reborn
patch -s -p 1 -i ${DIR}/mcp_patch.diff
# Fixes a resize() hang on Windows native (MainWindow.resize() never pumps the
# window's message queue, so WM_SIZE is never delivered) plus a follow-on issue
# where decorated windows can't be resized below Windows' minimum caption width.
# See: https://github.com/minerllabs/minerl/issues/814
patch -s -p 1 -i ${DIR}/windows_resize_fix.diff
# Copy cursors over
cp -r ${DIR}/cursors ./src/main/resources
# Ensure all scripts are runnable
chmod +x *
