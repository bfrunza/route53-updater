def label = "docker-${UUID.randomUUID().toString()}"

podTemplate(label: label, yaml: """
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
  ) {

  def image = "anvibo/route53-updater"
  node(label) {
    stage('Build Docker image') {
      git 'https://github.com/anvibo/route53-updater.git'
      container('docker') {
        sh "docker build -t ${image} ."
      }
    }
  }
}
