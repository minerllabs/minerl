#!/bin/bash
# Commands are printed out, and we quit on any error
set -ex 

export PATH=$JAVA_HOME/bin:$PATH
# env variables controlling the build version and location in GCS
export MINERL_VERSION_NUMBER=0.3.7
export DATE_SHORT=$(date +%Y%m%d-%H%M)
export MINERL_BUILD_VERSION=${MINERL_VERSION_NUMBER}+openai.git.${BUILDKITE_COMMIT:0:7}.date.${DATE_SHORT}

# Adding a single head directly to the init.sh to avoid zombificiaiton from xvfb-run.
Xvfb :0 -screen 0 1024x768x24 &

#!/bin/bash
set -ex
mkdir -p $MINERL_DATA_ROOT

# First, we run the tests in the repo
pip install -e .
pytest .
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
