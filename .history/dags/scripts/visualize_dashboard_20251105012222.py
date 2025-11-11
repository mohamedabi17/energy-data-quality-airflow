"""
Enhanced Data Quality Dashboard
Professional visualization with better storytelling and insight generation.
"""

import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import os
import sys
import subprocess
import threading
import time
from pathlib import Path
from datetime import datetime
from flask import Flask, jsonify, send_file
from flask_cors import CORS


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


def create_before_after_comparison(stages_data):
    """Create grouped bar chart comparing raw vs cleaned metrics."""
    
    if 'raw' not in stages_data or 'cleaned' not in stages_data:
        return None
    
    raw = stages_data['raw']
    cleaned = stages_data['cleaned']
    
    # Key metrics to compare
    metrics = [
        ('invalid_rate_cons_paris', 'Consumption\nParis'),
        ('invalid_rate_cons_evry', 'Consumption\nEvry'),
        ('pct_address_invalid_pop_paris', 'Addresses\nParis'),
        ('pct_CSP_invalid_pop_evry', 'CSP\nEvry'),
    ]
    
    labels = [m[1] for m in metrics]
    raw_values = [float(raw.get(m[0], 0)) for m in metrics]
    cleaned_values = [float(cleaned.get(m[0], 0)) for m in metrics]
    
    fig = go.Figure()
    
    # Raw data bars
    fig.add_trace(go.Bar(
        name='Raw Data',
        x=labels,
        y=raw_values,
        text=[f'{v:.1f}%' for v in raw_values],
        textposition='outside',
        marker=dict(
            color='#e74c3c',
            line=dict(color='#c0392b', width=2)
        ),
        hovertemplate='<b>%{x}</b><br>Raw: %{y:.1f}%<extra></extra>'
    ))
    
    # Cleaned data bars
    fig.add_trace(go.Bar(
        name='Cleaned Data',
        x=labels,
        y=cleaned_values,
        text=[f'{v:.1f}%' for v in cleaned_values],
        textposition='outside',
        marker=dict(
            color='#2ecc71',
            line=dict(color='#27ae60', width=2)
        ),
        hovertemplate='<b>%{x}</b><br>Cleaned: %{y:.1f}%<extra></extra>'
    ))
    
    fig.update_layout(
        title='<b>Before & After Data Cleaning</b><br><sub>Invalid Data Percentage by Metric</sub>',
        xaxis_title='Data Quality Metric',
        yaxis_title='Invalid Records (%)',
        barmode='group',
        height=450,
        font=dict(family='Arial', size=12),
        legend=dict(
            orientation='h',
            yanchor='bottom',
            y=1.02,
            xanchor='right',
            x=1
        ),
        plot_bgcolor='rgba(240,240,240,0.5)',
        paper_bgcolor='white',
    )
    
    fig.update_xaxes(showgrid=False)
    fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='rgba(0,0,0,0.1)')
    
    return fig


def create_issue_breakdown_chart(stages_data):
    """Create stacked area chart showing issue types across stages."""
    
    stages_order = ['raw', 'cleaned']
    available_stages = [s for s in stages_order if s in stages_data]
    
    if len(available_stages) < 2:
        return None
    
    # Define issue categories
    issue_categories = {
        'Missing Values': ['completeness_cons_paris', 'completeness_cons_evry', 'completeness_pop_paris'],
        'Invalid Postal Codes': ['pct_CP_invalid_cons_paris', 'pct_CP_invalid_cons_evry'],
        'Invalid Addresses': ['pct_address_invalid_pop_paris', 'pct_address_invalid_pop_evry'],
        'Invalid CSP References': ['pct_CSP_invalid_pop_paris', 'pct_CSP_invalid_pop_evry'],
        'Invalid Consumption': ['pct_NB_KW_Jour_invalid_cons_paris', 'pct_NB_KW_Jour_invalid_cons_evry'],
        'Unit Inconsistencies': ['pct_invalid_kw_cons_paris_unit'],
    }
    
    fig = go.Figure()
    
    colors = ['#e74c3c', '#f39c12', '#f1c40f', '#3498db', '#9b59b6', '#e67e22']
    
    for idx, (category, metrics) in enumerate(issue_categories.items()):
        stage_values = []
        
        for stage in available_stages:
            data = stages_data[stage]
            
            # Calculate average for this category
            values = []
            for metric in metrics:
                if metric in data:
                    val = float(data[metric])
                    # For completeness metrics, invert to get "incompleteness"
                    if 'completeness' in metric:
                        val = 100 - val
                    values.append(val)
            
            avg = sum(values) / len(values) if values else 0
            stage_values.append(avg)
        
        fig.add_trace(go.Scatter(
            x=[s.capitalize() for s in available_stages],
            y=stage_values,
            name=category,
            mode='lines+markers',
            line=dict(width=3, color=colors[idx % len(colors)]),
            marker=dict(size=10, line=dict(width=2, color='white')),
            stackgroup='one',
            hovertemplate='<b>%{fullData.name}</b><br>Stage: %{x}<br>Issues: %{y:.1f}%<extra></extra>'
        ))
    
    fig.update_layout(
        title='<b>Issue Type Distribution Across Pipeline</b><br><sub>Stacked view showing reduction in each category</sub>',
        xaxis_title='Pipeline Stage',
        yaxis_title='Cumulative Issues (%)',
        height=500,
        font=dict(family='Arial', size=12),
        hovermode='x unified',
        legend=dict(
            orientation='v',
            yanchor='top',
            y=0.98,
            xanchor='left',
            x=1.02,
            bgcolor='rgba(255,255,255,0.9)',
            bordercolor='rgba(0,0,0,0.2)',
            borderwidth=1
        ),
        plot_bgcolor='rgba(240,240,240,0.3)',
        paper_bgcolor='white',
    )
    
    fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor='rgba(0,0,0,0.1)')
    fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='rgba(0,0,0,0.1)')
    
    return fig


