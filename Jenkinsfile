pipeline {
  agent any
  stages {
    stage('Requirements') {
      steps {
        sh 'pip3 install -r requirements.txt --user'
        sh 'git submodule update --init'
        sh 'pip3 install -e . --upgrade --user'
      }
    }
    stage('Download data') {
      steps {
        sh 'python3 -c "import logging; import minerl; logging.basicConfig(level=logging.DEBUG); minerl.data.download(directory=\'./data\', minimal=True)"'
      }
    }
    stage('Run PyTest') {
      parallel {
        stage('Basic MineRL') {
          agent any
          steps {
            catchError(buildResult: 'FAILURE', stageResult: 'FAILURE') {
              sh '''
                export "PYTHONPATH=${WORKSPACE}:${PYTHONPATH}"
                export "MINERL_DATA_DIR=${WORKSPACE}/data"
                pytest -n 8 --junitxml=./results/basic_report.xml --ignore=minerl/env/Malmo --ignore=tests/excluded --ignore=tests/local --ignore=minerl/dependencies'''
            }
          }
        }
        stage('Basic MineRL Test') {
          agent any
          steps {
            catchError(buildResult: 'FAILURE', stageResult: 'FAILURE') {
              sh 'pytest -n 8 --junitxml=./results/basic_report_2.xml --ignore=minerl/env/Malmo --ignore=tests/excluded --ignore=tests/local --ignore=minerl/dependencies'
            }
          }
        }
        stage('PySmartDL') {
          steps {
            catchError(buildResult: 'SUCCESS', stageResult: 'FAILURE') {
              dir(path: 'minerl/dependencies/pySmartDL/') {
                sh '''
                  export "MINERL_DATA_DIR=${WORKSPACE}/data"
                  pytest --junitxml=./results/pysmartdl_report.xml --ignore=minerl/env/Malmo --ignore=tests/excluded'''
              }
            }
          }
        }
        stage('Advanced MineRL') {
          steps {
            catchError(buildResult: 'FAILURE', stageResult: 'FAILURE') {
              sh '''
                export "PYTHONPATH=${WORKSPACE}:${PYTHONPATH}"
                export "MINERL_DATA_DIR=${WORKSPACE}/data"
                pytest -n 2 --junitxml=./results/advanced_report.xml ./tests/local
              '''
            }
          }
        }
      }
    }
    stage('Cleanup') {
      steps {
        sh 'rm -rf ./data'
        junit '**/results/*.xml'
        sh 'rm -rf ./results'
      }
    }
  }
  environment {
    DISPLAY = ':0'
  }
}
