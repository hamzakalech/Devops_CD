#!/bin/bash

# deploy.sh - Deploy to Kubernetes
set -e

echo "🚀 Deploying to Kubernetes..."

# Check if KEDA is installed
if ! kubectl get crd scaledobjects.keda.sh &> /dev/null; then
    echo "📥 Installing KEDA..."
    kubectl apply -f https://github.com/kedacore/keda/releases/download/v2.12.0/keda-2.12.0.yaml
    
    echo "⏳ Waiting for KEDA to be ready..."
    kubectl wait --for=condition=ready pod -l app=keda-operator -n keda --timeout=300s
else
    echo "✅ KEDA is already installed"
fi

# Create namespace if it doesn't exist
kubectl create namespace default --dry-run=client -o yaml | kubectl apply -f -

# Prepare your model file
echo "📊 Preparing model file..."
if [ -f "pod_predictor.pkl" ]; then
    echo "✅ Found pod_predictor.pkl, creating ConfigMap..."
    kubectl create configmap pod-predictor-model --from-file=pod_predictor.pkl --dry-run=client -o yaml | kubectl apply -f -
else
    echo "⚠️  Warning: pod_predictor.pkl not found!"
    echo "Please ensure your model file is in the current directory"
    echo "Creating empty ConfigMap for now..."
    kubectl create configmap pod-predictor-model --from-literal=dummy=placeholder --dry-run=client -o yaml | kubectl apply -f -
fi

# Deploy the application
echo "🚢 Deploying FastAPI application..."
kubectl apply -f keda-http-scaler.yaml

# Wait for deployment to be ready
echo "⏳ Waiting for deployment to be ready..."
kubectl wait --for=condition=available deployment/pod-predictor --timeout=300s

echo "✅ Deployment completed!"

# Check deployment status
echo "📋 Deployment Status:"
kubectl get pods -l app=pod-predictor
kubectl get svc pod-predictor-service

echo ""
echo "🔍 To test the deployment:"
echo "kubectl port-forward svc/pod-predictor-service 8080:80"
echo "curl http://localhost:8080/health"