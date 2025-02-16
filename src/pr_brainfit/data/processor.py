# PR_brainfit_analysis/data/processors.py

import pandas as pd
import numpy as np
from datetime import datetime, time
from ..config.settings import *


def clean_biometric_data(biometric_df, user_df):
    """Clean and prepare biometric data"""
    df = biometric_df.copy()
    
    # Convert timestamp to datetime if not already
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    
    # Add local time columns
    df['local_time'] = df['timestamp'].dt.tz_convert(DEFAULT_TIMEZONE)
    df['hour'] = df['local_time'].dt.hour
    df['date'] = df['local_time'].dt.date
    df['day_of_week'] = df['local_time'].dt.day_name()
    
    # Filter for working hours (8am-5pm) and weekdays
    working_start = time.fromisoformat(WORKING_HOURS['start'])  # 08:00
    working_end = time.fromisoformat(WORKING_HOURS['end'])      # 17:00
    
    df['is_working_hours'] = df['local_time'].apply(
        lambda x: working_start <= x.time() <= working_end
    )
    
    # Filter for only weekdays and working hours
    df = df[
        (df['is_working_hours']) & 
        (df['day_of_week'].isin(['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']))
    ]
    
    # Filter outlier heart rates
    df = df[
        (df['heart_rate'] >= QUALITY_THRESHOLDS['min_hr']) & 
        (df['heart_rate'] <= QUALITY_THRESHOLDS['max_hr'])
    ]
    
    # Merge with user data (which is already filtered for PR org and relevant groups)
    df = df.merge(
        user_df[['user_id', 'age', 'group']],
        on='user_id',
        how='inner'  # Changed to inner join to keep only matched users
    )
    
    # Standardize group names
    def standardize_group(group):
        if pd.isna(group):
            return 'Unknown'
        group = str(group).upper()
        # Simplified mapping for just our three groups
        mapping = {
            'KILMALID': ['KILMALID'],
            'DALMUIR': ['DALMUIR'],
            'KB3': ['KB3', 'NOPS']
        }
        for std_name, variants in mapping.items():
            if group.upper() in variants:
                return std_name
        return 'Other'
    
    df['standardized_group'] = df['group'].apply(standardize_group)
    
    # Final filter to ensure only our three groups remain
    df = df[df['standardized_group'].isin(['KILMALID', 'DALMUIR', 'KB3'])]
    
    # Calculate stress score based purely on heart rate (0-100)
    def calculate_stress_score(row):
        if pd.isna(row['age']):
            max_hr = 180
        else:
            max_hr = 220 - row['age']
            
        stress_score = ((row['heart_rate'] - QUALITY_THRESHOLDS['min_hr']) / 
                       (max_hr - QUALITY_THRESHOLDS['min_hr'])) * 100
                        
        return max(0, min(100, stress_score))  # Ensure within 0-100 range
    
    df['stress_score'] = df.apply(calculate_stress_score, axis=1)
    
    return df
  
def calculate_individual_baselines(df):
    """Calculate baseline metrics for each individual"""
    baselines = {}
    
    for user_id in df['user_id'].unique():
        user_data = df[df['user_id'] == user_id]
        
        # Calculate resting heart rate (5th percentile during working hours)
        resting_hr = user_data[
            user_data['is_working_hours']
        ]['heart_rate'].quantile(STRESS_PARAMS['resting_hr_percentile']/100)
        
        # Calculate max heart rate based on age
        age = user_data['age'].iloc[0]
        if pd.notna(age):
            max_hr = 220 - age
        else:
            max_hr = 180  # Default if age unknown
            
        baselines[user_id] = {
            'resting_hr': resting_hr,
            'max_hr': max_hr,
            'hr_reserve': max_hr - resting_hr
        }
    
    return baselines