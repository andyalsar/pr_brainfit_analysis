# PR_brainfit_analysis/visualization/plots.py

import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
from ..config.settings import *
import matplotlib
import matplotlib.colors

def create_stress_patterns_plot(hourly_patterns):
    """Create 15-min interval body stress pattern visualization for PR teams"""
    # Filter for PR groups only
    pr_groups = ['DALMUIR', 'KILMALID', 'KB3']
    filtered_data = hourly_patterns[hourly_patterns['standardized_group'].isin(pr_groups)]
    
    # Make sure data is sorted by time
    filtered_data = filtered_data.sort_values(['standardized_group', 'time'])
    
    fig = go.Figure()
    
    # Color scheme for groups
    colors = {
        'DALMUIR': '#1f77b4',    # blue
        'KB3': '#2ca02c',        # green
        'KILMALID': '#ff7f0e'    # orange
    }
    
    for group in filtered_data['standardized_group'].unique():
        group_data = filtered_data[filtered_data['standardized_group'] == group]
        
        # Add mean line
        fig.add_trace(go.Scatter(
            x=group_data['time'],
            y=group_data['stress_mean'],
            name=f"{group} - Mean",
            mode='lines+markers',
            line=dict(
                color=colors[group],
                width=2
            ),
            marker=dict(
                size=8,
                color=colors[group]
            ),
            showlegend=True
        ))
        
        # Add standard deviation range
        fig.add_trace(go.Scatter(
            x=group_data['time'],
            y=group_data['stress_mean'] + group_data['stress_std'],
            name=f"{group} - Upper",
            mode='lines',
            line=dict(width=0),
            showlegend=False
        ))
        
        fig.add_trace(go.Scatter(
            x=group_data['time'],
            y=group_data['stress_mean'] - group_data['stress_std'],
            name=f"{group} - Lower",
            mode='lines',
            line=dict(width=0),
            fill='tonexty',
            fillcolor=f'rgba{tuple(list(matplotlib.colors.to_rgb(colors[group])) + [0.2])}',
            showlegend=False
        ))
    
    # Update layout with expanded time range
    fig.update_layout(
        title="Team Body Stress Patterns Throughout Working Hours",
        xaxis_title="Time of Day",
        yaxis_title="Body Stress Score",
        hovermode='x unified',
        height=600,
        width=1000,
        margin=dict(t=100, l=50, r=50, b=50),
        xaxis=dict(
            tickangle=45,
            gridcolor='lightgrey',
            zeroline=True,
            zerolinecolor='lightgrey',
            # Add range to show full working hours
            range=['08:00', '17:00']
        ),
        yaxis=dict(
            gridcolor='lightgrey',
            zeroline=True,
            zerolinecolor='lightgrey'
        ),
        plot_bgcolor='white'
    )
    
    return fig

def create_stress_patterns_heatmap(patterns):
    """Create heat map visualization of body stress patterns for PR teams"""
    # Filter for PR groups only
    pr_groups = ['DALMUIR', 'KILMALID', 'KB3']
    filtered_data = patterns[patterns['standardized_group'].isin(pr_groups)]
    
    # Create heat map data
    heatmap_data = []
    
    for group in pr_groups:
        group_data = filtered_data[filtered_data['standardized_group'] == group]
        for _, row in group_data.iterrows():
            heatmap_data.append({
                'group': group,
                'time': row['time'],
                'stress': row['stress_mean']
            })
    
    # Convert to DataFrame for plotting
    heatmap_df = pd.DataFrame(heatmap_data)
    
    # Pivot the data for the heatmap
    pivot_data = heatmap_df.pivot(
        index='group',
        columns='time',
        values='stress'
    )
    
    # Create single heatmap
    fig = go.Figure(
        go.Heatmap(
            z=pivot_data.values,
            x=pivot_data.columns,
            y=pivot_data.index,
            colorscale='RdYlBu_r',
            showscale=False,  # First attempt to remove colorbar
            colorbar=None     # Explicitly set colorbar to None
        )
    )
    
    # Update layout
    fig.update_layout(
        title="Team Body Stress Patterns Throughout Working Hours",
        height=400,
        width=1200,
        xaxis=dict(
            title="Time of Day",
            tickangle=45,
            tickmode='array',
            ticktext=pivot_data.columns[::4],  # Show every 4th time point
            tickvals=pivot_data.columns[::4],
            gridcolor='lightgrey'
        ),
        yaxis=dict(
            title="",
            gridcolor='lightgrey'
        ),
        margin=dict(t=100, l=50, r=50, b=100)
    )
    
    return fig

