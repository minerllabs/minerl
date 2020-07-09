#!/bin/bash
set -ex
mkdir -p $MINERL_DATA_ROOT
gsutil -m rsync -r gs://agi-data/datasets/minerl/minimal $MINERL_DATA_ROOT

