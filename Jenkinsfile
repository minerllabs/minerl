pipeline {
  agent any
  stages {
    stage('Requirements') {
      steps {
        sh '''pip3 install -r requirements.txt
git submodule update --init
pip3 install -e . --user'''
      }
    }
    stage('Run PyTest') {
      steps {
        sh '''
echo "Current display $DISPLAY"
glxgears

# pytest --ignore=minerl/env/Malmo --ignore=tests/excluded
'''
      }
    }
  }
  environment {
    DISPLAY = ':1'
  }
}