def create_activity_distribution_plot(patterns_df):
    """Create activity level distribution plot by team in 15-min intervals"""
    pr_groups = ['DALMUIR', 'KILMALID', 'KB3']
    
    # Create subplots - one row per group
    fig = make_subplots(
        rows=3, cols=1,
        subplot_titles=[f"{group} Activity Distribution" for group in pr_groups],
        shared_xaxes=True,
        vertical_spacing=0.08
    )
    
    # Softer colors
    colors = {
        'intense': '#ff6666',     # stronger red
        'moderate': '#ffcc66',    # stronger orange
        'light': '#66cc66',       # stronger green
        'sedentary': '#66b3ff'    # stronger blue
    }
    
    # Add stacked bars for each group
    for i, group in enumerate(pr_groups, 1):
        group_data = patterns_df[patterns_df['standardized_group'] == group]
        
        for activity in ['sedentary', 'light', 'moderate', 'intense']:
            fig.add_trace(
                go.Bar(
                    name=activity.capitalize(),
                    x=group_data['time'],
                    y=[d[activity]/sum(d.values())*100 for d in group_data['activity_level']],
                    marker_color=colors[activity],
                    showlegend=(i==1)
                ),
                row=i, col=1
            )
            
        # Calculate and add trend line of total activity
        active_pct = [
            sum(d[k] for k in ['light','moderate','intense'])/sum(d.values())*100 
            for d in group_data['activity_level']
        ]
        
        fig.add_trace(
            go.Scatter(
                x=group_data['time'],
                y=active_pct,
                name=f"{group} Activity Trend",
                line=dict(color='rgba(0,0,0,0.3)', width=1.5),  # Lighter black line
                showlegend=False
            ),
            row=i, col=1
        )
    
    fig.update_layout(
        height=900,
        barmode='stack',
        title="Activity Distribution Throughout the Day by Group",
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        )
    )
    
    # Update axes
    for i in range(3):
        fig.update_yaxes(title="Percentage", range=[0, 100], row=i+1, col=1)
    fig.update_xaxes(title="Time of Day", row=3, col=1)
    
    return fig

def add_participant_count_overlay(fig, patterns_df):
    """Add participant count overlay to existing visualization"""
    # Add secondary y-axis showing participant count
    for group in patterns_df['standardized_group'].unique():
        group_data = patterns_df[patterns_df['standardized_group'] == group]
        
        # Count participants based on sum of activity levels
        participant_counts = group_data.apply(
            lambda x: sum(x['activity_level'].values()) > 0,  # Changed this line
            axis=1
        ).astype(int)
        
        fig.add_trace(
            go.Scatter(
                x=group_data['time'],
                y=participant_counts,
                name=f"{group} - Participants",
                yaxis='y2',
                line=dict(dash='dot'),
                showlegend=True
            )
        )
    
    fig.update_layout(
        yaxis2=dict(
            title="Number of Participants",
            overlaying='y',
            side='right',
            range=[0, 10]  # Adjust based on max participants
        )
    )
    
    return fig

