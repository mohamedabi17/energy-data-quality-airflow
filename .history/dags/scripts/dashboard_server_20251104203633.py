"""
Interactive Dashboard Server with Pipeline Control
Provides real-time pipeline execution and metrics tracking
"""

from flask import Flask, render_template_string, jsonify, request
from flask_cors import CORS
import subprocess
import threading
import time
import os
import sys
from pathlib import Path
import pandas as pd
from datetime import datetime
import json

# Setup paths
BASE_PATH = Path(__file__).parent.parent.parent
METADATA_DIR = BASE_PATH / 'metadata'
DAGS_DIR = BASE_PATH / 'dags'

app = Flask(__name__)
CORS(app)

# Global state for pipeline execution
pipeline_state = {
    'running': False,
    'current_task': None,
    'tasks': [
        {'id': 'compute_uncleaned_metrics', 'name': 'Raw Metrics', 'status': 'pending', 'progress': 0},
        {'id': 'clean_data', 'name': 'Clean Data', 'status': 'pending', 'progress': 0},
        {'id': 'aggregate_data', 'name': 'Aggregate Data', 'status': 'pending', 'progress': 0},
        {'id': 'compute_cleaned_metrics', 'name': 'Cleaned Metrics', 'status': 'pending', 'progress': 0},
    ],
    'start_time': None,
    'end_time': None,
    'logs': []
}


def load_metrics_data(stage='raw'):
    """Load latest metrics for a given stage"""
    try:
        metrics_file = METADATA_DIR / f'metadata_qd_{stage}_latest.csv'
        if metrics_file.exists():
            df = pd.read_csv(metrics_file, sep=';')
            return df.to_dict('records')[0] if len(df) > 0 else {}
        return {}
    except Exception as e:
        print(f"Error loading metrics for {stage}: {e}")
        return {}


def execute_pipeline_task(task_id):
    """Execute a specific pipeline task"""
    sys.path.insert(0, str(Path(__file__).parent))
    
    try:
        if task_id == 'compute_uncleaned_metrics':
            from compute_metrics import main as compute_metrics_main
            compute_metrics_main(stage='raw', source_dir='input_data')
            
        elif task_id == 'clean_data':
            from clean_data import main as clean_data_main
            clean_data_main()
            
        elif task_id == 'aggregate_data':
            from aggregate_data import main as aggregate_data_main
            aggregate_data_main()
            
        elif task_id == 'compute_cleaned_metrics':
            from compute_metrics import main as compute_metrics_main
            compute_metrics_main(stage='cleaned', source_dir='cleaned_data')
            
        return True
    except Exception as e:
        pipeline_state['logs'].append(f"❌ Error in {task_id}: {str(e)}")
        return False


def run_pipeline():
    """Execute the complete data quality pipeline"""
    global pipeline_state
    
    pipeline_state['running'] = True
    pipeline_state['start_time'] = datetime.now().isoformat()
    pipeline_state['logs'] = [f"🚀 Pipeline started at {datetime.now().strftime('%H:%M:%S')}"]
    
    try:
        for i, task in enumerate(pipeline_state['tasks']):
            # Update current task
            pipeline_state['current_task'] = task['id']
            task['status'] = 'running'
            pipeline_state['logs'].append(f"▶️ Starting: {task['name']}")
            
            # Execute task
            success = execute_pipeline_task(task['id'])
            
            if success:
                task['status'] = 'success'
                task['progress'] = 100
                pipeline_state['logs'].append(f"✅ Completed: {task['name']}")
            else:
                task['status'] = 'failed'
                pipeline_state['logs'].append(f"❌ Failed: {task['name']}")
                break
            
            time.sleep(0.5)  # Brief pause for UI updates
        
        pipeline_state['end_time'] = datetime.now().isoformat()
        pipeline_state['running'] = False
        pipeline_state['current_task'] = None
        pipeline_state['logs'].append(f"🏁 Pipeline completed at {datetime.now().strftime('%H:%M:%S')}")
        
    except Exception as e:
        pipeline_state['logs'].append(f"❌ Pipeline error: {str(e)}")
        pipeline_state['running'] = False
        pipeline_state['current_task'] = None


