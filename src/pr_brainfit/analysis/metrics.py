# PR_brainfit_analysis/analysis/metrics.py

import pandas as pd
import pytz
from ..config.settings import *
import scipy.stats as stats
import plotly.graph_objects as go
import matplotlib
from plotly.subplots import make_subplots


def analyze_team_patterns(df, baselines):
    """Analyze patterns in the biometric data by team"""
    df = df.copy()
    
    # Create 15-minute interval timestamps with DST handling
    try:
        df['time_15'] = df['local_time'].dt.floor('15min')
    except pytz.exceptions.AmbiguousTimeError:
        df['time_15'] = df['local_time'].dt.floor('15min', ambiguous='NaT')
        df = df.dropna(subset=['time_15'])
    
    df['hour_minute'] = df['time_15'].dt.strftime('%H:%M')
    df['date'] = df['local_time'].dt.date  # Add date
    df['month'] = df['local_time'].dt.month  # Add month directly
    
    # Create complete time range from 08:00 to 17:00 in 15-min intervals
    all_times = pd.date_range(
        start='2024-01-01 08:00:00',
        end='2024-01-01 17:00:00',
        freq='15min'
    ).strftime('%H:%M').tolist()
    
    # Create patterns with date and month information
    patterns = []
    
    for group in df['standardized_group'].unique():
        group_data = df[
            (df['standardized_group'] == group) & 
            (df['is_working_hours'])
        ]
        
        for time_slot in all_times:
            time_data = group_data[group_data['hour_minute'] == time_slot]
            
            if len(time_data) > 0:
                stress_mean = time_data['stress_score'].mean()
                stress_std = time_data['stress_score'].std()
                date = time_data['date'].iloc[0]  # Get date from the data
                month = time_data['month'].iloc[0]  # Get month from the data
            else:
                stress_mean = None
                stress_std = None
                date = None
                month = None
            
            activity_levels = {
                'sedentary': 0,
                'light': 0,
                'moderate': 0,
                'intense': 0
            }
            
            if len(time_data) > 0:
                for _, row in time_data.iterrows():
                    hr_reserve_used = (row['heart_rate'] - baselines[row['user_id']]['resting_hr']) / \
                                    baselines[row['user_id']]['hr_reserve']
                    
                    if hr_reserve_used <= ACTIVITY_THRESHOLDS['sedentary']/100:
                        activity_levels['sedentary'] += 1
                    elif hr_reserve_used <= ACTIVITY_THRESHOLDS['light']/100:
                        activity_levels['light'] += 1
                    elif hr_reserve_used <= ACTIVITY_THRESHOLDS['moderate']/100:
                        activity_levels['moderate'] += 1
                    else:
                        activity_levels['intense'] += 1
            
            patterns.append({
                'standardized_group': group,
                'time': time_slot,
                'date': date,
                'month': month,
                'stress_mean': stress_mean,
                'stress_std': stress_std,
                'activity_level': activity_levels
            })
    
    patterns_df = pd.DataFrame(patterns)
    patterns_df = patterns_df.sort_values(['standardized_group', 'time'])
    
    # Interpolate missing values within each group
    patterns_df['stress_mean'] = patterns_df.groupby('standardized_group')['stress_mean'].transform(
        lambda x: x.interpolate(method='linear', limit_direction='both')
    )
    patterns_df['stress_std'] = patterns_df.groupby('standardized_group')['stress_std'].transform(
        lambda x: x.interpolate(method='linear', limit_direction='both')
    )
    
    return {
        'hourly_patterns': patterns_df,
        'processed_data': df
    }

def analyze_productivity_correlations(df):
    """Analyze correlations between physical metrics and productivity"""
    
    # Define metric groups
    physical_metrics = ['heart_rate_mean', 'stress_mean']
    productivity_metrics = ['receipts', 'efficiency_ratio']
    
    # Create empty correlation results
    correlation_results = {
        'correlations': {},
        'statistics': {},
        'summary': {}
    }
    
    # Calculate correlations for each group
    for group in df['standardized_group'].unique():
        group_data = df[df['standardized_group'] == group]
        
        # Calculate correlations between physical and productivity metrics
        correlations = pd.DataFrame(
            index=physical_metrics,
            columns=productivity_metrics
        )
        
        # Add p-values matrix
        p_values = correlations.copy()
        
        # Calculate correlations and p-values
        for phys_metric in physical_metrics:
            for prod_metric in productivity_metrics:
                if phys_metric in group_data.columns and prod_metric in group_data.columns:
                    valid_data = group_data[[phys_metric, prod_metric]].dropna()
                    if len(valid_data) > 1:  # Need at least 2 points for correlation
                        correlation, p_value = stats.pearsonr(
                            valid_data[phys_metric],
                            valid_data[prod_metric]
                        )
                        correlations.loc[phys_metric, prod_metric] = correlation
                        p_values.loc[phys_metric, prod_metric] = p_value
        
        correlation_results['correlations'][group] = correlations
        correlation_results['statistics'][group] = p_values
        
        # Add summary statistics
        correlation_results['summary'][group] = {
            'strongest_correlation': correlations.abs().max().max() if not correlations.isna().all().all() else None,
            'strongest_pair': (
                correlations.abs().max(axis=1).idxmax() if not correlations.abs().max(axis=1).isna().all() else None,
                correlations.abs().max(axis=0).idxmax() if not correlations.abs().max(axis=0).isna().all() else None
            ),
            'sample_size': len(group_data)
        }
    
    return correlation_results

