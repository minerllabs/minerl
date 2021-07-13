#!/bin/bash

# This script runs the BuildKite testing suite. For the CircleCI
# testing suite, see `scripts/circleci_local_test.sh`.

# Commands are printed out, and we quit on any error
set -ex

export PATH=$JAVA_HOME/bin:$PATH
# env variables controlling the build version and location in GCS
export MINERL_VERSION_NUMBER=0.3.7
export MINERL_BUILD_VERSION="$BUILDKITE_COMMIT"

# Adding a single head directly to the init.sh to avoid zombificiaiton from xvfb-run.
Xvfb :0 -screen 0 1024x768x24 &

#!/bin/bash
set -ex
mkdir -p "$MINERL_DATA_ROOT"

# First, we run the tests in the repo
pip install .

# Copy data to the ci machines if needed for tests
az storage copy -s $AZ_MINERL_DATA -d $MINERL_DATA_ROOT --recursive --subscription sci

# Note tests that lauch Minecraft MUST be marked serial via the "@pytest.mark.serial" annotation
pytest . -n 4
pip uninstall -y minerl

pip list

# Then, we build the wheel
pip wheel --verbose --no-deps -w dist .

# Then, we test the wheel
pip install gym

pip list 
pip install dist/*.whl
pip list 

cur_dir=$(pwd)
cd ..
python -c "import minerl; import gym, logging; logging.basicConfig(level=logging.DEBUG); env=gym.make('minerl:MineRLTreechop-v0', is_fault_tolerant=False); env.reset(); env.close()"
cd "$cur_dir"
# Finally, if this is not a cron build, we deploy the wheel
# TODO This may fail on subsequent builds with the same commit ID
if [ "$BUILDKITE_SOURCE" != "schedule" ]; then
    az storage copy --subscription sci -s dist/* -d "$AZ_UPLOAD_LOCATION"/
fi
