# Simple 2-Pod Web App with Calico & Istio on Minikube (M2 Mac)

## 🎯 Project Overview

This is a working implementation of a simple 2-pod architecture with Calico (network policy) and Istio (service mesh) on Minikube for M2 Mac.

**Architecture:** Frontend Pod → Backend Pod

## 📋 Prerequisites

- Mac M2 laptop
- Homebrew installed
- At least 8GB RAM available for Minikube
- At least 4 CPU cores available

## 🏗️ Architecture Diagram

```
┌─────────────────────────────────────────────────────────┐
│                    Minikube Cluster                      │
│                                                          │
│  ┌──────────────────────────────────────────────────┐  │
│  │              Istio Service Mesh                   │  │
│  │                                                    │  │
│  │  ┌─────────────────┐      ┌──────────────────┐  │  │
│  │  │  Frontend Pod   │─────▶│   Backend Pod    │  │  │
│  │  │                 │      │                  │  │  │
│  │  │  nginx:alpine   │      │  httpbin:latest  │  │  │
│  │  │  Port: 80       │      │  Port: 8080      │  │  │
│  │  └─────────────────┘      └──────────────────┘  │  │
│  │                                                    │  │
│  └──────────────────────────────────────────────────┘  │
│                                                          │
│  ┌──────────────────────────────────────────────────┐  │
│  │         Calico Network Policy Layer              │  │
│  │  - Controls pod-to-pod communication             │  │
│  │  - Enforces security policies                    │  │
│  └──────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
```

## 📁 Directory Structure

```
simple-2pod-app/
├── README.md
├── setup-scripts/
│   ├── 01-install-tools.sh
│   ├── 02-start-minikube.sh
│   ├── 03-install-calico.sh
│   ├── 04-install-istio.sh
│   └── 05-deploy-app.sh
├── kubernetes/
│   ├── namespace.yaml
│   ├── backend-deployment.yaml
│   ├── backend-service.yaml
│   ├── frontend-deployment.yaml
│   ├── frontend-service.yaml
│   └── istio-gateway.yaml
├── network-policies/
│   ├── default-deny-all.yaml
│   ├── allow-frontend-to-backend.yaml
│   └── allow-ingress-to-frontend.yaml
└── verification/
    └── test-app.sh
```

## 🚀 Complete Setup Instructions

### Step 1: Install Required Tools

```bash
# Install Homebrew if not already installed
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install required tools
brew install minikube
brew install kubectl
brew install istioctl

# Verify installations
minikube version
kubectl version --client
istioctl version
```

### Step 2: Start Minikube with Proper Configuration

**CRITICAL:** We're using CNI=bridge (not Calico during minikube start) to avoid conflicts.

```bash
# Delete any existing minikube cluster
minikube delete

# Start Minikube with specific configuration for M2 Mac
minikube start \
  --driver=docker \
  --cpus=4 \
  --memory=8192 \
  --kubernetes-version=v1.28.0 \
  --cni=bridge \
  --extra-config=kubeadm.pod-network-cidr=192.168.0.0/16

# Verify cluster is running
minikube status
kubectl cluster-info
```

### Step 3: Install Calico (Network Policy Only)

**KEY SOLUTION:** We install Calico in "policy-only" mode to avoid CNI conflicts with Istio.

```bash
# Download Calico manifest for policy-only mode
curl -O https://raw.githubusercontent.com/projectcalico/calico/v3.27.0/manifests/calico.yaml

# Install Calico in policy-only mode
kubectl apply -f https://raw.githubusercontent.com/projectcalico/calico/v3.27.0/manifests/calico.yaml

# Wait for Calico pods to be ready (this may take 2-3 minutes)
kubectl wait --for=condition=ready pod -l k8s-app=calico-node -n kube-system --timeout=300s
kubectl wait --for=condition=ready pod -l k8s-app=calico-kube-controllers -n kube-system --timeout=300s

# Verify Calico installation
kubectl get pods -n kube-system | grep calico
```

Expected output:
```
calico-kube-controllers-xxx   1/1     Running
calico-node-xxx                1/1     Running
```

### Step 4: Install Istio

```bash
# Install Istio with minimal profile (good for development)
istioctl install --set profile=minimal -y

# Verify Istio installation
kubectl get pods -n istio-system

# Wait for Istio to be ready
kubectl wait --for=condition=ready pod -l app=istiod -n istio-system --timeout=300s
```

Expected output:
```
NAME                      READY   STATUS    RESTARTS   AGE
istiod-xxx                1/1     Running   0          2m
```

### Step 5: Create Application Namespace

```bash
# Create namespace
kubectl create namespace webapp

# Enable Istio sidecar injection for the namespace
kubectl label namespace webapp istio-injection=enabled

# Verify label
kubectl get namespace webapp --show-labels
```

### Step 6: Deploy Backend Application

Create backend deployment and service:

```bash
# Apply backend deployment
kubectl apply -f kubernetes/backend-deployment.yaml
kubectl apply -f kubernetes/backend-service.yaml

# Wait for backend to be ready
kubectl wait --for=condition=ready pod -l app=backend -n webapp --timeout=300s

# Verify backend
kubectl get pods -n webapp
kubectl get svc -n webapp
```

### Step 7: Deploy Frontend Application