def create_monthly_biometric_summaries(df):
    """Create monthly summaries of biometric data for each group"""
    # Add month and year columns for alignment with productivity data
    df = df.copy()  # Create copy to avoid modifying original
    df['month'] = df['local_time'].dt.month
    df['year'] = df['local_time'].dt.year
    
    # Create monthly summaries
    monthly_summaries = df.groupby(['year', 'month', 'standardized_group']).agg({
        'stress_score': ['mean', 'std', 'median'],
        'heart_rate': ['mean', 'std'],
        'user_id': 'nunique'  # Track participation
    }).reset_index()
    
    # Flatten column names and remove the trailing underscore
    monthly_summaries.columns = [
        '_'.join(col).strip('_') if isinstance(col, tuple) else col 
        for col in monthly_summaries.columns
    ]
    
    return monthly_summaries

def analyze_productive_periods(biometric_df, cask_df, metric='receipts', threshold_percentile=75):
    """Identify high productivity periods and analyze corresponding biometric patterns"""
    # Ensure we have year and month columns in biometric_df
    biometric_df = biometric_df.copy()
    biometric_df['year'] = biometric_df['local_time'].dt.year
    biometric_df['month'] = biometric_df['local_time'].dt.month
    
    # Calculate productivity thresholds for each group
    high_prod_thresholds = cask_df.groupby('site')[metric].quantile(threshold_percentile/100)
    
    # Identify high productivity months
    high_prod_months = cask_df[
        cask_df.apply(lambda x: x[metric] >= high_prod_thresholds[x['site']], axis=1)
    ][['year', 'month', 'site']].copy()
    
    # Tag biometric data for high productivity months
    biometric_df['month_key'] = biometric_df.apply(
        lambda x: f"{x['year']}_{x['month']}_{x['standardized_group']}", axis=1
    )
    high_prod_months['month_key'] = high_prod_months.apply(
        lambda x: f"{x['year']}_{x['month']}_{x['site']}", axis=1
    )
    
    biometric_df['is_high_prod'] = biometric_df['month_key'].isin(high_prod_months['month_key'])
    
    return biometric_df

def analyze_time_patterns(df, time_grouping='15min'):
    """Analyze time-of-day patterns, segmented by productivity levels"""
    # Create time block column
    df = df.copy()
    df['time_block'] = df['local_time'].dt.floor(time_grouping)
    df['time_of_day'] = df['time_block'].dt.strftime('%H:%M')
    
    # Analyze patterns for high vs low productivity periods
    time_patterns = df.groupby([
        'standardized_group', 
        'time_of_day',
        'is_high_prod'
    ]).agg({
        'stress_score': ['mean', 'std', 'count'],
        'heart_rate': ['mean', 'std']
    }).reset_index()
    
    # Flatten column names consistently with other functions
    time_patterns.columns = [
        '_'.join(col).strip('_') if isinstance(col, tuple) else col 
        for col in time_patterns.columns
    ]
    
    # Print column names for debugging
    print("\nTime patterns columns:", time_patterns.columns.tolist())
    
    return time_patterns

def calculate_effort_score(activity_dict):
    """Calculate effort score considering all activity levels."""
    total = sum(activity_dict.values())
    if total == 0:
        return 0
        
    # Calculate percentages for each activity level
    intense_pct = (activity_dict['intense'] / total) * 100
    moderate_pct = (activity_dict['moderate'] / total) * 100
    light_pct = (activity_dict['light'] / total) * 100
    sedentary_pct = (activity_dict['sedentary'] / total) * 100
    
    # Calculate weighted score
    score = (intense_pct * 3 + moderate_pct * 2 + light_pct * 1 - sedentary_pct * 2)
    
    # Normalize to 0-100 scale
    # Maximum possible score would be 300 (100% intense)
    # Minimum possible score would be -200 (100% sedentary)
    normalized_score = (score + 200) / 500 * 100
    
    return max(0, min(100, normalized_score))  # Ensure between 0-100

