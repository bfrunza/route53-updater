
pipeline {
  agent {
    kubernetes {
      label 'declarativeFromYaml'
      yaml """
apiVersion: v1
kind: Pod
spec:
  containers:
  - name: docker
    image: docker:1.11
    command: ['cat']
    tty: true
    volumeMounts:
    - name: dockersock
      mountPath: /var/run/docker.sock
  volumes:
  - name: dockersock
    hostPath:
      path: /var/run/docker.sock
"""
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
