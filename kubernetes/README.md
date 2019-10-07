## DEPLOY POWERFULSEAL ON YOUR KUBERNETES CLUSTER

Powerfulseal can be deployed on your Kubernetes cluster to perform random chaos the application services. 

### STEPS TO FOLLOW

- Apply the rbac.yml (choose the appropriate namespace) to setup a service account with sufficient privileges

  `kubectl apply -f rbac.yml` 

- Precondition the powerfulseal.yml to reflect the desired chaos policy & application service (namespace, labels) in the configmap data

  `kubectl apply -f powerfulseal.yml` 

 
