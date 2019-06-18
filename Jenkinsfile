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
       steps{
        // Define custom steps as per requirement
       }
     }
  }
}
