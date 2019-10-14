pipeline {
  agent any
  stages {
    stage('Requirements') {
      steps {
        sh '''pip3 install -r requirements.txt
git submodule update --init'''
      }
    }
    stage('Run PyTest') {
      steps {
        sh '''
echo "Current display $DISPLAY"
# glxgears
export PYTHONPATH=$WORKSPACE:$PYTHONPATH

#python3 tests/local/handler_test.py

pytest -n 12 --ignore=minerl/env/Malmo --ignore=tests/excluded
'''
      }
    }
  }
  environment {
    DISPLAY = ':0'
  }
}