def create_participation_heatmap(df):
    """Create heatmap showing number of participants over time"""
    # Resample data to 15-min intervals and count unique participants
    participation_df = df.groupby(
        ['standardized_group', pd.Grouper(key='local_time', freq='15min')] 
    )['user_id'].nunique().reset_index()
    
    fig = px.imshow(
        participation_df.pivot(
            index='standardized_group',
            columns='local_time',
            values='user_id'
        ),
        title="Participant Coverage Over Time",
        labels={'color': 'Number of Participants'},
        aspect='auto'
    )
    
    return fig

def create_temporal_pattern_analysis(df):
    """Analyze and visualize patterns over weeks/months"""
    # Create weekly averages
    weekly_stats = df.groupby(
        ['standardized_group', pd.Grouper(key='local_time', freq='W')]
    ).agg({
        'stress_score': ['mean', 'std'],
        'user_id': 'nunique',
        'heart_rate': 'mean'
    }).reset_index()
    
    # Create visualization with multiple subplots
    fig = make_subplots(
        rows=3, cols=1,
        subplot_titles=(
            "Weekly Average Stress Score",
            "Weekly Average Heart Rate",
            "Number of Active Participants"
        )
    )
    
    for group in weekly_stats['standardized_group'].unique():
        group_data = weekly_stats[weekly_stats['standardized_group'] == group]
        
        # Stress score trend
        fig.add_trace(
            go.Scatter(
                x=group_data['local_time'],
                y=group_data[('stress_score', 'mean')],
                name=f"{group} - Stress",
                error_y=dict(
                    type='data',
                    array=group_data[('stress_score', 'std')],
                    visible=True
                )
            ),
            row=1, col=1
        )
        
        # Heart rate trend
        fig.add_trace(
            go.Scatter(
                x=group_data['local_time'],
                y=group_data[('heart_rate', 'mean')],
                name=f"{group} - HR"
            ),
            row=2, col=1
        )
        
        # Participation trend
        fig.add_trace(
            go.Scatter(
                x=group_data['local_time'],
                y=group_data[('user_id', 'nunique')],
                name=f"{group} - Participants"
            ),
            row=3, col=1
        )
    
    fig.update_layout(
        height=900,
        showlegend=True,
        title="Long-term Patterns Analysis"
    )
    
    return fig

def create_monthly_comparison(df):
    """Compare patterns between months"""
    # Create working copy
    df = df.copy()
    
    # Add month and year columns
    df['month'] = df['local_time'].dt.month
    df['year'] = df['local_time'].dt.year
    df['hour_minute'] = df['local_time'].dt.strftime('%H:%M')
    
    monthly_patterns = df.groupby(
        ['standardized_group', 'year', 'month', 'hour_minute']
    ).agg({
        'stress_score': ['mean', 'std'],
        'user_id': 'nunique'
    }).reset_index()
    
    # Flatten column names
    monthly_patterns.columns = [
        f"{col[0]}_{col[1]}" if col[1] else col[0] 
        for col in monthly_patterns.columns
    ]
    
    fig = px.scatter(
        monthly_patterns,
        x='hour_minute',
        y='stress_score_mean',
        color='standardized_group',
        facet_row='month',
        error_y='stress_score_std',
        size='user_id_nunique',
        title="Monthly Stress Patterns Comparison",
        labels={
            'hour_minute': 'Time of Day',
            'stress_score_mean': 'Average Stress Score',
            'user_id_nunique': 'Number of Participants'
        }
    )
    
    return fig

