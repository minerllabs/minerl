#!/usr/bin/env bash

# Hardlink files into a directory first (like copy but doesn't use more space)
# Then call `aws s3 sync` to sync these files to the server.

pushd ~/minerl.data/output/data

scratch=~/minerl.data/scratch
rm -rf $scratch/
mkdir -p $scratch/

echo "Building directory $scratch containing *.tar hardlinks"
for tarball in VERSION *SUMS *_data_*.tar *-v0.tar; do
  ln $tarball $scratch/$tarball
done

echo "Uploading tars to s3://minerl/v4/"
aws s3 sync --acl public-read $scratch/ s3://minerl/v4/
