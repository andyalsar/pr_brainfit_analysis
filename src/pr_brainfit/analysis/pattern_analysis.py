import pandas as pd
import numpy as np
from scipy import signal
from ..config.settings import *

def analyze_daily_patterns(df):
    """Analyze patterns across days of the week."""
    # Add day of week
    df = df.copy() 
    df['day_of_week'] = df['local_time'].dt.day_name()
    
    patterns = {
        'daily_means': {},
        'daily_variance': {},
        'peak_times': {},
        'weekly_trends': {}
    }
    
    for group in df['standardized_group'].unique():
        group_data = df[df['standardized_group'] == group].copy()
        
        # Calculate daily means and variance
        daily_stats = group_data.groupby('day_of_week').agg({
            'stress_score': ['mean', 'std', 'count'],
            'heart_rate': ['mean', 'std']
        })
        
        patterns['daily_means'][group] = daily_stats['stress_score']['mean']
        patterns['daily_variance'][group] = daily_stats['stress_score']['std']
        
        # Calculate rolling statistics
        group_data['rolling_mean'] = group_data.groupby('user_id')['stress_score'].transform(
            lambda x: x.rolling(window=12, min_periods=1).mean()  # 1-hour window (12 * 5min)
        )
        
        # Find peaks in stress patterns
        peaks, _ = signal.find_peaks(
            group_data.groupby('day_of_week')['stress_score'].mean(),
            distance=6  # Minimum 30 minutes between peaks
        )
        
        patterns['peak_times'][group] = peaks
        
        # Calculate weekly trends
        patterns['weekly_trends'][group] = group_data.groupby(
            [group_data['local_time'].dt.isocalendar().week, 'day_of_week']
        )['stress_score'].mean().unstack()
    
    return patterns

def calculate_group_variance(df):
    """Calculate variance scores within groups."""
    variance_scores = {}
    
    for group in df['standardized_group'].unique():
        group_data = df[df['standardized_group'] == group]
        
        # Calculate within-day variance
        within_day = group_data.groupby(['date', 'user_id'])['stress_score'].std().mean()
        
        # Calculate between-day variance
        between_day = group_data.groupby('date')['stress_score'].mean().std()
        
        # Calculate user-to-user variance
        user_variance = group_data.groupby('user_id')['stress_score'].mean().std()
        
        variance_scores[group] = {
            'within_day_variance': within_day,
            'between_day_variance': between_day,
            'user_variance': user_variance,
            'total_variance': group_data['stress_score'].std()
        }
    
    return variance_scores

def find_recurring_patterns(df, window_size=12):  # 1-hour window
    """Identify recurring patterns in stress scores."""
    patterns = {}
    
    for group in df['standardized_group'].unique():
        group_data = df[df['standardized_group'] == group]
        
        # Calculate autocorrelation
        autocorr = pd.Series(
            [group_data['stress_score'].autocorr(lag=i) for i in range(1, 49)]  # 4-hour span
        )
        
        # Find peaks in autocorrelation
        peaks, properties = signal.find_peaks(
            autocorr,
            height=0.3,  # Minimum correlation
            distance=6   # Minimum 30 minutes between peaks
        )
        
        # Identify common patterns
        rolling_patterns = group_data['stress_score'].rolling(window=window_size).mean()
        pattern_times = rolling_patterns.groupby(
            rolling_patterns.round(1)
        ).size().sort_values(ascending=False)
        
        patterns[group] = {
            'autocorrelation_peaks': peaks,
            'peak_heights': properties['peak_heights'],
            'common_patterns': pattern_times.head(5),
            'pattern_frequency': len(peaks)
        }
    
    return patterns