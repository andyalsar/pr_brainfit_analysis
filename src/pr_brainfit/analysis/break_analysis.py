import pandas as pd
import numpy as np
from scipy import signal
import scipy

def detect_breaks(df, threshold_duration=10, stress_drop=20):
    """Detect breaks based on sustained drops in stress score."""
    breaks = {}
    
    for group in df['standardized_group'].unique():
        group_data = df[df['standardized_group'] == group]
        group_breaks = []
        
        for user_id in group_data['user_id'].unique():
            user_data = group_data[group_data['user_id'] == user_id].copy()
            user_data = user_data.sort_values('local_time')
            
            # Calculate rolling mean to smooth data
            user_data['smooth_stress'] = user_data['stress_score'].rolling(
                window=5, min_periods=1
            ).mean()
            
            # Find significant drops
            user_data['stress_drop'] = user_data['smooth_stress'].diff()
            
            # Identify break periods
            in_break = False
            break_start = None
            
            for idx, row in user_data.iterrows():
                if not in_break and row['stress_drop'] < -stress_drop:
                    break_start = row['local_time']
                    in_break = True
                elif in_break and row['stress_drop'] > stress_drop:
                    break_duration = (row['local_time'] - break_start).total_seconds() / 60
                    if break_duration >= threshold_duration:
                        group_breaks.append({
                            'user_id': user_id,
                            'start_time': break_start,
                            'end_time': row['local_time'],
                            'duration': break_duration,
                            'stress_reduction': user_data[
                                (user_data['local_time'] >= break_start) &
                                (user_data['local_time'] <= row['local_time'])
                            ]['stress_score'].mean()
                        })
                    in_break = False
        
        breaks[group] = pd.DataFrame(group_breaks)
    
    return breaks

def analyze_break_patterns(breaks_dict):
    """Analyze patterns in break timing and duration."""
    patterns = {}
    
    for group, breaks_df in breaks_dict.items():
        if len(breaks_df) == 0:
            continue
            
        # Convert times to hour of day
        breaks_df['hour'] = breaks_df['start_time'].dt.hour
        
        patterns[group] = {
            'average_duration': breaks_df['duration'].mean(),
            'break_frequency': len(breaks_df) / breaks_df['user_id'].nunique(),
            'common_times': breaks_df['hour'].value_counts().head(3),
            'stress_reduction': breaks_df['stress_reduction'].mean(),
            'duration_distribution': breaks_df['duration'].describe()
        }
    
    return patterns

def compare_group_breaks(breaks_dict):
    """Compare break patterns between groups."""
    comparisons = {}
    
    # Extract key metrics for each group
    metrics = {
        group: {
            'durations': breaks_df['duration'],
            'times': breaks_df['start_time'].dt.hour,
            'reductions': breaks_df['stress_reduction']
        }
        for group, breaks_df in breaks_dict.items()
        if len(breaks_df) > 0
    }
    
    # Perform statistical comparisons
    groups = list(metrics.keys())
    for i in range(len(groups)):
        for j in range(i + 1, len(groups)):
            # Compare break durations
            stat, p_val = scipy.stats.mannwhitneyu(
                metrics[groups[i]]['durations'],
                metrics[groups[j]]['durations']
            )
            
            comparisons[f'{groups[i]}_vs_{groups[j]}'] = {
                'duration_difference': stat,
                'p_value': p_val,
                'effect_size': stat / np.sqrt(
                    len(metrics[groups[i]]['durations']) * 
                    len(metrics[groups[j]]['durations'])
                )
            }
    
    return comparisons