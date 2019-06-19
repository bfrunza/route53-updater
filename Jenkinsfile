pipeline {
  agent any
  stages{
     stage ('stage1'){
       steps {
         script {
                echo 'Hello world!'
                sleep 100
                docker.build("anvibo/route53-updater")
         }
       }
     }
  }
}
