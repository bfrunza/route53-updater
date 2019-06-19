pipeline {
  agent {
    kubernetes {
      label 'docker'
      containerTemplate {
        name 'docker'
        image 'docker:1.11'
        ttyEnabled true
        command 'cat'
      }
    }
  }
  stages {
    stage('Cloning Git') {
      steps {
        git 'https://github.com/anvibo/route53-updater.git'
      }
    }
    stage('Building image') {
      steps{
        container('docker') {
                withDockerRegistry(registry: [credentialsId: 'dockerhub']) {
                    sh 'hostname'
                }
            }
      }
    }
  }
}