def create_effort_gap_visualization(patterns, cask_df):
    """Create effort gap visualization with both daily and monthly analysis."""
    df = patterns.copy()
    
    # Calculate effort scores and sedentary percentages
    effort_data = []
    for _, row in df.iterrows():
        time = row['time']
        hour = pd.to_datetime(time, format='%H:%M').hour
        total_time = sum(row['activity_level'].values())
        sedentary_pct = (row['activity_level']['sedentary'] / total_time * 100) if total_time > 0 else 0
        
        effort_data.append({
            'time': time,
            'hour': hour,
            'month': row['month'],
            'standardized_group': row['standardized_group'],
            'effort_score': calculate_effort_score(row['activity_level']),
            'sedentary_pct': sedentary_pct,
            'period': 'Morning' if hour < 13 else 'Afternoon'
        })
    
    effort_df = pd.DataFrame(effort_data)
    
    # Calculate period averages for morning and afternoon
    for period in ['Morning', 'Afternoon']:
        period_data = effort_df[effort_df['period'] == period]
        averages = period_data.groupby('standardized_group').agg({
            'effort_score': 'mean',
            'sedentary_pct': 'mean'
        })
        
        print(f"\n{period} Rankings:")
        for i, (group, row) in enumerate(averages.sort_values('effort_score', ascending=False).iterrows(), 1):
            print(f"{i}. {group}: {row['effort_score']:.2f} ({row['sedentary_pct']:.0f}% sedentary)")

    # Calculate daily averages
    daily_averages = effort_df.groupby('standardized_group').agg({
        'effort_score': 'mean',
        'sedentary_pct': 'mean'
    })
    
    print("\nDaily Rankings:")
    for i, (group, row) in enumerate(daily_averages.sort_values('effort_score', ascending=False).iterrows(), 1):
        print(f"{i}. {group}: {row['effort_score']:.2f} ({row['sedentary_pct']:.0f}% sedentary)")

    # Create separate trace collections
    daily_traces = []
    monthly_traces = []
    
    colors = {
        'DALMUIR': '#1f77b4',
        'KB3': '#2ca02c',
        'KILMALID': '#ff7f0e'
    }

    # Create daily effort traces
    for group in ['DALMUIR', 'KILMALID', 'KB3']:
        group_data = effort_df[effort_df['standardized_group'] == group]
        daily_traces.append(
            go.Scatter(
                x=group_data['time'],
                y=group_data['effort_score'],
                name=group,
                line=dict(color=colors[group], width=3),
                mode='lines'
            )
        )

    # Prepare cask data
    cask_monthly = cask_df.copy()
    cask_monthly['period'] = pd.to_datetime(
        cask_monthly['year'].astype(str) + '-' + 
        cask_monthly['month'].astype(str) + '-01'
    ).dt.to_period('M')

    # Calculate monthly effort averages
    monthly_effort = effort_df.groupby(['month', 'standardized_group'])['effort_score'].mean().reset_index()
    monthly_effort['period'] = pd.to_datetime(
        '2024-' + monthly_effort['month'].astype(str) + '-01'
    ).dt.to_period('M')
    monthly_effort = monthly_effort.rename(columns={'standardized_group': 'site'})

    # Merge effort and cask data
    correlation_data = pd.merge(
        monthly_effort,
        cask_monthly[['period', 'site', 'receipts', 'efficiency_ratio']],
        on=['period', 'site'],
        how='inner'  # Only keep months where we have both effort and cask data
    )

    # Create monthly traces
    print("\nCorrelation Analysis Debug:")
    for group in correlation_data['site'].unique():
        group_data = correlation_data[correlation_data['site'] == group]
        print(f"\n{group}:")
        print(f"Number of data points: {len(group_data)}")
        print("Available months:", group_data['period'].tolist())
        if len(group_data) >= 2:
            print("Data points:")
            print(group_data[['period', 'effort_score', 'receipts', 'efficiency_ratio']])
        if not group_data.empty:
            # Sort by period to ensure correct line plotting
            group_data = group_data.sort_values('period')
            
            # Add effort score trace
            monthly_traces.append(
                go.Scatter(
                    x=group_data['period'].astype(str),
                    y=group_data['effort_score'],
                    name=f"{group} - Effort",
                    mode='lines+markers',
                    line=dict(color=colors[group])
                )
            )

            # Add receipt overlay (on secondary y-axis)
            monthly_traces.append(
                go.Scatter(
                    x=group_data['period'].astype(str),
                    y=group_data['receipts'],
                    name=f"{group} - Receipts",
                    mode='lines+markers',
                    line=dict(color=colors[group], dash='dot'),
                    yaxis='y2'
                )
            )

    # Print correlations only where we have sufficient data
    print("\nMonthly Effort-Productivity Analysis:")
    for group in correlation_data['site'].unique():
        group_data = correlation_data[correlation_data['site'] == group]
        if len(group_data) >= 2:  # Need at least 2 points for correlation
            effort_receipt_corr = group_data['effort_score'].corr(group_data['receipts'])
            effort_efficiency_corr = group_data['effort_score'].corr(group_data['efficiency_ratio'])
            
            print(f"\n{group} (Based on {len(group_data)} months of data):")
            print(f"Effort vs Receipts correlation: {effort_receipt_corr:.2f}")
            print(f"Effort vs Efficiency correlation: {effort_efficiency_corr:.2f}")
            
            # Print monthly details
            print("\nMonthly Details:")
            for _, row in group_data.sort_values('period').iterrows():
                print(f"Month {row['period']}: Effort={row['effort_score']:.2f}, Receipts={row['receipts']}")
        else:
            print(f"\n{group}: Insufficient data for correlation analysis")

    return {
        'daily_traces': daily_traces,
        'monthly_traces': monthly_traces
    }