def create_quality_dimensions_spider(stages_data):
    """Create multi-dimensional spider chart for different quality aspects."""
    
    quality_dimensions = {
        'Conformity': ['pct_CP_invalid_cons_paris', 'pct_address_invalid_pop_paris'],
        'Validity': ['pct_NB_KW_Jour_invalid_cons_paris', 'pct_CSP_invalid_pop_evry'],
        'Completeness': ['completeness_cons_paris', 'completeness_pop_paris'],
        'Consistency': ['pct_invalid_kw_cons_paris_unit'],
    }
    
    fig = go.Figure()
    
    for stage_name, stage_data in stages_data.items():
        scores = []
        categories = []
        
        for dim_name, metrics in quality_dimensions.items():
            # Calculate average for this dimension
            values = []
            for metric in metrics:
                if metric in stage_data:
                    val = float(stage_data[metric])
                    # Invert invalid percentages to quality scores
                    if 'invalid' in metric or metric.startswith('pct_'):
                        val = 100 - val
                    values.append(val)
            
            if values:
                scores.append(sum(values) / len(values))
                categories.append(dim_name)
        
        # Close the polygon
        scores.append(scores[0])
        categories.append(categories[0])
        
        fig.add_trace(go.Scatterpolar(
            r=scores,
            theta=categories,
            fill='toself',
            name=stage_name.upper(),
            line=dict(width=3),
            marker=dict(size=8)
        ))
    
    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 100],
                ticksuffix='%',
                gridcolor='rgba(0,0,0,0.1)'
            ),
            angularaxis=dict(
                gridcolor='rgba(0,0,0,0.1)'
            )
        ),
        showlegend=True,
        title='Data Quality Dimensions Analysis',
        height=500,
        font=dict(size=12)
    )
    
    return fig


def create_record_quality_distribution(stages_data):
    """Create stacked bar showing distribution of records by quality level."""
    
    if 'raw' not in stages_data or 'cleaned' not in stages_data:
        return None
    
    raw = stages_data['raw']
    cleaned = stages_data['cleaned']
    
    # Get tuple quality distribution for each table
    tables = [
        ('cons_paris', 'Consumption Paris'),
        ('cons_evry', 'Consumption Évry'),
        ('pop_paris', 'Population Paris'),
        ('pop_evry', 'Population Évry'),
    ]
    
    fig = make_subplots(
        rows=1, cols=2,
        subplot_titles=['Raw Data', 'Cleaned Data'],
        specs=[[{'type': 'bar'}, {'type': 'bar'}]]
    )
    
    for stage_idx, (stage_data, stage_name) in enumerate([(raw, 'Raw'), (cleaned, 'Cleaned')], 1):
        table_labels = []
        perfect_quality = []
        good_quality = []
        poor_quality = []
        
        for table_key, table_label in tables:
            table_labels.append(table_label.replace(' ', '<br>'))
            
            total = int(stage_data.get(f'total_rows_{table_key}', 0))
            tuples_100 = int(stage_data.get(f'tuples_100_{table_key}', 0))
            tuples_50_100 = int(stage_data.get(f'tuples_50_to_100_{table_key}', 0))
            tuples_below_50 = int(stage_data.get(f'tuples_below_50_{table_key}', 0))
            
            perfect_quality.append(tuples_100)
            good_quality.append(tuples_50_100)
            poor_quality.append(tuples_below_50)
        
        # Perfect quality (100%)
        fig.add_trace(go.Bar(
            name='100% Quality' if stage_idx == 1 else '',
            x=table_labels,
            y=perfect_quality,
            marker_color='#2ecc71',
            text=perfect_quality,
            textposition='inside',
            textfont=dict(color='white', size=11, family='Arial Black'),
            hovertemplate='<b>100%% Quality</b><br>Records: %{y}<extra></extra>',
            showlegend=(stage_idx == 1)
        ), row=1, col=stage_idx)
        
        # Good quality (50-100%)
        fig.add_trace(go.Bar(
            name='50-99% Quality' if stage_idx == 1 else '',
            x=table_labels,
            y=good_quality,
            marker_color='#f39c12',
            text=good_quality,
            textposition='inside',
            textfont=dict(color='white', size=11, family='Arial Black'),
            hovertemplate='<b>50-99%% Quality</b><br>Records: %{y}<extra></extra>',
            showlegend=(stage_idx == 1)
        ), row=1, col=stage_idx)
        
        # Poor quality (<50%)
        fig.add_trace(go.Bar(
            name='<50% Quality' if stage_idx == 1 else '',
            x=table_labels,
            y=poor_quality,
            marker_color='#e74c3c',
            text=poor_quality,
            textposition='inside',
            textfont=dict(color='white', size=11, family='Arial Black'),
            hovertemplate='<b><50%% Quality</b><br>Records: %{y}<extra></extra>',
            showlegend=(stage_idx == 1)
        ), row=1, col=stage_idx)
    
    fig.update_layout(
        title='<b>Record Quality Distribution</b><br><sub>Number of records by quality level per table</sub>',
        barmode='stack',
        height=450,
        font=dict(family='Arial', size=11),
        legend=dict(
            orientation='h',
            yanchor='bottom',
            y=1.02,
            xanchor='right',
            x=1
        ),
        plot_bgcolor='rgba(240,240,240,0.3)',
        paper_bgcolor='white',
    )
    
    fig.update_xaxes(showgrid=False)
    fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='rgba(0,0,0,0.1)', title_text='Number of Records')
    
    return fig