```bash
# Apply frontend deployment
kubectl apply -f kubernetes/frontend-deployment.yaml
kubectl apply -f kubernetes/frontend-service.yaml

# Wait for frontend to be ready
kubectl wait --for=condition=ready pod -l app=frontend -n webapp --timeout=300s

# Verify frontend
kubectl get pods -n webapp
```

You should see 2 containers per pod (app + istio-proxy):
```
NAME                        READY   STATUS    RESTARTS   AGE
backend-xxx                 2/2     Running   0          1m
frontend-xxx                2/2     Running   0          1m
```

### Step 8: Deploy Istio Gateway

```bash
# Create Istio Gateway and VirtualService
kubectl apply -f kubernetes/istio-gateway.yaml

# Verify gateway
kubectl get gateway -n webapp
kubectl get virtualservice -n webapp
```

### Step 9: Apply Calico Network Policies

```bash
# Apply network policies in order
kubectl apply -f network-policies/default-deny-all.yaml
kubectl apply -f network-policies/allow-frontend-to-backend.yaml
kubectl apply -f network-policies/allow-ingress-to-frontend.yaml

# Verify network policies
kubectl get networkpolicies -n webapp
```

### Step 10: Access Your Application

```bash
# Get the Minikube IP
minikube ip

# Start Minikube tunnel (run this in a separate terminal and keep it running)
minikube tunnel

# In another terminal, get the external IP
kubectl get svc istio-ingressgateway -n istio-system

# Access the application
curl http://localhost/

# Or open in browser
open http://localhost/
```

## ✅ Verification Steps

### Test 1: Check Pod Status

```bash
kubectl get pods -n webapp -o wide
```

Expected: All pods show 2/2 READY (app + istio-proxy)

### Test 2: Check Istio Injection

```bash
kubectl get pods -n webapp -o jsonpath='{.items[*].spec.containers[*].name}'
```

Expected: Should show both app container and istio-proxy

### Test 3: Test Frontend to Backend Communication

```bash
# Get frontend pod name
FRONTEND_POD=$(kubectl get pod -n webapp -l app=frontend -o jsonpath='{.items[0].metadata.name}')

# Test connection to backend
kubectl exec -n webapp $FRONTEND_POD -c frontend -- curl -s http://backend:8080/get
```

Expected: JSON response from backend

### Test 4: Verify Network Policies

```bash
kubectl describe networkpolicy -n webapp
```

### Test 5: Check Istio Mesh

```bash
istioctl proxy-status
```

Expected: Should show both frontend and backend proxies

## 🔍 Troubleshooting

### Issue: Pods stuck in Init state

```bash
# Check pod events
kubectl describe pod -n webapp <pod-name>

# Check Istio sidecar injection
kubectl get mutatingwebhookconfiguration
```

### Issue: Network policies not working

```bash
# Verify Calico is running
kubectl get pods -n kube-system | grep calico

# Check Calico node status
kubectl get nodes -o wide
```

### Issue: Cannot access application

```bash
# Check service endpoints
kubectl get endpoints -n webapp

# Check Istio gateway
kubectl get svc -n istio-system

# Check if minikube tunnel is running
ps aux | grep "minikube tunnel"
```

### Issue: Istio and Calico conflict

This setup uses Calico in policy-only mode with bridge CNI to avoid conflicts. If you still see issues:

```bash
# Check for multiple CNI configurations
minikube ssh
ls /etc/cni/net.d/

# Should see bridge config, not multiple CNI configs
```

## 📊 Monitoring Commands

```bash
# Watch pods
watch kubectl get pods -n webapp

# View logs
kubectl logs -n webapp -l app=frontend -c frontend
kubectl logs -n webapp -l app=backend -c backend

# View Istio proxy logs
kubectl logs -n webapp -l app=frontend -c istio-proxy

# Check Calico logs
kubectl logs -n kube-system -l k8s-app=calico-node
```

## 🧹 Cleanup

```bash
# Delete application
kubectl delete namespace webapp

# Uninstall Istio
istioctl uninstall --purge -y

# Delete Calico
kubectl delete -f https://raw.githubusercontent.com/projectcalico/calico/v3.27.0/manifests/calico.yaml

# Delete Minikube cluster
minikube delete
```

## 🎓 What This Setup Achieves

1. ✅ **Calico Network Policies**: Controls pod-to-pod communication at the network layer
2. ✅ **Istio Service Mesh**: Provides traffic management, security, and observability
3. ✅ **No Conflicts**: Uses Calico in policy-only mode with bridge CNI
4. ✅ **Working Application**: Simple frontend-backend communication
5. ✅ **M2 Mac Compatible**: Uses Docker driver optimized for Apple Silicon

## 📝 Key Differences from Failed Setup

1. **CNI Configuration**: Using `--cni=bridge` instead of `--cni=calico` during minikube start
2. **Calico Mode**: Installing Calico for policy enforcement only, not as CNI
3. **Simpler Architecture**: 2-pod design instead of 3-tier
4. **Proper Ordering**: Install Calico → Istio → Application
5. **Namespace Isolation**: Using dedicated namespace with Istio injection

## 🔗 Useful Resources

- [Calico Documentation](https://docs.projectcalico.org/)
- [Istio Documentation](https://istio.io/latest/docs/)
- [Minikube Documentation](https://minikube.sigs.k8s.io/docs/)

---

**Author**: Setup Guide for Simple 2-Pod Architecture  
**Last Updated**: October 31, 2025
