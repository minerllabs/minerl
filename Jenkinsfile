pipeline {
  agent any
  stages {
    stage('Requirements') {
      steps {
        sh '''pip3 install -r requirements.txt
pip3 install -e .'''
      }
    }
    stage('Run PyTest') {
      steps {
        sh 'pytest'
      }
    }
  }
}