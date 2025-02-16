# PR_brainfit_analysis/visualization/advanced_plots.py

import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np

def create_patterns_visualization(daily_patterns, variance_scores):
    """Create visualization for daily patterns and variance analysis."""
    
    # Define consistent colors for groups
    colors = {
        'DALMUIR': '#1f77b4',    # blue
        'KB3': '#2ca02c',        # green
        'KILMALID': '#ff7f0e'    # orange
    }
    
    # Create subplots with 2 rows (removed heatmap)
    fig = make_subplots(
        rows=2, cols=1,
        subplot_titles=(
            "Daily Biometric Productivity by Group",
            "Group Variance Analysis"
        ),
        vertical_spacing=0.2
    )
    
    # 1. Daily patterns plot with correct day order
    days_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
    for group in sorted(daily_patterns['daily_means'].keys()):
        data = daily_patterns['daily_means'][group]
        # Reorder data according to days_order
        ordered_data = pd.Series([data[day] for day in days_order], index=days_order)
        
        fig.add_trace(
            go.Scatter(
                x=days_order,
                y=ordered_data.values,
                name=group,
                mode='lines+markers',
                line=dict(color=colors[group], width=2),
                marker=dict(size=8, color=colors[group]),
                showlegend=False
            ),
            row=1, col=1
        )
    
    # 2. Variance analysis with consistent colors
    for group in sorted(variance_scores.keys()):
        fig.add_trace(
            go.Bar(
                x=['Within Day', 'Between Day'],
                y=[
                    variance_scores[group]['within_day_variance'],
                    variance_scores[group]['between_day_variance']
                ],
                name=group,
                marker_color=colors[group]
            ),
            row=2, col=1
        )
    
    # Update layout
    fig.update_layout(
        height=800,  # Reduced height since we removed one subplot
        width=1000,
        showlegend=True,
        title_text="Days by Day Analysis",
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        )
    )
    
    # Update axes labels and formatting
    fig.update_xaxes(title="Day of Week", row=1, col=1)
    fig.update_yaxes(title="Biometric Productivity", row=1, col=1)
    
    fig.update_xaxes(title="Variance Type", row=2, col=1)
    fig.update_yaxes(title="Variance Score", row=2, col=1)

    return fig