def create_productivity_metrics_plot(cask_df):
    """Create comprehensive visualization of all productivity metrics"""
    
    # Create subplots in a 2x2 grid (removed YTD cumulative and ratio)
    fig = make_subplots(
        rows=2, cols=2,
            subplot_titles=(
                "Monthly Volume Trends - Site Performance Comparison",
                "Month-over-Month Change",
                "Volume Consistency - Site Stability Analysis"
            ),
        vertical_spacing=0.15,
        horizontal_spacing=0.12
    )
    
    colors = {
        'DALMUIR': '#1f77b4',
        'KILMALID': '#ff7f0e',
        'KB3': '#2ca02c'
    }

    # Add short explanations to the subplot titles
    explanations = {
        "Monthly Volume Trends - Site Performance Comparison": "<br>Raw number of cask receipts (solid) and dispatches (dotted) per month",
        "Month-over-Month Change": "<br>Percentage changes vs previous month",
        "Volume Consistency - Site Stability Analysis": "<br>Spread of month-over-month changes"
    }
    
    for site in cask_df['site'].unique():
        site_data = cask_df[cask_df['site'] == site].copy()
        
        # Monthly Volume
        fig.add_trace(
            go.Scatter(
                x=site_data['date'],
                y=site_data['receipts'],
                name=f"{site} - Receipts",
                line=dict(color=colors[site], dash='solid'),
                mode='lines+markers',
                showlegend=True
            ),
            row=1, col=1
        )
        fig.add_trace(
            go.Scatter(
                x=site_data['date'],
                y=site_data['dispatches'],
                name=f"{site} - Dispatches",
                line=dict(color=colors[site], dash='dot'),
                mode='lines+markers',
                showlegend=True
            ),
            row=1, col=1
        )
        
        # Month-over-Month Changes
        fig.add_trace(
            go.Bar(
                x=site_data['date'],
                y=site_data['receipts_mom_var'],
                name=f"{site} - Receipts MoM",
                marker_color=colors[site],
                opacity=0.7,
                showlegend=False
            ),
            row=1, col=2
        )
        fig.add_trace(
            go.Bar(
                x=site_data['date'],
                y=site_data['dispatches_mom_var'],
                name=f"{site} - Dispatches MoM",
                marker_color=colors[site],
                opacity=0.3,
                showlegend=False
            ),
            row=1, col=2
        )
        
        # Volatility Analysis
        fig.add_trace(
            go.Box(
                y=abs(site_data['receipts_mom_var']),
                name=f"{site} - Receipts",
                marker_color=colors[site],
                boxpoints='all',
                showlegend=False
            ),
            row=2, col=1
        )
        fig.add_trace(
            go.Box(
                y=abs(site_data['dispatches_mom_var']),
                name=f"{site} - Dispatches",
                marker_color=colors[site],
                opacity=0.6,
                boxpoints='all',
                showlegend=False
            ),
            row=2, col=1
        )

    # Update subplot titles with explanations
    for i, title in enumerate(fig.layout.annotations[:3]):  # Changed from 6 to 3
        title.text = title.text + explanations[title.text]
        title.font.size = 10
    
    # Update layout
    fig.update_layout(
        height=800,  # Reduced height since we removed charts
        width=1200,
        showlegend=True,
        title_text="Comprehensive Productivity Analysis",
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        )
    )
    
    # Update axes labels
    fig.update_yaxes(title_text="Volume", row=1, col=1)
    fig.update_yaxes(title_text="% Change", row=1, col=2)
    fig.update_yaxes(title_text="Absolute % Change", row=2, col=1)
    
    # Update x-axis labels
    fig.update_xaxes(title_text="Date", row=1, col=1)
    fig.update_xaxes(title_text="Date", row=1, col=2)
    fig.update_xaxes(title_text="", row=2, col=1)
    
    return fig


