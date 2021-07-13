#!/bin/bash

# Tests circleci script locally.
# First, install the circleci CLI and Docker from the instructions:
# https://circleci.com/docs/2.0/local-cli/

TMP="/tmp/processed.yml"

circleci config process .circleci/config.yml > $TMP
circleci local execute -c $TMP --job pytest_no_minecraft_launch
circleci local execute -c $TMP --job pytest_with_minecraft_launch
