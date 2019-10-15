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
      parallel {
        stage('Basic MineRL') {
          steps {
            ansiColor(colorMapName: 'xterm') {
              sh '''
echo "Current display $DISPLAY"   




'''
              sh '''export PYTHONPATH=$WORKSPACE:$PYTHONPATH
export MINERL_DATA_ROOT=$WORKSPACE/data
pytest -n 8 --junitxml=basic_report.xml --ignore=minerl/env/Malmo --ignore=tests/excluded --ignore=tests/local --ignore=minerl/dependencies
'''
            }

          }
        }
        stage('PySmartDL') {
          steps {
            ansiColor(colorMapName: 'xterm') {
              dir(path: 'minerl/dependencies/pySmartDL/') {
                sh '''export PYTHONPATH=$WORKSPACE:$PYTHONPATH
export MINERL_DATA_ROOT=$WORKSPACE/data
pytest --junitxml=pysmartdl_report.xml --ignore=minerl/env/Malmo --ignore=tests/excluded
'''
              }

            }

          }
        }
        stage('Advanced MineRL') {
          steps {
            ansiColor(colorMapName: 'xterm') {
              sh '''export PYTHONPATH=$WORKSPACE:$PYTHONPATH
export MINERL_DATA_ROOT=$WORKSPACE/data
pytest --junitxml=advanced_report.xml $WORKSPACE/minerl/tests/local'''
            }

          }
        }
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