def create_comprehensive_dashboard(cleaned_df, pattern_results, correlation_results):
    """Create comprehensive dashboard with all analyses"""
    
    # Create subplot grid
    fig = make_subplots(
        rows=4, cols=2,
        subplot_titles=[
            "Daily Stress Patterns", "Activity Distribution",
            "Participation Coverage", "Temporal Patterns",
            "Monthly Comparison", "Correlation Analysis",
            "Stress Heatmap", "Data Quality Overview"
        ],
        vertical_spacing=0.1,
        horizontal_spacing=0.1,
        specs=[
            [{"type": "scatter"}, {"type": "bar"}],
            [{"type": "heatmap"}, {"type": "scatter"}],
            [{"type": "scatter"}, {"type": "heatmap"}],
            [{"type": "heatmap", "colspan": 2}, None]
        ]
    )
    
    # Add daily patterns
    stress_plot = create_stress_patterns_plot(pattern_results['hourly_patterns'])
    add_participant_count_overlay(stress_plot, pattern_results['hourly_patterns'])
    for trace in stress_plot.data:
        fig.add_trace(trace, row=1, col=1)
    
    # Add activity distribution
    activity_plot = create_activity_distribution_plot(pattern_results['hourly_patterns'])
    for trace in activity_plot.data:
        fig.add_trace(trace, row=1, col=2)
    
    # Add participation heatmap
    participation_map = create_participation_heatmap(cleaned_df)
    fig.add_trace(participation_map.data[0], row=2, col=1)
    
    # Add temporal patterns
    temporal_patterns = create_temporal_pattern_analysis(cleaned_df)
    for trace in temporal_patterns.data:
        fig.add_trace(trace, row=2, col=2)
    
    # Add monthly comparison
    monthly_comparison = create_monthly_comparison(cleaned_df)
    for trace in monthly_comparison.data:
        fig.add_trace(trace, row=3, col=1)
    
    # Add correlation heatmap
    correlation_plot = create_correlation_plots(correlation_results)
    fig.add_trace(correlation_plot.data[0], row=3, col=2)
    
    # Add stress heatmap at bottom
    stress_heatmap = create_stress_patterns_heatmap(pattern_results['hourly_patterns'])
    fig.add_trace(stress_heatmap.data[0], row=4, col=1)
    
    # Update layout
    fig.update_layout(
        height=2000,  # Increased height for better visibility
        width=1500,
        showlegend=True,
        title_text="Comprehensive Analysis Dashboard",
        title_x=0.5,
        title_font_size=24
    )
    
    return fig

def create_productivity_correlation_plot(df, cask_df):
    """Create correlation plot between stress and productivity (receipts only)"""
    # Ensure date is datetime type
    df = df.copy()
    df['date'] = pd.to_datetime(df['date'])
    df = df.set_index('date')
    
    # Aggregate stress scores to monthly level
    monthly_stress = df[df['is_working_hours']].groupby(
        ['standardized_group', pd.Grouper(freq='ME')]
    )['stress_score'].mean().reset_index()
    
    # Convert end-of-month dates to start-of-month dates to match cask data
    monthly_stress['date'] = monthly_stress['date'].dt.to_period('M').dt.to_timestamp()
    
    # Ensure cask_df date is in the right format
    cask_df = cask_df.copy()
    cask_df['date'] = pd.to_datetime(cask_df['date'])
    
    # Merge with cask data
    merged_data = monthly_stress.merge(
        cask_df,
        left_on=['standardized_group', 'date'],
        right_on=['site', 'date']
    )
    
    # Define consistent colors for each group
    color_map = {
        'DALMUIR': '#1f77b4',    # blue
        'KB3': '#2ca02c',        # green
        'KILMALID': '#ff7f0e'    # orange
    }
    
    # Create single subplot for stress vs receipts
    fig = go.Figure()
    
    # Add one trace per group showing only receipts
    for group in merged_data['standardized_group'].unique():
        group_data = merged_data[merged_data['standardized_group'] == group]
        
        fig.add_trace(
            go.Scatter(
                x=group_data['stress_score'],
                y=group_data['receipts'],
                mode='markers',
                name=group,
                marker=dict(
                    color=color_map[group],
                    size=12,
                    symbol='circle'
                ),
                text=[f"{group}<br>{d.strftime('%Y-%m')}<br>Receipts: {r}<br>Stress: {s:.1f}" 
                      for d, r, s in zip(group_data['date'], 
                                       group_data['receipts'], 
                                       group_data['stress_score'])],
                hovertemplate="%{text}<extra></extra>"
            )
        )
    
    # Update layout
    fig.update_layout(
        title="Team Biometric Productivity (active roles) vs Monthly Receipts",
        xaxis_title="Average Stress Score",
        yaxis_title="Monthly Receipts",
        showlegend=True,
        hovermode='closest',
        height=500,
        width=800,
        margin=dict(t=100, l=50, r=50, b=50),
        plot_bgcolor='white'
    )
    
    # Update axes for better formatting
    fig.update_xaxes(
        gridcolor='lightgrey',
        zeroline=True,
        zerolinecolor='lightgrey'
    )
    
    fig.update_yaxes(
        gridcolor='lightgrey',
        zeroline=True,
        zerolinecolor='lightgrey'
    )
    
    return fig

