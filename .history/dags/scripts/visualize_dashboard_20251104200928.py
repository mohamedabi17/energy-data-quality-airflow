"""
Data Quality Dashboard
Interactive visualization of data quality metrics across pipeline stages.
Run this script to launch a web-based dashboard (no Docker required).
"""

import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import os
from pathlib import Path
from datetime import datetime


def load_latest_metrics(metadata_dir):
    """Load latest metrics for all available stages."""
    stages = {}
    
    for stage_name in ['raw', 'cleaned', 'aggregated']:
        latest_file = os.path.join(metadata_dir, f'metadata_qd_{stage_name}_latest.csv')
        if os.path.exists(latest_file):
            try:
                df = pd.read_csv(latest_file, sep=';')
                if len(df) > 0:
                    stages[stage_name] = df.iloc[0].to_dict()
            except Exception as e:
                print(f"Warning: Could not load {stage_name} metrics: {e}")
    
    return stages


def create_comparison_chart(stages_data):
    """Create comparison bar chart for key metrics across stages."""
    
    # Key metrics to visualize
    metrics = [
        ('pct_CP_invalid_cons_paris', 'Invalid Postal Codes - Paris'),
        ('pct_NB_KW_Jour_invalid_cons_paris', 'Invalid Consumption - Paris'),
        ('pct_invalid_kw_cons_paris_unit', 'Unit Errors - Paris'),
        ('pct_CP_invalid_cons_evry', 'Invalid Postal Codes - Evry'),
        ('pct_address_invalid_pop_paris', 'Invalid Addresses - Pop Paris'),
        ('pct_address_invalid_pop_evry', 'Invalid Addresses - Pop Evry'),
        ('pct_CSP_invalid_pop_evry', 'Invalid CSP - Pop Evry'),
        ('completeness_salaire_csp', 'Salary Completeness - CSP'),
    ]
    
    fig = go.Figure()
    
    for stage_name, stage_data in stages_data.items():
        values = []
        labels = []
        
        for metric_key, metric_label in metrics:
            if metric_key in stage_data:
                values.append(float(stage_data[metric_key]))
                labels.append(metric_label)
        
        fig.add_trace(go.Bar(
            name=stage_name.upper(),
            x=labels,
            y=values,
            text=[f'{v:.1f}%' for v in values],
            textposition='outside',
        ))
    
    fig.update_layout(
        title='Data Quality Metrics Comparison Across Pipeline Stages',
        xaxis_title='Metric',
        yaxis_title='Percentage (%)',
        barmode='group',
        height=500,
        showlegend=True,
        xaxis={'tickangle': -45},
    )
    
    return fig


def create_improvement_gauge(stages_data):
    """Create gauge charts showing improvement from raw to cleaned."""
    
    if 'raw' not in stages_data or 'cleaned' not in stages_data:
        return None
    
    raw = stages_data['raw']
    cleaned = stages_data['cleaned']
    
    # Calculate overall improvement score
    improvement_metrics = [
        'pct_NB_KW_Jour_invalid_cons_paris',
        'pct_invalid_kw_cons_paris_unit',
        'pct_CP_invalid_cons_evry',
        'pct_CSP_invalid_pop_evry',
    ]
    
    improvements = []
    for metric in improvement_metrics:
        if metric in raw and metric in cleaned:
            raw_val = float(raw[metric])
            cleaned_val = float(cleaned[metric])
            if raw_val > 0:
                improvement = ((raw_val - cleaned_val) / raw_val) * 100
                improvements.append(improvement)
    
    avg_improvement = sum(improvements) / len(improvements) if improvements else 0
    
    fig = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=avg_improvement,
        domain={'x': [0, 1], 'y': [0, 1]},
        title={'text': "Overall Data Quality Improvement", 'font': {'size': 24}},
        delta={'reference': 0, 'suffix': '%'},
        gauge={
            'axis': {'range': [None, 100], 'ticksuffix': '%'},
            'bar': {'color': "darkgreen"},
            'steps': [
                {'range': [0, 25], 'color': "lightgray"},
                {'range': [25, 50], 'color': "lightyellow"},
                {'range': [50, 75], 'color': "lightgreen"},
                {'range': [75, 100], 'color': "green"}
            ],
            'threshold': {
                'line': {'color': "red", 'width': 4},
                'thickness': 0.75,
                'value': 90
            }
        }
    ))
    
    fig.update_layout(height=400)
    
    return fig


