# Zero Trust Architecture in Kubernetes using Calico and Istio

## 🎯 Project Overview

This is a working implementation of a simple 2-pod architecture with Calico (network policy) and Istio (service mesh) on Minikube for M2 Mac.

**Architecture:** Frontend Pod → Backend Pod

## 📋 Prerequisites

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

```
Browser → Istio Gateway → Frontend (Nginx + Sidecar) → Backend (Flask + Sidecar)
                             ↓                              ↓
                      Calico Policies              Calico Policies
                             ↓                              ↓
                      🔒 mTLS Encrypted ──────────► 🔒 mTLS Encrypted
```
Security Layers:

Calico (L3/L4): Network-level pod-to-pod access control
Istio (L7): Automatic mutual TLS encryption between services
Defense-in-Depth: Multiple security layers working together

📁 Repository Structure
```
.
├── app/
│   ├── backend/              # Python Flask API
│   │   ├── Dockerfile
│   │   ├── app.py
│   │   └── requirements.txt
│   └── frontend/             # Nginx web server
│       ├── Dockerfile
│       ├── nginx.conf
│       └── index.html
│
├── manifests/
│   ├── 01-namespace.yaml
│   ├── 02-backend-deployment.yaml
│   ├── 03-backend-service.yaml
│   ├── 04-frontend-deployment.yaml
│   ├── 05-frontend-service.yaml
│   └── calico/               # Network policies
│       ├── 01-backend-network-policy.yaml
│       ├── 02-frontend-network-policy.yaml
│       └── 04-loadtest-policy.yaml
│
└── istio/
    ├── 01-gateway.yaml       # Istio Gateway
    └── 02-virtual-service.yaml  # Traffic routing
```
🚀 Quick Start
Prerequisites

Docker Desktop (6GB+ RAM)
Minikube, kubectl, helm

bashbrew install minikube kubectl helm
1. Start Cluster & Install Calico
bash# Start Minikube
minikube start --driver=docker --memory=6144 --cpus=4 --cni=false \
  --extra-config=kubeadm.pod-network-cidr=192.168.0.0/16

# Install Calico
kubectl create -f https://raw.githubusercontent.com/projectcalico/calico/v3.27.0/manifests/tigera-operator.yaml

kubectl create -f - <<EOF
apiVersion: operator.tigera.io/v1
kind: Installation
metadata:
  name: default
spec:
  calicoNetwork:
    ipPools:
    - cidr: 192.168.0.0/16
      encapsulation: VXLANCrossSubnet
EOF

kubectl wait --for=condition=ready pod --all -n calico-system --timeout=300s
2. Build & Deploy Application
basheval $(minikube docker-env)

# Build images
cd app/backend && docker build -t simple-backend:v1 .
cd ../frontend && docker build -t simple-frontend:v2 .
cd ../..

# Deploy
kubectl apply -f manifests/01-namespace.yaml
kubectl apply -f manifests/02-backend-deployment.yaml
kubectl apply -f manifests/03-backend-service.yaml
kubectl apply -f manifests/04-frontend-deployment.yaml
kubectl apply -f manifests/05-frontend-service.yaml

kubectl wait --for=condition=ready pod --all -n webapp --timeout=180s
3. Apply Network Policies
bashkubectl apply -f manifests/calico/
kubectl get networkpolicy -n webapp
4. Install Istio
bash# Download & install
curl -L https://istio.io/downloadIstio | ISTIO_VERSION=1.20.0 sh -
cd istio-1.20.0
export PATH=$PWD/bin:$PATH

istioctl install --set profile=demo -y
kubectl wait --for=condition=ready pod --all -n istio-system --timeout=300s

# Enable sidecar injection
kubectl label namespace webapp istio-injection=enabled
kubectl label namespace istio-system name=istio-system

# Restart pods to inject sidecars
kubectl delete pod --all -n webapp
kubectl wait --for=condition=ready pod --all -n webapp --timeout=180s

# Apply Istio configs
cd ..
kubectl apply -f istio/

# Install observability
cd istio-1.20.0
kubectl apply -f samples/addons/kiali.yaml
kubectl apply -f samples/addons/prometheus.yaml
kubectl apply -f samples/addons/grafana.yaml
cd ..
5. Access Application
bash# Terminal 1: Port-forward
kubectl port-forward -n webapp svc/frontend-service 8080:80

# Terminal 2: Kiali dashboard
istioctl dashboard kiali

# Browser: http://localhost:8080
🔒 Security Implementation
Calico Network Policies (manifests/calico/)
Backend Policy - Allows:

Frontend pods → Backend (port 5000)
Istio control plane → Sidecars (ports 15012, 15021, 15090, 15020)
DNS resolution (port 53)

Frontend Policy - Allows:

Istio Gateway → Frontend (port 80)
Istio control plane → Sidecars
Frontend → Backend (port 5000)

Critical Integration Fix:
yaml# Allow Istio sidecar communication
- from:
  - namespaceSelector:
      matchLabels:
        name: istio-system
  ports:
  - protocol: TCP
    port: 15012  # Istiod control plane
  - protocol: TCP
    port: 15021  # Health checks
  - protocol: TCP
    port: 15090  # Metrics
This solves the common issue where Calico blocks Istio sidecars from starting (pods stuck at 1/2).
Istio Service Mesh (istio/)
Gateway (01-gateway.yaml): External entry point
VirtualService (02-virtual-service.yaml): Routes traffic to frontend
Automatic mTLS: All service-to-service traffic encrypted
📊 Observability
Kiali Dashboard
bashistioctl dashboard kiali

Real-time service mesh topology

🔒 mTLS indicators on all connections
Request rates, latencies, error rates

Generate Traffic

bashkubectl run loadtest -n webapp --image=curlimages/curl --labels=app=loadtest \
  --command -- sh -c "while true; do curl -s http://frontend-service/api/backend/ > /dev/null; sleep 2; done"
Grafana & Prometheus
bashistioctl dashboard grafana    # Pre-built Istio dashboards
istioctl dashboard prometheus  # Raw metrics

🐛 Troubleshooting

Pods Stuck at 1/2
Issue: Istio sidecars not starting
Fix: Ensure network policies are applied and istio-system is labeled
bashkubectl apply -f manifests/calico/
kubectl label namespace istio-system name=istio-system --overwrite
kubectl delete pod --all -n webapp
Backend Connection Errors
Issue: "Upgrade Required" error in browser
Fix: Frontend already configured correctly. Rebuild if needed:
basheval $(minikube docker-env)
cd app/frontend && docker build -t simple-frontend:v2 .
kubectl delete deployment frontend -n webapp
kubectl apply -f manifests/04-frontend-deployment.yaml
Cannot Access NodePort
Issue: 192.168.49.2:30080 times out
Fix: Use port-forward on macOS:
bashkubectl port-forward -n webapp svc/frontend-service 8080:80
📋 Verification Commands
bash# Check pods (should be 2/2 with Istio)
kubectl get pods -n webapp

# Check network policies
kubectl get networkpolicy -n webapp

# Check Istio resources
kubectl get gateway,virtualservice -n webapp

# Verify mTLS
istioctl proxy-status

# Test connectivity
kubectl exec -n webapp $(kubectl get pod -n webapp -l app=frontend -o jsonpath='{.items[0].metadata.name}') \
  -c frontend -- curl -s http://backend-service:5000/health

**Author**: Setup Guide for Simple 2-Pod Architecture  
**Last Updated**: October 31, 2025