def create_group_analysis_visualization(consistency_scores, group_variability):
    """Create visualization for group analysis results."""
    if not consistency_scores or not group_variability:
        # Create empty figure with error message
        fig = go.Figure()
        fig.add_annotation(
            text="No data available for group analysis",
            xref="paper", yref="paper",
            x=0.5, y=0.5,
            showarrow=False,
            font=dict(size=14)
        )
        return fig
    
    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=(
            "Consistency Scores by Group",
            "Variability Metrics",
            "Temporal Consistency",
            "Group Comparisons"
        )
    )
    
    # Consistency scores
    try:
        consistency_df = pd.DataFrame(consistency_scores).T
        if not consistency_df.empty and 'cv_stress' in consistency_df.columns:
            fig.add_trace(
                go.Bar(
                    x=consistency_df.index,
                    y=consistency_df['cv_stress'],
                    name='Stress CV',
                    marker_color='blue'
                ),
                row=1, col=1
            )
            
            fig.update_xaxes(title_text="Group", row=1, col=1)
            fig.update_yaxes(title_text="Coefficient of Variation", row=1, col=1)
    except Exception as e:
        print(f"Warning: Could not create consistency score plot: {str(e)}")
        fig.add_annotation(
            text="Error creating consistency scores plot",
            xref="x", yref="y",
            x=0.5, y=0.5,
            showarrow=False,
            row=1, col=1
        )
    
    # Variability metrics
    try:
        for group, metrics in group_variability.items():
            if isinstance(metrics, dict) and 'stability_score' in metrics:
                fig.add_trace(
                    go.Scatter(
                        x=['Intraday', 'Interday', 'User', 'Stability'],
                        y=[
                            metrics.get('intraday_variability', 0),
                            metrics.get('interday_variability', 0),
                            metrics.get('user_variability', 0),
                            metrics.get('stability_score', 0)
                        ],
                        name=group,
                        mode='lines+markers'
                    ),
                    row=1, col=2
                )
                
        fig.update_xaxes(title_text="Metric Type", row=1, col=2)
        fig.update_yaxes(title_text="Variability Score", row=1, col=2)
    except Exception as e:
        print(f"Warning: Could not create variability metrics plot: {str(e)}")
        fig.add_annotation(
            text="Error creating variability metrics plot",
            xref="x2", yref="y2",
            x=0.5, y=0.5,
            showarrow=False,
            row=1, col=2
        )
    
    # Temporal consistency
    try:
        if consistency_scores and any('temporal_consistency' in scores for scores in consistency_scores.values()):
            for group, scores in consistency_scores.items():
                if 'temporal_consistency' in scores:
                    fig.add_trace(
                        go.Scatter(
                            x=list(range(24)),
                            y=[scores['temporal_consistency']] * 24,
                            name=f"{group} Consistency",
                            mode='lines'
                        ),
                        row=2, col=1
                    )
            
            fig.update_xaxes(title_text="Hour of Day", row=2, col=1)
            fig.update_yaxes(title_text="Consistency Score", row=2, col=1)
    except Exception as e:
        print(f"Warning: Could not create temporal consistency plot: {str(e)}")
        fig.add_annotation(
            text="Error creating temporal consistency plot",
            xref="x3", yref="y3",
            x=0.5, y=0.5,
            showarrow=False,
            row=2, col=1
        )
    
    # Group comparisons heatmap
    try:
        comparison_data = []
        groups = list(consistency_scores.keys())
        for i, group1 in enumerate(groups):
            for j, group2 in enumerate(groups):
                if i < j:
                    key = f'{group1}_vs_{group2}'
                    if key in group_variability:
                        comparison_data.append({
                            'group1': group1,
                            'group2': group2,
                            'difference': group_variability[key].get('levene_statistic', 0)
                        })
        
        if comparison_data:
            comparison_df = pd.DataFrame(comparison_data)
            heatmap_data = pd.pivot_table(
                comparison_df,
                values='difference',
                index='group1',
                columns='group2',
                fill_value=0
            )
            
            fig.add_trace(
                go.Heatmap(
                    z=heatmap_data.values,
                    x=heatmap_data.columns,
                    y=heatmap_data.index,
                    colorscale='RdBu_r',
                    showscale=True
                ),
                row=2, col=2
            )
            
            fig.update_xaxes(title_text="Group 2", row=2, col=2)
            fig.update_yaxes(title_text="Group 1", row=2, col=2)
    except Exception as e:
        print(f"Warning: Could not create group comparisons heatmap: {str(e)}")
        fig.add_annotation(
            text="Error creating group comparisons plot",
            xref="x4", yref="y4",
            x=0.5, y=0.5,
            showarrow=False,
            row=2, col=2
        )
    
    # Update layout
    fig.update_layout(
        height=1000,
        width=1200,
        showlegend=True,
        title_text="Group Analysis Results",
        title_x=0.5,
        legend=dict(
            yanchor="top",
            y=0.99,
            xanchor="right",
            x=0.99
        ),
        margin=dict(t=100, l=50, r=50, b=50)
    )
    
    # Add explanatory annotations
    fig.add_annotation(
        text=(
            "How to read this dashboard:<br>" +
            "• Top left: Lower CV indicates more consistent stress levels<br>" +
            "• Top right: Compare different types of variability across groups<br>" +
            "• Bottom left: How consistency changes throughout the day<br>" +
            "• Bottom right: Statistical differences between groups"
        ),
        xref="paper", yref="paper",
        x=1.15, y=0.5,
        showarrow=False,
        align="left",
        bgcolor="white",
        bordercolor="black",
        borderwidth=1
    )
    
    return fig

def create_activity_visualization(activity_stats, transition_probs):
    """Create visualization for activity analysis results."""
    
    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=(
            "Activity Distribution by Group",
            "Activity Transitions",
            "Hourly Activity Patterns",
            "Activity Level Stability"
        )
    )
    
    # Activity distribution
    for group, stats in activity_stats.items():
        fig.add_trace(
            go.Bar(
                x=list(stats['overall_distribution'].keys()),
                y=list(stats['overall_distribution'].values()),
                name=group
            ),
            row=1, col=1
        )
    
    # Transition probabilities
    for group, probs in transition_probs.items():
        matrix = probs['matrix']
        fig.add_trace(
            go.Heatmap(
                z=matrix.values,
                x=matrix.columns,
                y=matrix.index,
                colorscale='Viridis',
                name=f"{group} Transitions"
            ),
            row=1, col=2
        )
    
    # Hourly patterns
    for group, stats in activity_stats.items():
        hourly_dist = stats['hourly_distribution']
        fig.add_trace(
            go.Heatmap(
                z=hourly_dist.values,
                x=hourly_dist.columns,
                y=hourly_dist.index,
                colorscale='Viridis',
                name=f"{group} Hourly"
            ),
            row=2, col=1
        )
    
    # Activity stability
    for group, probs in transition_probs.items():
        steady_state = probs['steady_state']
        fig.add_trace(
            go.Bar(
                x=steady_state.index,
                y=steady_state.values,
                name=f"{group} Steady State"
            ),
            row=2, col=2
        )
    
    fig.update_layout(
        height=1000,
        showlegend=True,
        title_text="Activity Analysis Results"
    )
    
    return fig


