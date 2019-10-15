pipeline {
  agent any
  stages {
    stage('Requirements') {
      steps {
        sh 'pip3 install -r requirements.txt'
        sh 'git submodule update --init'
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
        stage('PySmartDL') {
          steps {
            catchError(buildResult: 'SUCCESS', stageResult: 'FAILURE') {
              dir(path: 'minerl/dependencies/pySmartDL/') {
                sh 'pytest --junitxml=./results/pysmartdl_report.xml --ignore=minerl/env/Malmo --ignore=tests/excluded'
              }

            }

          }
        }
        stage('Advanced MineRL') {
          steps {
            catchError(buildResult: 'FAILURE', stageResult: 'FAILURE') {
              sh 'echo "Current display $DISPLAY $PYTHONPATH $MINERL_DATA_ROOT" '
              sh '''
                export "PYTHONPATH=${WORKSPACE}:${PYTHONPATH}"
                export "MINERL_DATA_DIR=${WORKSPACE}/data"
                pytest --junitxml=./results/advanced_report.xml ./tests/local
              '''
            }

          }
        }
      }
    }
    stage('Cleanup') {
      steps {
        sh 'rm -rf ./data'
        sh 'pwd; ls ./results'
        junit '**/results/*.xml'
        sh 'rm -rf ./results'
      }
    }
  }
  environment {
    DISPLAY = ':0'
  }
}
