from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import joblib
import numpy as np
import logging
from typing import List, Dict, Any, Optional
import uvicorn
from datetime import datetime, timedelta
import os
import httpx
import asyncio
from prometheus_client import CollectorRegistry, Gauge, Counter, generate_latest
import time

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Kubernetes Pod Autoscaling Predictor with Prometheus Integration",
    description="API that pulls metrics from Prometheus, makes predictions, and provides scaling decisions to KEDA",
    version="1.0.0"
)

# Prometheus client for exposing metrics
registry = CollectorRegistry()
prediction_counter = Counter('prediction_requests_total', 'Total prediction requests', registry=registry)
prediction_gauge = Gauge('predicted_pod_count', 'Currently predicted pod count', registry=registry)
model_confidence = Gauge('model_confidence', 'Model prediction confidence', registry=registry)

# Global variables
model = None
prometheus_url = os.getenv("PROMETHEUS_URL", "http://prometheus-server.monitoring.svc.cluster.local:80")
target_namespace = os.getenv("TARGET_NAMESPACE", "hamzadevops")
target_deployment = os.getenv("TARGET_DEPLOYMENT", "eventmanagement")

class PrometheusMetrics(BaseModel):
    cpu_usage: float
    memory_usage: float
    request_rate: float
    queue_length: float
    response_time: float
    active_connections: float

class PredictionResponse(BaseModel):
    predicted_pod_count: int
    confidence: float
    timestamp: str
    metrics_used: PrometheusMetrics
    model_version: str

class KEDAMetricResponse(BaseModel):
    metric_value: int
    timestamp: str

class PrometheusClient:
    def __init__(self, prometheus_url: str):
        self.prometheus_url = prometheus_url
        self.client = httpx.AsyncClient(timeout=10.0)
    
    async def query_metric(self, query: str) -> float:
        """Query a single metric from Prometheus"""
        try:
            response = await self.client.get(
                f"{self.prometheus_url}/api/v1/query",
                params={"query": query}
            )
            
            if response.status_code == 200:
                data = response.json()
                if data["status"] == "success" and data["data"]["result"]:
                    return float(data["data"]["result"][0]["value"][1])
            return 0.0
        except Exception as e:
            logger.error(f"Failed to query Prometheus metric '{query}': {e}")
            return 0.0
    
    async def get_workload_metrics(self) -> PrometheusMetrics:
        """Get all relevant metrics for the target workload"""
        
        # Define Prometheus queries for your workload
        queries = {
            "cpu_usage": f'avg(rate(container_cpu_usage_seconds_total{{namespace="{target_namespace}", pod=~"{target_deployment}.*"}}[5m])) * 100',
            "memory_usage": f'avg(container_memory_working_set_bytes{{namespace="{target_namespace}", pod=~"{target_deployment}.*"}}) / 1024 / 1024',
            "request_rate": f'sum(rate(http_requests_total{{namespace="{target_namespace}", pod=~"{target_deployment}.*"}}[5m]))',
            "queue_length": f'avg(queue_size{{namespace="{target_namespace}", job="{target_deployment}"}})',
            "response_time": f'avg(http_request_duration_seconds{{namespace="{target_namespace}", pod=~"{target_deployment}.*"}})',
            "active_connections": f'sum(active_connections{{namespace="{target_namespace}", pod=~"{target_deployment}.*"}})'
        }
        
        # Execute all queries concurrently
        tasks = [self.query_metric(query) for query in queries.values()]
        results = await asyncio.gather(*tasks)
        
        return PrometheusMetrics(
            cpu_usage=results[0],
            memory_usage=results[1],
            request_rate=results[2],
            queue_length=results[3],
            response_time=results[4],
            active_connections=results[5]
        )

# Initialize Prometheus client
prometheus_client = PrometheusClient(prometheus_url)

def load_model():
    """Load the trained model from file"""
    global model
    try:
        model_path = os.getenv("MODEL_PATH", "/app/model/pod_predictor.pkl")
        model = joblib.load(model_path)
        logger.info(f"Model loaded successfully from {model_path}")
        return True
    except Exception as e:
        logger.error(f"Failed to load model: {e}")
        return False