def create_break_visualization(break_patterns, break_comparisons):
    """Create visualization for break analysis results."""
    if not break_patterns or not break_comparisons:
        # Create empty figure with error message
        fig = go.Figure()
        fig.add_annotation(
            text="No data available for break analysis",
            xref="paper", yref="paper",
            x=0.5, y=0.5,
            showarrow=False,
            font=dict(size=14)
        )
        return fig

    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=(
            "Break Duration Distribution",
            "Break Timing Patterns",
            "Stress Reduction During Breaks",
            "Group Comparisons"
        )
    )
    
    # Break duration distribution
    try:
        for group, patterns in break_patterns.items():
            if 'duration_distribution' in patterns:
                fig.add_trace(
                    go.Box(
                        y=patterns['duration_distribution'],
                        name=group
                    ),
                    row=1, col=1
                )
        fig.update_yaxes(title_text="Duration (minutes)", row=1, col=1)
    except Exception as e:
        print(f"Warning: Could not create duration distribution plot: {str(e)}")

    # Break timing patterns
    try:
        for group, patterns in break_patterns.items():
            if 'common_times' in patterns:
                fig.add_trace(
                    go.Bar(
                        x=patterns['common_times'].index,
                        y=patterns['common_times'].values,
                        name=group
                    ),
                    row=1, col=2
                )
        fig.update_xaxes(title_text="Hour of Day", row=1, col=2)
        fig.update_yaxes(title_text="Break Frequency", row=1, col=2)
    except Exception as e:
        print(f"Warning: Could not create timing patterns plot: {str(e)}")

    # Stress reduction
    try:
        stress_reduction = {
            group: patterns.get('stress_reduction', 0)
            for group, patterns in break_patterns.items()
        }
        fig.add_trace(
            go.Bar(
                x=list(stress_reduction.keys()),
                y=list(stress_reduction.values()),
                name='Stress Reduction'
            ),
            row=2, col=1
        )
        fig.update_yaxes(title_text="Stress Reduction (%)", row=2, col=1)
    except Exception as e:
        print(f"Warning: Could not create stress reduction plot: {str(e)}")

    # Group comparisons
    try:
        comparison_data = pd.DataFrame(break_comparisons).T
        fig.add_trace(
            go.Scatter(
                x=comparison_data.index,
                y=comparison_data.get('duration_difference', [0] * len(comparison_data)),
                mode='markers',
                marker=dict(
                    size=10,
                    color=comparison_data.get('p_value', [1] * len(comparison_data)),
                    colorscale='RdBu',
                    showscale=True
                ),
                name='Break Duration Difference'
            ),
            row=2, col=2
        )
        fig.update_yaxes(title_text="Duration Difference", row=2, col=2)
    except Exception as e:
        print(f"Warning: Could not create group comparisons plot: {str(e)}")

    # Update layout
    fig.update_layout(
        height=1000,
        width=1200,
        showlegend=True,
        title_text="Break Analysis Results",
        title_x=0.5,
        legend=dict(
            yanchor="top",
            y=0.99,
            xanchor="right",
            x=0.99
        ),
        margin=dict(t=100, l=50, r=50, b=50)
    )

    # Add explanatory annotations
    fig.add_annotation(
        text=(
            "How to read this dashboard:<br>" +
            "• Top left: Distribution of break durations<br>" +
            "• Top right: When breaks typically occur<br>" +
            "• Bottom left: Average stress reduction during breaks<br>" +
            "• Bottom right: Statistical comparison between groups"
        ),
        xref="paper", yref="paper",
        x=1.15, y=0.5,
        showarrow=False,
        align="left",
        bgcolor="white",
        bordercolor="black",
        borderwidth=1
    )

    return fig