def create_correlation_plots(correlation_results):
    """Create correlation visualization between physical metrics and productivity"""
    
    # Create subplots for each group
    groups = list(correlation_results['correlations'].keys())
    
    fig = make_subplots(
        rows=len(groups), cols=1,
        subplot_titles=[f"{group} Correlations" for group in groups],
        vertical_spacing=0.1
    )
    
    # Add correlation heatmap for each group
    for idx, group in enumerate(groups, 1):
        correlations = correlation_results['correlations'][group]
        p_values = correlation_results['statistics'][group]
        
        # Create annotation text showing correlation and p-value
        annotations = []
        for i in range(len(correlations.index)):
            for j in range(len(correlations.columns)):
                corr = correlations.iloc[i, j]
                p_val = p_values.iloc[i, j]
                if not pd.isna(corr):
                    annotations.append(
                        f"r={corr:.2f}<br>p={p_val:.3f}"
                    )
                else:
                    annotations.append("")
        
        # Add heatmap trace
        fig.add_trace(
            go.Heatmap(
                z=correlations.values,
                x=correlations.columns,
                y=correlations.index,
                text=annotations,
                texttemplate="%{text}",
                textfont={"size": 10},
                colorscale='RdBu',
                zmid=0,
                zmin=-1,
                zmax=1,
                showscale=True if idx == 1 else False
            ),
            row=idx, col=1
        )
    
    # Update layout
    fig.update_layout(
        height=200 * len(groups),
        title="Physical Metrics vs Productivity Correlations",
        showlegend=False
    )
    
    return fig

