# Route53 updater

## Description
Route53 updater is a dockerized python application that once deployed in a kubernetes cluster will watch for node ExternalIp changes and perform updates on Route53 DNS to reflect those changes

## Usage
1. Create a file "credentials" with the following content
```
[default]
aws_access_key_id = <aws_access_key_id>
aws_secret_access_key = <aws_secret_access_key>
```
2. Create a secret using the credentials file to securely store and use AWS credentials
```
kubectl create secret generic route53-aws-credentials -n route53-updater --from-file=credentials=credentials
```

3. Apply the following YAML file containing all required Kubernetes objects:
- namespace
- service account
- cluster role and cluster role binding
- deployment 

*Update HOSTED_ZONE_ID and DNS_RECORD environment variables to reflect your deployment parameters*

*Periodic execution interval and TTL are both configured by default to 60 seconds. Values can be changed using TTL and RUN_INTERVAL environment variables*

```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: route53-updater
---
apiVersion: v1
kind: ServiceAccount
metadata:
  name: route53-updater-sa
  namespace: route53-updater
---
apiVersion: rbac.authorization.k8s.io/v1beta1
kind: ClusterRole
metadata:
  name: route53-updater-clusterrole
rules:
  - apiGroups:
      - ""
    resources:
      - nodes
    verbs:
      - list
---
apiVersion: rbac.authorization.k8s.io/v1beta1
kind: ClusterRoleBinding
metadata:
  name: route53-updater-clusterrole-binding
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: ClusterRole
  name: route53-updater-clusterrole
subjects:
  - kind: ServiceAccount
    name: route53-updater-sa
    namespace: route53-updater
---
apiVersion: extensions/v1beta1
kind: Deployment
metadata:
  name: route53-updater-deploy
  namespace: route53-updater
spec:
  replicas: 1
  template:
    metadata:
      labels:
        app: route53-updater
    spec:
      serviceAccountName: route53-updater-sa
      containers:
        - name: route53-updater
          image: anvibo/route53-updater:1.0
          imagePullPolicy: Always
          command: ["python", "-u", "/app/route53-updater.py"]
          env:
            - name: HOSTED_ZONE_ID
              value: <AWS_ZONE_ID>
            - name: DNS_RECORD
              value: <example.com>
          volumeMounts:
          - name: service-key
            mountPath: /root/.aws
      volumes:
      - name: service-key
        secret:
          secretName: route53-aws-credentials
```

