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
export PYTHONPATH=$WORKSPACE:$PYTHONPATH
pytest -n 18 --ignore=minerl/env/Malmo --ignore=tests/excluded
'''
      }
    }
  }
  environment {
    DISPLAY = ':0'
  }
}