def create_time_patterns_plot(time_patterns):
    """Create visualization of time-of-day patterns split by productivity levels."""
    
    # Define consistent colors for groups
    colors = {
        'DALMUIR': '#1f77b4',    # blue
        'KB3': '#2ca02c',        # green
        'KILMALID': '#ff7f0e'    # orange
    }
    
    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=(
            "Biometric Productivity - High Productivity Periods",
            "Biometric Productivity - Normal Productivity Periods",
            "Pattern Comparison"
        ),
        vertical_spacing=0.15
    )

    # Separate high and normal productivity periods
    high_prod = time_patterns[time_patterns['is_high_prod']]
    normal_prod = time_patterns[~time_patterns['is_high_prod']]

    # High productivity patterns
    for group in sorted(high_prod['standardized_group'].unique()):
        group_data = high_prod[high_prod['standardized_group'] == group]
        
        fig.add_trace(
            go.Scatter(
                x=group_data['time_of_day'],
                y=group_data['stress_score_mean'],
                name=group,
                mode='lines+markers',
                line=dict(color=colors[group], width=2),
                marker=dict(size=6),
                showlegend=True
            ),
            row=1, col=1
        )

    # Normal productivity patterns
    for group in sorted(normal_prod['standardized_group'].unique()):
        group_data = normal_prod[normal_prod['standardized_group'] == group]
        
        fig.add_trace(
            go.Scatter(
                x=group_data['time_of_day'],
                y=group_data['stress_score_mean'],
                name=group,
                mode='lines+markers',
                line=dict(color=colors[group], width=2),
                marker=dict(size=6),
                showlegend=False
            ),
            row=1, col=2
        )

    # Pattern comparison (difference)
    for group in time_patterns['standardized_group'].unique():
        group_high = high_prod[high_prod['standardized_group'] == group]
        group_normal = normal_prod[normal_prod['standardized_group'] == group]
        
        # Merge on time_of_day to calculate difference
        comparison = pd.merge(
            group_high, 
            group_normal, 
            on='time_of_day',
            suffixes=('_high', '_normal')
        )
        
        fig.add_trace(
            go.Scatter(
                x=comparison['time_of_day'],
                y=comparison['stress_score_mean_high'] - comparison['stress_score_mean_normal'],
                name=group,
                mode='lines+markers',
                line=dict(color=colors[group], width=2),
                marker=dict(size=6),
                showlegend=False
            ),
            row=2, col=1
        )

    # Update layout
    fig.update_layout(
        height=800,  # Reduced height since we removed participation chart
        showlegend=True,
        title_text="Time-of-Day Patterns by Productivity Level",
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        )
    )

    # Update axes labels
    fig.update_xaxes(title="Time of Day", row=2, col=1)
    fig.update_xaxes(title="Time of Day", row=1, col=1)
    fig.update_xaxes(title="Time of Day", row=1, col=2)
    
    fig.update_yaxes(title="Biometric Productivity", row=1, col=1)
    fig.update_yaxes(title="Biometric Productivity", row=1, col=2)
    fig.update_yaxes(title="Difference in Biometric Productivity", row=2, col=1)

    return fig


def create_peak_visualization(peak_patterns, recovery_metrics):
    """Create visualization for peak analysis focusing on time distribution."""
    
    # Define consistent colors for groups
    colors = {
        'DALMUIR': '#1f77b4',    # blue
        'KB3': '#2ca02c',        # green
        'KILMALID': '#ff7f0e'    # orange
    }
    
    # Create single plot
    fig = go.Figure()
    
    # Define working hours
    working_hours = range(8, 18)  # 8am to 5pm (17:00)
    
    # Add bar plots for each group
    for group in sorted(peak_patterns.keys()):
        distribution = peak_patterns[group]['peak_distribution']
        
        # Create working hours range with zeros for missing hours
        working_hours_data = pd.Series(0, index=working_hours)
        working_hours_data.update(distribution[distribution.index.isin(working_hours)])
        
        # Add bar plot
        fig.add_trace(
            go.Bar(
                x=working_hours_data.index,
                y=working_hours_data.values,
                name=f"{group} - Peaks",
                marker_color=colors[group],
                opacity=0.7
            )
        )
        
        # Add line plot connecting peaks
        fig.add_trace(
            go.Scatter(
                x=working_hours_data.index,
                y=working_hours_data.values,
                name=f"{group} - Trend",
                line=dict(
                    color=colors[group],
                    width=2
                ),
                mode='lines'
            )
        )

    # Update layout
    fig.update_layout(
        title="Peak Distribution Throughout the Working Day",
        xaxis_title="Hour of Day",
        yaxis_title="Number of Peaks",
        height=600,
        width=1000,
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        ),
        xaxis=dict(
            tickmode='array',
            ticktext=[f'{i:02d}:00' for i in working_hours],
            tickvals=list(working_hours),
            tickangle=90,
            range=[7.5, 17.5]  # Set range to show 8am-5pm with some padding
        ),
        plot_bgcolor='white',
        bargap=0.15
    )
    
    # Update axes
    fig.update_xaxes(
        showgrid=True,
        gridwidth=1,
        gridcolor='lightgrey'
    )
    
    fig.update_yaxes(
        showgrid=True,
        gridwidth=1,
        gridcolor='lightgrey'
    )

    return fig