def create_completeness_radar(stages_data):
    """Create radar chart for completeness metrics."""
    
    completeness_metrics = [
        ('completeness_cons_evry', 'Cons Evry'),
        ('completeness_cons_paris', 'Cons Paris'),
        ('completeness_pop_paris', 'Pop Paris'),
        ('completeness_pop_evry', 'Pop Evry'),
        ('completeness_csp', 'CSP'),
    ]
    
    fig = go.Figure()
    
    for stage_name, stage_data in stages_data.items():
        values = []
        labels = []
        
        for metric_key, metric_label in completeness_metrics:
            if metric_key in stage_data:
                values.append(float(stage_data[metric_key]))
                labels.append(metric_label)
        
        # Close the radar chart
        if values:
            values.append(values[0])
            labels.append(labels[0])
            
            fig.add_trace(go.Scatterpolar(
                r=values,
                theta=labels,
                fill='toself',
                name=stage_name.upper()
            ))
    
    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 100]
            )
        ),
        showlegend=True,
        title='Data Completeness Across Tables',
        height=500,
    )
    
    return fig


def create_row_count_chart(stages_data):
    """Create bar chart showing row counts per table."""
    
    if not stages_data:
        return None
    
    # Use the first available stage
    stage_data = list(stages_data.values())[0]
    
    tables = {
        'Consommation Evry': stage_data.get('total_rows_cons_evry', 0),
        'Consommation Paris': stage_data.get('total_rows_cons_paris', 0),
        'Population Paris': stage_data.get('total_rows_pop_paris', 0),
        'Population Evry': stage_data.get('total_rows_pop_evry', 0),
        'CSP': stage_data.get('total_rows_csp', 0),
    }
    
    fig = go.Figure(data=[
        go.Bar(
            x=list(tables.keys()),
            y=list(tables.values()),
            text=list(tables.values()),
            textposition='outside',
            marker_color='steelblue'
        )
    ])
    
    fig.update_layout(
        title='Row Counts Per Table',
        xaxis_title='Table',
        yaxis_title='Number of Rows',
        height=400,
    )
    
    return fig


def create_invalid_rate_heatmap(stages_data):
    """Create heatmap showing invalid rates across tables and stages."""
    
    metrics_map = {
        'Cons Paris - Postal Code': 'pct_CP_invalid_cons_paris',
        'Cons Paris - Consumption': 'pct_NB_KW_Jour_invalid_cons_paris',
        'Cons Paris - Unit Error': 'pct_invalid_kw_cons_paris_unit',
        'Cons Evry - Postal Code': 'pct_CP_invalid_cons_evry',
        'Pop Paris - Address': 'pct_address_invalid_pop_paris',
        'Pop Paris - CSP': 'pct_CSP_invalid_pop_paris',
        'Pop Evry - Address': 'pct_address_invalid_pop_evry',
        'Pop Evry - CSP': 'pct_CSP_invalid_pop_evry',
    }
    
    # Build matrix
    stages = list(stages_data.keys())
    metrics = list(metrics_map.keys())
    
    z_data = []
    for metric_label in metrics:
        metric_key = metrics_map[metric_label]
        row = []
        for stage in stages:
            value = float(stages_data[stage].get(metric_key, 0))
            row.append(value)
        z_data.append(row)
    
    fig = go.Figure(data=go.Heatmap(
        z=z_data,
        x=[s.upper() for s in stages],
        y=metrics,
        colorscale='RdYlGn_r',  # Red for high invalid, green for low
        text=[[f'{val:.1f}%' for val in row] for row in z_data],
        texttemplate='%{text}',
        textfont={"size": 10},
        colorbar=dict(title='Invalid %'),
    ))
    
    fig.update_layout(
        title='Invalid Rates Heatmap (Red=Bad, Green=Good)',
        xaxis_title='Pipeline Stage',
        yaxis_title='Metric',
        height=500,
    )
    
    return fig