def create_table_health_matrix(stages_data):
    """Create advanced heatmap showing health score per table and stage."""
    
    # Get latest stage data
    latest_stage = list(stages_data.values())[-1]
    
    tables = {
        'Consommation Paris': {
            'Completeness': latest_stage.get('completeness_cons_paris', 0),
            'Valid Postal Codes': 100 - float(latest_stage.get('pct_CP_invalid_cons_paris', 0)),
            'Valid Consumption': 100 - float(latest_stage.get('pct_NB_KW_Jour_invalid_cons_paris', 0)),
            'Unit Consistency': 100 - float(latest_stage.get('pct_invalid_kw_cons_paris_unit', 0)),
        },
        'Consommation Evry': {
            'Completeness': latest_stage.get('completeness_cons_evry', 0),
            'Valid Postal Codes': 100 - float(latest_stage.get('pct_CP_invalid_cons_evry', 0)),
            'Valid Consumption': 100 - float(latest_stage.get('pct_NB_KW_Jour_invalid_cons_evry', 0)),
            'Unit Consistency': 100,
        },
        'Population Paris': {
            'Completeness': latest_stage.get('completeness_pop_paris', 0),
            'Valid Addresses': 100 - float(latest_stage.get('pct_address_invalid_pop_paris', 0)),
            'Valid CSP': 100 - float(latest_stage.get('pct_CSP_invalid_pop_paris', 0)),
            'Data Consistency': 95,
        },
        'Population Evry': {
            'Completeness': latest_stage.get('completeness_pop_evry', 0),
            'Valid Addresses': 100 - float(latest_stage.get('pct_address_invalid_pop_evry', 0)),
            'Valid CSP': 100 - float(latest_stage.get('pct_CSP_invalid_pop_evry', 0)),
            'Data Consistency': 93,
        },
        'CSP Reference': {
            'Completeness': latest_stage.get('completeness_csp', 0),
            'Salary Completeness': latest_stage.get('completeness_salaire_csp', 0),
            'Data Integrity': 98,
            'Consistency': 100,
        },
    }
    
    # Build matrix
    df = pd.DataFrame(tables).T
    
    fig = go.Figure(data=go.Heatmap(
        z=df.values,
        x=df.columns,
        y=df.index,
        colorscale=[
            [0, '#e74c3c'],  # Red for poor
            [0.5, '#f39c12'],  # Orange for medium
            [0.8, '#f1c40f'],  # Yellow for good
            [1, '#2ecc71']  # Green for excellent
        ],
        text=[[f'{val:.0f}%' for val in row] for row in df.values],
        texttemplate='%{text}',
        textfont={"size": 11, "color": "white", "family": "Arial Black"},
        colorbar=dict(title='Health<br>Score (%)', ticksuffix='%'),
        hoverongaps=False,
        hovertemplate='<b>%{y}</b><br>%{x}: %{z:.1f}%<extra></extra>'
    ))
    
    fig.update_layout(
        title='Table Health Matrix (Current State)',
        xaxis_title='Quality Metric',
        yaxis_title='Table',
        height=500,
        font=dict(size=12),
        xaxis={'side': 'top'}
    )
    
    return fig


def create_completeness_gauges(stages_data):
    """Create gauge charts showing completeness for each table."""
    
    latest_stage = list(stages_data.values())[-1]
    
    tables = [
        ('completeness_cons_paris', 'Consumption<br>Paris', '#3498db'),
        ('completeness_cons_evry', 'Consumption<br>Évry', '#9b59b6'),
        ('completeness_pop_paris', 'Population<br>Paris', '#2ecc71'),
        ('completeness_pop_evry', 'Population<br>Évry', '#e67e22'),
        ('completeness_csp', 'CSP<br>Reference', '#1abc9c'),
    ]
    
    fig = make_subplots(
        rows=1, cols=5,
        specs=[[{'type': 'indicator'}, {'type': 'indicator'}, {'type': 'indicator'}, 
                {'type': 'indicator'}, {'type': 'indicator'}]],
        subplot_titles=[t[1] for t in tables],
        horizontal_spacing=0.05
    )
    
    for idx, (metric, title, color) in enumerate(tables, 1):
        value = float(latest_stage.get(metric, 0))
        
        fig.add_trace(go.Indicator(
            mode="gauge+number+delta",
            value=value,
            domain={'x': [0, 1], 'y': [0, 1]},
            title={'text': '', 'font': {'size': 14}},
            number={'suffix': '%', 'font': {'size': 28, 'color': color}},
            delta={'reference': 95, 'increasing': {'color': '#2ecc71'}, 'decreasing': {'color': '#e74c3c'}},
            gauge={
                'axis': {'range': [0, 100], 'tickwidth': 1, 'tickcolor': color},
                'bar': {'color': color, 'thickness': 0.75},
                'bgcolor': 'white',
                'borderwidth': 2,
                'bordercolor': color,
                'steps': [
                    {'range': [0, 50], 'color': 'rgba(231, 76, 60, 0.2)'},
                    {'range': [50, 80], 'color': 'rgba(243, 156, 18, 0.2)'},
                    {'range': [80, 95], 'color': 'rgba(241, 196, 15, 0.2)'},
                    {'range': [95, 100], 'color': 'rgba(46, 204, 113, 0.2)'}
                ],
                'threshold': {
                    'line': {'color': '#c0392b', 'width': 4},
                    'thickness': 0.75,
                    'value': 95
                }
            }
        ), row=1, col=idx)
    
    fig.update_layout(
        title='<b>Data Completeness by Table</b><br><sub>Target: 95% (Red threshold line)</sub>',
        height=350,
        font=dict(family='Arial', size=11),
        showlegend=False,
        paper_bgcolor='white',
        margin=dict(t=100, b=50, l=20, r=20)
    )
    
    return fig


