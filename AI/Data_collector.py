#!/usr/bin/env python3

import requests
import pandas as pd
import datetime
import time
import json
import os
import numpy as np
from typing import Dict, List, Optional, Tuple
import urllib3
import logging
from dataclasses import dataclass

# Disable SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('prometheus_collector.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class PrometheusConfig:
    """Configuration for Prometheus data collection"""
    url: str = "https://prometheus.hamzakalech.com"
    namespace: str = "hamzadevops"
    step_seconds: int = 30  # Higher resolution for ML
    days_back: int = 1  # Focus on recent load test data
    timeout: int = 30
    verify_ssl: bool = True
    max_retries: int = 3
    retry_delay: int = 5

class PrometheusCollector:
    """Enhanced Prometheus data collector for autoscaling ML models"""
    
    def __init__(self, config: PrometheusConfig):
        self.config = config
        self.session = requests.Session()
        self.session.headers.update({'Accept': 'application/json'})
        
        # Define comprehensive PromQL queries for autoscaling
        self.queries = self._build_queries()
        
    def _build_queries(self) -> Dict[str, str]:
        """Build comprehensive PromQL queries for autoscaling metrics"""
        ns = self.config.namespace
        
        return {
            # === RESOURCE UTILIZATION ===
            "cpu_usage_rate": f'rate(container_cpu_usage_seconds_total{{namespace="{ns}", container!="", container!="POD"}}[2m])',
            "cpu_requests": f'kube_pod_container_resource_requests{{namespace="{ns}", resource="cpu"}}',
            "cpu_limits": f'kube_pod_container_resource_limits{{namespace="{ns}", resource="cpu"}}',
            "memory_usage": f'container_memory_working_set_bytes{{namespace="{ns}", container!="", container!="POD"}}',
            "memory_requests": f'kube_pod_container_resource_requests{{namespace="{ns}", resource="memory"}}',
            "memory_limits": f'kube_pod_container_resource_limits{{namespace="{ns}", resource="memory"}}',
            
            # === NETWORK METRICS ===
            "network_rx_rate": f'rate(container_network_receive_bytes_total{{namespace="{ns}"}}[2m])',
            "network_tx_rate": f'rate(container_network_transmit_bytes_total{{namespace="{ns}"}}[2m])',
            "network_rx_packets": f'rate(container_network_receive_packets_total{{namespace="{ns}"}}[2m])',
            "network_tx_packets": f'rate(container_network_transmit_packets_total{{namespace="{ns}"}}[2m])',
            
            # === APPLICATION METRICS ===
            "http_requests_rate": f'rate(http_requests_total{{namespace="{ns}"}}[2m])',
            "http_request_duration": f'histogram_quantile(0.95, rate(http_request_duration_seconds_bucket{{namespace="{ns}"}}[2m]))',
            "error_rate": f'rate(http_requests_total{{namespace="{ns}", status=~"5.."}}[2m])',
            
            # === KUBERNETES METRICS ===
            "pod_count_running": f'count(kube_pod_status_phase{{namespace="{ns}", phase="Running"}})',
            "pod_count_pending": f'count(kube_pod_status_phase{{namespace="{ns}", phase="Pending"}})',
            "pod_restart_rate": f'rate(kube_pod_container_status_restarts_total{{namespace="{ns}"}}[5m])',
            
            # === HPA METRICS ===
            "hpa_current_replicas": f'kube_horizontalpodautoscaler_status_current_replicas{{namespace="{ns}"}}',
            "hpa_desired_replicas": f'kube_horizontalpodautoscaler_status_desired_replicas{{namespace="{ns}"}}',
            "hpa_target_cpu": f'kube_horizontalpodautoscaler_spec_target_cpu_utilization_percentage{{namespace="{ns}"}}',
            
            # === NODE METRICS ===
            "node_count_ready": 'count(kube_node_status_condition{condition="Ready", status="true", node_label_agentpool="worker"})',
            "node_cpu_usage": 'rate(node_cpu_seconds_total{mode!="idle", node_label_agentpool="worker"}[2m])',
            "node_memory_usage": 'node_memory_MemAvailable_bytes{node_label_agentpool="worker"}',
            "node_load1": 'node_load1{node_label_agentpool="worker"}',
            "node_load5": 'node_load5{node_label_agentpool="worker"}',
            
            # === DISK AND I/O ===
            "disk_usage": f'container_fs_usage_bytes{{namespace="{ns}", container!="", container!="POD"}}',
            "disk_io_read": f'rate(container_fs_reads_bytes_total{{namespace="{ns}", container!=""}}[2m])',
            "disk_io_write": f'rate(container_fs_writes_bytes_total{{namespace="{ns}", container!=""}}[2m])',
            
            # === DERIVED METRICS FOR ML ===
            "cpu_utilization_pct": f'(rate(container_cpu_usage_seconds_total{{namespace="{ns}", container!="", container!="POD"}}[2m]) / on(pod) kube_pod_container_resource_requests{{namespace="{ns}", resource="cpu"}}) * 100',
            "memory_utilization_pct": f'(container_memory_working_set_bytes{{namespace="{ns}", container!="", container!="POD"}} / on(pod) kube_pod_container_resource_requests{{namespace="{ns}", resource="memory"}}) * 100',
        }
    
    def query_prometheus(self, query: str, start_time: int, end_time: int) -> Optional[Dict]:
        """Query Prometheus with retry logic"""
        url = f"{self.config.url}/api/v1/query_range"
        params = {
            "query": query,
            "start": start_time,
            "end": end_time,
            "step": f"{self.config.step_seconds}s"
        }
        
        for attempt in range(self.config.max_retries):
            try:
                logger.info(f"Querying: {query[:60]}... (attempt {attempt + 1})")
                response = self.session.get(
                    url, 
                    params=params, 
                    timeout=self.config.timeout,
                    verify=self.config.verify_ssl
                )
                
                if response.status_code == 200:
                    data = response.json()
                    if data.get('status') == 'success':
                        return data
                    else:
                        logger.error(f"Prometheus error: {data.get('error', 'Unknown error')}")
                else:
                    logger.error(f"HTTP {response.status_code}: {response.text[:200]}")
                    
            except requests.exceptions.RequestException as e:
                logger.error(f"Request failed: {str(e)}")
                
            if attempt < self.config.max_retries - 1:
                logger.info(f"Retrying in {self.config.retry_delay} seconds...")
                time.sleep(self.config.retry_delay)
        
        logger.error(f"Failed to query after {self.config.max_retries} attempts")
        return None
    
    def extract_time_series(self, prom_data: Dict, metric_name: str, 
                           aggregation: str = "mean") -> pd.DataFrame:
        """Extract and aggregate time series data"""
        if not prom_data or 'data' not in prom_data:
            return pd.DataFrame()
        
        results = prom_data['data'].get('result', [])
        if not results:
            return pd.DataFrame()
        
        all_data = []
        for result in results:
            labels = result.get('metric', {})
            values = result.get('values', [])
            
            for timestamp_str, value_str in values:
                try:
                    timestamp = datetime.datetime.fromtimestamp(float(timestamp_str))
                    value = float(value_str)
                    
                    row = {
                        'timestamp': timestamp,
                        metric_name: value,
                        **{f"{metric_name}_{k}": v for k, v in labels.items()}
                    }
                    all_data.append(row)
                except (ValueError, TypeError) as e:
                    logger.warning(f"Skipping invalid data point: {e}")
                    continue
        
        if not all_data:
            return pd.DataFrame()
        
        df = pd.DataFrame(all_data)
        
        # Aggregate by timestamp if multiple series
        if len(results) > 1:
            numeric_cols = [col for col in df.columns if col.startswith(metric_name) and not col.endswith('_' + col.split('_')[-1])]
            if numeric_cols:
                agg_funcs = {col: aggregation for col in numeric_cols}
                df = df.groupby('timestamp').agg(agg_funcs).reset_index()
        
        return df
    
    def collect_all_metrics(self, start_time: datetime.datetime, 
                           end_time: datetime.datetime) -> pd.DataFrame:
        """Collect all metrics and merge into single DataFrame"""
        start_unix = int(start_time.timestamp())
        end_unix = int(end_time.timestamp())
        
        logger.info(f"Collecting metrics from {start_time} to {end_time}")
        logger.info(f"Time range: {start_unix} to {end_unix} (step: {self.config.step_seconds}s)")
        
        # Collect all metrics
        dataframes = []
        failed_queries = []
        
        for metric_name, query in self.queries.items():
            logger.info(f"Processing metric: {metric_name}")
            
            prom_data = self.query_prometheus(query, start_unix, end_unix)
            if prom_data:
                df = self.extract_time_series(prom_data, metric_name)
                if not df.empty:
                    dataframes.append(df)
                    logger.info(f"✅ {metric_name}: {len(df)} data points")
                else:
                    logger.warning(f"⚠️  {metric_name}: No data points")
            else:
                failed_queries.append(metric_name)
                logger.error(f"❌ {metric_name}: Query failed")
        
        if failed_queries:
            logger.warning(f"Failed queries: {', '.join(failed_queries)}")
        
        if not dataframes:
            logger.error("No data collected from any metric!")
            return pd.DataFrame()
        
        # Merge all dataframes
        logger.info("Merging all metrics...")
        merged_df = dataframes[0]
        
        for df in dataframes[1:]:
            merged_df = pd.merge(merged_df, df, on='timestamp', how='outer')
        
        # Sort by timestamp
        merged_df = merged_df.sort_values('timestamp').reset_index(drop=True)
        
        # Forward fill missing values (common in time series)
        merged_df = merged_df.fillna(method='forward').fillna(method='backward')
        
        logger.info(f"✅ Merged dataset: {len(merged_df)} rows × {len(merged_df.columns)} columns")
        return merged_df
    
    def add_derived_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add derived features useful for ML model training"""
        if df.empty:
            return df
        
        logger.info("Adding derived features for ML...")
        
        # Time-based features
        df['hour'] = df['timestamp'].dt.hour
        df['day_of_week'] = df['timestamp'].dt.dayofweek
        df['is_weekend'] = df['day_of_week'].isin([5, 6]).astype(int)
        
        # Rolling averages (5 minute, 15 minute, 1 hour windows)
        for col in df.select_dtypes(include=[np.number]).columns:
            if col not in ['hour', 'day_of_week', 'is_weekend']:
                for window in [10, 30, 120]:  # 5min, 15min, 1hr at 30s intervals
                    df[f'{col}_rolling_{window}'] = df[col].rolling(window=window, min_periods=1).mean()
        
        # Rate of change features
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        for col in ['cpu_usage_rate', 'memory_usage', 'http_requests_rate', 'pod_count_running']:
            if col in numeric_cols:
                df[f'{col}_rate_of_change'] = df[col].diff()
                df[f'{col}_rate_of_change_pct'] = df[col].pct_change() * 100
        
        # Load indicators
        if 'http_requests_rate' in df.columns and 'pod_count_running' in df.columns:
            df['requests_per_pod'] = df['http_requests_rate'] / df['pod_count_running'].replace(0, 1)
        
        if 'cpu_usage_rate' in df.columns and 'pod_count_running' in df.columns:
            df['cpu_per_pod'] = df['cpu_usage_rate'] / df['pod_count_running'].replace(0, 1)
        
        # HPA efficiency metrics
        if all(col in df.columns for col in ['hpa_current_replicas', 'hpa_desired_replicas']):
            df['hpa_replica_gap'] = df['hpa_desired_replicas'] - df['hpa_current_replicas']
            df['hpa_scaling_pressure'] = (df['hpa_replica_gap'] != 0).astype(int)
        
        logger.info(f"✅ Added derived features: {len(df.columns)} total columns")
        return df
    
    def save_data(self, df: pd.DataFrame, base_filename: str = "prometheus_autoscaling_data"):
        """Save data in multiple formats for ML training"""
        if df.empty:
            logger.error("No data to save!")
            return
        
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Create results directory
        os.makedirs("ml_data", exist_ok=True)
        
        # Save as CSV
        csv_file = f"ml_data/{base_filename}_{timestamp}.csv"
        df.to_csv(csv_file, index=False)
        logger.info(f"✅ Saved CSV: {csv_file}")
        
        # Save as Parquet (better for ML workflows)
        parquet_file = f"ml_data/{base_filename}_{timestamp}.parquet"
        df.to_parquet(parquet_file, index=False)
        logger.info(f"✅ Saved Parquet: {parquet_file}")
        
        # Save metadata
        metadata = {
            "collection_time": datetime.datetime.now().isoformat(),
            "data_points": len(df),
            "features": len(df.columns),
            "time_range": {
                "start": str(df['timestamp'].min()),
                "end": str(df['timestamp'].max())
            },
            "metrics_collected": [col for col in df.columns if not col.startswith(('timestamp', 'hour', 'day_of_week'))],
            "config": {
                "prometheus_url": self.config.url,
                "namespace": self.config.namespace,
                "step_seconds": self.config.step_seconds,
                "days_back": self.config.days_back
            }
        }
        
        metadata_file = f"ml_data/{base_filename}_{timestamp}_metadata.json"
        with open(metadata_file, 'w') as f:
            json.dump(metadata, f, indent=2, default=str)
        logger.info(f"✅ Saved metadata: {metadata_file}")
        
        # Data quality report
        self.generate_data_quality_report(df, f"ml_data/{base_filename}_{timestamp}_quality_report.txt")
        
        return csv_file, parquet_file, metadata_file

    def generate_data_quality_report(self, df: pd.DataFrame, filename: str):
        """Generate data quality report"""
        with open(filename, 'w') as f:
            f.write("=== DATA QUALITY REPORT ===\n\n")
            f.write(f"Dataset Shape: {df.shape}\n")
            f.write(f"Time Range: {df['timestamp'].min()} to {df['timestamp'].max()}\n")
            f.write(f"Duration: {df['timestamp'].max() - df['timestamp'].min()}\n\n")
            
            f.write("=== MISSING DATA ===\n")
            missing = df.isnull().sum()
            missing_pct = (missing / len(df)) * 100
            for col, count in missing.items():
                if count > 0:
                    f.write(f"{col}: {count} ({missing_pct[col]:.1f}%)\n")
            
            f.write("\n=== BASIC STATISTICS ===\n")
            f.write(str(df.describe()))
            
        logger.info(f"✅ Generated quality report: {filename}")

def main():
    """Main execution function"""
    print("🚀 Enhanced Prometheus Data Collector for Predictive Autoscaling")
    print("=" * 70)
    
    # Configuration
    config = PrometheusConfig(
        url="https://prometheus.hamzakalech.com",
        namespace="hamzadevops",
        step_seconds=30,  # 30-second resolution for detailed ML training
        days_back=1,  # Collect last 24 hours (adjust based on your load test duration)
        verify_ssl=True
    )
    
    # Calculate time range
    end_time = datetime.datetime.utcnow()
    start_time = end_time - datetime.timedelta(days=config.days_back)
    
    print(f"📊 Collection Config:")
    print(f"   • Prometheus: {config.url}")
    print(f"   • Namespace: {config.namespace}")
    print(f"   • Time Range: {start_time} to {end_time}")
    print(f"   • Resolution: {config.step_seconds} seconds")
    print(f"   • Expected Data Points: ~{int((end_time - start_time).total_seconds() / config.step_seconds)}")
    print()
    
    # Initialize collector
    collector = PrometheusCollector(config)
    
    try:
        # Collect metrics
        print("🔍 Starting data collection...")
        df = collector.collect_all_metrics(start_time, end_time)
        
        if df.empty:
            logger.error("❌ No data collected! Check Prometheus connectivity and queries.")
            return
        
        # Add ML features
        df = collector.add_derived_features(df)
        
        # Save data
        print("💾 Saving data for ML training...")
        files = collector.save_data(df)
        
        print("\n🎉 Data Collection Complete!")
        print(f"   • Collected {len(df)} data points")
        print(f"   • Features: {len(df.columns)}")
        print(f"   • Files saved in ml_data/ directory")
        print("\n📈 Ready for ML model training!")
        
        # Display sample data
        print("\n📋 Sample Data Preview:")
        print(df.head())
        
    except Exception as e:
        logger.error(f"❌ Collection failed: {str(e)}")
        raise

if __name__ == "__main__":
    main()