def combine_productivity_biometrics(monthly_biometrics, cask_df):
    """Combine monthly biometric summaries with productivity data"""
    # Print debug info
    print("\nMonthly biometrics head:")
    print(monthly_biometrics.head())
    print("\nMonthly biometrics columns:", monthly_biometrics.columns.tolist())
    
    print("\nCask df head:")
    print(cask_df.head())
    print("\nCask df columns:", cask_df.columns.tolist())
    
    # Ensure consistent group names
    monthly_biometrics = monthly_biometrics.copy()
    cask_df = cask_df.copy()
    
    # Convert all group names to uppercase
    monthly_biometrics['standardized_group'] = monthly_biometrics['standardized_group'].str.upper()
    cask_df['site'] = cask_df['site'].str.upper()
    
    # Merge datasets
    combined_data = pd.merge(
        monthly_biometrics,
        cask_df,
        left_on=['year', 'month', 'standardized_group'],
        right_on=['year', 'month', 'site'],
        how='inner'
    )
    
    print("\nCombined data:")
    print(combined_data.head())
    print("\nNumber of rows in combined data:", len(combined_data))
    print("\nUnique months in combined data:", combined_data[['year', 'month']].drop_duplicates().values.tolist())
    print("\nUnique groups in combined data:", combined_data['standardized_group'].unique())
    
    # Calculate productivity per stress unit
    if 'stress_score_mean' in combined_data.columns:
        stress_col = 'stress_score_mean'
    elif 'stress_score' in combined_data.columns:
        stress_col = 'stress_score'
    else:
        print("Warning: No stress score column found in combined data")
        stress_col = None
        
    if stress_col:
        combined_data['productivity_stress_ratio'] = combined_data['receipts'] / combined_data[stress_col]
        print(f"\nUsing {stress_col} for productivity ratio calculation")
    
    return combined_data

def create_layered_analysis(biometric_df, cask_df):
    """Create multi-level analysis of productivity and biometrics"""
    
    print("Creating monthly summaries...")
    print("Biometric df columns:", biometric_df.columns.tolist())
    
    # 1. Create monthly summaries
    monthly_summaries = create_monthly_biometric_summaries(biometric_df)
    print("Monthly summaries columns:", monthly_summaries.columns.tolist())
    
    print("\nCask df columns:", cask_df.columns.tolist())
    print("\nCask df head:")
    print(cask_df.head())
    
    # 2. Combine with productivity data
    monthly_combined = combine_productivity_biometrics(monthly_summaries, cask_df)
    
    # 3. Identify high productivity periods
    biometric_df_tagged = analyze_productive_periods(biometric_df, cask_df)
    
    # 4. Analyze time patterns
    time_patterns = analyze_time_patterns(biometric_df_tagged)
    
    # 5. Calculate daily patterns
    daily_patterns = analyze_time_patterns(biometric_df_tagged, 'D')
    
    return {
        'monthly_data': monthly_combined,
        'time_patterns': time_patterns,
        'daily_patterns': daily_patterns,
        'biometric_data_tagged': biometric_df_tagged
    }