def create_monthly_summary_plot(monthly_data):
    """Create comprehensive monthly comparison of productivity and biometrics."""
    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=(
            "Key Chart 12: Monthly Site Productivity - Direct Volume Comparison",
            "Key Chart 13: Stress-Productivity Relationship - Impact Analysis",
            "Key Chart 14: Monthly Stress Patterns - Team Wellbeing Trends",
            "Key Chart 15: Productivity Per Stress Unit - Team Efficiency Analysis"
        ),
        vertical_spacing=0.15
    )

    # Productivity trends
    for group in monthly_data['standardized_group'].unique():
        group_data = monthly_data[monthly_data['standardized_group'] == group]
        
        fig.add_trace(
            go.Scatter(
                x=pd.to_datetime(group_data[['year', 'month']].assign(day=1)),
                y=group_data['receipts'],
                name=f"{group} - Receipts",
                mode='lines+markers'
            ),
            row=1, col=1
        )

    # Stress vs Productivity scatter
    for group in monthly_data['standardized_group'].unique():
        group_data = monthly_data[monthly_data['standardized_group'] == group]
        
        fig.add_trace(
            go.Scatter(
                x=group_data['stress_score_mean'],
                y=group_data['receipts'],
                mode='markers',
                name=group,
                text=[f"{y}-{m}" for y, m in zip(group_data['year'], group_data['month'])],
                hovertemplate="Month: %{text}<br>Stress: %{x:.1f}<br>Receipts: %{y:,}"
            ),
            row=1, col=2
        )

    # Monthly stress distributions
    for group in monthly_data['standardized_group'].unique():
        group_data = monthly_data[monthly_data['standardized_group'] == group]
        
        fig.add_trace(
            go.Box(
                y=group_data['stress_score_mean'],
                name=group,
                boxpoints='all'
            ),
            row=2, col=1
        )

    # Productivity per stress unit
    for group in monthly_data['standardized_group'].unique():
        group_data = monthly_data[monthly_data['standardized_group'] == group]
        
        fig.add_trace(
            go.Bar(
                x=pd.to_datetime(group_data[['year', 'month']].assign(day=1)),
                y=group_data['productivity_stress_ratio'],
                name=f"{group} - Efficiency"
            ),
            row=2, col=2
        )

    fig.update_layout(
        height=1000,
        title_text="Monthly Productivity and Stress Analysis",
        showlegend=True
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

def create_daily_patterns_plot(daily_patterns):
    """Create visualization of daily patterns in high vs normal productivity periods."""
    
    # Define consistent colors for groups
    colors = {
        'DALMUIR': '#1f77b4',    # blue
        'KB3': '#2ca02c',        # green
        'KILMALID': '#ff7f0e'    # orange
    }
    
    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=(
            "Average Biometric Productivity (Active Worker) During High-Volume Months",
            "Average Biometric Productivity (Active Worker) During Normal-Volume Months",
            "Biometric Productivity Difference (High vs Normal Volume)"
        ),
        vertical_spacing=0.15
    )

    # Separate high and normal productivity days
    high_prod = daily_patterns[daily_patterns['is_high_prod']]
    normal_prod = daily_patterns[~daily_patterns['is_high_prod']]

    # High productivity days
    for group in sorted(high_prod['standardized_group'].unique()):
        group_data = high_prod[high_prod['standardized_group'] == group]
        
        fig.add_trace(
            go.Box(
                y=group_data['stress_score_mean'],
                name=group,
                marker_color=colors[group],
                boxpoints='all',
                showlegend=True,  # Only show legend for first subplot
                hovertemplate=(
                    "Group: %{fullData.name}<br>" +
                    "Biometric Productivity: %{y:.1f}<br>" +
                    "<extra></extra>"
                )
            ),
            row=1, col=1
        )

    # Normal productivity days
    for group in sorted(normal_prod['standardized_group'].unique()):
        group_data = normal_prod[normal_prod['standardized_group'] == group]
        
        fig.add_trace(
            go.Box(
                y=group_data['stress_score_mean'],
                name=group,
                marker_color=colors[group],
                boxpoints='all',
                showlegend=False,  # Don't repeat in legend
                hovertemplate=(
                    "Group: %{fullData.name}<br>" +
                    "Biometric Productivity: %{y:.1f}<br>" +
                    "<extra></extra>"
                )
            ),
            row=1, col=2
        )

    # Pattern comparison (High vs Normal Volume Difference)
    for group in sorted(daily_patterns['standardized_group'].unique()):
        high_mean = high_prod[high_prod['standardized_group'] == group]['stress_score_mean'].mean()
        normal_mean = normal_prod[normal_prod['standardized_group'] == group]['stress_score_mean'].mean()
        
        fig.add_trace(
            go.Bar(
                x=[group],
                y=[high_mean - normal_mean],
                name=group,
                marker_color=colors[group],
                showlegend=False,  # Don't repeat in legend
                hovertemplate=(
                    "Group: %{x}<br>" +
                    "Difference: %{y:.1f}<br>" +
                    "<extra></extra>"
                )
            ),
            row=2, col=1
        )

    # Update layout
    fig.update_layout(
        height=800,  # Reduced height since we removed one subplot
        showlegend=True,
        title={
            'text': "Biometric Productivity Patterns Analysis: High Volume vs Normal Volume Months",
            'y': 0.95,
            'x': 0.5,
            'xanchor': 'center',
            'yanchor': 'top',
            'font': {'size': 20}
        }
    )
    
    # Update axes labels
    fig.update_yaxes(title="Biometric Productivity", row=1, col=1)
    fig.update_yaxes(title="Biometric Productivity", row=1, col=2)
    fig.update_yaxes(title="Biometric Productivity Difference", row=2, col=1)
    
    return fig

