#!/usr/bin/env python3
"""Agent Health Monitoring System

Track Agent health metrics: resource usage, quality trends, burnout risk.
Run this alongside evolution cycles to monitor sustainability.
"""
import json
import time
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional

# These would be populated from actual metrics
METRICS_HISTORY = []

class AgentHealth:
    def __init__(self, metrics_file='health_metrics.json'):
        self.metrics_file = metrics_file
        self.history = self.load_history()
        
    def load_history(self) -> List[Dict]:
        if os.path.exists(self.metrics_file):
            with open(self.metrics_file, 'r') as f:
                return json.load(f)
        return []
    
    def save_metrics(self, metrics: Dict):
        metrics['timestamp'] = datetime.now().isoformat()
        self.history.append(metrics)
        # Keep only last 30 days
        cutoff = datetime.now() - timedelta(days=30)
        self.history = [
            m for m in self.history
            if datetime.fromisoformat(m['timestamp']) > cutoff
        ]
        with open(self.metrics_file, 'w') as f:
            json.dump(self.history, f, indent=2)
    
    def current_metrics(self) -> Dict:
        """Collect current health metrics (simulated for now)."""
        # In production, these would come from system metrics
        return {
            'memory_usage_mb': 0,  # would get from psutil
            'cpu_percent': 0,
            'api_costs_last_hour': 0,
            'capsule_count_24h': 0,
            'avg_quality_last_5': 0.0,
            'error_count_24h': 0,
            'decision_time_avg': 0.0,
        }
    
    def calculate_health_score(self, metrics: Dict) -> float:
        """Calculate overall health score 0-100."""
        score = 100.0
        
        # Memory pressure
        mem_mb = metrics.get('memory_usage_mb', 0)
        if mem_mb > 3000:
            score -= 20
        elif mem_mb > 2000:
            score -= 10
            
        # Quality trend
        avg_q = metrics.get('avg_quality_last_5', 1.0)
        if avg_q < 0.7:
            score -= 25
        elif avg_q < 0.8:
            score -= 10
            
        # Error rate
        errors = metrics.get('error_count_24h', 0)
        if errors > 10:
            score -= 20
        elif errors > 5:
            score -= 5
            
        return max(0, min(100, score))
    
    def burnout_risk(self) -> str:
        """Assess burnout risk based on recent trends."""
        if len(self.history) < 5:
            return "insufficient_data"
        
        recent = self.history[-5:]
        qualities = [m.get('avg_quality_last_5', 0.8) for m in recent]
        memories = [m.get('memory_usage_mb', 0) for m in recent]
        
        quality_trend = qualities[-1] - qualities[0]
        memory_growth = memories[-1] - memories[0]
        
        if quality_trend < -0.1 and memory_growth > 500:
            return "high"
        elif quality_trend < -0.05:
            return "medium"
        else:
            return "low"
    
    def generate_report(self) -> str:
        """Generate a human-readable health report."""
        current = self.current_metrics()
        score = self.calculate_health_score(current)
        risk = self.burnout_risk()
        
        report = f"""Agent Health Report — {datetime.now().strftime('%Y-%m-%d %H:%M')}
{'='*50}
Health Score: {score:.1f}/100
Burnout Risk: {risk.upper()}

Current Metrics:
- Memory: {current['memory_usage_mb']:.0f} MB
- CPU: {current['cpu_percent']:.1f}%
- Quality (last 5): {current['avg_quality_last_5']:.2f}
- API errors (24h): {current['error_count_24h']}
- Decision time avg: {current['decision_time_avg']:.1f}s

Recommendations:"""
        
        if score < 70:
            report += "\n- ⚠️  Consider slowing down evolution cycles"
        if score < 80:
            report += "\n- ⏰ Insert longer breaks between cycles"
        if risk == "high":
            report += "\n- 🛑 Take a complete break for at least 2 hours"
        if score >= 90:
            report += "\n- ✅ Operating within healthy parameters"
            
        return report

if __name__ == "__main__":
    health = AgentHealth()
    print(health.generate_report())
