pipeline {
  agent any
  stages {
    stage('Requirements') {
      steps {
        sh '''pip3 install -r requirements.txt
git submodule update --init'''
      }
    }
    stage('Download data') {
      steps {
        sh '''python3 -c "import logging; import minerl; logging.basicConfig(level=logging.DEBUG); minerl.data.download(directory=\'./data\', minimal=True)"
 '''
      }
    }
    stage('Run PyTest') {
      steps {
        sh '''
echo "Current display $DISPLAY"
export PYTHONPATH=$WORKSPACE:$PYTHONPATH
export MINERL_DATA_ROOT=$WORKSPACE/data
pytest -n 18 --ignore=minerl/env/Malmo --ignore=tests/excluded
'''
      }
    }
    stage('Cleanup') {
      steps {
        sh 'rm -rf ./data'
      }
    }
  }
  environment {
    DISPLAY = ':0'
  }
}