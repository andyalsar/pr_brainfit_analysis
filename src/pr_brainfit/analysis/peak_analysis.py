import pandas as pd
import numpy as np
from scipy import signal
from datetime import timedelta

def detect_peaks(df, prominence=20, width=5):
    """Detect stress score peaks and analyze their characteristics."""
    peaks_data = {}
    
    for group in df['standardized_group'].unique():
        group_data = df[df['standardized_group'] == group]
        group_peaks = []
        
        for user_id in group_data['user_id'].unique():
            user_data = group_data[group_data['user_id'] == user_id].copy()
            user_data = user_data.sort_values('local_time')
            
            # Find peaks
            peaks, properties = signal.find_peaks(
                user_data['stress_score'],
                prominence=prominence,
                width=width
            )
            
            for idx, peak in enumerate(peaks):
                peak_time = user_data.iloc[peak]['local_time']
                
                # Calculate recovery time
                recovery_end = find_recovery_end(
                    user_data.iloc[peak:],
                    user_data.iloc[peak]['stress_score']
                )
                
                group_peaks.append({
                    'user_id': user_id,
                    'peak_time': peak_time,
                    'peak_value': user_data.iloc[peak]['stress_score'],
                    'prominence': properties['prominences'][idx],
                    'width': properties['widths'][idx],
                    'recovery_time': recovery_end - peak_time if recovery_end else None
                })
        
        peaks_data[group] = pd.DataFrame(group_peaks)
    
    return peaks_data

def find_recovery_end(data, peak_value):
    """Find when stress returns to normal after a peak."""
    baseline = data['stress_score'].mean()
    threshold = baseline + (peak_value - baseline) * 0.2  # 80% recovery
    
    recovery_data = data[data['stress_score'] <= threshold]
    if len(recovery_data) > 0:
        return recovery_data.iloc[0]['local_time']
    return None

def analyze_peak_patterns(peaks_dict):
    """Analyze patterns in peak occurrence and characteristics."""
    patterns = {}
    
    for group, peaks_df in peaks_dict.items():
        if len(peaks_df) == 0:
            continue
            
        patterns[group] = {
            'average_peak_value': peaks_df['peak_value'].mean(),
            'peak_frequency': len(peaks_df) / peaks_df['user_id'].nunique(),
            'average_recovery': peaks_df['recovery_time'].mean(),
            'peak_distribution': peaks_df['peak_time'].dt.hour.value_counts(),
            'typical_prominence': peaks_df['prominence'].mean(),
            'recovery_distribution': peaks_df['recovery_time'].describe()
        }
    
    return patterns

def calculate_recovery_metrics(peaks_dict):
    """Calculate detailed recovery metrics for each group."""
    recovery_metrics = {}
    
    for group, peaks_df in peaks_dict.items():
        if len(peaks_df) == 0:
            continue
        
        # Filter valid recovery times
        valid_recoveries = peaks_df.dropna(subset=['recovery_time'])
        
        recovery_metrics[group] = {
            'median_recovery': valid_recoveries['recovery_time'].median(),
            'recovery_variability': valid_recoveries['recovery_time'].std(),
            'recovery_success_rate': len(valid_recoveries) / len(peaks_df) * 100,
            'recovery_by_time': valid_recoveries.groupby(
                valid_recoveries['peak_time'].dt.hour
            )['recovery_time'].mean()
        }
    
    return recovery_metrics