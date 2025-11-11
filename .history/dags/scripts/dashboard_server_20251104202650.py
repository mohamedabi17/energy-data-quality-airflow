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
        
        <div class="chart-container">
            <div id="comparisonChart"></div>
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
        }
        
        function displayComparison(data) {
            const metrics = Object.keys(data.raw).filter(k => k.startsWith('pct_')).slice(0, 10);
            
            const trace1 = {
                x: metrics.map(m => m.replace('pct_', '').replace(/_/g, ' ')),
                y: metrics.map(m => data.raw[m] || 0),
                name: 'Raw Data',
                type: 'bar',
                marker: { color: '#e74c3c' }
            };
            
            const trace2 = {
                x: metrics.map(m => m.replace('pct_', '').replace(/_/g, ' ')),
                y: metrics.map(m => data.cleaned[m] || 0),
                name: 'Cleaned Data',
                type: 'bar',
                marker: { color: '#27ae60' }
            };
            
            const layout = {
                title: 'Data Quality Metrics Comparison',
                barmode: 'group',
                xaxis: { tickangle: -45 },
                yaxis: { title: 'Percentage (%)' },
                height: 500
            };
            
            Plotly.newPlot('comparisonChart', [trace1, trace2], layout);
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
