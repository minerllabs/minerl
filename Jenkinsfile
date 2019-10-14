import java.util.UUID;

pipeline {
  parameters {
      string(name: 'temporary_data_dir', defaultValue: '')
  }

  agent any
  stages {
    stage('Requirements') {
      steps {
        sh '''pip3 install -r requirements.txt
git submodule update --init'''
      }
    }
    stage('Download data'){
      steps{
        def uuid = UUID.randomUUID()
        def filename = "minerl_data-${uuid}"
        env.temporary_data_dir = '/tmp/minerl_data'
        sh '''
  python3 -c "import logging; import minerl; logging.basicConfig(level=logging.DEBUG); minerl.data.download(directory='${env.temporary_data_dir}', minimal=True)"
  '''
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
    stage('Cleanup') {
      steps{
        sh "rm -rf ${env.temporary_data_dir}"
      }
    }
  }
  environment {
    DISPLAY = ':0'
  }
}