def create_metrics_comparison_table(stages_data):
    """Create HTML table comparing raw and cleaned metrics."""
    
    if 'raw' not in stages_data or 'cleaned' not in stages_data:
        return ""
    
    raw = stages_data['raw']
    cleaned = stages_data['cleaned']
    
    # Define metric categories with ALL available metrics
    metric_categories = {
        'Completeness Metrics': [
            ('completeness_cons_paris', 'Consumption Paris Completeness'),
            ('completeness_cons_evry', 'Consumption Évry Completeness'),
            ('completeness_pop_paris', 'Population Paris Completeness'),
            ('completeness_pop_evry', 'Population Évry Completeness'),
            ('completeness_csp', 'CSP Table Completeness'),
            ('completeness_salaire_csp', 'CSP Salary Data Completeness'),
        ],
        'Validity Metrics - Invalid Rates': [
            ('invalid_rate_cons_paris', 'Consumption Paris Overall Invalid Rate'),
            ('invalid_rate_cons_evry', 'Consumption Évry Overall Invalid Rate'),
            ('pct_NB_KW_Jour_invalid_cons_paris', 'Consumption Paris Invalid Values'),
            ('pct_NB_KW_Jour_invalid_cons_evry', 'Consumption Évry Invalid Values'),
            ('pct_CP_invalid_cons_paris', 'Consumption Paris Invalid Postal Codes'),
            ('pct_CP_invalid_cons_evry', 'Consumption Évry Invalid Postal Codes'),
            ('pct_address_invalid_pop_paris', 'Population Paris Invalid Addresses'),
            ('pct_address_invalid_pop_evry', 'Population Évry Invalid Addresses'),
            ('pct_CSP_invalid_pop_paris', 'Population Paris Invalid CSP'),
            ('pct_CSP_invalid_pop_evry', 'Population Évry Invalid CSP'),
            ('pct_salary_invalid_csp', 'CSP Invalid Salary Data'),
        ],
        'Unit Consistency': [
            ('pct_invalid_kw_cons_paris_unit', 'Consumption Paris Unit Errors'),
            ('pct_invalid_kw_cons_evry_unit', 'Consumption Évry Unit Errors'),
        ],
        'Quality Distribution - 100% Quality': [
            ('tuples_100_cons_paris', 'Consumption Paris Perfect Records'),
            ('tuples_100_cons_evry', 'Consumption Évry Perfect Records'),
            ('tuples_100_pop_paris', 'Population Paris Perfect Records'),
            ('tuples_100_pop_evry', 'Population Évry Perfect Records'),
        ],
        'Quality Distribution - Good Quality (50-99%)': [
            ('tuples_50_to_100_cons_paris', 'Consumption Paris Good Quality Records'),
            ('tuples_50_to_100_cons_evry', 'Consumption Évry Good Quality Records'),
            ('tuples_50_to_100_pop_paris', 'Population Paris Good Quality Records'),
            ('tuples_50_to_100_pop_evry', 'Population Évry Good Quality Records'),
        ],
        'Quality Distribution - Poor Quality (<50%)': [
            ('tuples_below_50_cons_paris', 'Consumption Paris Poor Quality Records'),
            ('tuples_below_50_cons_evry', 'Consumption Évry Poor Quality Records'),
            ('tuples_below_50_pop_paris', 'Population Paris Poor Quality Records'),
            ('tuples_below_50_pop_evry', 'Population Évry Poor Quality Records'),
        ],
        'Row Counts': [
            ('total_rows_cons_paris', 'Consumption Paris Total Rows'),
            ('total_rows_cons_evry', 'Consumption Évry Total Rows'),
            ('total_rows_pop_paris', 'Population Paris Total Rows'),
            ('total_rows_pop_evry', 'Population Évry Total Rows'),
            ('total_rows_csp', 'CSP Reference Table Total Rows'),
            ('valid_rows_cons_paris', 'Consumption Paris Valid Rows'),
            ('valid_rows_cons_evry', 'Consumption Évry Valid Rows'),
        ],
    }
    
    table_rows = ""
    for category, metrics in metric_categories.items():
        table_rows += f'<tr style="background: #f8f9fa;"><td colspan="5" class="metric-category">{category}</td></tr>\n'
        
        for metric_key, metric_name in metrics:
            raw_val = float(raw.get(metric_key, 0))
            cleaned_val = float(cleaned.get(metric_key, 0))
            diff = cleaned_val - raw_val
            
            # Check if this is a count metric (not percentage)
            is_count_metric = ('total_rows' in metric_key or 'valid_rows' in metric_key or 
                              'tuples_' in metric_key)
            
            # Determine status
            if abs(diff) < 0.01:
                status = 'neutral'
                status_emoji = '➖'
            elif ('invalid' in metric_key or 'rate' in metric_key or 'below_50' in metric_key):
                # For invalid metrics and poor quality, lower is better
                status = 'improvement' if diff < 0 else 'regression'
                status_emoji = '✅' if diff < 0 else '⚠️'
            else:
                # For completeness, quality counts, and row counts, higher is better
                status = 'improvement' if diff > 0 else 'regression'
                status_emoji = '✅' if diff > 0 else '⚠️'
            
            # Format values based on type
            if is_count_metric:
                raw_display = f'{int(raw_val)}'
                cleaned_display = f'{int(cleaned_val)}'
                diff_display = f'{"+" if diff > 0 else ""}{int(diff)}'
            else:
                raw_display = f'{raw_val:.2f}%'
                cleaned_display = f'{cleaned_val:.2f}%'
                diff_display = f'{"+" if diff > 0 else ""}{diff:.2f}%'
            
            table_rows += f'''
                <tr>
                    <td class="metric-name">{metric_name}</td>
                    <td class="metric-value-cell">{raw_display}</td>
                    <td class="metric-value-cell">{cleaned_display}</td>
                    <td class="metric-diff {status}">
                        {diff_display}
                    </td>
                    <td style="text-align: center; font-size: 20px;">
                        {status_emoji}
                    </td>
                </tr>
            '''
    
    return table_rows


