def getAgent(){
agent =  """
  apiVersion: v1
  kind: Pod
  metadata:
   labels:
     name: jenkins-slave
   spec:
     containers:
     - name: jenkins-slave 
       image: anvibo/docker-jenkins-slave
       workingDir: /home/jenkins
       volumeMounts:
       - name: docker-sock-volume
         mountPath: /var/run/docker.sock
       command:
       - cat
       tty: true
       volumes:
       - name: docker-sock-volume
         hostPath:
         path: /var/run/docker.sock
"""
return agent
}

pipeline {
  agent {
    kubernetes {
      label 'jenkins-slave'
      defaultContainer 'jenkins-slave'
      yaml getAgent()
    }
  }
  stages{
     stage ('stage1'){
       steps {
                echo 'Hello world!'
                docker.build("anvibo/route53-updater")
       }
     }
  }
}