def generate_html_dashboard(metadata_dir, output_file='dashboard.html'):
    """Generate standalone HTML dashboard."""
    
    print("Loading metrics data...")
    stages_data = load_latest_metrics(metadata_dir)
    
    if not stages_data:
        print("❌ No metrics data found!")
        return
    
    print(f"✓ Loaded metrics for stages: {', '.join(stages_data.keys())}")
    
    # Create all visualizations
    print("\nGenerating visualizations...")
    
    fig1 = create_comparison_chart(stages_data)
    fig2 = create_improvement_gauge(stages_data)
    fig3 = create_completeness_radar(stages_data)
    fig4 = create_row_count_chart(stages_data)
    fig5 = create_invalid_rate_heatmap(stages_data)
    
    # Create HTML with all charts
    html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Data Quality Dashboard</title>
    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
    <style>
        body {{
            font-family: Arial, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
        }}
        .header {{
            background-color: #2c3e50;
            color: white;
            padding: 20px;
            border-radius: 5px;
            margin-bottom: 20px;
        }}
        .header h1 {{
            margin: 0;
            font-size: 32px;
        }}
        .header p {{
            margin: 10px 0 0 0;
            font-size: 14px;
            opacity: 0.8;
        }}
        .stats {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin-bottom: 20px;
        }}
        .stat-card {{
            background: white;
            padding: 20px;
            border-radius: 5px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .stat-card h3 {{
            margin: 0 0 10px 0;
            font-size: 14px;
            color: #666;
            text-transform: uppercase;
        }}
        .stat-card .value {{
            font-size: 28px;
            font-weight: bold;
            color: #2c3e50;
        }}
        .chart {{
            background: white;
            padding: 20px;
            border-radius: 5px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            margin-bottom: 20px;
        }}
        .footer {{
            text-align: center;
            margin-top: 30px;
            color: #666;
            font-size: 12px;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>📊 Data Quality Dashboard</h1>
        <p>Interactive visualization of data quality metrics across pipeline stages</p>
        <p>Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
    </div>
    
    <div class="stats">
        <div class="stat-card">
            <h3>Pipeline Stages</h3>
            <div class="value">{len(stages_data)}</div>
        </div>
        <div class="stat-card">
            <h3>Total Tables</h3>
            <div class="value">5</div>
        </div>
        <div class="stat-card">
            <h3>Total Metrics</h3>
            <div class="value">40+</div>
        </div>
        <div class="stat-card">
            <h3>Data Sources</h3>
            <div class="value">Paris + Evry</div>
        </div>
    </div>
    
    <div class="chart" id="chart1"></div>
    <div class="chart" id="chart2"></div>
    <div class="chart" id="chart3"></div>
    <div class="chart" id="chart4"></div>
    <div class="chart" id="chart5"></div>
    
    <div class="footer">
        <p>Data Quality Dashboard - Airflow Pipeline Project</p>
        <p>Path: {metadata_dir}</p>
    </div>
    
    <script>
        {fig1.to_html(include_plotlyjs=False, div_id='chart1').split('<div')[1].split('</div>')[0].replace('id="chart1"', '')}
        Plotly.newPlot('chart1', {fig1.to_json()}.split('"data":')[1].split(',"layout"')[0], {fig1.to_json()}.split('"layout":')[1].split(',"config"')[0]);
        
        {fig2.to_html(include_plotlyjs=False, div_id='chart2').split('<div')[1].split('</div>')[0].replace('id="chart2"', '') if fig2 else ''}
        {'Plotly.newPlot("chart2", ' + fig2.to_json().split('"data":')[1].split(',"layout"')[0] + ', ' + fig2.to_json().split('"layout":')[1].split(',"config"')[0] + ');' if fig2 else ''}
        
        Plotly.newPlot('chart3', {fig3.to_json()}.split('"data":')[1].split(',"layout"')[0], {fig3.to_json()}.split('"layout":')[1].split(',"config"')[0]);
        
        {'' if not fig4 else 'Plotly.newPlot("chart4", ' + fig4.to_json().split('"data":')[1].split(',"layout"')[0] + ', ' + fig4.to_json().split('"layout":')[1].split(',"config"')[0] + ');'}
        
        Plotly.newPlot('chart5', {fig5.to_json()}.split('"data":')[1].split(',"layout"')[0], {fig5.to_json().split('"layout":')[1].split(',"config"')[0]);
    </script>
</body>
</html>
"""
    
    # Write HTML file
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"\n✓ Dashboard generated: {output_file}")
    print(f"\nTo view the dashboard:")
    print(f"  1. Open in browser: {os.path.abspath(output_file)}")
    print(f"  2. Or run: start {output_file}")


def main():
    """Main function to generate dashboard."""
    script_dir = Path(__file__).parent
    base_path = script_dir.parent.parent
    metadata_dir = os.path.join(base_path, 'metadata')
    output_file = os.path.join(base_path, 'dashboard.html')
    
    print("="*60)
    print("DATA QUALITY DASHBOARD GENERATOR")
    print("="*60)
    
    generate_html_dashboard(metadata_dir, output_file)
    
    # Auto-open in browser
    import webbrowser
    print(f"\n🌐 Opening dashboard in browser...")
    webbrowser.open('file://' + os.path.abspath(output_file))


if __name__ == '__main__':
    main()
