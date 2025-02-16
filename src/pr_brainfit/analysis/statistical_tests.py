import pandas as pd
import numpy as np
from scipy import stats
import plotly.graph_objects as go
from plotly.subplots import make_subplots

def run_time_comparisons(df):
    """
    Run statistical comparisons between groups for each 15-min time block,
    aggregating across days.
    """
    # Ensure local_time is datetime and create time_block
    df['time_block'] = df['local_time'].dt.strftime('%H:%M')
    
    # Add date column for aggregation
    df['date'] = df['local_time'].dt.date
    
    # Initialize results storage
    results = {
        'time_blocks': [],
        'h_statistic': [],
        'p_value': [],
        'effect_size': [],
        'group_medians': {},
        'significant_differences': [],
        'sample_sizes': {}  # Add sample size tracking
    }
    
    # Initialize storage for each group
    groups = df['standardized_group'].unique()
    for group in groups:
        results['group_medians'][group] = []
        results['sample_sizes'][group] = []
    
    min_samples = 5  # Minimum samples needed per group
    
    # Analyze each 15-min block
    for time_block in sorted(df['time_block'].unique()):
        block_data = df[df['time_block'] == time_block]
        
        # Get data for each group, aggregating across days
        groups_data = []
        sufficient_data = True
        
        for group in groups:
            group_data = block_data[block_data['standardized_group'] == group]
            # Count unique days with data for this time block
            sample_size = len(group_data['date'].unique())
            results['sample_sizes'][group].append(sample_size)
            
            if sample_size < min_samples:
                sufficient_data = False
            
            groups_data.append(group_data['stress_score'].values)
        
        # Skip this time block if insufficient data
        if not sufficient_data:
            # Add NaN values to maintain array lengths
            results['time_blocks'].append(time_block)
            results['h_statistic'].append(np.nan)
            results['p_value'].append(np.nan)
            results['effect_size'].append(np.nan)
            for group in groups:
                results['group_medians'][group].append(np.nan)
            continue
        
        # Run Kruskal-Wallis test
        h_stat, p_val = stats.kruskal(*groups_data)
        
        # Calculate effect size (epsilon-squared)
        n = sum(len(gd) for gd in groups_data)
        effect_size = (h_stat - len(groups_data) + 1) / (n - len(groups_data))
        
        # Store results
        results['time_blocks'].append(time_block)
        results['h_statistic'].append(h_stat)
        results['p_value'].append(p_val)
        results['effect_size'].append(effect_size)
        
        # Store group medians
        for group in groups:
            group_data = block_data[block_data['standardized_group'] == group]
            results['group_medians'][group].append(group_data['stress_score'].median())
        
        # If significant difference found, run post-hoc tests
        if p_val < 0.05:
            for i in range(len(groups)):
                for j in range(i + 1, len(groups)):
                    group1_data = block_data[block_data['standardized_group'] == groups[i]]['stress_score']
                    group2_data = block_data[block_data['standardized_group'] == groups[j]]['stress_score']
                    
                    if len(group1_data) >= min_samples and len(group2_data) >= min_samples:
                        stat, p = stats.mannwhitneyu(group1_data, group2_data, alternative='two-sided')
                        
                        # Apply Bonferroni correction
                        if p < (0.05 / (len(groups) * (len(groups) - 1) / 2)):
                            results['significant_differences'].append({
                                'time_block': time_block,
                                'group1': groups[i],
                                'group2': groups[j],
                                'p_value': p
                            })
    
    return results


def analyze_group_differences(df):
    """Analyze when each group is significantly different from others"""
    # Filter for working hours (7am-5pm)
    df['hour'] = pd.to_datetime(df['time_block'], format='%H:%M').dt.hour
    df = df[(df['hour'] >= 7) & (df['hour'] <= 17)]
    
    groups = ['DALMUIR', 'KILMALID', 'KB3']
    significant_differences = {group: {} for group in groups}
    
    # For each time block, check if each group is different from others
    for time_block in sorted(df['time_block'].unique()):
        block_data = df[df['time_block'] == time_block]
        
        for group in groups:
            group_data = block_data[block_data['standardized_group'] == group]['stress_score']
            other_data = block_data[block_data['standardized_group'] != group]['stress_score']
            
            if len(group_data) >= 5 and len(other_data) >= 5:
                stat, p = stats.mannwhitneyu(group_data, other_data, alternative='two-sided')
                
                if p < 0.05:  # Store only significant differences
                    significant_differences[group][time_block] = {
                        'p_value': p,
                        'group_median': group_data.median(),
                        'others_median': other_data.median(),
                        'difference': group_data.median() - other_data.median()
                    }
    
    return significant_differences


def plot_group_differences(differences):
    """Create a visualization showing when each group differs significantly"""
    fig = make_subplots(
        rows=3, cols=1,
        subplot_titles=(
            "Times when DALMUIR differs significantly from other groups",
            "Times when KILMALID differs significantly from other groups",
            "Times when KB3 differs significantly from other groups"
        ),
        vertical_spacing=0.15
    )
    
    colors = {
        'DALMUIR': '#1f77b4',
        'KILMALID': '#ff7f0e',
        'KB3': '#2ca02c'
    }
    
    for idx, (group, data) in enumerate(differences.items(), 1):
        if data:  # Only plot if there are significant differences
            times = list(data.keys())
            diffs = [data[t]['difference'] for t in times]
            p_values = [data[t]['p_value'] for t in times]
            
            fig.add_trace(
                go.Bar(
                    x=times,
                    y=diffs,
                    name=group,
                    marker_color=colors[group],
                    customdata=p_values,
                    hovertemplate=(
                        "Time: %{x}<br>" +
                        "Difference from others: %{y:.2f}<br>" +
                        "p-value: %{customdata:.3f}<br>" +
                        "<extra></extra>"
                    )
                ),
                row=idx, col=1
            )
    
    # Update layout
    fig.update_layout(
        height=900,
        showlegend=False,
        title={
            'text': "Significant Differences in Group Biometric Productivity Levels (active roles)",
            'y': 0.95,
            'x': 0.5,
            'xanchor': 'center',
            'yanchor': 'top'
        },
        margin=dict(t=150, l=50, r=50, b=50)  # Increased top margin to accommodate explanation
    )
    
    # Add explanation at top right
    fig.add_annotation(
        text=(
            "<b>How to read this visualization:</b><br><br>" +
            "• Each bar shows how much a group's biometric productivity level differs<br>" +
            "  from the average of other groups at that time<br>" +
            "• Positive values mean the group has higher productivity<br>" +
            "• Negative values mean the group has lower productivity<br>"
        ),
        xref="paper", yref="paper",
        x=0.94, y=1.2,  # Positioned at top right
        showarrow=False,
        align="left",
        bgcolor="white",
        bordercolor="black",
        borderwidth=1,
        font=dict(size=12)
    )
    
    # Update axes
    for i in range(1, 4):
        fig.update_yaxes(
            title="Difference in Biometric Productivity Score",
            row=i, col=1,
            zeroline=True,
            zerolinecolor='black',
            zerolinewidth=1
        )
    
    fig.update_xaxes(
        title="Time of Day",
        tickangle=90,
        row=3, col=1
    )
    
    return fig