@app.route('/')
def dashboard():
    """Serve the interactive dashboard"""
    html = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Data Quality Pipeline Dashboard</title>
    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 20px;
            min-height: 100vh;
        }
        .container {
            max-width: 1400px;
            margin: 0 auto;
        }
        .header {
            background: white;
            border-radius: 10px;
            padding: 30px;
            margin-bottom: 20px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.3);
        }
        .header h1 {
            font-size: 36px;
            color: #2c3e50;
            margin-bottom: 10px;
        }
        .header p {
            color: #7f8c8d;
            font-size: 16px;
        }
        
        .control-panel {
            background: white;
            border-radius: 10px;
            padding: 25px;
            margin-bottom: 20px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.3);
        }
        .control-panel h2 {
            font-size: 24px;
            color: #2c3e50;
            margin-bottom: 15px;
        }
        
        .pipeline-controls {
            display: flex;
            gap: 15px;
            align-items: center;
            margin-bottom: 20px;
        }
        
        #startPipeline {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            padding: 15px 30px;
            font-size: 18px;
            font-weight: bold;
            border-radius: 8px;
            cursor: pointer;
            transition: all 0.3s;
            box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
        }
        #startPipeline:hover:not(:disabled) {
            transform: translateY(-2px);
            box-shadow: 0 6px 20px rgba(102, 126, 234, 0.6);
        }
        #startPipeline:disabled {
            background: #95a5a6;
            cursor: not-allowed;
            box-shadow: none;
        }
        
        .pipeline-status {
            display: flex;
            align-items: center;
            gap: 10px;
            font-size: 16px;
            color: #34495e;
        }
        .status-indicator {
            width: 12px;
            height: 12px;
            border-radius: 50%;
            background: #95a5a6;
        }
        .status-indicator.running {
            background: #f39c12;
            animation: pulse 1.5s infinite;
        }
        .status-indicator.success {
            background: #27ae60;
        }
        
        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.5; }
        }
        
        .tasks-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 15px;
            margin-bottom: 20px;
        }
        
        .task-card {
            background: #ecf0f1;
            border-radius: 8px;
            padding: 20px;
            transition: all 0.3s;
        }
        .task-card.running {
            background: #fff3cd;
            border-left: 4px solid #f39c12;
        }
        .task-card.success {
            background: #d4edda;
            border-left: 4px solid #27ae60;
        }
        .task-card.failed {
            background: #f8d7da;
            border-left: 4px solid #e74c3c;
        }
        
        .task-card h3 {
            font-size: 18px;
            color: #2c3e50;
            margin-bottom: 10px;
        }
        .task-card .progress-bar {
            width: 100%;
            height: 6px;
            background: #bdc3c7;
            border-radius: 3px;
            overflow: hidden;
            margin-top: 10px;
        }
        .task-card .progress-fill {
            height: 100%;
            background: linear-gradient(90deg, #667eea, #764ba2);
            width: 0%;
            transition: width 0.5s;
        }
        
        .logs-panel {
            background: #2c3e50;
            border-radius: 10px;
            padding: 20px;
            margin-bottom: 20px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.3);
            max-height: 300px;
            overflow-y: auto;
        }
        .logs-panel h3 {
            color: white;
            margin-bottom: 15px;
            font-size: 20px;
        }
        .log-entry {
            color: #ecf0f1;
            font-family: 'Courier New', monospace;
            font-size: 14px;
            padding: 5px 0;
            border-bottom: 1px solid #34495e;
        }
        
        .metrics-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin-bottom: 20px;
        }
        
        .metric-card {
            background: white;
            border-radius: 10px;
            padding: 25px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.3);
        }
        .metric-card h3 {
            font-size: 18px;
            color: #7f8c8d;
            margin-bottom: 15px;
            text-transform: uppercase;
            letter-spacing: 1px;
        }
        .metric-value {
            font-size: 48px;
            font-weight: bold;
            color: #2c3e50;
            margin-bottom: 10px;
        }
        .metric-change {
            font-size: 16px;
            padding: 5px 10px;
            border-radius: 5px;
            display: inline-block;
        }
        .metric-change.positive {
            background: #d4edda;
            color: #27ae60;
        }
        .metric-change.negative {
            background: #f8d7da;
            color: #e74c3c;
        }
        
        .chart-container {
            background: white;
            border-radius: 10px;
            padding: 20px;
            margin-bottom: 20px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.3);
        }
        
        .detailed-metrics {
            background: white;
            border-radius: 10px;
            padding: 25px;
            margin-bottom: 20px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.3);
        }
        .detailed-metrics h2 {
            font-size: 24px;
            color: #2c3e50;
            margin-bottom: 20px;
        }
        
        .metrics-table {
            width: 100%;
            border-collapse: collapse;
            margin-bottom: 20px;
        }
        .metrics-table th {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 15px;
            text-align: left;
            font-weight: 600;
            position: sticky;
            top: 0;
        }
        .metrics-table td {
            padding: 12px 15px;
            border-bottom: 1px solid #ecf0f1;
        }
        .metrics-table tr:hover {
            background: #f8f9fa;
        }
        .metric-category {
            font-weight: bold;
            color: #2c3e50;
            font-size: 14px;
        }
        .metric-name {
            color: #7f8c8d;
            font-size: 13px;
        }
        .metric-value-cell {
            text-align: center;
            font-weight: 600;
        }
        .metric-diff {
            text-align: center;
            font-weight: bold;
            padding: 5px 10px;
            border-radius: 5px;
        }
        .metric-diff.improvement {
            background: #d4edda;
            color: #27ae60;
        }
        .metric-diff.regression {
            background: #f8d7da;
            color: #e74c3c;
        }
        .metric-diff.neutral {
            background: #e2e3e5;
            color: #6c757d;
        }
        
        .filter-tabs {
            display: flex;
            gap: 10px;
            margin-bottom: 20px;
            flex-wrap: wrap;
        }
        .filter-tab {
            padding: 10px 20px;
            background: #ecf0f1;
            border: 2px solid transparent;
            border-radius: 8px;
            cursor: pointer;
            transition: all 0.3s;
            font-weight: 500;
        }
        .filter-tab:hover {
            background: #d5d8dc;
        }
        .filter-tab.active {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border-color: #5a67d8;
        }
        
        .charts-row {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(500px, 1fr));
            gap: 20px;
            margin-bottom: 20px;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🚀 Data Quality Pipeline Dashboard</h1>
            <p>Real-time pipeline execution and metrics tracking</p>
        </div>
        
        <div class="control-panel">
            <h2>Pipeline Control</h2>
            <div class="pipeline-controls">
                <button id="startPipeline" onclick="startPipeline()">▶️ Launch Pipeline</button>
                <div class="pipeline-status">
                    <div class="status-indicator" id="statusIndicator"></div>
                    <span id="statusText">Ready</span>
                </div>
            </div>
            
            <div class="tasks-grid" id="tasksGrid"></div>
        </div>
        
        <div class="logs-panel">
            <h3>📋 Execution Logs</h3>
            <div id="logsContainer"></div>
        </div>
        
        <div class="metrics-grid" id="metricsGrid"></div>
        
        <div class="detailed-metrics">
            <h2>📊 Detailed Metrics Comparison</h2>
            
            <div class="filter-tabs">
                <button class="filter-tab active" onclick="filterMetrics('all')">All Metrics</button>
                <button class="filter-tab" onclick="filterMetrics('completeness')">Completeness</button>
                <button class="filter-tab" onclick="filterMetrics('validity')">Validity</button>
                <button class="filter-tab" onclick="filterMetrics('duplicates')">Duplicates</button>
                <button class="filter-tab" onclick="filterMetrics('consistency')">Consistency</button>
            </div>
            
            <div style="overflow-x: auto; max-height: 600px; overflow-y: auto;">
                <table class="metrics-table" id="metricsTable">
                    <thead>
                        <tr>
                            <th style="min-width: 300px;">Metric</th>
                            <th style="min-width: 120px;">Raw Data</th>
                            <th style="min-width: 120px;">Cleaned Data</th>
                            <th style="min-width: 150px;">Improvement</th>
                            <th style="min-width: 100px;">Status</th>
                        </tr>
                    </thead>
                    <tbody id="metricsTableBody"></tbody>
                </table>
            </div>
        </div>
        
        <div class="charts-row">
            <div class="chart-container">
                <div id="comparisonChart"></div>
            </div>
            <div class="chart-container">
                <div id="categoryChart"></div>
            </div>
        </div>
        
        <div class="charts-row">
            <div class="chart-container">
                <div id="heatmapChart"></div>
            </div>
            <div class="chart-container">
                <div id="radarChart"></div>
            </div>
        </div>
    </div>
    
    <script>
        let updateInterval = null;
        
        function startPipeline() {
            const btn = document.getElementById('startPipeline');
            btn.disabled = true;
            btn.textContent = '⏳ Running...';
            
            fetch('/api/start-pipeline', { method: 'POST' })
                .then(r => r.json())
                .then(data => {
                    console.log('Pipeline started:', data);
                    updateInterval = setInterval(updateDashboard, 1000);
                })
                .catch(err => {
                    console.error('Error starting pipeline:', err);
                    btn.disabled = false;
                    btn.textContent = '▶️ Launch Pipeline';
                });
        }
        
        function updateDashboard() {
            fetch('/api/pipeline-status')
                .then(r => r.json())
                .then(data => {
                    updateStatus(data);
                    updateTasks(data.tasks);
                    updateLogs(data.logs);
                    
                    if (!data.running && updateInterval) {
                        clearInterval(updateInterval);
                        document.getElementById('startPipeline').disabled = false;
                        document.getElementById('startPipeline').textContent = '▶️ Launch Pipeline';
                        loadMetrics();
                    }
                });
        }
        
        function updateStatus(data) {
            const indicator = document.getElementById('statusIndicator');
            const text = document.getElementById('statusText');
            
            if (data.running) {
                indicator.className = 'status-indicator running';
                text.textContent = `Running: ${data.current_task || 'Initializing...'}`;
            } else {
                const allSuccess = data.tasks.every(t => t.status === 'success');
                indicator.className = 'status-indicator ' + (allSuccess ? 'success' : '');
                text.textContent = allSuccess ? 'Completed Successfully' : 'Ready';
            }
        }
        
        function updateTasks(tasks) {
            const grid = document.getElementById('tasksGrid');
            grid.innerHTML = tasks.map(task => `
                <div class="task-card ${task.status}">
                    <h3>${task.name}</h3>
                    <div>${getStatusEmoji(task.status)} ${task.status.toUpperCase()}</div>
                    <div class="progress-bar">
                        <div class="progress-fill" style="width: ${task.progress}%"></div>
                    </div>
                </div>
            `).join('');
        }
        
        function getStatusEmoji(status) {
            const emojis = {
                'pending': '⏳',
                'running': '▶️',
                'success': '✅',
                'failed': '❌'
            };
            return emojis[status] || '⏳';
        }
        
        function updateLogs(logs) {
            const container = document.getElementById('logsContainer');
            container.innerHTML = logs.slice(-15).reverse().map(log => 
                `<div class="log-entry">${log}</div>`
            ).join('');
        }
        
        function loadMetrics() {
            fetch('/api/metrics')
                .then(r => r.json())
                .then(data => {
                    displayMetrics(data);
                    displayComparison(data);
                });
        }
        
        let allMetricsData = [];
        let currentFilter = 'all';
        
        function displayMetrics(data) {
            const grid = document.getElementById('metricsGrid');
            
            const metrics = [
                {
                    title: 'Paris Invalid Records',
                    raw: data.raw.pct_invalid_kw_cons_paris_unit || 0,
                    cleaned: data.cleaned.pct_invalid_kw_cons_paris_unit || 0
                },
                {
                    title: 'Evry Invalid Records',
                    raw: data.raw.pct_invalid_kw_cons_evry_unit || 0,
                    cleaned: data.cleaned.pct_invalid_kw_cons_evry_unit || 0
                },
                {
                    title: 'Paris Duplicates',
                    raw: data.raw.pct_duplicates_cons_paris || 0,
                    cleaned: data.cleaned.pct_duplicates_cons_paris || 0
                },
                {
                    title: 'CSP Completeness',
                    raw: data.raw.pct_complete_csp_salary || 0,
                    cleaned: data.cleaned.pct_complete_csp_salary || 0
                }
            ];
            
            grid.innerHTML = metrics.map(m => {
                const improvement = m.cleaned - m.raw;
                const isPositive = m.title.includes('Completeness') ? improvement > 0 : improvement < 0;
                
                return `
                    <div class="metric-card">
                        <h3>${m.title}</h3>
                        <div class="metric-value">${m.cleaned.toFixed(1)}%</div>
                        <div class="metric-change ${isPositive ? 'positive' : 'negative'}">
                            ${isPositive ? '↑' : '↓'} ${Math.abs(improvement).toFixed(1)}% from raw
                        </div>
                    </div>
                `;
            }).join('');
            
            // Build detailed metrics table
            buildDetailedMetrics(data);
        }
        
        function buildDetailedMetrics(data) {
            allMetricsData = [];
            
            // Categorize metrics - using actual column names from CSV
            const metricCategories = {
                'completeness': {
                    name: 'Completeness Metrics',
                    metrics: [
                        { key: 'pct_address_valid_cons_paris', name: 'Paris Consumption - Address Validity', better: 'higher' },
                        { key: 'completeness_cons_paris', name: 'Paris Consumption - Overall Completeness', better: 'higher' },
                        { key: 'pct_address_valid_cons_evry', name: 'Evry Consumption - Address Validity', better: 'higher' },
                        { key: 'completeness_cons_evry', name: 'Evry Consumption - Overall Completeness', better: 'higher' },
                        { key: 'completeness_pop_paris', name: 'Paris Population - Overall Completeness', better: 'higher' },
                        { key: 'completeness_pop_evry', name: 'Evry Population - Overall Completeness', better: 'higher' },
                        { key: 'completeness_salaire_csp', name: 'CSP - Salary Completeness', better: 'higher' },
                        { key: 'completeness_csp', name: 'CSP - Overall Completeness', better: 'higher' }
                    ]
                },
                'validity': {
                    name: 'Data Validity (Invalid Rates)',
                    metrics: [
                        { key: 'pct_invalid_kw_cons_paris_unit', name: 'Paris - Invalid Consumption Unit', better: 'lower' },
                        { key: 'pct_NB_KW_Jour_invalid_cons_paris', name: 'Paris - Invalid Daily Consumption', better: 'lower' },
                        { key: 'pct_CP_invalid_cons_paris', name: 'Paris - Invalid Postal Code', better: 'lower' },
                        { key: 'invalid_rate_cons_paris', name: 'Paris - Overall Invalid Rate', better: 'lower' },
                        { key: 'pct_invalid_kw_cons_evry_unit', name: 'Evry - Invalid Consumption Unit', better: 'lower' },
                        { key: 'pct_NB_KW_Jour_invalid_cons_evry', name: 'Evry - Invalid Daily Consumption', better: 'lower' },
                        { key: 'pct_CP_invalid_cons_evry', name: 'Evry - Invalid Postal Code', better: 'lower' },
                        { key: 'invalid_rate_cons_evry', name: 'Evry - Overall Invalid Rate', better: 'lower' },
                        { key: 'pct_CSP_invalid_pop_paris', name: 'Paris Population - Invalid CSP', better: 'lower' },
                        { key: 'pct_address_invalid_pop_paris', name: 'Paris Population - Invalid Address', better: 'lower' },
                        { key: 'pct_CSP_invalid_pop_evry', name: 'Evry Population - Invalid CSP', better: 'lower' },
                        { key: 'pct_address_invalid_pop_evry', name: 'Evry Population - Invalid Address', better: 'lower' },
                        { key: 'pct_salary_invalid_csp', name: 'CSP - Invalid Salary', better: 'lower' }
                    ]
                },
                'distribution': {
                    name: 'Data Quality Distribution',
                    metrics: [
                        { key: 'tuples_below_50_cons_paris', name: 'Paris Consumption - Records <50% Quality', better: 'lower' },
                        { key: 'tuples_50_to_100_cons_paris', name: 'Paris Consumption - Records 50-100% Quality', better: 'lower' },
                        { key: 'tuples_100_cons_paris', name: 'Paris Consumption - Records 100% Quality', better: 'higher' },
                        { key: 'tuples_below_50_cons_evry', name: 'Evry Consumption - Records <50% Quality', better: 'lower' },
                        { key: 'tuples_50_to_100_cons_evry', name: 'Evry Consumption - Records 50-100% Quality', better: 'lower' },
                        { key: 'tuples_100_cons_evry', name: 'Evry Consumption - Records 100% Quality', better: 'higher' },
                        { key: 'tuples_below_50_pop_paris', name: 'Paris Population - Records <50% Quality', better: 'lower' },
                        { key: 'tuples_50_to_100_pop_paris', name: 'Paris Population - Records 50-100% Quality', better: 'lower' },
                        { key: 'tuples_100_pop_paris', name: 'Paris Population - Records 100% Quality', better: 'higher' },
                        { key: 'tuples_below_50_pop_evry', name: 'Evry Population - Records <50% Quality', better: 'lower' },
                        { key: 'tuples_50_to_100_pop_evry', name: 'Evry Population - Records 50-100% Quality', better: 'lower' },
                        { key: 'tuples_100_pop_evry', name: 'Evry Population - Records 100% Quality', better: 'higher' }
                    ]
                },
                'rowcounts': {
                    name: 'Row Counts & Valid Records',
                    metrics: [
                        { key: 'total_rows_cons_paris', name: 'Paris Consumption - Total Rows', better: 'higher' },
                        { key: 'valid_rows_cons_paris', name: 'Paris Consumption - Valid Rows', better: 'higher' },
                        { key: 'total_rows_cons_evry', name: 'Evry Consumption - Total Rows', better: 'higher' },
                        { key: 'valid_rows_cons_evry', name: 'Evry Consumption - Valid Rows', better: 'higher' },
                        { key: 'total_rows_pop_paris', name: 'Paris Population - Total Rows', better: 'higher' },
                        { key: 'total_rows_pop_evry', name: 'Evry Population - Total Rows', better: 'higher' },
                        { key: 'total_rows_csp', name: 'CSP - Total Rows', better: 'higher' }
                    ]
                }
            };
            
            Object.entries(metricCategories).forEach(([category, info]) => {
                info.metrics.forEach(metric => {
                    const rawValue = data.raw[metric.key] || 0;
                    const cleanedValue = data.cleaned[metric.key] || 0;
                    const diff = cleanedValue - rawValue;
                    
                    let status = 'neutral';
                    if (metric.better === 'higher') {
                        status = diff > 0.1 ? 'improvement' : diff < -0.1 ? 'regression' : 'neutral';
                    } else {
                        status = diff < -0.1 ? 'improvement' : diff > 0.1 ? 'regression' : 'neutral';
                    }
                    
                    allMetricsData.push({
                        category: category,
                        categoryName: info.name,
                        name: metric.name,
                        raw: rawValue,
                        cleaned: cleanedValue,
                        diff: diff,
                        status: status,
                        better: metric.better
                    });
                });
            });
            
            renderMetricsTable();
        }
        
        function renderMetricsTable() {
            const tbody = document.getElementById('metricsTableBody');
            const filtered = currentFilter === 'all' 
                ? allMetricsData 
                : allMetricsData.filter(m => m.category === currentFilter);
            
            let currentCategory = '';
            tbody.innerHTML = filtered.map(metric => {
                let categoryRow = '';
                if (metric.categoryName !== currentCategory) {
                    currentCategory = metric.categoryName;
                    categoryRow = `
                        <tr style="background: #f8f9fa;">
                            <td colspan="5" class="metric-category">${currentCategory}</td>
                        </tr>
                    `;
                }
                
                const statusEmoji = {
                    'improvement': '✅',
                    'regression': '⚠️',
                    'neutral': '➖'
                };
                
                return categoryRow + `
                    <tr>
                        <td class="metric-name">${metric.name}</td>
                        <td class="metric-value-cell">${metric.raw.toFixed(2)}%</td>
                        <td class="metric-value-cell">${metric.cleaned.toFixed(2)}%</td>
                        <td class="metric-diff ${metric.status}">
                            ${metric.diff > 0 ? '+' : ''}${metric.diff.toFixed(2)}%
                        </td>
                        <td style="text-align: center; font-size: 20px;">
                            ${statusEmoji[metric.status]}
                        </td>
                    </tr>
                `;
            }).join('');
        }
        
        function filterMetrics(category) {
            currentFilter = category;
            
            // Update tab styles
            document.querySelectorAll('.filter-tab').forEach(tab => {
                tab.classList.remove('active');
            });
            event.target.classList.add('active');
            
            renderMetricsTable();
        }
        
        function displayComparison(data) {
            // Top 10 most improved metrics
            const improvements = [];
            Object.keys(data.raw).filter(k => k.startsWith('pct_')).forEach(key => {
                const raw = data.raw[key] || 0;
                const cleaned = data.cleaned[key] || 0;
                const diff = Math.abs(cleaned - raw);
                improvements.push({ key, raw, cleaned, diff });
            });
            
            improvements.sort((a, b) => b.diff - a.diff);
            const top10 = improvements.slice(0, 10);
            
            const trace1 = {
                x: top10.map(m => m.key.replace('pct_', '').replace(/_/g, ' ')),
                y: top10.map(m => m.raw),
                name: 'Raw Data',
                type: 'bar',
                marker: { color: '#e74c3c' }
            };
            
            const trace2 = {
                x: top10.map(m => m.key.replace('pct_', '').replace(/_/g, ' ')),
                y: top10.map(m => m.cleaned),
                name: 'Cleaned Data',
                type: 'bar',
                marker: { color: '#27ae60' }
            };
            
            const layout = {
                title: 'Top 10 Improved Metrics',
                barmode: 'group',
                xaxis: { tickangle: -45 },
                yaxis: { title: 'Percentage (%)' },
                height: 400,
                showlegend: true
            };
            
            Plotly.newPlot('comparisonChart', [trace1, trace2], layout);
            
            // Category-wise improvement
            displayCategoryChart(data);
            
            // Heatmap of all metrics
            displayHeatmap(data);
            
            // Radar chart for completeness
            displayRadarChart(data);
        }
        
        function displayCategoryChart(data) {
            const categories = {
                'Completeness': ['complete'],
                'Validity': ['invalid', 'negative'],
                'Duplicates': ['duplicates'],
                'Consistency': ['consistent']
            };
            
            const categoryScores = {};
            Object.entries(categories).forEach(([cat, keywords]) => {
                const metrics = Object.keys(data.raw).filter(k => 
                    keywords.some(kw => k.includes(kw))
                );
                
                const rawAvg = metrics.reduce((sum, k) => sum + (data.raw[k] || 0), 0) / metrics.length;
                const cleanedAvg = metrics.reduce((sum, k) => sum + (data.cleaned[k] || 0), 0) / metrics.length;
                
                categoryScores[cat] = { raw: rawAvg, cleaned: cleanedAvg };
            });
            
            const trace1 = {
                x: Object.keys(categoryScores),
                y: Object.values(categoryScores).map(v => v.raw),
                name: 'Raw Data',
                type: 'bar',
                marker: { color: '#e74c3c' }
            };
            
            const trace2 = {
                x: Object.keys(categoryScores),
                y: Object.values(categoryScores).map(v => v.cleaned),
                name: 'Cleaned Data',
                type: 'bar',
                marker: { color: '#27ae60' }
            };
            
            const layout = {
                title: 'Category-wise Quality Score',
                barmode: 'group',
                yaxis: { title: 'Average Score (%)' },
                height: 400
            };
            
            Plotly.newPlot('categoryChart', [trace1, trace2], layout);
        }
        
        function displayHeatmap(data) {
            const tables = ['paris', 'evry', 'csp', 'iris', 'pop'];
            const dimensions = ['complete', 'invalid', 'duplicates', 'consistent', 'negative'];
            
            const zData = [];
            const yLabels = [];
            
            tables.forEach(table => {
                dimensions.forEach(dim => {
                    const key = Object.keys(data.cleaned).find(k => 
                        k.includes(table) && k.includes(dim)
                    );
                    
                    if (key) {
                        const improvement = Math.abs((data.cleaned[key] || 0) - (data.raw[key] || 0));
                        zData.push([improvement]);
                        yLabels.push(`${table.toUpperCase()} - ${dim}`);
                    }
                });
            });
            
            const trace = {
                z: zData,
                y: yLabels,
                x: ['Improvement'],
                type: 'heatmap',
                colorscale: [
                    [0, '#ecf0f1'],
                    [0.5, '#f39c12'],
                    [1, '#27ae60']
                ],
                hovertemplate: '%{y}<br>Improvement: %{z:.2f}%<extra></extra>'
            };
            
            const layout = {
                title: 'Improvement Heatmap by Dimension',
                height: 500,
                yaxis: { tickfont: { size: 10 } }
            };
            
            Plotly.newPlot('heatmapChart', [trace], layout);
        }
        
        function displayRadarChart(data) {
            const completenessMetrics = Object.keys(data.raw)
                .filter(k => k.includes('complete'))
                .slice(0, 8);
            
            const trace1 = {
                type: 'scatterpolar',
                r: completenessMetrics.map(k => data.raw[k] || 0),
                theta: completenessMetrics.map(k => k.replace('pct_complete_', '').replace(/_/g, ' ')),
                fill: 'toself',
                name: 'Raw Data',
                marker: { color: '#e74c3c' }
            };
            
            const trace2 = {
                type: 'scatterpolar',
                r: completenessMetrics.map(k => data.cleaned[k] || 0),
                theta: completenessMetrics.map(k => k.replace('pct_complete_', '').replace(/_/g, ' ')),
                fill: 'toself',
                name: 'Cleaned Data',
                marker: { color: '#27ae60' }
            };
            
            const layout = {
                title: 'Completeness Metrics Radar',
                polar: {
                    radialaxis: {
                        visible: true,
                        range: [0, 100]
                    }
                },
                height: 500
            };
            
            Plotly.newPlot('radarChart', [trace1, trace2], layout);
        }
        
        // Initial load
        loadMetrics();
    </script>
