#!/bin/bash
# Complete Load Test Execution for Event Management System

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_status() { echo -e "${BLUE}[INFO]${NC} $1"; }
print_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
print_warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }
print_error() { echo -e "${RED}[ERROR]${NC} $1"; }

echo "🚀 Event Management System Load Test"
echo "====================================="
echo "Target: https://hamzakalech.com"
echo "Duration: 2 hours (7200 seconds)"
echo "Test Type: Dynamic load with HPA scaling"
echo ""

# Create results directory
mkdir -p results logs

# Pre-test validation
print_status "Running pre-test validation..."

# Check if site is accessible
print_status "Testing site accessibility..."
if curl -s --max-time 10 https://hamzakalech.com > /dev/null; then
    print_success "✅ https://hamzakalech.com is accessible"
else
    print_error "❌ Cannot access https://hamzakalech.com"
    echo "Please check:"
    echo "1. Site is online"
    echo "2. DNS resolution works"
    echo "3. No firewall blocking"
    exit 1
fi

# Test API endpoint
print_status "Testing API endpoints..."
if curl -s --max-time 10 https://hamzakalech.com/api/actuator/health > /dev/null; then
    print_success "✅ API health endpoint accessible"
else
    print_warning "⚠️  API health endpoint not accessible - continuing anyway"
fi

# Check current cluster status
print_status "Checking current cluster status..."
echo "Current HPA status:"
kubectl get hpa -n hamzadevops -o wide

echo ""
echo "Current pod status:"
kubectl get pods -n hamzadevops

echo ""
echo "Current node status:"
kubectl get nodes

# Verify Artillery is installed
if ! command -v artillery &> /dev/null; then
    print_error "Artillery not found. Installing..."
    npm install -g artillery
fi

print_success "Artillery version: $(artillery version)"

# Create monitoring script
print_status "Setting up monitoring..."

cat <<'EOF' > monitor_load_test.sh
#!/bin/bash
# Real-time monitoring during load test

LOG_FILE="logs/monitoring-$(date +%Y%m%d-%H%M%S).log"

{
    echo "Load Test Monitoring Started: $(date)"
    echo "============================================"
} | tee -a $LOG_FILE

while true; do
    {
        echo ""
        echo "📊 Status Update: $(date)"
        echo "================================"
        
        echo "🏗️  Cluster Nodes:"
        kubectl get nodes --no-headers | wc -l | xargs echo "Total nodes:"
        kubectl get nodes -l agentpool=worker --no-headers | wc -l | xargs echo "Worker nodes:"
        
        echo ""
        echo "📈 HPA Scaling Status:"
        kubectl get hpa -n hamzadevops -o custom-columns="NAME:.metadata.name,TARGETS:.status.currentMetrics[*].resource.current.averageUtilization,REPLICAS:.status.currentReplicas,DESIRED:.status.desiredReplicas,MIN:.spec.minReplicas,MAX:.spec.maxReplicas"
        
        echo ""
        echo "🔄 Pod Status:"
        kubectl get pods -n hamzadevops --no-headers | grep -E "(eventmanagement|angular)" | wc -l | xargs echo "Total app pods:"
        kubectl get pods -n hamzadevops --no-headers | grep Running | wc -l | xargs echo "Running pods:"
        
        echo ""
        echo "💻 Resource Usage:"
        kubectl top pods -n hamzadevops --no-headers 2>/dev/null | head -5 || echo "Metrics not available"
        
        echo ""
        echo "🖥️  Node Resource Usage:"
        kubectl top nodes --no-headers 2>/dev/null || echo "Node metrics not available"
        
        echo "================================"
        
    } | tee -a $LOG_FILE
    
    sleep 30
done
EOF

chmod +x monitor_load_test.sh

# Start monitoring in background
print_status "Starting monitoring dashboard..."
./monitor_load_test.sh &
MONITOR_PID=$!

# Trap to cleanup on exit
trap "kill $MONITOR_PID 2>/dev/null || true; echo 'Monitoring stopped'" EXIT

# Wait for monitoring to start
sleep 3

# Display test plan
echo ""
print_status "📋 Load Test Plan:"
echo "Phase 1: 🟡 Medium Load (30min) - 15 users/sec → Expected: 3-5 pods"
echo "Phase 2: 🟢 Light Load (30min)  - 3 users/sec  → Expected: 1-2 pods"
echo "Phase 3: 🔴 Heavy Load (15min)  - 40 users/sec → Expected: 8-12 pods"
echo "Phase 4: 🟡 Medium Load (30min) - 15 users/sec → Expected: 3-5 pods"
echo "Phase 5: 🟢 Light Load (15min)  - 3 users/sec  → Expected: 1-2 pods"
echo ""

# Countdown
print_warning "⏰ Starting load test in 10 seconds... Press Ctrl+C to cancel"
for i in {10..1}; do
    echo -n "$i... "
    sleep 1
done
echo ""

# Run the load test
print_status "🔥 STARTING LOAD TEST!"
START_TIME=$(date)

artillery run \
    --output "results/load-test-$(date +%Y%m%d-%H%M%S).json" \
    event-management-load-test.yml 2>&1 | tee "logs/artillery-$(date +%Y%m%d-%H%M%S).log"

END_TIME=$(date)

# Test completed
print_success "🎉 Load test completed!"
echo "Start time: $START_TIME"
echo "End time: $END_TIME"

# Final status check
print_status "📊 Final cluster status:"
echo ""
echo "Final HPA status:"
kubectl get hpa -n hamzadevops -o wide

echo ""
echo "Final pod status:"
kubectl get pods -n hamzadevops

echo ""
echo "Final node status:"
kubectl get nodes

# Generate summary
print_status "📈 Generating test summary..."

echo ""
echo "🎯 Test Summary:"
echo "==============="
echo "• Target: https://hamzakalech.com"
echo "• Duration: 2 hours"
echo "• Total phases: 5"
echo "• Max expected pods: ~12"
echo "• Max expected nodes: ~6"
echo ""

echo "📁 Files generated:"
echo "• Results: results/load-test-*.json"
echo "• Logs: logs/artillery-*.log"
echo "• Monitoring: logs/monitoring-*.log"
echo ""

print_success "✅ Load test execution completed successfully!"
echo "Check Grafana dashboard for detailed metrics: https://your-grafana-url"
echo "Check Prometheus for detailed metrics: https://your-prometheus-url"

# Keep monitoring running for 5 more minutes to observe scale-down
print_status "🔍 Monitoring scale-down for 5 more minutes..."
sleep 300

print_success "🏁 All done! Check your results and monitoring logs."