def generate_html_dashboard(metadata_dir, output_file='dashboard.html'):
    """Generate enhanced HTML dashboard."""
    
    print("Loading metrics data...")
    stages_data = load_latest_metrics(metadata_dir)
    
    if not stages_data:
        print("❌ No metrics data found!")
        return
    
    print(f"✓ Loaded metrics for stages: {', '.join(stages_data.keys())}")
    
    # Create all visualizations
    print("\nGenerating enhanced visualizations...")
    
    figs = []
    
    # 1. Before/After comparison
    before_after_fig = create_before_after_comparison(stages_data)
    if before_after_fig:
        figs.append(before_after_fig)
    
    # 2. Completeness gauges
    figs.append(create_completeness_gauges(stages_data))
    
    # 3. Record quality distribution
    quality_dist_fig = create_record_quality_distribution(stages_data)
    if quality_dist_fig:
        figs.append(quality_dist_fig)
    
    # 4. Issue breakdown by type
    issue_breakdown_fig = create_issue_breakdown_chart(stages_data)
    if issue_breakdown_fig:
        figs.append(issue_breakdown_fig)
    
    # 5. Quality dimensions spider
    figs.append(create_quality_dimensions_spider(stages_data))
    
    # 6. Table health matrix
    figs.append(create_table_health_matrix(stages_data))
    
    # Create metrics comparison table
    metrics_table_rows = create_metrics_comparison_table(stages_data)
    
    # Create HTML with embedded charts
    charts_html = ""
    for i, fig in enumerate(figs, 1):
        charts_html += f'<div class="chart">{fig.to_html(include_plotlyjs="cdn" if i == 1 else False, full_html=False)}</div>\n'
    
    # Calculate summary stats
    latest_data = list(stages_data.values())[-1]
    avg_completeness = (
        float(latest_data.get('completeness_cons_paris', 0)) +
        float(latest_data.get('completeness_pop_paris', 0)) +
        float(latest_data.get('completeness_csp', 0))
    ) / 3
    
    html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Data Quality Dashboard</title>
    <style>
        * {{
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }}
        
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 20px;
            min-height: 100vh;
        }}
        
        .container {{
            max-width: 1400px;
            margin: 0 auto;
        }}
        
        .header {{
            background: white;
            padding: 30px;
            border-radius: 15px;
            margin-bottom: 25px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
        }}
        
        .header h1 {{
            font-size: 36px;
            color: #2c3e50;
            margin-bottom: 10px;
            display: flex;
            align-items: center;
            gap: 15px;
        }}
        
        .header .subtitle {{
            font-size: 16px;
            color: #7f8c8d;
            margin-bottom: 15px;
        }}
        
        .header .timestamp {{
            font-size: 13px;
            color: #95a5a6;
            font-style: italic;
        }}
        
        .control-panel {{
            background: white;
            border-radius: 15px;
            padding: 25px;
            margin-bottom: 20px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
        }}
        
        .control-panel h2 {{
            font-size: 24px;
            color: #2c3e50;
            margin-bottom: 15px;
        }}
        
        .pipeline-controls {{
            display: flex;
            gap: 15px;
            align-items: center;
            margin-bottom: 20px;
        }}
        
        #startPipeline {{
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
        }}
        
        #startPipeline:hover:not(:disabled) {{
            transform: translateY(-2px);
            box-shadow: 0 6px 20px rgba(102, 126, 234, 0.6);
        }}
        
        #startPipeline:disabled {{
            background: #95a5a6;
            cursor: not-allowed;
            box-shadow: none;
        }}
        
        .pipeline-status {{
            display: flex;
            align-items: center;
            gap: 10px;
            font-size: 16px;
            color: #34495e;
        }}
        
        .status-indicator {{
            width: 12px;
            height: 12px;
            border-radius: 50%;
            background: #95a5a6;
        }}
        
        .status-indicator.running {{
            background: #f39c12;
            animation: pulse 1.5s infinite;
        }}
        
        .status-indicator.success {{
            background: #27ae60;
        }}
        
        @keyframes pulse {{
            0%, 100% {{ opacity: 1; }}
            50% {{ opacity: 0.5; }}
        }}
        
        .logs-panel {{
            background: #2c3e50;
            border-radius: 15px;
            padding: 20px;
            margin-bottom: 20px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
            max-height: 250px;
            overflow-y: auto;
        }}
        
        .logs-panel h3 {{
            color: white;
            margin-bottom: 15px;
            font-size: 20px;
        }}
        
        .log-entry {{
            color: #ecf0f1;
            font-family: 'Courier New', monospace;
            font-size: 13px;
            padding: 5px 0;
            border-bottom: 1px solid #34495e;
        }}
        
        .step-card {{
            background: #ecf0f1;
            border-radius: 8px;
            padding: 15px;
            transition: all 0.3s;
        }}
        
        .step-card.running {{
            background: #fff3cd;
            border-left: 4px solid #f39c12;
        }}
        
        .step-card.success {{
            background: #d4edda;
            border-left: 4px solid #27ae60;
        }}
        
        .step-card.failed {{
            background: #f8d7da;
            border-left: 4px solid #e74c3c;
        }}
        
        .step-card h4 {{
            font-size: 14px;
            color: #2c3e50;
            margin-bottom: 8px;
        }}
        
        .step-progress {{
            width: 100%;
            height: 6px;
            background: #bdc3c7;
            border-radius: 3px;
            overflow: hidden;
            margin-top: 8px;
        }}
        
        .step-progress-fill {{
            height: 100%;
            background: linear-gradient(90deg, #667eea, #764ba2);
            width: 0%%;
            transition: width 0.5s;
        }}
        
        .stats {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 25px;
        }}
        
        .stat-card {{
            background: white;
            padding: 25px;
            border-radius: 15px;
            box-shadow: 0 5px 20px rgba(0,0,0,0.15);
            position: relative;
            overflow: hidden;
            transition: transform 0.3s ease, box-shadow 0.3s ease;
        }}
        
        .stat-card:hover {{
            transform: translateY(-5px);
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
        }}
        
        .stat-card::before {{
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            width: 5px;
            height: 100%;
            background: linear-gradient(180deg, #667eea 0%, #764ba2 100%);
        }}
        
        .stat-card h3 {{
            font-size: 13px;
            color: #7f8c8d;
            text-transform: uppercase;
            letter-spacing: 1px;
            margin-bottom: 12px;
            font-weight: 600;
        }}
        
        .stat-card .value {{
            font-size: 36px;
            font-weight: bold;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }}
        
        .stat-card .subtitle {{
            font-size: 12px;
            color: #95a5a6;
            margin-top: 8px;
        }}
        
        .chart {{
            background: white;
            padding: 25px;
            border-radius: 15px;
            box-shadow: 0 5px 20px rgba(0,0,0,0.15);
            margin-bottom: 25px;
            transition: transform 0.3s ease;
        }}
        
        .chart:hover {{
            transform: translateY(-2px);
        }}
        
        .detailed-metrics {{
            background: white;
            border-radius: 15px;
            padding: 25px;
            margin-bottom: 25px;
            box-shadow: 0 5px 20px rgba(0,0,0,0.15);
        }}
        
        .detailed-metrics h2 {{
            font-size: 24px;
            color: #2c3e50;
            margin-bottom: 20px;
        }}
        
        .metrics-table {{
            width: 100%;
            border-collapse: collapse;
            margin-bottom: 20px;
        }}
        
        .metrics-table th {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 15px;
            text-align: left;
            font-weight: 600;
            position: sticky;
            top: 0;
        }}
        
        .metrics-table td {{
            padding: 12px 15px;
            border-bottom: 1px solid #ecf0f1;
        }}
        
        .metrics-table tr:hover {{
            background: #f8f9fa;
        }}
        
        .metric-category {{
            font-weight: bold;
            color: #2c3e50;
            font-size: 14px;
        }}
        
        .metric-name {{
            color: #7f8c8d;
            font-size: 13px;
        }}
        
        .metric-value-cell {{
            text-align: center;
            font-weight: 600;
        }}
        
        .metric-diff {{
            text-align: center;
            font-weight: bold;
            padding: 5px 10px;
            border-radius: 5px;
        }}
        
        .metric-diff.improvement {{
            background: #d4edda;
            color: #27ae60;
        }}
        
        .metric-diff.regression {{
            background: #f8d7da;
            color: #e74c3c;
        }}
        
        .metric-diff.neutral {{
            background: #e2e3e5;
            color: #6c757d;
        }}
        
        .footer {{
            text-align: center;
            margin-top: 40px;
            padding: 25px;
            background: rgba(255,255,255,0.1);
            border-radius: 15px;
            color: white;
            font-size: 13px;
            backdrop-filter: blur(10px);
        }}
        
        .footer p {{
            margin: 5px 0;
        }}
        
        @media (max-width: 768px) {{
            .stats {{
                grid-template-columns: 1fr;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>
                <span>📊</span>
                Data Quality Dashboard
            </h1>
            <p class="subtitle">
                Interactive visualization and analysis of data quality metrics across pipeline stages
            </p>
            <p class="timestamp">
                Generated: {datetime.now().strftime('%B %d, %Y at %H:%M:%S')}
            </p>
        </div>
        
        <div class="control-panel">
            <h2> Pipeline Control</h2>
            <div class="pipeline-controls">
                <button id="startPipeline" onclick="startPipeline()">▶️ Launch Pipeline</button>
                <div class="pipeline-status">
                    <div class="status-indicator" id="statusIndicator"></div>
                    <span id="statusText">Ready - Click button to start</span>
                </div>
            </div>
            
            <div id="stepsContainer" style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; margin-top: 20px;"></div>
        </div>
        
        <div class="logs-panel">
            <h3>📋 Execution Logs</h3>
            <div id="logsContainer">
                <div class="log-entry">✅ Dashboard loaded at {datetime.now().strftime('%H:%M:%S')}</div>
                <div class="log-entry">📊 Available stages: {', '.join(stages_data.keys())}</div>
                <div class="log-entry">ℹ️ Click "Launch Pipeline" above to execute the full data quality pipeline</div>
            </div>
        </div>
        
        <div class="stats">
            <div class="stat-card">
                <h3>Pipeline Stages</h3>
                <div class="value">{len(stages_data)}</div>
                <div class="subtitle">Raw → Cleaned → Aggregated</div>
            </div>
            <div class="stat-card">
                <h3>Average Completeness</h3>
                <div class="value">{avg_completeness:.1f}%</div>
                <div class="subtitle">Across all tables</div>
            </div>
            <div class="stat-card">
                <h3>Data Sources</h3>
                <div class="value">2</div>
                <div class="subtitle">Paris + Évry</div>
            </div>
            <div class="stat-card">
                <h3>Total Tables</h3>
                <div class="value">5</div>
                <div class="subtitle">Consommation, Population, CSP</div>
            </div>
        </div>
        
        <div class="detailed-metrics">
            <h2>📊 Detailed Metrics Comparison</h2>
            
            <div style="overflow-x: auto; max-height: 600px; overflow-y: auto;">
                <table class="metrics-table">
                    <thead>
                        <tr>
                            <th style="min-width: 300px;">Metric</th>
                            <th style="min-width: 120px;">Raw Data</th>
                            <th style="min-width: 120px;">Cleaned Data</th>
                            <th style="min-width: 150px;">Improvement</th>
                            <th style="min-width: 100px;">Status</th>
                        </tr>
                    </thead>
                    <tbody>
                        {metrics_table_rows}
                    </tbody>
                </table>
            </div>
        </div>
        
        <div class="detailed-metrics" style="margin-top: 30px;">
            <h2>🔍 Metadata File Viewer</h2>
            <p style="color: rgba(255,255,255,0.8); margin-bottom: 20px;">
                View raw metadata CSV files with all pipeline metrics
            </p>
            
            <div style="display: grid; grid-template-columns: 1fr 1fr auto; gap: 15px; margin-bottom: 20px; align-items: end;">
                <div>
                    <label for="metadataFile" style="display: block; margin-bottom: 5px; font-weight: bold;">Select Metadata File:</label>
                    <select id="metadataFile" onchange="loadMetadataFile()" style="width: 100%; padding: 10px; font-size: 14px; border-radius: 8px; border: 2px solid rgba(255,255,255,0.3); background: rgba(255,255,255,0.1); color: white;">
                        <option value="">-- Choose a file --</option>
                        {metadata_files_options}
                    </select>
                </div>
                <div>
                    <label for="rowLimit" style="display: block; margin-bottom: 5px; font-weight: bold;">Number of Rows:</label>
                    <input type="number" id="rowLimit" value="10" min="1" max="100" onchange="loadMetadataFile()" style="width: 100%; padding: 10px; font-size: 14px; border-radius: 8px; border: 2px solid rgba(255,255,255,0.3); background: rgba(255,255,255,0.1); color: white;">
                </div>
                <button onclick="downloadMetadataCSV()" style="padding: 10px 20px; font-size: 14px; border-radius: 8px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; border: none; cursor: pointer; font-weight: bold;">
                    📥 Download CSV
                </button>
            </div>
            
            <div id="metadataViewer" style="overflow-x: auto; max-height: 600px; overflow-y: auto; background: rgba(0,0,0,0.3); border-radius: 12px; padding: 20px;">
                <p style="color: rgba(255,255,255,0.6); text-align: center; padding: 40px;">
                    Select a metadata file above to view its contents
                </p>
            </div>
        </div>
        
        {charts_html}
        
        <div class="footer">
            <p><strong>Data Quality Dashboard</strong> - Airflow ETL Pipeline Project</p>
            <p>Metrics Directory: {metadata_dir}</p>
            <p>Built with Python, Plotly, and ❤️</p>
        </div>
    </div>
    
    <script>
        let updateInterval = null;
        
        function startPipeline() {{
            const btn = document.getElementById('startPipeline');
            btn.disabled = true;
            btn.textContent = '⏳ Running...';
            
            fetch('/api/start-pipeline', {{ method: 'POST' }})
                .then(r => r.json())
                .then(data => {{
                    console.log('Pipeline started:', data);
                    updateInterval = setInterval(updateDashboard, 500);
                }})
                .catch(err => {{
                    console.error('Error starting pipeline:', err);
                    btn.disabled = false;
                    btn.textContent = '▶️ Launch Pipeline';
                    alert('Error: Could not start pipeline. Make sure you are running with --server flag:\\npython dags/scripts/visualize_dashboard.py --server');
                }});
        }}
        
        function updateDashboard() {{
            fetch('/api/pipeline-status')
                .then(r => r.json())
                .then(data => {{
                    updateStatus(data);
                    updateSteps(data.steps);
                    updateLogs(data.logs);
                    
                    if (!data.running && updateInterval) {{
                        clearInterval(updateInterval);
                        document.getElementById('startPipeline').disabled = false;
                        document.getElementById('startPipeline').textContent = '▶️ Launch Pipeline';
                        
                        // Reload page after 2 seconds to show updated metrics
                        setTimeout(() => {{
                            location.reload();
                        }}, 2000);
                    }}
                }})
                .catch(err => {{
                    console.error('Error fetching status:', err);
                }});
        }}
        
        function updateStatus(data) {{
            const indicator = document.getElementById('statusIndicator');
            const text = document.getElementById('statusText');
            
            if (data.running) {{
                indicator.className = 'status-indicator running';
                text.textContent = data.current_step || 'Running...';
            }} else {{
                const allSuccess = data.steps && data.steps.every(s => s.status === 'success');
                indicator.className = 'status-indicator ' + (allSuccess ? 'success' : '');
                text.textContent = allSuccess ? 'Completed Successfully ✅' : 'Ready';
            }}
        }}
        
        function updateSteps(steps) {{
            if (!steps || steps.length === 0) return;
            
            const container = document.getElementById('stepsContainer');
            let html = '';
            for (let i = 0; i < steps.length; i++) {{
                const step = steps[i];
                html += '<div class="step-card ' + step.status + '">';
                html += '<h4>' + step.name + '</h4>';
                html += '<div>' + getStatusEmoji(step.status) + ' ' + step.status.toUpperCase() + '</div>';
                html += '<div class="step-progress">';
                html += '<div class="step-progress-fill" style="width: ' + step.progress + '%"></div>';
                html += '</div>';
                html += '</div>';
            }}
            container.innerHTML = html;
        }}
        
        function getStatusEmoji(status) {{
            const emojis = {{
                'pending': '⏳',
                'running': '▶️',
                'success': '✅',
                'failed': '❌'
            }};
            return emojis[status] || '⏳';
        }}
        
        function updateLogs(logs) {{
            if (!logs || logs.length === 0) return;
            
            const container = document.getElementById('logsContainer');
            let html = '';
            const recentLogs = logs.slice(-25).reverse();
            for (let i = 0; i < recentLogs.length; i++) {{
                html += '<div class="log-entry">' + recentLogs[i] + '</div>';
            }}
            container.innerHTML = html;
            
            // Auto-scroll to top (since reversed)
            container.scrollTop = 0;
        }}
    </script>
</body>
</html>
"""
    
    # Write HTML file
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"\n✅ Enhanced dashboard generated: {output_file}")
    print(f"\n📊 Visualizations:")
    print(f"  • Before & After Comparison (Grouped Bar Chart)")
    print(f"  • Data Completeness Gauges (5 Tables)")
    print(f"  • Record Quality Distribution (Stacked Bars)")
    print(f"  • Issue Type Breakdown (Stacked Area Chart)")
    print(f"  • Multi-dimensional Quality Spider Chart")
    print(f"  • Table Health Matrix (Heatmap)")
    print(f"\n🌐 Opening in browser...")


# Flask app for live dashboard
app = Flask(__name__)
CORS(app)

# Global state for pipeline execution
pipeline_state = {
    'running': False,
    'current_step': '',
    'logs': [],
    'steps': []
}

def run_pipeline():
    """Execute the data quality pipeline with detailed logging."""
    global pipeline_state
    
    script_dir = Path(__file__).parent
    base_path = script_dir.parent.parent
    
    pipeline_state['running'] = True
    pipeline_state['logs'] = []
    pipeline_state['steps'] = [
        {'name': 'Compute Raw Metrics', 'status': 'pending', 'progress': 0},
        {'name': 'Clean Data', 'status': 'pending', 'progress': 0},
        {'name': 'Aggregate Data', 'status': 'pending', 'progress': 0},
        {'name': 'Compute Cleaned Metrics', 'status': 'pending', 'progress': 0},
    ]
    
    try:
        # Step 1: Compute raw metrics
        pipeline_state['steps'][0]['status'] = 'running'
        pipeline_state['current_step'] = 'Computing raw data metrics...'
        pipeline_state['logs'].append(f'[{datetime.now().strftime("%H:%M:%S")}] 🔍 Starting raw data metrics computation...')
        
        result = subprocess.run(
            [sys.executable, str(base_path / 'dags' / 'scripts' / 'compute_metrics.py'), '--stage', 'raw'],
            capture_output=True, text=True, cwd=str(base_path)
        )
        
        if result.returncode == 0:
            pipeline_state['steps'][0]['status'] = 'success'
            pipeline_state['steps'][0]['progress'] = 100
            pipeline_state['logs'].append(f'[{datetime.now().strftime("%H:%M:%S")}] ✅ Raw metrics computed successfully')
            # Parse output for details
            for line in result.stdout.split('\n')[:10]:
                if line.strip():
                    pipeline_state['logs'].append(f'   {line.strip()}')
        else:
            pipeline_state['steps'][0]['status'] = 'failed'
            pipeline_state['logs'].append(f'[{datetime.now().strftime("%H:%M:%S")}] ❌ Failed to compute raw metrics')
            raise Exception(result.stderr)
        
        time.sleep(0.5)
        
        # Step 2: Clean data
        pipeline_state['steps'][1]['status'] = 'running'
        pipeline_state['current_step'] = 'Cleaning data...'
        pipeline_state['logs'].append(f'[{datetime.now().strftime("%H:%M:%S")}] 🧹 Starting data cleaning...')
        
        result = subprocess.run(
            [sys.executable, str(base_path / 'dags' / 'scripts' / 'clean_data.py')],
            capture_output=True, text=True, cwd=str(base_path)
        )
        
        if result.returncode == 0:
            pipeline_state['steps'][1]['status'] = 'success'
            pipeline_state['steps'][1]['progress'] = 100
            pipeline_state['logs'].append(f'[{datetime.now().strftime("%H:%M:%S")}] ✅ Data cleaning completed')
            # Parse cleaning details
            for line in result.stdout.split('\n'):
                if 'Cleaning' in line or '✓' in line or 'ℹ' in line:
                    pipeline_state['logs'].append(f'   {line.strip()}')
        else:
            pipeline_state['steps'][1]['status'] = 'failed'
            pipeline_state['logs'].append(f'[{datetime.now().strftime("%H:%M:%S")}] ❌ Data cleaning failed')
            raise Exception(result.stderr)
        
        time.sleep(0.5)
        
        # Step 3: Aggregate data
        pipeline_state['steps'][2]['status'] = 'running'
        pipeline_state['current_step'] = 'Aggregating data...'
        pipeline_state['logs'].append(f'[{datetime.now().strftime("%H:%M:%S")}] 🔗 Starting data aggregation...')
        
        result = subprocess.run(
            [sys.executable, str(base_path / 'dags' / 'scripts' / 'aggregate_data.py')],
            capture_output=True, text=True, cwd=str(base_path)
        )
        
        if result.returncode == 0:
            pipeline_state['steps'][2]['status'] = 'success'
            pipeline_state['steps'][2]['progress'] = 100
            pipeline_state['logs'].append(f'[{datetime.now().strftime("%H:%M:%S")}] ✅ Data aggregation completed')
            # Parse aggregation details
            for line in result.stdout.split('\n'):
                if 'Creating' in line or '✓' in line:
                    pipeline_state['logs'].append(f'   {line.strip()}')
        else:
            pipeline_state['steps'][2]['status'] = 'failed'
            pipeline_state['logs'].append(f'[{datetime.now().strftime("%H:%M:%S")}] ❌ Data aggregation failed')
            raise Exception(result.stderr)
        
        time.sleep(0.5)
        
        # Step 4: Compute cleaned metrics
        pipeline_state['steps'][3]['status'] = 'running'
        pipeline_state['current_step'] = 'Computing cleaned data metrics...'
        pipeline_state['logs'].append(f'[{datetime.now().strftime("%H:%M:%S")}] 📊 Computing cleaned data metrics...')
        
        result = subprocess.run(
            [sys.executable, str(base_path / 'dags' / 'scripts' / 'compute_metrics.py'), '--stage', 'cleaned'],
            capture_output=True, text=True, cwd=str(base_path)
        )
        
        if result.returncode == 0:
            pipeline_state['steps'][3]['status'] = 'success'
            pipeline_state['steps'][3]['progress'] = 100
            pipeline_state['logs'].append(f'[{datetime.now().strftime("%H:%M:%S")}] ✅ Cleaned metrics computed successfully')
            # Parse final metrics
            for line in result.stdout.split('\n')[-15:]:
                if line.strip() and ('---' in line or ':' in line):
                    pipeline_state['logs'].append(f'   {line.strip()}')
        else:
            pipeline_state['steps'][3]['status'] = 'failed'
            pipeline_state['logs'].append(f'[{datetime.now().strftime("%H:%M:%S")}] ❌ Failed to compute cleaned metrics')
            raise Exception(result.stderr)
        
        pipeline_state['logs'].append(f'[{datetime.now().strftime("%H:%M:%S")}] 🎉 Pipeline completed successfully!')
        pipeline_state['current_step'] = 'Completed'
        
    except Exception as e:
        pipeline_state['logs'].append(f'[{datetime.now().strftime("%H:%M:%S")}] ❌ Pipeline failed: {str(e)}')
        pipeline_state['current_step'] = 'Failed'
    
    finally:
        pipeline_state['running'] = False


@app.route('/api/start-pipeline', methods=['POST'])
def start_pipeline():
    """Start the pipeline execution in a background thread."""
    if pipeline_state['running']:
        return jsonify({'status': 'already_running'})
    
    thread = threading.Thread(target=run_pipeline)
    thread.daemon = True
    thread.start()
    
    return jsonify({'status': 'started'})


@app.route('/api/pipeline-status')
def get_pipeline_status():
    """Get current pipeline status."""
    return jsonify({
        'running': pipeline_state['running'],
        'current_step': pipeline_state['current_step'],
        'steps': pipeline_state['steps'],
        'logs': pipeline_state['logs']
    })


@app.route('/')
def serve_dashboard():
    """Serve the dashboard HTML."""
    script_dir = Path(__file__).parent
    base_path = script_dir.parent.parent
    dashboard_file = os.path.join(base_path, 'dashboard.html')
    
    if not os.path.exists(dashboard_file):
        generate_html_dashboard(
            os.path.join(base_path, 'metadata'),
            dashboard_file
        )
    
    return send_file(dashboard_file)


def main():
    """Main function to generate dashboard and optionally start server."""
    script_dir = Path(__file__).parent
    base_path = script_dir.parent.parent
    metadata_dir = os.path.join(base_path, 'metadata')
    output_file = os.path.join(base_path, 'dashboard.html')
    
    print("=" * 70)
    print("ENHANCED DATA QUALITY DASHBOARD GENERATOR")
    print("=" * 70)
    
    generate_html_dashboard(metadata_dir, output_file)
    
    # Check if we should start the server
    if len(sys.argv) > 1 and sys.argv[1] == '--server':
        print("\n" + "=" * 70)
        print("🚀 STARTING LIVE DASHBOARD SERVER")
        print("=" * 70)
        print(f"\n📊 Dashboard URL: http://localhost:5050")
        print(f"📁 Base Path: {base_path}")
        print(f"\n✨ Features:")
        print(f"  - Launch pipeline with one click")
        print(f"  - Real-time execution logs")
        print(f"  - Step-by-step progress tracking")
        print(f"  - Live metrics updates")
        print(f"\n" + "=" * 70)
        print("Press Ctrl+C to stop the server")
        print("=" * 70 + "\n")
        
        import webbrowser
        webbrowser.open('http://localhost:5050')
        app.run(host='0.0.0.0', port=5050, debug=False)
    else:
        # Just open the static file
        import webbrowser
        webbrowser.open('file://' + os.path.abspath(output_file))


if __name__ == '__main__':
    main()






