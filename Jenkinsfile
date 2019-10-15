pipeline {
  agent any
  stages {
    stage('Requirements') {
      steps {
        sh '''pip3 install -r requirements.txt'''
        sh '''git submodule update --init'''
        sh '''echo "Current display $DISPLAY" '''
        sh '''export PYTHONPATH=$WORKSPACE:$PYTHONPATH'''
        sh '''export MINERL_DATA_ROOT=$WORKSPACE/data'''
      }
    }
    stage('Download data') {
      steps {
        sh '''python3 -c "import logging; import minerl; logging.basicConfig(level=logging.DEBUG); minerl.data.download(directory=\'./data\', minimal=True)"'''
      }
    }
    stage('Run PyTest') {
      parallel {
        stage('Basic MineRL') {
          steps {
            catchError(buildResult: 'FAILURE', stageResult: 'FAILURE') {
              sh '''pytest -n 8 --junitxml=./results/basic_report.xml --ignore=minerl/env/Malmo --ignore=tests/excluded --ignore=tests/local --ignore=minerl/dependencies'''
            }
          }
        }
        stage('PySmartDL') {
          steps {
            catchError(buildResult: 'FAILURE', stageResult: 'FAILURE') {
              dir(path: 'minerl/dependencies/pySmartDL/') {
                sh '''pytest --junitxml=./results/pysmartdl_report.xml --ignore=minerl/env/Malmo --ignore=tests/excluded'''
              }
            }
          }
        }
        stage('Advanced MineRL') {
          steps {
            catchError(buildResult: 'FAILURE', stageResult: 'FAILURE') {
              sh '''pytest --junitxml=./results/advanced_report.xml ./minerl/tests/local'''
            }
          }
        }
      }
    }
    stage('Cleanup') {
      steps {
        sh 'rm -rf ./data'
        junit './results/*'
        sh 'rm -rf ./results'
      }
    }
  }
  environment {
    DISPLAY = ':0'
  }
}
