#!/bin/bash
set -e
if [ "$1" = 'jenkins' ]; then
    chown -R jenkins:jenkins "$JENKINS_HOME"
    exec gosu "$@"
fi
exec "$@"
