import pandas as pd
import numpy as np
from collections import defaultdict
import networkx as nx
from ..config.settings import ACTIVITY_THRESHOLDS

def analyze_activity_distribution(df, baselines):
    """Analyze activity level distributions for each group."""
    activity_stats = {}
    
    for group in df['standardized_group'].unique():
        group_data = df[df['standardized_group'] == group]
        
        # Calculate activity levels based on heart rate reserve
        activity_levels = defaultdict(int)
        hourly_activity = defaultdict(lambda: defaultdict(int))
        total_records = len(group_data)
        
        for _, row in group_data.iterrows():
            # Get baseline values for this user
            user_baseline = baselines.get(row['user_id'])
            if user_baseline:
                resting_hr = user_baseline['resting_hr']
                hr_reserve = user_baseline['hr_reserve']
                
                hr_reserve_used = (row['heart_rate'] - resting_hr) / hr_reserve
                hour = row['local_time'].hour
                
                # Determine activity level
                if hr_reserve_used <= ACTIVITY_THRESHOLDS['sedentary']/100:
                    activity_level = 'sedentary'
                elif hr_reserve_used <= ACTIVITY_THRESHOLDS['light']/100:
                    activity_level = 'light'
                elif hr_reserve_used <= ACTIVITY_THRESHOLDS['moderate']/100:
                    activity_level = 'moderate'
                else:
                    activity_level = 'intense'
                
                activity_levels[activity_level] += 1
                hourly_activity[hour][activity_level] += 1
        
        # Convert overall distributions to percentages
        activity_distribution = {
            level: (count/total_records)*100 
            for level, count in activity_levels.items()
        }
        
        # Create hourly distribution DataFrame
        hourly_data = []
        for hour in range(24):
            hour_total = sum(hourly_activity[hour].values())
            if hour_total > 0:
                hour_dist = {
                    level: (count/hour_total)*100 
                    for level, count in hourly_activity[hour].items()
                }
                hour_dist['hour'] = hour
                hourly_data.append(hour_dist)
        
        hourly_distribution = pd.DataFrame(hourly_data)
        if not hourly_distribution.empty:
            hourly_distribution.set_index('hour', inplace=True)
        
        activity_stats[group] = {
            'overall_distribution': activity_distribution,
            'hourly_distribution': hourly_distribution,
            'total_samples': total_records
        }
    
    return activity_stats

def calculate_transition_probabilities(df, baselines):
    """Calculate transition probabilities between activity levels."""
    transition_matrices = {}
    
    for group in df['standardized_group'].unique():
        group_data = df[df['standardized_group'] == group].copy()
        group_data = group_data.sort_values(['user_id', 'local_time'])
        
        # Calculate activity levels
        activity_levels = []
        for _, row in group_data.iterrows():
            user_baseline = baselines.get(row['user_id'])
            if user_baseline:
                resting_hr = user_baseline['resting_hr']
                hr_reserve = user_baseline['hr_reserve']
                
                hr_reserve_used = (row['heart_rate'] - resting_hr) / hr_reserve
                
                if hr_reserve_used <= ACTIVITY_THRESHOLDS['sedentary']/100:
                    activity_levels.append('sedentary')
                elif hr_reserve_used <= ACTIVITY_THRESHOLDS['light']/100:
                    activity_levels.append('light')
                elif hr_reserve_used <= ACTIVITY_THRESHOLDS['moderate']/100:
                    activity_levels.append('moderate')
                else:
                    activity_levels.append('intense')
            else:
                activity_levels.append('unknown')
        
        group_data['activity_level'] = activity_levels
        group_data['next_activity'] = group_data.groupby('user_id')['activity_level'].shift(-1)
        
        # Remove rows with unknown activity levels or transitions
        group_data = group_data.dropna(subset=['activity_level', 'next_activity'])
        group_data = group_data[group_data['activity_level'] != 'unknown']
        group_data = group_data[group_data['next_activity'] != 'unknown']
        
        # Create transition matrix
        transitions = pd.crosstab(
            group_data['activity_level'],
            group_data['next_activity'],
            normalize='index'
        )
        
        # Calculate Markov chain properties
        markov_chain = nx.DiGraph(transitions.values)
        
        # Calculate steady state and duration only if we have transitions
        if not transitions.empty:
            steady_state = calculate_steady_state(transitions)
            avg_duration = calculate_average_duration(transitions)
        else:
            steady_state = pd.Series([], index=[])
            avg_duration = pd.Series([], index=[])
        
        transition_matrices[group] = {
            'matrix': transitions,
            'steady_state': steady_state,
            'average_duration': avg_duration
        }
    
    return transition_matrices

def calculate_steady_state(transition_matrix):
    """Calculate steady state probabilities for activity levels."""
    eigenvals, eigenvects = np.linalg.eig(transition_matrix.T)
    steady_state = eigenvects[:, np.argmax(eigenvals)].real
    steady_state = steady_state / steady_state.sum()
    
    return pd.Series(
        steady_state, 
        index=transition_matrix.columns
    )

def calculate_average_duration(transition_matrix):
    """Calculate average duration in each activity level."""
    # Probability of staying in same state
    stay_probs = np.diag(transition_matrix)
    
    # Average duration = 1/(1-p) where p is probability of staying
    durations = 1/(1-stay_probs)
    
    return pd.Series(
        durations, 
        index=transition_matrix.columns
    )