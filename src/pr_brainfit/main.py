# PR_brainfit_analysis/main.py
import webbrowser
import traceback
from pr_brainfit.analysis.statistical_tests import run_time_comparisons, analyze_group_differences
from pr_brainfit.analysis.pattern_analysis import analyze_daily_patterns, calculate_group_variance, find_recurring_patterns
from pr_brainfit.analysis.group_analysis import calculate_consistency_scores, identify_outliers, compare_group_variability
from pr_brainfit.analysis.activity_analysis import analyze_activity_distribution, calculate_transition_probabilities
from pr_brainfit.analysis.break_analysis import detect_breaks, analyze_break_patterns, compare_group_breaks
from pr_brainfit.analysis.peak_analysis import detect_peaks, analyze_peak_patterns, calculate_recovery_metrics

import pandas as pd

from plotly.subplots import make_subplots
import plotly.graph_objects as go

from pr_brainfit.analysis.metrics import (
    analyze_team_patterns, 
    analyze_productivity_correlations,
    create_layered_analysis
)

from pr_brainfit.data.loaders import load_biometric_data, load_user_data, load_cask_data
from pr_brainfit.data.processor import clean_biometric_data, calculate_individual_baselines
from pr_brainfit.visualization.plots import (
    create_stress_patterns_heatmap,
    create_daily_patterns_plot
)
from pr_brainfit.visualization.advanced_plots import (
    create_patterns_visualization,
    create_peak_visualization
)
from pr_brainfit.config.settings import *

output_dir = OUTPUT_DIR