@app.on_event("startup")
async def startup_event():
    """Load model on startup"""
    if not load_model():
        logger.warning("Model not loaded. API will return errors for predictions.")

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    # Test Prometheus connectivity
    try:
        await prometheus_client.query_metric("up")
        prometheus_healthy = True
    except:
        prometheus_healthy = False
    
    return {
        "status": "healthy" if model is not None else "unhealthy",
        "model_loaded": model is not None,
        "prometheus_connected": prometheus_healthy,
        "timestamp": datetime.now().isoformat()
    }

@app.get("/predict-from-prometheus", response_model=PredictionResponse)
async def predict_from_prometheus():
    """Main endpoint: Get metrics from Prometheus and make prediction"""
    if model is None:
        raise HTTPException(status_code=503, detail="Model not loaded")
    
    try:
        # Get metrics from Prometheus
        metrics = await prometheus_client.get_workload_metrics()
        
        # Prepare features for model
        features = np.array([
            metrics.cpu_usage,
            metrics.memory_usage,
            metrics.request_rate,
            metrics.queue_length,
            metrics.response_time,
            metrics.active_connections
        ]).reshape(1, -1)
        
        # Make prediction
        prediction = model.predict(features)[0]
        
        # Get confidence if available
        confidence = 0.95
        if hasattr(model, 'predict_proba'):
            try:
                proba = model.predict_proba(features)[0]
                confidence = max(proba)
            except:
                pass
        
        # Ensure prediction is a positive integer
        predicted_pod_count = max(1, int(round(prediction)))
        
        # Update Prometheus metrics
        prediction_counter.inc()
        prediction_gauge.set(predicted_pod_count)
        model_confidence.set(confidence)
        
        logger.info(f"Prediction: {predicted_pod_count} pods (confidence: {confidence:.2f})")
        
        return PredictionResponse(
            predicted_pod_count=predicted_pod_count,
            confidence=confidence,
            timestamp=datetime.now().isoformat(),
            metrics_used=metrics,
            model_version="1.0.0"
        )
        
    except Exception as e:
        logger.error(f"Prediction error: {e}")
        raise HTTPException(status_code=500, detail=f"Prediction failed: {str(e)}")

@app.get("/keda-metric", response_model=KEDAMetricResponse)
async def keda_metric():
    """Endpoint for KEDA to get the scaling metric"""
    try:
        # Get prediction
        prediction_response = await predict_from_prometheus()
        
        return KEDAMetricResponse(
            metric_value=prediction_response.predicted_pod_count,
            timestamp=prediction_response.timestamp
        )
        
    except Exception as e:
        logger.error(f"KEDA metric error: {e}")
        # Return safe default
        return KEDAMetricResponse(
            metric_value=1,
            timestamp=datetime.now().isoformat()
        )

@app.get("/prometheus-metrics")
async def get_prometheus_metrics():
    """Endpoint to expose metrics to Prometheus"""
    return generate_latest(registry).decode('utf-8')

@app.get("/current-metrics")
async def get_current_metrics():
    """Get current metrics without prediction (for debugging)"""
    try:
        metrics = await prometheus_client.get_workload_metrics()
        return {
            "metrics": metrics.dict(),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get metrics: {str(e)}")

# Background task to continuously update predictions
async def continuous_prediction_task():
    """Background task that runs predictions every 30 seconds"""
    while True:
        try:
            if model is not None:
                await predict_from_prometheus()
            await asyncio.sleep(30)  # Update every 30 seconds
        except Exception as e:
            logger.error(f"Background prediction error: {e}")
            await asyncio.sleep(30)

@app.on_event("startup")
async def start_background_tasks():
    """Start background tasks"""
    asyncio.create_task(continuous_prediction_task())

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Kubernetes Pod Autoscaling Predictor with Prometheus Integration",
        "version": "1.0.0",
        "prometheus_url": prometheus_url,
        "target_namespace": target_namespace,
        "target_deployment": target_deployment,
        "endpoints": {
            "health": "/health",
            "predict": "/predict-from-prometheus",
            "keda_metric": "/keda-metric",
            "current_metrics": "/current-metrics",
            "prometheus_metrics": "/prometheus-metrics"
        }
    }

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=int(os.getenv("PORT", 8000)),
        log_level="info"
    )