</body>
</html>
    """
    return render_template_string(html)


@app.route('/api/start-pipeline', methods=['POST'])
def start_pipeline():
    """Start the data quality pipeline"""
    global pipeline_state
    
    if pipeline_state['running']:
        return jsonify({'error': 'Pipeline already running'}), 400
    
    # Reset state
    for task in pipeline_state['tasks']:
        task['status'] = 'pending'
        task['progress'] = 0
    
    # Start pipeline in background thread
    thread = threading.Thread(target=run_pipeline, daemon=True)
    thread.start()
    
    return jsonify({'status': 'started', 'message': 'Pipeline execution started'})


@app.route('/api/pipeline-status')
def get_pipeline_status():
    """Get current pipeline execution status"""
    return jsonify(pipeline_state)


@app.route('/api/metrics')
def get_metrics():
    """Get current metrics data"""
    raw_metrics = load_metrics_data('raw')
    cleaned_metrics = load_metrics_data('cleaned')
    
    return jsonify({
        'raw': raw_metrics,
        'cleaned': cleaned_metrics,
        'timestamp': datetime.now().isoformat()
    })


if __name__ == '__main__':
    print("=" * 60)
    print("🚀 DATA QUALITY PIPELINE DASHBOARD")
    print("=" * 60)
    print(f"\n📊 Dashboard URL: http://localhost:5000")
    print(f"📁 Base Path: {BASE_PATH}")
    print(f"📈 Metadata Dir: {METADATA_DIR}")
    print("\n✨ Features:")
    print("  - Launch pipeline with one click")
    print("  - Real-time task progress tracking")
    print("  - Live metrics updates")
    print("  - Interactive visualizations")
    print("\n" + "=" * 60)
    print("Press Ctrl+C to stop the server")
    print("=" * 60 + "\n")
    
    app.run(debug=True, host='0.0.0.0', port=5000, use_reloader=False)