def print_date_ranges(df, original_df):
    """Print the date range of heart rate data for PR groups and others"""
    print("\nHeart Rate Data Date Ranges:")
    print("=" * 80)
    
    # PR Groups Analysis
    print("\nPR GROUPS:")
    print("-" * 50)
    for group in sorted(df['standardized_group'].unique()):
        group_data = df[df['standardized_group'] == group]
        start_date = group_data['local_time'].min()
        end_date = group_data['local_time'].max()
        total_days = (end_date - start_date).days
        
        print(f"\n{group}:")
        print(f"Start date: {start_date.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"End date:   {end_date.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Total days: {total_days}")
        
        # Individual user last dates
        print("\nLast date per user:")
        for user_id in group_data['user_id'].unique():
            user_last_date = group_data[group_data['user_id'] == user_id]['local_time'].max()
            print(f"User {user_id}: {user_last_date.strftime('%Y-%m-%d %H:%M:%S')}")

    # Non-PR Users Analysis
    print("\n\nNON-PR USERS:")
    print("-" * 50)
    
    # Get all user_ids in original data that aren't in PR data
    pr_user_ids = set(df['user_id'].unique())
    non_pr_users = original_df[~original_df['user_id'].isin(pr_user_ids)]
    
    if len(non_pr_users) > 0:
        start_date = non_pr_users['timestamp'].min()
        end_date = non_pr_users['timestamp'].max()
        total_days = (end_date - start_date).days
        total_users = non_pr_users['user_id'].nunique()
        
        print(f"\nTotal non-PR users: {total_users}")
        print(f"Start date: {start_date.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"End date:   {end_date.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Total days: {total_days}")
        
        # Sample of last dates for non-PR users
        print("\nLast 5 records:")
        last_records = non_pr_users.sort_values('timestamp', ascending=False).head()
        for _, record in last_records.iterrows():
            print(f"User {record['user_id']}: {record['timestamp'].strftime('%Y-%m-%d %H:%M:%S')}")
    else:
        print("\nNo non-PR users found in the data")

def create_key_findings_dashboard(cleaned_df, cask_df, pattern_results, correlation_results, layered_analysis):
    """Create focused dashboard with only the key charts for analysis."""
    
    # Create subplots with 2x2 grid
    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=(
            "Monthly Volume Trends - Site Performance Comparison",
            "Month-over-Month Change",
            "Volume Consistency - Site Stability Analysis",
            "Team Working Patterns - Hour by Hour Biometric Stress Levels"
        ),
        vertical_spacing=0.22,
        horizontal_spacing=0.15
    )

    colors = {
        'DALMUIR': '#1f77b4',
        'KILMALID': '#ff7f0e',
        'KB3': '#2ca02c'
    }

    # 1. Monthly Volume Trends (Key Chart 6)
    for site in cask_df['site'].unique():
        site_data = cask_df[cask_df['site'] == site].copy()
        
        # Add receipts line
        fig.add_trace(
            go.Scatter(
                x=site_data['date'],
                y=site_data['receipts'],
                name=f"{site} - Receipts",
                line=dict(color=colors[site], dash='solid'),
                mode='lines+markers'
            ),
            row=1, col=1
        )
        
        # Add dispatches line
        fig.add_trace(
            go.Scatter(
                x=site_data['date'],
                y=site_data['dispatches'],
                name=f"{site} - Dispatches",
                line=dict(color=colors[site], dash='dot'),
                mode='lines+markers'
            ),
            row=1, col=1
        )

    # 2. Month-over-Month Growth (Key Chart 7)
    for site in cask_df['site'].unique():
        site_data = cask_df[cask_df['site'] == site].copy()
        fig.add_trace(
            go.Bar(
                x=site_data['date'],
                y=site_data['receipts_mom_var'],
                name=f"{site} MoM Change",
                marker_color=colors[site]
            ),
            row=1, col=2
        )

    # 3. Volume Consistency (Key Chart 8)
    for site in cask_df['site'].unique():
        site_data = cask_df[cask_df['site'] == site].copy()
        fig.add_trace(
            go.Box(
                y=abs(site_data['receipts_mom_var']),
                name=site,
                marker_color=colors[site]
            ),
            row=2, col=1
        )

    # 4. Team Working Patterns (Key Chart 3)
    stress_heatmap = create_stress_patterns_heatmap(pattern_results['hourly_patterns'])
    for trace in stress_heatmap.data:
        fig.add_trace(trace, row=2, col=2)

    # Update layout
    fig.update_layout(
        height=1200,
        width=1400,
        showlegend=True,
        title={
            'text': "Key Findings Analysis - PR Groups Comparison",
            'y': 0.98,
            'x': 0.5,
            'xanchor': 'center',
            'yanchor': 'top',
            'font': {'size': 24}
        }
    )

    # Add axis updates
    fig.update_yaxes(title="Volume", row=1, col=1)
    fig.update_yaxes(
        title="Absolute % Change", 
        tickformat=',.0%',  # Format as percentage without decimal places
        range=[0, 1],     # Set range from 0 to 100%
        row=2, col=1
    )
    fig.update_yaxes(title="Absolute % Change", tickformat='%', row=2, col=1)
    fig.update_yaxes(title="Group", row=2, col=2)

    fig.update_xaxes(title="Date", row=1, col=1)
    fig.update_xaxes(title="Date", row=1, col=2)
    fig.update_xaxes(title="", row=2, col=1)
    fig.update_xaxes(title="Time of Day", row=2, col=2)

    return fig

def main():
    try:
        print("Loading data...")
        biometric_df = load_biometric_data(BIOMETRIC_DATA_PATH)
        user_df = load_user_data()
        cask_df = load_cask_data(CASK_DATA_PATH)
        
        print("Processing data...")
        cleaned_df = clean_biometric_data(biometric_df, user_df)
        baselines = calculate_individual_baselines(cleaned_df)
        
        print("Unique sites in cask data:", cask_df['site'].unique())
        print("Unique groups in cleaned data:", cleaned_df['standardized_group'].unique())
        print("\nCask data preview:")
        print(cask_df.head())
        print_date_ranges(cleaned_df, biometric_df)

        # Core analysis
        print("Running team pattern analysis...")
        pattern_results = analyze_team_patterns(cleaned_df, baselines)
        correlation_results = analyze_productivity_correlations(cleaned_df)
        layered_analysis = create_layered_analysis(cleaned_df, cask_df)

        # Advanced analyses
        print("\nRunning advanced analyses...")
        daily_patterns = analyze_daily_patterns(cleaned_df)
        variance_scores = calculate_group_variance(cleaned_df)
        peaks = detect_peaks(cleaned_df)
        peak_patterns = analyze_peak_patterns(peaks)
        recovery_metrics = calculate_recovery_metrics(peaks)

        # Generate all visualizations
        print("\nGenerating visualizations...")
        output_dir.mkdir(exist_ok=True)

        # 1. Key Findings Dashboard
        print("Creating key findings dashboard...")
        key_findings = create_key_findings_dashboard(
            cleaned_df=cleaned_df,
            cask_df=cask_df,
            pattern_results=pattern_results,
            correlation_results=correlation_results,
            layered_analysis=layered_analysis
        )
        key_findings_path = output_dir / 'key_findings_dashboard.html'
        key_findings.write_html(key_findings_path)

        # 2. Daily Patterns Plot
        daily_patterns_plot = create_daily_patterns_plot(layered_analysis['daily_patterns'])
        daily_patterns_path = output_dir / 'productivity_daily_patterns.html'
        daily_patterns_plot.write_html(daily_patterns_path)

        # 3. Advanced Patterns Plot
        patterns_plot = create_patterns_visualization(daily_patterns, variance_scores)
        patterns_plot_path = output_dir / 'advanced_patterns.html'
        patterns_plot.write_html(patterns_plot_path)
        
        # 4. Peak Analysis Plot
        peak_plot = create_peak_visualization(peak_patterns, recovery_metrics)
        peak_plot_path = output_dir / 'peak_analysis.html'
        peak_plot.write_html(peak_plot_path)

        # Open all visualizations
        visualization_paths = [
            key_findings_path,
            daily_patterns_path,
            patterns_plot_path,
            peak_plot_path
        ]
        
        for path in visualization_paths:
            webbrowser.open(f'file://{path.absolute()}')
        
        print("Analysis complete! All visualizations saved and opened in browser.")
        
        return {
            'patterns': pattern_results,
            'correlations': correlation_results,
            'layered': layered_analysis,
            'advanced': {
                'daily_patterns': daily_patterns,
                'variance_scores': variance_scores,
                'peaks': {
                    'patterns': peak_patterns,
                    'recovery': recovery_metrics
                }
            }
        }
        
    except Exception as e:
        print(f"Error in analysis: {str(e)}")
        traceback.print_exc()
        return None
     
if __name__ == "__main__":
    main()